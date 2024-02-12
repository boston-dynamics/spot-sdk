# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show sending a mobility and arm command at the same time"""
import argparse
import math
import sys
import time

import numpy as np

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import basic_command_pb2, robot_command_pb2
from bosdyn.api.geometry_pb2 import SE2Velocity, SE2VelocityLimit, Vec2
from bosdyn.api.spot import robot_command_pb2 as spot_command_pb2
from bosdyn.client.frame_helpers import VISION_FRAME_NAME, get_vision_tform_body
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                         block_until_arm_arrives, blocking_stand)
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.util import seconds_to_duration

# User-set params
# duration of the whole move [s]
_SECONDS_FULL = 15
# length of the square the robot walks [m]
_L_ROBOT_SQUARE = 0.5
# length of the square the robot walks [m]
_L_ARM_CIRCLE = 0.4
# how many points in the circle the hand will make. >4.
_N_POINTS = 8
# shift the circle that the robot draws in z [m]
_VERTICAL_SHIFT = 0


def hello_arm(config):
    """A simple example of using the Boston Dynamics API to command Spot's arm and body at the same time.

    Please be aware that this demo causes the robot to walk and move its arm. You can have some
    control over how much the robot moves -- see _L_ROBOT_SQUARE and _L_ARM_CIRCLE -- but regardless, the
    robot should have at least (_L_ROBOT_SQUARE + 3) m of space in each direction when this demo is used."""

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('HelloSpotClient')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    assert robot.has_arm(), 'Robot requires an arm to run this example.'

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    assert not robot.is_estopped(), 'Robot is estopped. Please use an external E-Stop client, ' \
                                    'such as the estop SDK example, to configure E-Stop.'

    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)

    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Now, we are ready to power on the robot. This call will block until the power
        # is on. Commands would fail if this did not happen. We can also check that the robot is
        # powered at any point.
        robot.logger.info('Powering on robot... This may take a several seconds.')
        robot.power_on(timeout_sec=20)
        assert robot.is_powered_on(), 'Robot power on failed.'
        robot.logger.info('Robot powered on.')

        # Tell the robot to stand up. The command service is used to issue commands to a robot.
        robot.logger.info('Commanding robot to stand...')
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        blocking_stand(command_client, timeout_sec=10)
        robot.logger.info('Robot standing.')

        # Unstow the arm
        # Build the unstow command using RobotCommandBuilder
        unstow = RobotCommandBuilder.arm_ready_command()

        # Issue the command via the RobotCommandClient
        unstow_command_id = command_client.robot_command(unstow)
        robot.logger.info('Unstow command issued.')

        # Wait until the stow command is successful.
        block_until_arm_arrives(command_client, unstow_command_id, 3.0)

        # Get robot pose in vision frame from robot state (we want to send commands in vision
        # frame relative to where the robot stands now)
        robot_state = robot_state_client.get_robot_state()
        vision_T_body = get_vision_tform_body(robot_state.kinematic_state.transforms_snapshot)

        # In this demo, the robot will walk in a square while moving its arm in a circle.
        # There are some parameters that you can set below:

        # Initialize a robot command message, which we will build out below
        command = robot_command_pb2.RobotCommand()

        # points in the square
        x_vals = np.array([0, 1, 1, 0, 0])
        y_vals = np.array([0, 0, 1, 1, 0])

        # duration in seconds for each move
        seconds_arm = _SECONDS_FULL / (_N_POINTS + 1)
        seconds_body = _SECONDS_FULL / x_vals.size

        # Commands will be sent in the visual odometry ("vision") frame
        frame_name = VISION_FRAME_NAME

        # Build an arm trajectory by assembling points (in meters)
        # x will be the same for each point
        x = _L_ROBOT_SQUARE + 0.5

        for ii in range(_N_POINTS + 1):
            # Get coordinates relative to the robot's body
            y = (_L_ROBOT_SQUARE / 2) - _L_ARM_CIRCLE * (np.cos(2 * ii * math.pi / _N_POINTS))
            z = _VERTICAL_SHIFT + _L_ARM_CIRCLE * (np.sin(2 * ii * math.pi / _N_POINTS))

            # Using the transform we got earlier, transform the points into the vision frame
            x_ewrt_vision, y_ewrt_vision, z_ewrt_vision = vision_T_body.transform_point(x, y, z)

            # Add a new point to the robot command's arm cartesian command se3 trajectory
            # This will be an se3 trajectory point
            point = command.synchronized_command.arm_command.arm_cartesian_command.pose_trajectory_in_task.points.add(
            )

            # Populate this point with the desired position, rotation, and duration information
            point.pose.position.x = x_ewrt_vision
            point.pose.position.y = y_ewrt_vision
            point.pose.position.z = z_ewrt_vision

            point.pose.rotation.x = vision_T_body.rot.x
            point.pose.rotation.y = vision_T_body.rot.y
            point.pose.rotation.z = vision_T_body.rot.z
            point.pose.rotation.w = vision_T_body.rot.w

            traj_time = (ii + 1) * seconds_arm
            duration = seconds_to_duration(traj_time)
            point.time_since_reference.CopyFrom(duration)

        # set the frame for the hand trajectory
        command.synchronized_command.arm_command.arm_cartesian_command.root_frame_name = frame_name

        # Build a body se2trajectory by first assembling points
        for ii in range(x_vals.size):
            # Pull the point in the square relative to the robot and scale according to param
            x = _L_ROBOT_SQUARE * x_vals[ii]
            y = _L_ROBOT_SQUARE * y_vals[ii]

            # Transform desired position into vision frame
            x_ewrt_vision, y_ewrt_vision, z_ewrt_vision = vision_T_body.transform_point(x, y, 0)

            # Add a new point to the robot command's arm cartesian command se3 trajectory
            # This will be an se2 trajectory point
            point = command.synchronized_command.mobility_command.se2_trajectory_request.trajectory.points.add(
            )

            # Populate this point with the desired position, angle, and duration information
            point.pose.position.x = x_ewrt_vision
            point.pose.position.y = y_ewrt_vision

            point.pose.angle = vision_T_body.rot.to_yaw()

            traj_time = (ii + 1) * seconds_body
            duration = seconds_to_duration(traj_time)
            point.time_since_reference.CopyFrom(duration)

        # set the frame for the body trajectory
        command.synchronized_command.mobility_command.se2_trajectory_request.se2_frame_name = frame_name

        # Constrain the robot not to turn, forcing it to strafe laterally.
        speed_limit = SE2VelocityLimit(max_vel=SE2Velocity(linear=Vec2(x=2, y=2), angular=0),
                                       min_vel=SE2Velocity(linear=Vec2(x=-2, y=-2), angular=0))
        mobility_params = spot_command_pb2.MobilityParams(vel_limit=speed_limit)

        command.synchronized_command.mobility_command.params.CopyFrom(
            RobotCommandBuilder._to_any(mobility_params))

        # Send the command using the command client
        # The SE2TrajectoryRequest requires an end_time, which is set
        # during the command client call
        robot.logger.info('Sending arm and body trajectory commands.')
        command_client.robot_command(command, end_time_secs=time.time() + _SECONDS_FULL)
        time.sleep(_SECONDS_FULL + 2)

        # Power the robot off. By specifying "cut_immediately=False", a safe power off command
        # is issued to the robot. This will attempt to sit the robot before powering off.
        robot.power_off(cut_immediately=False, timeout_sec=20)
        assert not robot.is_powered_on(), 'Robot power off failed.'
        robot.logger.info('Robot safely powered off.')


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()
    try:
        hello_arm(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception('Threw an exception')
        return False


if __name__ == '__main__':
    if not main():
        sys.exit(1)
