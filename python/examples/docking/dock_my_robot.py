# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
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
from bosdyn.client.docking import blocking_dock_robot, blocking_undock, get_dock_id


def run_docking(config):
    """A simple example of using the Boston Dynamics API to use the docking service.
        Copied from the hello_spot.py example"""

    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('DockingClient')

    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    command_client = robot.ensure_client(robot_command.RobotCommandClient.default_service_name)

    # To steal control away from another, uncomment the line below.
    # lease_client.take()
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Make sure we're powered on.
        robot.power_on()

        if config.undock:
            dock_id = get_dock_id(robot)
            if dock_id is None:
                print("Robot does not seem to be docked; trying anyway")
            else:
                print("Docked at {}".format(dock_id))
            blocking_undock(robot)
            print("Undocking Success")
        else:
            # Stand before trying to dock.
            robot_command.blocking_stand(command_client)
            blocking_dock_robot(robot, config.dock_id)
            print("Docking Success")


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dock-id', type=int, help='Docking station ID to dock at')
    group.add_argument('--undock', action='store_true', help='Undock, instead of docking.')
    options = parser.parse_args(argv)
    run_docking(options)


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
