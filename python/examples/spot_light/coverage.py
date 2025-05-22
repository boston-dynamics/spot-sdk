# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use Spot's arm.
"""

import time

from bosdyn.api import arm_command_pb2, robot_command_pb2, synchronized_command_pb2, trajectory_pb2
from bosdyn.client import math_helpers
from bosdyn.client.frame_helpers import GRAV_ALIGNED_BODY_FRAME_NAME
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient, blocking_stand
from bosdyn.util import seconds_to_duration


def arm_trajectory(robot, x, y_max, z_max, z_min, z_step, speed):
    y_min = - y_max
    z_min = z_max - 0.001  # TODO remove

    # Use the same rotation as the robot's body.
    rotation = math_helpers.Quat()

    # Define times (in seconds) for each point in the trajectory.
    t_horizontal_mot = (y_max * 2) / speed
    t_vertical_mot = z_step / speed
    t = 0.0

    # Move the arm along a simple trajectory.
    y1 = y_max
    y2 = y_min
    z = z_max
    trajectory = []
    while z >= z_min:
        print(x, y1, z, t)
        hand_pose = math_helpers.SE3Pose(x=x, y=y1, z=z, rot=rotation)
        trajectory.append(trajectory_pb2.SE3TrajectoryPoint(
            pose=hand_pose.to_proto(), time_since_reference=seconds_to_duration(t)))
        t += t_horizontal_mot

        print(x, y2, z, t)
        hand_pose = math_helpers.SE3Pose(x=x, y=y2, z=z, rot=rotation)
        trajectory.append(trajectory_pb2.SE3TrajectoryPoint(
            pose=hand_pose.to_proto(), time_since_reference=seconds_to_duration(t)))
        t += t_vertical_mot
        y1, y2 = y2, y1  # flip y limits so we go in the opposite direction
        z -= z_step

    # pre-stowing pose
    x -= 0.1
    y = 0.0
    z = 0.2
    t += t_vertical_mot
    hand_pose = math_helpers.SE3Pose(x=x, y=y, z=z, rot=rotation)
    trajectory.append(trajectory_pb2.SE3TrajectoryPoint(
        pose=hand_pose.to_proto(), time_since_reference=seconds_to_duration(t)))

    # Build the trajectory proto by combining the points.
    hand_traj = trajectory_pb2.SE3Trajectory(points=trajectory)

    # Build the command by taking the trajectory and specifying the frame it is expressed
    # in.
    #
    # In this case, we want to specify the trajectory in the body's frame, so we set the
    # root frame name to the flat body frame.
    arm_cartesian_command = arm_command_pb2.ArmCartesianCommand.Request(
        pose_trajectory_in_task=hand_traj, root_frame_name=GRAV_ALIGNED_BODY_FRAME_NAME)

    # Pack everything up in protos.
    arm_command = arm_command_pb2.ArmCommand.Request(
        arm_cartesian_command=arm_cartesian_command)

    synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
        arm_command=arm_command)

    robot_command = robot_command_pb2.RobotCommand(synchronized_command=synchronized_command)

    # Keep the gripper closed the whole time.
    robot_command = RobotCommandBuilder.claw_gripper_open_fraction_command(
        0, build_on_command=robot_command)

    robot.logger.info('Sending trajectory command...')

    # Send the trajectory to the robot.
    cmd_id = robot.client.robot_command(robot_command)

    # Wait until the arm arrives at the goal.
    while True:
        feedback_resp = robot.client.robot_command_feedback(cmd_id)
        measured_pos_distance_to_goal = feedback_resp.feedback.synchronized_feedback.arm_command_feedback.arm_cartesian_feedback.measured_pos_distance_to_goal
        measured_rot_distance_to_goal = feedback_resp.feedback.synchronized_feedback.arm_command_feedback.arm_cartesian_feedback.measured_rot_distance_to_goal
        robot.logger.info('Distance to go: %.2f meters, %.2f radians',
                          measured_pos_distance_to_goal, measured_rot_distance_to_goal)

        if feedback_resp.feedback.synchronized_feedback.arm_command_feedback.arm_cartesian_feedback.status == arm_command_pb2.ArmCartesianCommand.Feedback.STATUS_TRAJECTORY_COMPLETE:
            robot.logger.info('Move complete.')
            break
        time.sleep(0.1)
