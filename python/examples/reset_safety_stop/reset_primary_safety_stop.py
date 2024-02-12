# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import sys

import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import power_pb2
from bosdyn.client.power import PowerClient


def main():
    """Command line interface."""
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    config = parser.parse_args()

    bosdyn.client.util.setup_logging(config.verbose)
    sdk = bosdyn.client.create_standard_sdk('SafetyStopClient')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)

    # Acquire robot lease
    robot.logger.info('Acquiring lease...')
    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)

    # Initialize power client
    robot.logger.info('Starting power client...')
    power_client = robot.ensure_client(PowerClient.default_service_name)

    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        response = power_client.reset_safety_stop(
            safety_stop_type=power_pb2.ResetSafetyStopRequest.SAFETY_STOP_PRIMARY)

    # Clearing less pertinent fields, can delete these lines for full response
    response.ClearField('header')
    response.ClearField('lease_use_result')
    print('Initial Command Response:')
    print(response)

    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
