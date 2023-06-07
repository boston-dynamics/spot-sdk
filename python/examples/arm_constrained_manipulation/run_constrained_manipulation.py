# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Test script to run constrained manipulation
"""
import argparse
import sys
import time

import numpy as np
from constrained_manipulation_helper import *

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import robot_command_pb2
from bosdyn.client import math_helpers, robot_command
from bosdyn.client.frame_helpers import (GRAV_ALIGNED_BODY_FRAME_NAME, HAND_FRAME_NAME,
                                         ODOM_FRAME_NAME, get_a_tform_b)
from bosdyn.client.robot_state import RobotStateClient


def run_constrained_manipulation(config):
    """A simple example of using the Boston Dynamics API to run a
       constrained manipulation task."""

    print(
        "Start doing constrained manipulation. Make sure Object of interest is grasped before starting."
    )

    position_control_rot = False
    position_control_linear = False
    if (config.target_angle):
        position_control_rot = True

    if (config.target_linear_position):
        position_control_linear = True

    # Build constrained manipulation command
    # You can build the task type of interest by using functions
    # defined in constrained_manipulation_helper.py
    # The input to this function is a normalized task velocity in range [-1, 1].
    # The normalized task velocity is scaled as a function of the force limit
    # (See the constrained_manipulation_helper.py for more details)
    # For heavier tasks, consider specifying the force or torque limit as well.
    if (config.task_type == 'crank'):
        command = construct_crank_task(config.task_velocity, force_limit=config.force_limit,
                                       target_angle=config.target_angle,
                                       position_control=position_control_rot)
    elif (config.task_type == 'lever'):
        command = construct_lever_task(config.task_velocity, force_limit=config.force_limit,
                                       torque_limit=config.torque_limit,
                                       target_angle=config.target_angle,
                                       position_control=position_control_rot)
    elif (config.task_type == 'left_handed_ballvalve'):
        command = construct_left_handed_ballvalve_task(
            config.task_velocity, force_limit=config.force_limit, torque_limit=config.torque_limit,
            target_angle=config.target_angle, position_control=position_control_rot)
    elif (config.task_type == 'right_handed_ballvalve'):
        command = construct_right_handed_ballvalve_task(
            config.task_velocity, force_limit=config.force_limit, torque_limit=config.torque_limit,
            target_angle=config.target_angle, position_control=position_control_rot)
    elif (config.task_type == 'cabinet'):
        command = construct_cabinet_task(config.task_velocity, force_limit=config.force_limit,
                                         target_angle=config.target_angle,
                                         position_control=position_control_rot)

    elif (config.task_type == 'wheel'):
        command = construct_wheel_task(config.task_velocity, force_limit=config.force_limit,
                                       target_angle=config.target_angle,
                                       position_control=position_control_rot)

    elif (config.task_type == 'drawer'):
        command = construct_drawer_task(config.task_velocity, force_limit=config.force_limit,
                                        target_linear_position=config.target_linear_position,
                                        position_control=position_control_linear)

    elif (config.task_type == 'knob'):
        command = construct_knob_task(config.task_velocity, torque_limit=config.torque_limit,
                                      target_angle=config.target_angle,
                                      position_control=position_control_rot)
    else:
        print("Unspecified task type. Exit.")
        return

    bosdyn.client.util.setup_logging(config.verbose)
    sdk = bosdyn.client.create_standard_sdk('ConstrainedManipulationClient')

    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)

    # Check to see if robot is powered on.
    assert robot.is_powered_on(), "Robot must be powered on."
    robot.logger.info("Robot powered on.")
    # Check if the gripper is already holding the object.
    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    is_gripper_holding = robot_state_client.get_robot_state(
    ).manipulator_state.is_gripper_holding_item
    assert is_gripper_holding, "Gripper is empty. If incorrect, use the grasp_override_command."

    command_client = robot.ensure_client(robot_command.RobotCommandClient.default_service_name)

    # Note that the take lease API is used, rather than acquire. Using acquire is typically a
    # better practice, but in this example, a user might want to switch back and forth between
    # using the tablet and using this script. Using take allows for directly hijacking control
    # away from the tablet.
    lease_client.take()
    print("About to start")
    task_duration = 10.0
    if (position_control_linear or position_control_rot):
        # For position moves, we don't want a small end-time to cause a pre-mature stop,
        # so set the end-time to a large value.
        # In a position move even with a large end-time, the robot would stop
        # after achieving the desired position and we are robust to loss in communication.
        task_duration = 100000.0
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        command.full_body_command.constrained_manipulation_request.end_time.CopyFrom(
            robot.time_sync.robot_timestamp_from_local_secs(time.time() + task_duration))
        command_client.robot_command_async(command)
        time.sleep(2 * task_duration)


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument(
        '--task-type', help='Specify the task type to manipulate.', default='crank', choices=[
            'lever', 'left_handed_ballvalve', 'right_handed_ballvalve', 'crank', 'wheel', 'cabinet',
            'drawer', 'knob'
        ])
    parser.add_argument('--task-velocity', help='Desired task velocity', type=float, default=0.5)
    parser.add_argument('--force-limit', help='Max force to be applied along task dimensions',
                        type=float, default=40)
    parser.add_argument('--torque-limit', help='Max force to be applied along task dimensions',
                        type=float, default=5.0)
    parser.add_argument('--target-angle', help='Target displacement in task space', type=float,
                        default=None)
    parser.add_argument('--target-linear-position', help='Target linear displacement in task space',
                        type=float, default=None)
    parser.add_argument('--vel-lim-pos-move', help='Velocity limit for position moves', type=float,
                        default=None)
    options = parser.parse_args(argv)
    run_constrained_manipulation(options)


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
