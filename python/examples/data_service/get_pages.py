# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the Boston Dynamics API"""
from __future__ import print_function

import argparse
import datetime
import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.data_service import DataServiceClient
from bosdyn.client.time_sync import (NotEstablishedError, TimeSyncClient, TimeSyncEndpoint,
                                     timespec_to_robot_timespan)


def _timestamp_to_str(timestamp, first_timestamp=None):

    def _ts_to_dt(tstamp):
        return datetime.datetime.fromtimestamp(tstamp.seconds + 1e-9 * tstamp.nanos)

    this_dt = _ts_to_dt(timestamp)
    show_date = True
    if first_timestamp:
        first_dt = _ts_to_dt(first_timestamp)
        show_date = (this_dt.date() != first_dt.date())
    return str(this_dt if show_date else this_dt.time())


def _show_page(page):
    start_str = _timestamp_to_str(page.time_range.start)
    end_str = _timestamp_to_str(page.time_range.end, page.time_range.start)
    is_open = " (open)" if page.is_open else ""
    print("{}\n    {} - {} ({})\n    {} ticks {} bytes  {} {}{}\n    {}\n".format(
        page.id, start_str, end_str, page.source, page.num_ticks, page.total_bytes,
        page.PageFormat.Name(page.format), page.Compression.Name(page.compression), is_open,
        page.path))


def get_pages(options):
    """Get data pages from robot"""

    bosdyn.client.util.setup_logging(options.verbose)
    sdk = bosdyn.client.create_standard_sdk('GetPagesClient')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    service_client = robot.ensure_client(DataServiceClient.default_service_name)

    time_sync_endpoint = None
    if not options.robot_time:
        # Establish time sync with robot to obtain skew.
        time_sync_client = robot.ensure_client(TimeSyncClient.default_service_name)
        time_sync_endpoint = TimeSyncEndpoint(time_sync_client)
        if not time_sync_endpoint.establish_timesync():
            raise NotEstablishedError("time sync not established")

    resp = service_client.get_data_pages(
        timespec_to_robot_timespan(options.timespan, time_sync_endpoint))
    print("-------- {} pages --------\n".format(len(resp.pages)))
    for page in resp.pages:
        _show_page(page)


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('-T', '--timespan', default='5m', help='Time span (default last 5 minutes)')
    parser.add_argument('-R', '--robot-time', action='store_true',
                        help='Specified timespan is in robot time')
    options = parser.parse_args(argv)

    try:
        get_pages(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.error("get_pages threw an exception: %r", exc)
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
