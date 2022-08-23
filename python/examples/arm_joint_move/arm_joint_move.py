# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use Spot's arm.
"""
import argparse
import sys
import time

from google.protobuf import wrappers_pb2

import bosdyn.client
import bosdyn.client.estop
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import arm_command_pb2, estop_pb2, robot_command_pb2, synchronized_command_pb2
from bosdyn.client.estop import EstopClient
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                         block_until_arm_arrives, blocking_stand)
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.util import duration_to_seconds


def verify_estop(robot):
    """Verify the robot is not estopped"""

    client = robot.ensure_client(EstopClient.default_service_name)
    if client.get_status().stop_level != estop_pb2.ESTOP_LEVEL_NONE:
        error_message = "Robot is estopped. Please use an external E-Stop client, such as the" \
        " estop SDK example, to configure E-Stop."
        robot.logger.error(error_message)
        raise Exception(error_message)


def make_robot_command(arm_joint_traj):
    """ Helper function to create a RobotCommand from an ArmJointTrajectory.
        The returned command will be a SynchronizedCommand with an ArmJointMoveCommand
        filled out to follow the passed in trajectory. """

    joint_move_command = arm_command_pb2.ArmJointMoveCommand.Request(trajectory=arm_joint_traj)
    arm_command = arm_command_pb2.ArmCommand.Request(arm_joint_move_command=joint_move_command)
    sync_arm = synchronized_command_pb2.SynchronizedCommand.Request(arm_command=arm_command)
    arm_sync_robot_cmd = robot_command_pb2.RobotCommand(synchronized_command=sync_arm)
    return RobotCommandBuilder.build_synchro_command(arm_sync_robot_cmd)


def print_feedback(feedback_resp, logger):
    """ Helper function to query for ArmJointMove feedback, and print it to the console.
        Returns the time_to_goal value reported in the feedback """
    joint_move_feedback = feedback_resp.feedback.synchronized_feedback.arm_command_feedback.arm_joint_move_feedback
    logger.info(f'  planner_status = {joint_move_feedback.planner_status}')
    logger.info(
        f'  time_to_goal = {duration_to_seconds(joint_move_feedback.time_to_goal):.2f} seconds.')

    # Query planned_points to determine target pose of arm
    logger.info('  planned_points:')
    for idx, points in enumerate(joint_move_feedback.planned_points):
        pos = points.position
        pos_str = f'sh0 = {pos.sh0.value:.3f}, sh1 = {pos.sh1.value:.3f}, el0 = {pos.el0.value:.3f}, el1 = {pos.el1.value:.3f}, wr0 = {pos.wr0.value:.3f}, wr1 = {pos.wr1.value:.3f}'
        logger.info(f'    {idx}: {pos_str}')
    return duration_to_seconds(joint_move_feedback.time_to_goal)


def joint_move_example(config):
    """A simple example of using the Boston Dynamics API to command Spot's arm to perform joint moves."""

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('ArmJointMoveClient')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    assert robot.has_arm(), "Robot requires an arm to run this example."

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    verify_estop(robot)

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

        # Example 1: issue a single point trajectory without a time_since_reference in order to perform
        # a minimum time joint move to the goal obeying the default acceleration and velocity limits.
        sh0 = 0.0692
        sh1 = -1.882
        el0 = 1.652
        el1 = -0.0691
        wr0 = 1.622
        wr1 = 1.550

        traj_point = RobotCommandBuilder.create_arm_joint_trajectory_point(
            sh0, sh1, el0, el1, wr0, wr1)
        arm_joint_traj = arm_command_pb2.ArmJointTrajectory(points=[traj_point])
        # Make a RobotCommand
        command = make_robot_command(arm_joint_traj)

        # Send the request
        cmd_id = command_client.robot_command(command)
        robot.logger.info('Moving arm to position 1.')

        # Query for feedback to determine how long the goto will take.
        feedback_resp = command_client.robot_command_feedback(cmd_id)
        robot.logger.info("Feedback for Example 1: single point goto")
        time_to_goal = print_feedback(feedback_resp, robot.logger)
        time.sleep(time_to_goal)

        # Example 2: Single point trajectory with maximum acceleration/velocity constraints specified such
        # that the solver has to modify the desired points to honor the constraints
        sh0 = 0.0
        sh1 = -2.0
        el0 = 2.6
        el1 = 0.0
        wr0 = -0.6
        wr1 = 0.0
        max_vel = wrappers_pb2.DoubleValue(value=1)
        max_acc = wrappers_pb2.DoubleValue(value=5)
        traj_point = RobotCommandBuilder.create_arm_joint_trajectory_point(
            sh0, sh1, el0, el1, wr0, wr1, time_since_reference_secs=1.5)
        arm_joint_traj = arm_command_pb2.ArmJointTrajectory(points=[traj_point],
                                                            maximum_velocity=max_vel,
                                                            maximum_acceleration=max_acc)
        # Make a RobotCommand
        command = make_robot_command(arm_joint_traj)

        # Send the request
        cmd_id = command_client.robot_command(command)
        robot.logger.info('Requesting a single point trajectory with unsatisfiable constraints.')

        # Query for feedback
        feedback_resp = command_client.robot_command_feedback(cmd_id)
        robot.logger.info("Feedback for Example 2: planner modifies trajectory")
        time_to_goal = print_feedback(feedback_resp, robot.logger)
        time.sleep(time_to_goal)

        # Example 3: Single point trajectory with default acceleration/velocity constraints and
        # time_since_reference_secs large enough such that the solver can plan a solution to the
        # points that also satisfies the constraints.
        sh0 = 0.0692
        sh1 = -1.882
        el0 = 1.652
        el1 = -0.0691
        wr0 = 1.622
        wr1 = 1.550
        traj_point = RobotCommandBuilder.create_arm_joint_trajectory_point(
            sh0, sh1, el0, el1, wr0, wr1, time_since_reference_secs=1.5)

        arm_joint_traj = arm_command_pb2.ArmJointTrajectory(points=[traj_point])

        # Make a RobotCommand
        command = make_robot_command(arm_joint_traj)

        # Send the request
        cmd_id = command_client.robot_command(command)
        robot.logger.info('Requesting a single point trajectory with satisfiable constraints.')

        # Query for feedback
        feedback_resp = command_client.robot_command_feedback(cmd_id)
        robot.logger.info("Feedback for Example 3: unmodified trajectory")
        time_to_goal = print_feedback(feedback_resp, robot.logger)
        time.sleep(time_to_goal)

        # ----- Do a two-point joint move trajectory ------

        # First stow the arm.
        # Build the stow command using RobotCommandBuilder
        stow = RobotCommandBuilder.arm_stow_command()

        # Issue the command via the RobotCommandClient
        stow_command_id = command_client.robot_command(stow)

        robot.logger.info("Stow command issued.")
        block_until_arm_arrives(command_client, stow_command_id, 3.0)

        # First point position
        sh0 = -1.5
        sh1 = -0.8
        el0 = 1.7
        el1 = 0.0
        wr0 = 0.5
        wr1 = 0.0

        # First point time (seconds)
        first_point_t = 2.0

        # Build the proto for the trajectory point.
        traj_point1 = RobotCommandBuilder.create_arm_joint_trajectory_point(
            sh0, sh1, el0, el1, wr0, wr1, first_point_t)

        # Second point position
        sh0 = 1.0
        sh1 = -0.2
        el0 = 1.3
        el1 = -1.3
        wr0 = -1.5
        wr1 = 1.5

        # Second point time (seconds)
        second_point_t = 4.0

        # Build the proto for the second trajectory point.
        traj_point2 = RobotCommandBuilder.create_arm_joint_trajectory_point(
            sh0, sh1, el0, el1, wr0, wr1, second_point_t)

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
        arm_joint_traj = arm_command_pb2.ArmJointTrajectory(points=[traj_point1, traj_point2],
                                                            maximum_velocity=max_vel,
                                                            maximum_acceleration=max_acc)
        # Make a RobotCommand
        command = make_robot_command(arm_joint_traj)

        # Send the request
        cmd_id = command_client.robot_command(command)
        robot.logger.info('Moving arm along 2-point joint trajectory.')

        # Query for feedback to determine exactly what the planned trajectory is.
        feedback_resp = command_client.robot_command_feedback(cmd_id)
        robot.logger.info("Feedback for 2-point joint trajectory")
        print_feedback(feedback_resp, robot.logger)

        # Wait until the move completes before powering off.
        block_until_arm_arrives(command_client, cmd_id, second_point_t + 3.0)

        # Power the robot off. By specifying "cut_immediately=False", a safe power off command
        # is issued to the robot. This will attempt to sit the robot before powering off.
        robot.power_off(cut_immediately=False, timeout_sec=20)
        assert not robot.is_powered_on(), "Robot power off failed."
        robot.logger.info("Robot safely powered off.")


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
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
