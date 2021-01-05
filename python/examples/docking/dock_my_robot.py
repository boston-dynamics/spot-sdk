# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Test script to run a simple docking service.
"""
from __future__ import print_function

import argparse
import sys

import bosdyn.client
import bosdyn.client.estop
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.client import robot_command
from bosdyn.client.docking import blocking_dock_robot


def run_docking(config):
    """A simple example of using the Boston Dynamics API to use the docking service.
        Copied from the hello_spot.py example"""

    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('DockingClient')

    robot = sdk.create_robot(config.hostname)
    robot.authenticate(config.username, config.password)
    robot.time_sync.wait_for_sync()

    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    # To steal the lease on a running robot you'd like to dock, change this to `lease_client.take()`
    lease = lease_client.acquire()

    command_client = robot.ensure_client(robot_command.RobotCommandClient.default_service_name)
    try:
        with bosdyn.client.lease.LeaseKeepAlive(lease_client):
            # make sure we're powered on and standing
            robot.power_on()
            robot_command.blocking_stand(command_client)

            # Dock the robot
            blocking_dock_robot(robot, config.dock_id)

            print("Docking Success")

    finally:
        lease_client.return_lease(lease)


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument('--dock-id', required=True, type=int, help='Docking station ID to dock at')
    options = parser.parse_args(argv)
    run_docking(options)


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
