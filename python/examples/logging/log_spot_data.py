# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Example usage of the data-buffer features
"""
from __future__ import print_function

import argparse
import logging
import struct
import sys
import time

import bosdyn.api.data_buffer_pb2 as data_buffer_protos
import bosdyn.api.geometry_pb2 as geometry_protos
import bosdyn.client
import bosdyn.client.util
from bosdyn.api import basic_command_pb2
from bosdyn.client.data_buffer import DataBufferClient

LOGGER = logging.getLogger()


def log_spot_data(config):
    """A simple example of using the Boston Dynamics API to send data to spot to be logged."""

    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('AnnotateSpotClient')

    robot = sdk.create_robot(config.hostname)

    # Authenticate robot before being able to use it
    bosdyn.client.util.authenticate(robot)

    # Establish time sync with the robot
    robot.time_sync.wait_for_sync()

    # Create a log annotation client
    data_buffer_client = robot.ensure_client(DataBufferClient.default_service_name)

    # Log a text message.
    text_message = "This is a text message."
    txt_msg_proto = data_buffer_protos.TextMessage(message=text_message, timestamp=None)
    data_buffer_client.add_text_messages([txt_msg_proto])
    robot.logger.info('Added comment "%s" to robot log.', text_message)
    time.sleep(0.1)

    # Log an operator comment.
    op_comment = "This is an operator comment."
    data_buffer_client.add_operator_comment(op_comment)
    robot.logger.info('Added comment "%s" to robot log.', op_comment)
    time.sleep(0.1)

    data_buffer_client.add_operator_comment(op_comment)
    robot.logger.info('Added comment "%s" to robot log.', op_comment)
    time.sleep(0.1)

    # Log an event.
    event_time = robot.time_sync.robot_timestamp_from_local_secs(time.time())
    event = data_buffer_protos.Event(type='bosdyn:test', description='test event',
                                     start_time=event_time, end_time=event_time,
                                     level=data_buffer_protos.Event.LEVEL_LOW)
    data_buffer_client.add_events([event])
    robot.logger.info("Added event")
    time.sleep(0.1)

    # Log two blobs of data (serialized protobuf messages)
    geo_proto = geometry_protos.Quaternion(x=.91, y=.5, z=.9, w=.2)
    data_buffer_client.add_protobuf(geo_proto)
    robot.logger.info('Added geometry log blob to robot log.')
    time.sleep(0.1)
    cmd_proto = basic_command_pb2.SelfRightCommand()
    data_buffer_client.add_protobuf(cmd_proto)
    robot.logger.info('Added robot command log blob to robot log.')
    time.sleep(0.1)

    # Log two blobs of data of different types to the same 'channel'
    data_buffer_client.add_protobuf(geo_proto, channel='multi-proto-channel')
    data_buffer_client.add_protobuf(cmd_proto, channel='multi-proto-channel')
    robot.logger.info('Added protos of different types to the same channel.')
    time.sleep(0.1)



def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args(argv)

    LOGGER.setLevel(logging.DEBUG)

    log_spot_data(options)

    return True


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
