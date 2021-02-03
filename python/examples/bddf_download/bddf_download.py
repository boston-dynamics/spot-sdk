# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""This example shows how to download a bddf log file from the on-robot https server."""
import datetime
import logging
import re
import sys
import time

import requests
from urllib3.exceptions import InsecureRequestWarning

from bosdyn.client import create_standard_sdk, RpcError
from bosdyn.client.time_sync import TimeSyncEndpoint, TimeSyncClient
import bosdyn.client.util

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

LOGGER = logging.getLogger()

REQUEST_CHUNK_SIZE = 10 * (1024**2)  # This value is not guaranteed.

DEFAULT_OUTPUT = "./download.bddf"


def _before_now(strval, delta_t):
    now = datetime.datetime.now()
    val = int(strval)
    return now - val * delta_t


_TIME_FORMATS = (
    (re.compile(r'^\d{8}_\d{6}$'), lambda val: datetime.datetime.strptime(val, '%Y%m%d_%H%M%S')),
    (re.compile(r'^\d{8}$'), lambda val: datetime.datetime.strptime(val, '%Y%m%d')),
    (re.compile(r'^\d+[hH]$'), lambda val: _before_now(val[:-1], datetime.timedelta(hours=1))),
    (re.compile(r'^\d+s$'), lambda val: _before_now(val[:-1], datetime.timedelta(seconds=1))),
    (re.compile(r'^\d+m$'), lambda val: _before_now(val[:-1], datetime.timedelta(minutes=1))),
    (re.compile(r'^\d+d$'), lambda val: _before_now(val[:-1], datetime.timedelta(days=1))),
    (re.compile(r'^\d{10}?$'), lambda val: datetime.datetime.fromtimestamp(int(val))),
    (re.compile(r'^\d{10}(\.\d{0-9)?$'), lambda val: datetime.datetime.fromtimestamp(float(val))),
    (re.compile(r'^\d{19}$'), lambda val: datetime.datetime.fromtimestamp(int(1e-9 * int(val)))),
)


class DatetimeParseError(Exception):
    """Failed to parse any datetime formats known to parse_datetime()"""


def _print_help_timespan():
    print("""\
A timespan is {val} or {val}-{val} where:

{val} has one of these formats:
 - yyyymmdd_hhmmss  (e.g., 20200120_120000)
 - yyyymmdd         (e.g., 20200120)
 -  {n}d    {n} days ago
 -  {n}h    {n} hours ago
 -  {n}m    {n} minutes ago
 -  {n}s    {n} seconds ago
 - nnnnnnnnnn[.nn]       (e.g., 1581869515.256)  Seconds since epoch
 - nnnnnnnnnnnnnnnnnnnn  Nanoseconds since epoch

For example:
  '5m'                    From 5 minutes ago until now.
  '20201107-20201108'     All of 2020/11/07.
""")


def parse_datetime(val):
    """Parse datetime from string

    Args:
     val: string with format like as described by TIME_FORMAT_DESC.

    Returns: datetime.datetime.

    Raises: DatetimeParseError if format of val is not recognized.
    """
    for fmt, function in _TIME_FORMATS:
        if fmt.match(val):
            return function(val)
    raise DatetimeParseError("Could not parse time from '{}'".format(val))


def request_timespan(time_spec, time_sync_endpoint):
    """Requests last 5 minutes of all logs."""
    now = time.time()
    if not time_spec:
        start_time = now - 5 * 60
        end_time = now
    else:
        dash_idx = time_spec.find('-')
        if dash_idx < 0:
            start_time = parse_datetime(time_spec).timestamp()
            end_time = now
        else:
            start_time = parse_datetime(time_spec[0:dash_idx]).timestamp()
            end_time = parse_datetime(time_spec[dash_idx + 1:]).timestamp()

    skew = time_sync_endpoint.clock_skew.seconds + 1e-9 * time_sync_endpoint.clock_skew.nanos

    def _time_str(timeval):
        return str(int(timeval + skew))

    return {"from_sec": str(_time_str(start_time)), "to_sec": str(_time_str(end_time))}


def output_filename(options, response):
    """Get output filename either from command line options or http response, or default value."""
    if options.output:
        return options.output
    content = response.headers['Content-Disposition']
    if len(content) < 2:
        LOGGER.debug("Content-Disposition not set correctly.")
        return DEFAULT_OUTPUT
    match = re.search(r'filename=\"?([^\"]+)', content)
    if not match:
        return DEFAULT_OUTPUT
    return match.group(1)


def main():  # pylint: disable=too-many-locals
    """Command-line interface"""
    import argparse  # pylint: disable=import-outside-toplevel
    parser = argparse.ArgumentParser()
    parser.add_argument('-T', '--timespan', help='Time span (default last 5 minutes)')
    parser.add_argument('--help-timespan', action='store_true',
                        help='Print time span formatting options')
    parser.add_argument('-c', '--channel', help='Specify channel for data (default=all)')
    parser.add_argument('-t', '--type', help='Specify message type (default=all)')
    parser.add_argument('-s', '--service', help='Specify service name (default=all)')
    parser.add_argument('-o', '--output', help='Output file name (default is "download.bddf"')

    bosdyn.client.util.add_common_arguments(parser)
    options = parser.parse_args()

    if options.verbose:
        LOGGER.setLevel(logging.DEBUG)

    if options.help_timespan:
        _print_help_timespan()
        return 0

    # Create a robot object.
    sdk = create_standard_sdk('bddf')
    robot = sdk.create_robot(options.hostname)

    # Use the robot object to authenticate to the robot.
    # A JWT Token is required to download log data.
    try:
        robot.authenticate(options.username, options.password)
    except RpcError as err:
        LOGGER.error("Cannot authenticate to robot to obtain token: %s", err)
        return 1

    # Establish time sync with robot to obtain skew.
    time_sync_client = robot.ensure_client(TimeSyncClient.default_service_name)
    time_sync_endpoint = TimeSyncEndpoint(time_sync_client)
    did_establish = time_sync_endpoint.establish_timesync()
    if did_establish:
        LOGGER.debug("Established timesync, skew of sec:%d nanosec:%d",
                     time_sync_endpoint.clock_skew.seconds, time_sync_endpoint.clock_skew.nanos)

    # Now assemble the query to obtain a bddf file.
    url = 'https://{}/v1/data-buffer/bddf/'.format(options.hostname)
    headers = {"Authorization": "Bearer {}".format(robot.user_token)}

    # Get the parameters for limiting the timespan of the response.
    get_params = request_timespan(options.timespan, time_sync_endpoint)

    # Optional parameters for limiting the messages
    if options.channel:
        get_params['channel'] = options.channel
    if options.type:
        get_params['type'] = options.type
    if options.service:
        get_params['grpc_service'] = options.service

    # Request the data.
    with requests.get(url, headers=headers, verify=False, stream=True, params=get_params) as resp:
        if resp.status_code != 200:
            LOGGER.error("https response: %d", resp.status_code)
            sys.exit(1)
        outfile = output_filename(options, resp)
        with open(outfile, 'wb') as fid:
            for chunk in resp.iter_content(chunk_size=REQUEST_CHUNK_SIZE):
                print('.', end='', flush=True)
                fid.write(chunk)
        print()

    LOGGER.info("Wrote '%s'.", outfile)
    return 0


if __name__ == "__main__":
    sys.exit(main())
