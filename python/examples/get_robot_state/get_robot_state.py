# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Simple robot state capture tutorial."""

import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.robot_state import RobotStateClient


def main():
    import argparse

    commands = {
        'state': "get_robot_state",
        'hardware': "get_hardware_config_with_link_info",
        'metrics': "get_robot_metrics",
    }

    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument('command', choices=list(commands.keys()), help='Command to run')
    options = parser.parse_args()

    # Create robot object with an image client.
    sdk = bosdyn.client.create_standard_sdk('RobotStateClient')
    robot = sdk.create_robot(options.hostname)
    robot.authenticate(options.username, options.password)
    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)

    # Make a robot state request
    request_fn = getattr(robot_state_client, commands[options.command])
    response = request_fn()
    print(response)

    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
