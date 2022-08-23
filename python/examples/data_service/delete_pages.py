# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the Boston Dynamics API"""
from __future__ import print_function

import argparse
import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.data_service import DataServiceClient
from bosdyn.client.time_sync import (NotEstablishedError, TimeSyncClient, TimeSyncEndpoint,
                                     timespec_to_robot_timespan)


def delete_pages(config):
    """Delete data pages from robot"""

    bosdyn.client.util.setup_logging(config.verbose)
    sdk = bosdyn.client.create_standard_sdk('DeletePagesClient')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    service_client = robot.ensure_client(DataServiceClient.default_service_name)

    start_timestamp = None
    end_timestamp = None
    time_range = None

    time_sync_endpoint = None
    if not config.robot_time:
        # Establish time sync with robot to obtain skew.
        time_sync_client = robot.ensure_client(TimeSyncClient.default_service_name)
        time_sync_endpoint = TimeSyncEndpoint(time_sync_client)
        if not time_sync_endpoint.establish_timesync():
            raise NotEstablishedError("time sync not established")

    if config.timespan:
        time_range = timespec_to_robot_timespan(config.timespan, time_sync_endpoint)

    print(service_client.delete_data_pages(time_range, config.id))


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('-T', '--timespan', default='5m', help='Time span (default last 5 minutes)')
    parser.add_argument('-R', '--robot-time', action='store_true',
                        help='Specified timespan is in robot time')
    parser.add_argument("--id", nargs="+", help="delete pages by page id")

    options = parser.parse_args(argv)
    try:
        delete_pages(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.error("delete_pages threw an exception: %r", exc)
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
