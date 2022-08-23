# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Example for enabling/disabling the sensors that produce emissions near the IR spectrum."""

import argparse
import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import header_pb2
from bosdyn.client.ir_enable_disable import IREnableDisableServiceClient


def main(argv):
    # Parse args
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--enable', action='store_true', dest='enable', help='Enable IR emissions')
    group.add_argument('--disable', action='store_false', dest='enable',
                       help='Disable IR emissions')

    options = parser.parse_args(argv)

    # Create robot object with an IREnableDisableServiceClient client.
    sdk = bosdyn.client.create_standard_sdk('ir_emission_test')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    ir_enable_disable_client = robot.ensure_client(
        IREnableDisableServiceClient.default_service_name)

    # Send the request
    ir_enable_disable_client.set_ir_enabled(enable=options.enable)

    return True


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
