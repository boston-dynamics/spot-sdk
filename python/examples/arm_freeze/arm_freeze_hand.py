# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show differences of commanding Spot's end effector in the ODOM and BODY frames.
"""

import sys
import time

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import geometry_pb2
from bosdyn.api.spot import robot_command_pb2 as spot_command_pb2
from bosdyn.client import math_helpers
from bosdyn.client.frame_helpers import BODY_FRAME_NAME, ODOM_FRAME_NAME, get_a_tform_b
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                         block_for_trajectory_cmd, block_until_arm_arrives,
                                         blocking_stand)
from bosdyn.client.robot_state import RobotStateClient


def mobility_params_for_slow_walk():
    """
    Limit the x speed of the robot during the mobility phases of this example.  This is purely
      for aesthetic purposes to observe the hand's behavior longer while walking.
    """
    speed_limit = geometry_pb2.SE2VelocityLimit(
        max_vel=geometry_pb2.SE2Velocity(linear=geometry_pb2.Vec2(x=0.2, y=2), angular=1),
        min_vel=geometry_pb2.SE2Velocity(linear=geometry_pb2.Vec2(x=-0.2, y=-2), angular=-1))
    return spot_command_pb2.MobilityParams(vel_limit=speed_limit)


def get_hand_pose_for_example():
    """
    A hand pose in front of and to the side of the robot.  This pose of the end-effector
    was chosen such that the robot can walk forwards/backwards without having the body of
    the robot collide with the hand.
    """

    # Position of hand frame is in front of and to the right of the body.
    x = 0.75
    y = -0.5
    z = 0.20
    hand_ewrt_flat_body = geometry_pb2.Vec3(x=x, y=y, z=z)

    # Orientation of the hand is a 90-degree rotation about body z, e.g. x_hand points along -y_body
    qw = 0.7071068
    qx = 0
    qy = 0
    qz = -0.7071068
    flat_body_Q_hand = geometry_pb2.Quaternion(w=qw, x=qx, y=qy, z=qz)

    return geometry_pb2.SE3Pose(position=hand_ewrt_flat_body, rotation=flat_body_Q_hand)


def freeze_hand_example(config):
    """ This example commands Spot's end-effector to hold a pose expressed in the ODOM and BODY frames,
        demonstrating the differences of holding a pose relative to and expressed in fixed versus moving frame.
        Commanding the hand frame to hold position in ODOM means that even as Spot's base moves, the end-effector
        will remain fixed in space. In contrast, the same pose requested in the BODY frame will cause the hand
        to move in space as the body moves around since the BODY frame is moving in the world.

        Requesting Spot to hold a fixed Cartesian pose expressed in BODY is equivalent to freezing the arm's
        joints. This example also shows how to make a joint request freezer and demonstrates how that request is
        equivalent to the Cartesian BODY referenced command.
    """

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('HelloSpotClient')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    assert robot.has_arm(), "Robot requires an arm to run this example."

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    assert not robot.is_estopped(), "Robot is estopped. Please use an external E-Stop client, " \
                                    "such as the estop SDK example, to configure E-Stop."

    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)

    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Now, we are ready to power on the robot. This call will block until the power
        # is on. Commands would fail if this did not happen. We can also check that the robot is
        # powered at any point.
        robot.logger.info("Powering on robot... This may take a several seconds.")
        robot.power_on(timeout_sec=20)
        assert robot.is_powered_on(), "Robot power on failed."
        robot.logger.info("Robot powered on.")

        # Tell the robot to stand up. The command service is used to issue commands to a robot.
        # The set of valid commands for a robot depends on hardware configuration. See
        # RobotCommandBuilder for more detailed examples on command building. The robot
        # command service requires timesync between the robot and the client.
        robot.logger.info("Commanding robot to stand...")
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        blocking_stand(command_client, timeout_sec=10)
        robot.logger.info("Robot standing.")

        # A hand pose front of and to the side of the robot.
        flat_body_T_hand = get_hand_pose_for_example()

        # Request the end effector to move to a pose expressed in ODOM.  After arriving at the pose request
        # Spot to walk forward. Since the arm command is expressed in ODOM, the hand will remain fixed in space
        # as the robot walks forwards.
        odom_T_flat_body = get_a_tform_b(
            robot_state_client.get_robot_state().kinematic_state.transforms_snapshot,
            ODOM_FRAME_NAME, BODY_FRAME_NAME)
        odom_T_hand = odom_T_flat_body * math_helpers.SE3Pose.from_proto(flat_body_T_hand)
        arm_command = RobotCommandBuilder.arm_pose_command_from_pose(odom_T_hand.to_proto(),
                                                                     ODOM_FRAME_NAME, seconds=2)

        # Construct a RobotCommand from the arm command
        command = RobotCommandBuilder.build_synchro_command(arm_command)

        # Send the request to the robot.
        cmd_id = command_client.robot_command(command)
        robot.logger.info(
            'Moving end-effector to a location in front of and to the side of the robot.')

        # Wait until the arm arrives at the goal.
        block_until_arm_arrives(command_client, cmd_id, timeout_sec=5)

        # Now walk forwards.
        WALK_DIST = 1.0  # meters
        mobility_params = mobility_params_for_slow_walk()
        command = RobotCommandBuilder.synchro_trajectory_command_in_body_frame(
            WALK_DIST, 0, 0,
            robot_state_client.get_robot_state().kinematic_state.transforms_snapshot,
            params=mobility_params)

        end_time = 10  # seconds
        cmd_id = command_client.robot_command(command, end_time_secs=time.time() + end_time)
        robot.logger.info('Walking forward with hand fixed in world.')

        # Wait until the body arrives at the goal.
        block_for_trajectory_cmd(command_client, cmd_id, timeout_sec=10)

        # Now request the same hand pose, but this time make the request in the BODY frame.
        # After arriving at the pose, request Spot to walk backwards. Since the arm command
        # is expressed in BODY, the hand will remain fixed relative to the robot's base as
        # the robot walks backwards.
        arm_command = RobotCommandBuilder.arm_pose_command_from_pose(flat_body_T_hand,
                                                                     BODY_FRAME_NAME, seconds=2)

        # Construct a RobotCommand from the arm command
        command = RobotCommandBuilder.build_synchro_command(arm_command)

        # Send the request to the robot.
        cmd_id = command_client.robot_command(command)
        robot.logger.info(
            'Moving end-effector to a location in front of and to the side of the robot.')

        # Wait until the body arrives at the goal.
        block_until_arm_arrives(command_client, cmd_id, timeout_sec=5)

        # Now walk backwards.
        command = RobotCommandBuilder.synchro_trajectory_command_in_body_frame(
            -WALK_DIST, 0, 0,
            robot_state_client.get_robot_state().kinematic_state.transforms_snapshot,
            params=mobility_params)

        # Send the request
        cmd_id = command_client.robot_command(command, end_time_secs=time.time() + end_time)
        robot.logger.info('Walking backwards with hand fixed in body.')

        # Wait until the body arrives at the goal.
        block_for_trajectory_cmd(command_client, cmd_id, timeout_sec=10)

        # A potentially easier way to freeze the hand relative to the robot is to use a joint move request
        # to lock the joint angles in place.  Our SDK provides a helper for making arm joint freeze requests.
        # The command to lock the joints requires no user input and can be called from any arm configuration.
        command = RobotCommandBuilder.arm_joint_freeze_command()

        # Issue a mobility command to test the joint command freezer call.
        command = RobotCommandBuilder.synchro_trajectory_command_in_body_frame(
            0.75 * WALK_DIST, 0, 0,
            robot_state_client.get_robot_state().kinematic_state.transforms_snapshot,
            params=mobility_params, build_on_command=command)

        # Send the request
        cmd_id = command_client.robot_command(command, end_time_secs=time.time() + end_time)
        robot.logger.info('Walking with joint move to freeze.')

        # Wait until the body arrives at the goal.
        block_for_trajectory_cmd(command_client, cmd_id, timeout_sec=10)

        # And return to start.
        command = RobotCommandBuilder.synchro_trajectory_command_in_body_frame(
            -0.75 * WALK_DIST, 0, 0,
            robot_state_client.get_robot_state().kinematic_state.transforms_snapshot,
            params=mobility_params)

        # Send the request
        cmd_id = command_client.robot_command(command, end_time_secs=time.time() + end_time)

        # Wait until the body arrives at the goal.
        block_for_trajectory_cmd(command_client, cmd_id, timeout_sec=10)

        robot.logger.info('Done.')

        # Exiting the context manager "with bosdyn.client.lease.LeaseKeepAlive()" will return the
        # lease and the robot will sit down and power off.


def main():
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()
    try:
        freeze_hand_example(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception("Threw an exception")
        return False


if __name__ == '__main__':
    if not main():
        sys.exit(1)
