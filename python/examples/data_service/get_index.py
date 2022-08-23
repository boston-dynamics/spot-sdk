# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the Boston Dynamics API"""
from __future__ import print_function

import argparse
import sys

import bosdyn.api.data_index_pb2 as data_index_protos
import bosdyn.client
import bosdyn.client.util
from bosdyn.client.data_service import DataServiceClient
from bosdyn.client.time_sync import (NotEstablishedError, TimeSyncClient, TimeSyncEndpoint,
                                     timespec_to_robot_timespan)


def run_query(options, query):
    """Get data index from robot"""

    bosdyn.client.util.setup_logging(options.verbose)
    sdk = bosdyn.client.create_standard_sdk('GetIndexClient')
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

    # Now assemble the query to obtain a bddf file.

    # Get the parameters for limiting the timespan of the response.
    # pylint: disable=no-member
    query.time_range.CopyFrom(timespec_to_robot_timespan(options.timespan, time_sync_endpoint))
    return service_client.get_data_index(query)


def get_blobs(options):
    """Get pages with message blobs from robot"""
    query = data_index_protos.DataQuery()
    # pylint: disable=no-member
    blobspec = query.blobs.add()
    if options.channel:
        blobspec.channel = options.channel
    if options.message_type:
        blobspec.message_type = options.message_type
    print(run_query(options, query))


def get_text(options):
    """Get pages with text-messages from robot"""
    query = data_index_protos.DataQuery()
    query.text_messages = True
    print(run_query(options, query))


def get_events(options):
    """Get pages with events from robot"""
    query = data_index_protos.DataQuery()
    query.events = True
    print(run_query(options, query))


def get_comments(options):
    """Get pages with operator comments from robot"""
    query = data_index_protos.DataQuery()
    query.comments = True
    print(run_query(options, query))


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)

    def _add_common_args(subparser):
        subparser.add_argument('-T', '--timespan', default='5m',
                               help='Time span (default last 5 minutes)')
        subparser.add_argument('-R', '--robot-time', action='store_true',
                               help='Specified timespan is in robot time')

    subparsers = parser.add_subparsers(help='commands', dest='command')
    blob_parser = subparsers.add_parser('blob', help='Get blob pages')
    _add_common_args(blob_parser)
    blob_parser.add_argument('--message-type', help='limit to message-type')
    blob_parser.add_argument('--channel', help='limit to channel')

    text_parser = subparsers.add_parser('text', help='Get text-message pages')
    _add_common_args(text_parser)
    event_parser = subparsers.add_parser('event', help='Get event pages')
    _add_common_args(event_parser)
    comment_parser = subparsers.add_parser('comment', help='Get operator-comment pages')
    _add_common_args(comment_parser)

    options = parser.parse_args(argv)
    print(options)

    try:
        if options.command == 'blob':
            get_blobs(options)
        elif options.command == 'text':
            get_text(options)
        elif options.command == 'event':
            get_events(options)
        elif options.command == 'comment':
            get_comments(options)
        else:
            parser.print_help()
            sys.exit(1)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.error("get_index threw an exception: %s", exc)
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
