# Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Example usage of the log annotation features
"""
from __future__ import print_function
import argparse
import sys
import logging
import io
import struct
import time

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.log_annotation import LogAnnotationClient

import bosdyn.api.log_annotation_pb2 as log_annotation_protos
import bosdyn.api.log_annotation_service_pb2_grpc as log_annotation_service
import bosdyn.api.robot_command_pb2 as robot_command_protos
import bosdyn.api.geometry_pb2 as geometry_protos

LOGGER = logging.getLogger()


def annotate_spot(config):
    """A simple example of using the Boston Dynamics API to communicate log annotations to spot."""

    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('AnnotateSpotClient')
    sdk.load_app_token(config.app_token)

    robot = sdk.create_robot(config.hostname)

    # Authenticate robot before being able to use it
    robot.authenticate(config.username, config.password)

    # Establish time sync with the robot
    robot.time_sync.wait_for_sync()

    # Create a log annotation client
    log_annotation_client = robot.ensure_client(LogAnnotationClient.default_service_name)

    # Log a text message.
    text_message = "This is a text message."
    txt_msg_proto = log_annotation_protos.LogAnnotationTextMessage(message=text_message,
                                                                   timestamp=None)
    log_annotation_client.add_text_messages([txt_msg_proto])
    robot.logger.info('Added comment "%s" to robot log.', text_message)
    time.sleep(0.1)

    # Log an operator comment.
    op_comment = "This is an operator comment."
    log_annotation_client.add_operator_comment(op_comment)
    robot.logger.info('Added comment "%s" to robot log.', op_comment)
    time.sleep(0.1)

    # Log two blobs of data (serialized protobuf messages)
    geo_proto = geometry_protos.Quaternion(x=.91, y=.5, z=.9, w=.2)
    log_annotation_client.add_log_protobuf(geo_proto)
    robot.logger.info('Added geometry log blob to robot log.')
    time.sleep(0.1)
    cmd_proto = robot_command_protos.SelfRightCommand()
    log_annotation_client.add_log_protobuf(cmd_proto)
    robot.logger.info('Added robot command log blob to robot log.')
    time.sleep(0.1)



def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    options = parser.parse_args(argv)

    LOGGER.setLevel(logging.DEBUG)

    annotate_spot(options)

    return True


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
