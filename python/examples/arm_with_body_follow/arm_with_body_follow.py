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
import bosdyn.client.lease
import bosdyn.client.util

from bosdyn.client import math_helpers
from bosdyn.client.frame_helpers import *
from bosdyn.client.robot_command import RobotCommandClient, RobotCommandBuilder, blocking_stand
from bosdyn.client.robot_state import RobotStateClient

from bosdyn.api import geometry_pb2

import traceback
import time


def arm_with_body_follow(config):
    """A simple example that moves the arm and asks the body to move to a good position based
       on the arm's location."""

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('ArmWithBodyFollowClient')
    robot = sdk.create_robot(config.hostname)
    robot.authenticate(config.username, config.password)
    robot.time_sync.wait_for_sync()

    assert robot.has_arm(), "Robot requires an arm to run this example."

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    assert not robot.is_estopped(), "Robot is estopped. Please use an external E-Stop client, " \
                                    "such as the estop SDK example, to configure E-Stop."

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

            # Move the arm to a spot in front of the robot, and command the body to follow the hand.
            # Build a position to move the arm to (in meters, relative to the body frame origin.)
            x = 1.25
            y = 0
            z = 0.25
            hand_pos_rt_body = geometry_pb2.Vec3(x=x, y=y, z=z)

            # Rotation as a quaternion.
            qw = 1
            qx = 0
            qy = 0
            qz = 0
            body_Q_hand = geometry_pb2.Quaternion(w=qw, x=qx, y=qy, z=qz)

            # Build the SE(3) pose of the desired hand position in the moving body frame.
            body_T_hand = geometry_pb2.SE3Pose(position=hand_pos_rt_body, rotation=body_Q_hand)

            # Transform the desired from the moving body frame to the odom frame.
            robot_state = robot_state_client.get_robot_state()
            odom_T_body = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot,
                                        ODOM_FRAME_NAME, GRAV_ALIGNED_BODY_FRAME_NAME)
            odom_T_hand = odom_T_body * math_helpers.SE3Pose.from_obj(body_T_hand)

            # duration in seconds
            seconds = 5

            # Create the arm command.
            arm_command = RobotCommandBuilder.arm_pose_command(
                odom_T_hand.x, odom_T_hand.y, odom_T_hand.z, odom_T_hand.rot.w, odom_T_hand.rot.x,
                odom_T_hand.rot.y, odom_T_hand.rot.z, ODOM_FRAME_NAME, seconds)

            # Tell the robot's body to follow the arm
            follow_arm_command = RobotCommandBuilder.follow_arm_command()

            # Combine the arm and mobility commands into one synchronized command.
            command = RobotCommandBuilder.build_synchro_command(follow_arm_command, arm_command)

            # Send the request
            command_client.robot_command(command)
            robot.logger.info('Moving arm to position.')

            time.sleep(6.0)

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
        arm_with_body_follow(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception("Threw an exception")
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
