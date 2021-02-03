# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use Spot's arm.
"""
from __future__ import print_function
import argparse
import sys

import bosdyn.client
import bosdyn.client.estop
import bosdyn.client.lease
import bosdyn.client.util

from bosdyn.client.robot_command import RobotCommandClient, RobotCommandBuilder, blocking_stand
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.estop import EstopClient
from bosdyn.client import math_helpers
from bosdyn.api import estop_pb2

from bosdyn.api import arm_command_pb2
from bosdyn.api import synchronized_command_pb2
from bosdyn.api import robot_command_pb2
from google.protobuf import wrappers_pb2
from bosdyn.client.frame_helpers import *
from bosdyn.api import geometry_pb2
from bosdyn.util import seconds_to_duration

import traceback
import time


def verify_estop(robot):
    """Verify the robot is not estopped"""

    client = robot.ensure_client(EstopClient.default_service_name)
    if client.get_status().stop_level != estop_pb2.ESTOP_LEVEL_NONE:
        error_message = "Robot is estopped. Please use an external E-Stop client, such as the" \
        " estop SDK example, to configure E-Stop."
        robot.logger.error(error_message)
        raise Exception(error_message)


def to_double_val(val):
    return wrappers_pb2.DoubleValue(value=val)


def joint_move_example(config):
    """A simple example of using the Boston Dynamics API to command Spot's arm."""

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('ArmJointMoveClient')
    robot = sdk.create_robot(config.hostname)
    robot.authenticate(config.username, config.password)
    robot.time_sync.wait_for_sync()

    assert robot.has_arm(), "Robot requires an arm to run this example."

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    verify_estop(robot)

    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)

    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    lease = lease_client.acquire()
    try:
        with bosdyn.client.lease.LeaseKeepAlive(lease_client):
            # Now, we are ready to power on the robot. This call will block until the power
            # is on. Commands would fail if this did not happen. We can also check that the robot is
            # powered at any point.
            robot.logger.info("Powering on robot... This may take a several seconds.")
            robot.power_on(timeout_sec=20)
            assert robot.is_powered_on(), "Robot power on failed."
            robot.logger.info("Robot powered on.")

            # Tell the robot to stand up. The command service is used to issue commands to a robot.
            # The set of valid commands for a robot depends on hardware configuration. See
            # SpotCommandHelper for more detailed examples on command building. The robot
            # command service requires timesync between the robot and the client.
            robot.logger.info("Commanding robot to stand...")
            command_client = robot.ensure_client(RobotCommandClient.default_service_name)
            blocking_stand(command_client, timeout_sec=10)
            robot.logger.info("Robot standing.")

            time.sleep(2.0)

            # Do a joint move to move the arm around.
            sh0 = wrappers_pb2.DoubleValue(value=0.0692)
            sh1 = wrappers_pb2.DoubleValue(value=-1.882)
            el0 = wrappers_pb2.DoubleValue(value=1.652)
            el1 = wrappers_pb2.DoubleValue(value=-0.0691)
            wr0 = wrappers_pb2.DoubleValue(value=1.622)
            wr1 = wrappers_pb2.DoubleValue(value=1.550)

            # Build up a proto.
            joint_position1 = arm_command_pb2.ArmJointPosition(sh0=sh0, sh1=sh1, el0=el0, el1=el1,
                                                               wr0=wr0, wr1=wr1)

            traj_point = arm_command_pb2.ArmJointTrajectoryPoint(position=joint_position1)
            arm_joint_traj = arm_command_pb2.ArmJointTrajectory(points=[traj_point])
            joint_move_command = arm_command_pb2.ArmJointMoveCommand.Request(
                trajectory=arm_joint_traj)
            arm_command = arm_command_pb2.ArmCommand.Request(
                arm_joint_move_command=joint_move_command)
            sync_arm = synchronized_command_pb2.SynchronizedCommand.Request(arm_command=arm_command)
            arm_sync_robot_cmd = robot_command_pb2.RobotCommand(synchronized_command=sync_arm)

            # Make the open gripper RobotCommand
            gripper_command = RobotCommandBuilder.claw_gripper_open_fraction_command(1.0)

            # Combine the arm and gripper commands into one RobotCommand
            command = RobotCommandBuilder.build_synchro_command(gripper_command, arm_sync_robot_cmd)

            # Send the request
            command_client.robot_command(command)
            robot.logger.info('Moving arm to position 1.')

            time.sleep(4.0)

            # ----- Do a two-point joint move trajectory ------

            # First stow the arm.
            # Build the stow command using RobotCommandBuilder
            stow = RobotCommandBuilder.arm_stow_command()

            # Issue the command via the RobotCommandClient
            command_client.robot_command(stow)

            robot.logger.info("Stow command issued.")
            time.sleep(2.0)

            # First point position
            sh0 = wrappers_pb2.DoubleValue(value=-1.5)
            sh1 = wrappers_pb2.DoubleValue(value=-0.8)
            el0 = wrappers_pb2.DoubleValue(value=1.7)
            el1 = wrappers_pb2.DoubleValue(value=0.0)
            wr0 = wrappers_pb2.DoubleValue(value=0.5)
            wr1 = wrappers_pb2.DoubleValue(value=0.0)

            # Build up a proto.
            joint_position1 = arm_command_pb2.ArmJointPosition(sh0=sh0, sh1=sh1, el0=el0, el1=el1,
                                                               wr0=wr0, wr1=wr1)
            # Second point position
            sh0 = wrappers_pb2.DoubleValue(value=1.0)
            sh1 = wrappers_pb2.DoubleValue(value=-0.2)
            el0 = wrappers_pb2.DoubleValue(value=1.3)
            el1 = wrappers_pb2.DoubleValue(value=-1.3)
            wr0 = wrappers_pb2.DoubleValue(value=-1.5)
            wr1 = wrappers_pb2.DoubleValue(value=1.5)

            # Second point time (seconds)
            first_point_t = 2.0
            second_point_t = 4.0

            joint_position2 = arm_command_pb2.ArmJointPosition(sh0=sh0, sh1=sh1, el0=el0, el1=el1,
                                                               wr0=wr0, wr1=wr1)

            # Optionally, set the maximum allowable velocity in rad/s that a joint is allowed to
            # travel at. Also set the maximum allowable acceleration in rad/s^2 that a joint is
            # allowed to accelerate at. If these values are not set, a default will be used on
            # the robot.
            # Note that if these values are set too low and the trajectories are too aggressive
            # in terms of time, the desired joint angles will not be hit at the specified time.
            # Some other ways to help the robot actually hit the specified trajectory is to
            # increase the time between trajectory points, or to only specify joint position
            # goals without specifying velocity goals.
            max_vel = wrappers_pb2.DoubleValue(value=2.5)
            max_acc = wrappers_pb2.DoubleValue(value=15)

            # Build up a proto.
            traj_point1 = arm_command_pb2.ArmJointTrajectoryPoint(
                position=joint_position1, time_since_reference=seconds_to_duration(first_point_t))
            traj_point2 = arm_command_pb2.ArmJointTrajectoryPoint(
                position=joint_position2, time_since_reference=seconds_to_duration(second_point_t))
            arm_joint_traj = arm_command_pb2.ArmJointTrajectory(
                points=[traj_point1, traj_point2], maximum_velocity=max_vel, maximum_acceleration=max_acc)
            joint_move_command = arm_command_pb2.ArmJointMoveCommand.Request(
                trajectory=arm_joint_traj)
            arm_command = arm_command_pb2.ArmCommand.Request(
                arm_joint_move_command=joint_move_command)
            sync_arm = synchronized_command_pb2.SynchronizedCommand.Request(arm_command=arm_command)
            arm_sync_robot_cmd = robot_command_pb2.RobotCommand(synchronized_command=sync_arm)

            # Make the open gripper RobotCommand
            gripper_command = RobotCommandBuilder.claw_gripper_open_fraction_command(1.0)

            # Combine the arm and gripper commands into one RobotCommand
            command = RobotCommandBuilder.build_synchro_command(gripper_command, arm_sync_robot_cmd)

            # Send the request
            command_client.robot_command(command)
            robot.logger.info('Moving arm along 2-point joint trajectory.')

            time.sleep(5.0)

            # Power the robot off. By specifying "cut_immediately=False", a safe power off command
            # is issued to the robot. This will attempt to sit the robot before powering off.
            robot.power_off(cut_immediately=False, timeout_sec=20)
            assert not robot.is_powered_on(), "Robot power off failed."
            robot.logger.info("Robot safely powered off.")
    finally:
        # If we successfully acquired a lease, return it.
        lease_client.return_lease(lease)


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    options = parser.parse_args(argv)
    try:
        joint_move_example(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception("Threw an exception")
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
