# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
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
from bosdyn.client.data_service import DataServiceClient
import bosdyn.client.util


def run_query(options, query):
    """Get data index from robot"""

    bosdyn.client.util.setup_logging(options.verbose)
    sdk = bosdyn.client.create_standard_sdk('GetIndexClient')
    robot = sdk.create_robot(options.hostname)
    robot.authenticate(options.username, options.password)
    service_client = robot.ensure_client(DataServiceClient.default_service_name)
    return service_client.get_data_index(query)

def get_blobs(options):
    """Get pages with message blobs from robot"""
    query = data_index_protos.DataQuery()
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
    bosdyn.client.util.add_common_arguments(parser)

    subparsers = parser.add_subparsers(help='commands', dest='command')
    blob_parser = subparsers.add_parser('blob', help='Get blob pages')
    blob_parser.add_argument('--message-type', help='limit to message-type')
    blob_parser.add_argument('--channel', help='limit to channel')

    _text_parser = subparsers.add_parser('text', help='Get text-message pages')
    _event_parser = subparsers.add_parser('event', help='Get event pages')
    _comment_parser = subparsers.add_parser('comment', help='Get operator-comment pages')

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
        logger.error("get_index threw an exception: %r", exc)
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
