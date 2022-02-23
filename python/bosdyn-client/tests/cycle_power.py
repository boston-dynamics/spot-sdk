# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Simple tutorial inspecting and cycling power on robot."""

import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.power import PowerClient


def main():
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()

    # Create robot object with a power client.
    sdk = bosdyn.client.create_standard_sdk('PowerClient')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    power_client = robot.ensure_client(PowerClient.default_service_name)

    try:
        power_client.power_command(lease=None, request=None)
    except bosdyn.client.LeaseUseError as e:
        print("{}".format(e))

    try:
        power_client.power_command_feedback(1337)
    except bosdyn.client.InvalidRequestError as e:
        print("{}".format(e))


if __name__ == "__main__":
    if not main():
        sys.exit(1)
