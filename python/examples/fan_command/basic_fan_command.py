# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import sys
import time

import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.client.power import PowerClient


def main(argv):
    """Command line interface."""
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    config = parser.parse_args(argv)

    bosdyn.client.util.setup_logging(config.verbose)
    sdk = bosdyn.client.create_standard_sdk('FanCommandClient')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)

    # Acquire robot lease
    robot.logger.info('Acquiring lease...')
    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Initialize power client
        robot.logger.info('Starting power client...')
        power_client = robot.ensure_client(PowerClient.default_service_name)

        response = power_client.fan_power_command(percent_power=100, duration=5)
        #Clearing less pertinent fields, can delete these lines for full response
        response.ClearField("header")
        response.ClearField("lease_use_result")
        print("Initial Command Response:")
        print(response)

        time.sleep(1)

        feedback1 = power_client.fan_power_command_feedback(response.command_id)
        #Clearing less pertinent fields, can delete these lines for full response
        feedback1.ClearField("header")
        print("Active Command Feedback:")
        print(feedback1)

        time.sleep(5)

        feedback2 = power_client.fan_power_command_feedback(response.command_id)
        #Clearing less pertinent fields, can delete these lines for full response
        feedback2.ClearField("header")
        print("Completed Command Feedback:")
        print(feedback2)


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
