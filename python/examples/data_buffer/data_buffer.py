# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the Boston Dynamics API to log data."""
import argparse
import sys
import time

import bosdyn.api.data_buffer_pb2 as data_buffer_protos
import bosdyn.client
import bosdyn.client.util
from bosdyn.api.parameter_pb2 import Parameter
from bosdyn.client.data_buffer import DataBufferClient


def add_blob(robot, options):
    """Add binary data to the log."""

    client = robot.ensure_client(DataBufferClient.default_service_name)
    robot.time_sync.wait_for_sync()
    robot_timestamp = robot.time_sync.robot_timestamp_from_local_secs(time.time())

    # create a text message proto, just to have something to store.
    msg = data_buffer_protos.TextMessage(
        message='test message',
        timestamp=robot_timestamp,
        source='test-source',
        level=data_buffer_protos.TextMessage.LEVEL_INFO,  # pylint: disable=no-member
        tag='test')

    typename = msg.DESCRIPTOR.full_name
    client.add_blob(msg.SerializeToString(), type_id=typename, channel=typename,
                    robot_timestamp=robot_timestamp, write_sync=options.write_sync)
    print("Added message blob.")


def add_protobuf(robot, options):
    """Add protobuf data to the log."""

    client = robot.ensure_client(DataBufferClient.default_service_name)
    robot.time_sync.wait_for_sync()
    robot_timestamp = robot.time_sync.robot_timestamp_from_local_secs(time.time())

    # create a text message proto, just to have something to store.
    msg = data_buffer_protos.TextMessage(
        message='test protobuf',
        timestamp=robot_timestamp,
        source=robot.client_name,
        level=data_buffer_protos.TextMessage.LEVEL_INFO,  # pylint: disable=no-member
        tag='test')

    client.add_protobuf(msg, robot_timestamp=robot_timestamp, write_sync=options.write_sync)
    print("Added protobuf message.")


def add_event(robot):
    """Record an event in the log."""

    robot.time_sync.wait_for_sync()
    # pylint: disable=no-member
    robot.log_event(
        'examples:example_event', level=data_buffer_protos.Event.LEVEL_LOW,
        description='This is an example event from demonstrating the API',
        start_timestamp_secs=time.time(), parameters=[
            Parameter(label='test:length', units='m', float_value=3.141),
            Parameter(label='test:boolean', bool_value=True)
        ])
    print("Added event.")


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)

    subparsers = parser.add_subparsers(help='commands', dest='command')
    operator_parser = subparsers.add_parser('operator', help='add operator comment')
    operator_parser.add_argument('message', help='operator comment message')

    blob_parser = subparsers.add_parser('blob', help='write a blob to the log')
    blob_parser.add_argument('--write-sync', action='store_true',
                             help='ensure data is on disk before returning')

    protobuf_parser = subparsers.add_parser('protobuf', help='serialize a protobuf to the log')
    protobuf_parser.add_argument('--write-sync', action='store_true',
                                 help='ensure data is on disk before returning')

    _event_parser = subparsers.add_parser('event', help='add an event to the log')

    options = parser.parse_args()

    bosdyn.client.util.setup_logging(options.verbose)

    sdk = bosdyn.client.create_standard_sdk('DataBufferClientExample')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    if options.command == 'operator':
        # If timestamp is not given, robot uses current time on message receipt.
        robot.operator_comment(options.message)
        print("Added operator comment")
    elif options.command == 'event':
        add_event(robot)
    elif options.command == 'blob':
        add_blob(robot, options)
    elif options.command == 'protobuf':
        add_protobuf(robot, options)
    else:
        parser.print_help()
        return False
    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
