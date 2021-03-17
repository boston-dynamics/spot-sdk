# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Code for downloading robot data in bddf format."""
import logging
import re
import sys

import requests
from urllib3.exceptions import InsecureRequestWarning

from bosdyn.client.time_sync import (TimeSyncEndpoint, TimeSyncClient, NotEstablishedError,
                                     robot_time_range_from_nanoseconds, timespec_to_robot_timespan)
from bosdyn.util import TIME_FORMAT_DESC

LOGGER = logging.getLogger()

REQUEST_CHUNK_SIZE = 10 * (1024**2)  # This value is not guaranteed.

DEFAULT_OUTPUT = "./download.bddf"


def _print_help_timespan():
    print("""\
A timespan is {{timeval}} or {{timeval}}-{{timeval}}.

{}

For example:
  '5m'                    From 5 minutes ago until now.
  '20201107-20201108'     All of 2020/11/07.
""".format(TIME_FORMAT_DESC))


def _bddf_url(hostname):
    return 'https://{}/v1/data-buffer/bddf/'.format(hostname)


def _http_headers(robot):
    return {"Authorization": "Bearer {}".format(robot.user_token)}


def _request_timespan_from_time_range(time_range):
    ret = {}
    # pylint: disable=no-member
    if time_range.HasField('start'):
        ret['from_sec'] = str(time_range.start.seconds)
    if time_range.HasField('end'):
        ret['to_sec'] = str(time_range.end.seconds)
    return ret


def _request_timespan_from_spec(timespec, time_sync_endpoint):
    return _request_timespan_from_time_range(
        timespec_to_robot_timespan(timespec, time_sync_endpoint))


def _request_timespan_from_nanoseconds(start_nsec, end_nsec, time_sync_endpoint):
    return _request_timespan_from_time_range(
        robot_time_range_from_nanoseconds(start_nsec, end_nsec, time_sync_endpoint))


def download_data(  # pylint: disable=too-many-arguments,too-many-locals
        robot, hostname, start_nsec=None, end_nsec=None, timespan_spec=None, output_filename=None,
        robot_time=False, channel=None, message_type=None, grpc_service=None, show_progress=False):
    """
    Download data from robot in bddf format

    Args:
      robot           API robot object
      hostname        hostname/ip-address of robot
      start_nsec      start time of log
      end_nsec        end time of log
      timespan_spec   if start_time, end_time are None, string representing the timespan to download
      robot_time      if True, timespan is in robot_clock, if False, in host clock
      channel         if set, limit data to download to a specific channel
      message_type    if set, limit data by specified message-type
      grpc_service    if set, limit GRPC log data by name of service

    Returns:
      output filename, or None on error
    """
    # pylint: disable=no-member
    # Suppress only the single warning from urllib3 needed.
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    # pylint: enable=no-member

    time_sync_endpoint = None
    if not robot_time:
        # Establish time sync with robot to obtain skew.
        time_sync_client = robot.ensure_client(TimeSyncClient.default_service_name)
        time_sync_endpoint = TimeSyncEndpoint(time_sync_client)
        if not time_sync_endpoint.establish_timesync():
            raise NotEstablishedError("time sync not established")

    # Now assemble the query to obtain a bddf file.

    # Get the parameters for limiting the timespan of the response.
    if start_nsec or end_nsec:
        get_params = _request_timespan_from_nanoseconds(start_nsec, end_nsec, time_sync_endpoint)
    else:
        get_params = _request_timespan_from_spec(timespan_spec, time_sync_endpoint)

    # Optional parameters for limiting the messages
    if channel:
        get_params['channel'] = channel
    if message_type:
        get_params['type'] = message_type
    if grpc_service:
        get_params['grpc_service'] = grpc_service

    # Request the data.
    url = _bddf_url(hostname)
    with requests.get(url, headers=_http_headers(robot), verify=False, stream=True,
                      params=get_params) as resp:
        if resp.status_code != 200:
            LOGGER.error("%s %s response: %d", url, get_params, resp.status_code)
            return None

        outfile = output_filename if output_filename else _output_filename(resp)
        with open(outfile, 'wb') as fid:
            for chunk in resp.iter_content(chunk_size=REQUEST_CHUNK_SIZE):
                if show_progress:
                    print('.', end='', flush=True)
                fid.write(chunk)
        if show_progress:
            print()

    return outfile


def _output_filename(response):
    """Get output filename either from http response, or default value."""
    content = response.headers['Content-Disposition']
    if len(content) < 2:
        LOGGER.debug("Content-Disposition not set correctly.")
        return DEFAULT_OUTPUT
    match = re.search(r'filename=\"?([^\"]+)', content)
    if not match:
        return DEFAULT_OUTPUT
    return match.group(1)


def main():
    """Command-line interface"""
    # pylint: disable=import-outside-toplevel
    import argparse
    from bosdyn.client import create_standard_sdk, InvalidLoginError
    from bosdyn.client.util import add_common_arguments

    parser = argparse.ArgumentParser()
    parser.add_argument('-T', '--timespan', default='5m', help='Time span (default last 5 minutes)')
    parser.add_argument('--help-timespan', action='store_true',
                        help='Print time span formatting options')
    parser.add_argument('-c', '--channel', help='Specify channel for data (default=all)')
    parser.add_argument('-t', '--type', help='Specify message type (default=all)')
    parser.add_argument('-s', '--service', help='Specify service name (default=all)')
    parser.add_argument('-o', '--output', help='Output file name (default is "download.bddf"')
    parser.add_argument('-R', '--robot-time', action='store_true',
                        help='Specified timespan is in robot time')

    add_common_arguments(parser)
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
    except InvalidLoginError as err:
        LOGGER.error("Cannot authenticate to robot to obtain token: %s", err)
        return 1

    output_filename = download_data(robot, options.hostname, options.timespan,
                                    robot_time=options.robot_time, channel=options.channel,
                                    message_type=options.type, grpc_service=options.service,
                                    show_progress=True)

    if not output_filename:
        return 1

    LOGGER.info("Wrote '%s'.", output_filename)
    return 0


if __name__ == "__main__":
    sys.exit(main())
