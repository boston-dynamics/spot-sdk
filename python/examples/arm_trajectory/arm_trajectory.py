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

from bosdyn.client.robot_command import RobotCommandClient, RobotCommandBuilder, blocking_stand
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client import math_helpers

from bosdyn.api import arm_command_pb2
import bosdyn.api.gripper_command_pb2
from bosdyn.client.frame_helpers import *
from bosdyn.api import geometry_pb2
from bosdyn.util import seconds_to_duration
from bosdyn.api import trajectory_pb2
from bosdyn.api import synchronized_command_pb2
from bosdyn.api import robot_command_pb2


import traceback
import time


def arm_trajectory(config):

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('ArmTrajectory')
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


            # Move the arm along a simple trajectory

            vo_T_flat_body = get_a_tform_b(robot_state_client.get_robot_state().kinematic_state.transforms_snapshot,
                          VISION_FRAME_NAME, GRAV_ALIGNED_BODY_FRAME_NAME)

            x = 0.75     # a reasonable position in front of the robot
            y1 = 0 # centered
            y2 = 0.4 # 0.4 meters to the robot's left
            y3 = -0.4 # 0.4 meters to the robot's right
            z = 0       # at the body's height

            # Use the same rotation as the robot's body.
            rotation = math_helpers.Quat()

            t_first_point = 0    # first point starts at t = 0 for the trajectory.
            t_second_point = 4.0 # trajectory will last 1.0 seconds
            t_third_point = 8.0 # trajectory will last 1.0 seconds

            # Build the two points in the trajectory
            hand_pose1 = math_helpers.SE3Pose(x=x, y=y1, z=z, rot=rotation)
            hand_pose2 = math_helpers.SE3Pose(x=x, y=y2, z=z, rot=rotation)
            hand_pose3 = math_helpers.SE3Pose(x=x, y=y3, z=z, rot=rotation)

            # Build the points by combining the pose and times into protos.
            traj_point1 = trajectory_pb2.SE3TrajectoryPoint(
                pose=hand_pose1.to_proto(), time_since_reference=seconds_to_duration(t_first_point))
            traj_point2 = trajectory_pb2.SE3TrajectoryPoint(
                pose=hand_pose2.to_proto(), time_since_reference=seconds_to_duration(t_second_point))
            traj_point3 = trajectory_pb2.SE3TrajectoryPoint(
                pose=hand_pose3.to_proto(), time_since_reference=seconds_to_duration(t_third_point))

            # Build the trajectory proto by combining the two points
            hand_traj = trajectory_pb2.SE3Trajectory(points=[traj_point1, traj_point2, traj_point3])

            # Build the command by taking the trajectory and specifying the frame it is expressed
            # in.
            #
            # In this case, we want to specify the trajectory in the body's frame, so we set the
            # root frame name to the the flat body frame.
            arm_cartesian_command = arm_command_pb2.ArmCartesianCommand.Request(
                pose_trajectory_in_task=hand_traj, root_frame_name=GRAV_ALIGNED_BODY_FRAME_NAME)

            # Pack everything up in protos.
            arm_command = arm_command_pb2.ArmCommand.Request(
                arm_cartesian_command=arm_cartesian_command)

            synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
                arm_command=arm_command)

            robot_command = robot_command_pb2.RobotCommand(
                synchronized_command=synchronized_command)

            # Keep the gripper closed the whole time.
            robot_command = RobotCommandBuilder.claw_gripper_open_fraction_command(0, build_on_command=robot_command)

            robot.logger.info("Sending trajectory command...")

            # Send the trajectory to the robot.
            cmd_id = command_client.robot_command(robot_command)

            # Wait until the arm arrives at the goal.
            while True:
                feedback_resp = command_client.robot_command_feedback(cmd_id)
                robot.logger.info('Distance to final point: ' + '{:.2f} meters'.format(feedback_resp.feedback.synchronized_feedback.arm_command_feedback.arm_cartesian_feedback.measured_pos_distance_to_goal) + ', {:.2f} radians'.format(feedback_resp.feedback.synchronized_feedback.arm_command_feedback.arm_cartesian_feedback.measured_rot_distance_to_goal))

                if feedback_resp.feedback.synchronized_feedback.arm_command_feedback.arm_cartesian_feedback.status == arm_command_pb2.ArmCartesianCommand.Feedback.STATUS_TRAJECTORY_COMPLETE:
                    robot.logger.info('Move complete.')
                    break
                time.sleep(0.1)

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
        arm_trajectory(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception("Threw an exception")
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
