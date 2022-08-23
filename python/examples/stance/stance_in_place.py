# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Test script to run a simple stance command.
"""
from __future__ import print_function

import argparse
import sys
import time
import traceback

import bosdyn.client
import bosdyn.client.estop
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.client import frame_helpers, math_helpers, robot_command
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client.robot_state import RobotStateClient


def run(config):
    """Testing API Stance

    This example will cause the robot to power on, stand and reposition its feet (Stance) at the
    location it's already standing at.

    * Use sw-estop running on tablet/python etc.
    * Have ~1m of free space all around the robot
    * Ctrl-C to exit and return lease.
    """

    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('StanceClient')

    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    # Acquire lease
    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
        state = robot_state_client.get_robot_state()

        # This example ues the current body position, but you can specify any position.
        # A common use is to specify it relative to something you know, like a fiducial.
        vo_T_body = frame_helpers.get_se2_a_tform_b(state.kinematic_state.transforms_snapshot,
                                                    frame_helpers.VISION_FRAME_NAME,
                                                    frame_helpers.GRAV_ALIGNED_BODY_FRAME_NAME)

        # Power On
        robot.power_on()
        assert robot.is_powered_on(), "Robot power on failed."

        # Stand
        robot_command.blocking_stand(command_client)

        #### Example stance offsets from body position. ####
        x_offset = config.x_offset
        y_offset = config.y_offset

        pos_fl_rt_vision = vo_T_body * math_helpers.SE2Pose(x_offset, y_offset, 0)
        pos_fr_rt_vision = vo_T_body * math_helpers.SE2Pose(x_offset, -y_offset, 0)
        pos_hl_rt_vision = vo_T_body * math_helpers.SE2Pose(-x_offset, y_offset, 0)
        pos_hr_rt_vision = vo_T_body * math_helpers.SE2Pose(-x_offset, -y_offset, 0)

        stance_cmd = RobotCommandBuilder.stance_command(
            frame_helpers.VISION_FRAME_NAME, pos_fl_rt_vision.position, pos_fr_rt_vision.position,
            pos_hl_rt_vision.position, pos_hr_rt_vision.position)

        print("After stance adjustment, press Ctrl-C to sit Spot and turn off motors.")

        while True:
            # Update end time
            stance_cmd.synchronized_command.mobility_command.stance_request.end_time.CopyFrom(
                robot.time_sync.robot_timestamp_from_local_secs(time.time() + 5))

            # Send the command
            command_client.robot_command(stance_cmd)

            time.sleep(1)


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('--x-offset', default=0.3, type=float, help='Offset in X for Spot to step')
    parser.add_argument('--y-offset', default=0.3, type=float, help="Offset in Y for Spot to step")
    options = parser.parse_args(argv)

    if not 0.2 <= abs(options.x_offset) <= 0.5:
        print("Invalid x-offset value. Please pass a value between 0.2 and 0.5")
        sys.exit(1)
    if not 0.1 <= abs(options.y_offset) <= 0.4:
        print("Invalid y-offset value. Please pass a value between 0.1 and 0.4")
        sys.exit(1)

    try:
        run(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.error("Threw an exception: %s\n%s", exc, traceback.format_exc())
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
