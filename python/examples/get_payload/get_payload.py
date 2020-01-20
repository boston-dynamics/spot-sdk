# Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Example code for using the payload service API
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

import bosdyn.api.payload_pb2 as payload_protos
import bosdyn.api.payload_pb2 as payload_service_protos
import bosdyn.api.payload_service_pb2_grpc as payload_service
import bosdyn.api.geometry_pb2 as geometry_protos

from bosdyn.client.payload import PayloadClient

LOGGER = logging.getLogger()


def payload_spot(config):
    """A simple example of using the Boston Dynamics API to communicate payload configs to spot."""

    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('PayloadSpotClient')
    sdk.load_app_token(config.app_token)

    robot = sdk.create_robot(config.hostname)

    # Authenticate robot before being able to use it
    robot.authenticate(config.username, config.password)

    # Create a log annotation client
    payload_client = robot.ensure_client(PayloadClient.default_service_name)

    # List all payloads
    payloads = payload_client.list_payloads()
    print(payloads)


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    options = parser.parse_args(argv)

    payload_spot(options)

    return True


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
