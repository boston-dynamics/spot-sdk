# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the Boston Dynamics API"""
from __future__ import print_function
import argparse
import sys

from google.protobuf.timestamp_pb2 import Timestamp
import bosdyn.api.data_index_pb2 as data_index_protos
from bosdyn.api.time_range_pb2 import TimeRange
import bosdyn.client
from bosdyn.client.data_service import DataServiceClient
import bosdyn.client.util


def delete_pages(config):
    """Delete data pages from robot"""

    bosdyn.client.util.setup_logging(config.verbose)
    sdk = bosdyn.client.create_standard_sdk('DeletePagesClient')
    robot = sdk.create_robot(config.hostname)
    robot.authenticate(config.username, config.password)
    service_client = robot.ensure_client(DataServiceClient.default_service_name)

    start_timestamp = None
    end_timestamp = None
    time_range = None

    if config.start:
        start_timestamp = Timestamp()
        start_timestamp.FromJsonString(config.start)
    if config.end:
        end_timestamp = Timestamp()
        end_timestamp.FromJsonString(config.end)

    if end_timestamp or start_timestamp:
        time_range = TimeRange(start=start_timestamp, end=end_timestamp)

    print(service_client.delete_data_pages(time_range, config.id))


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument(
        "--start", help="delete pages after this time (in RFC3339 format: YYYY-MM-DDTHH:MM:SSTZ)")
    parser.add_argument(
        "--end", help="delete pages before this time (in RFC3339 format: YYYY-MM-DDTHH:MM:SSTZ)")

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
