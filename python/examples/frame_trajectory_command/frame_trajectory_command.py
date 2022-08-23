# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Command the robot to go to an offset position using a trajectory command."""

import logging
import math
import sys
import time

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import basic_command_pb2
from bosdyn.api import geometry_pb2 as geo
from bosdyn.api.basic_command_pb2 import RobotCommandFeedbackStatus
from bosdyn.client import math_helpers
from bosdyn.client.frame_helpers import (BODY_FRAME_NAME, ODOM_FRAME_NAME, VISION_FRAME_NAME,
                                         get_se2_a_tform_b)
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                         block_for_trajectory_cmd, blocking_stand)
from bosdyn.client.robot_state import RobotStateClient

_LOGGER = logging.getLogger(__name__)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('--dx', default=0, type=float,
                        help='Position offset in body frame (meters forward).')
    parser.add_argument('--dy', default=0, type=float,
                        help='Position offset in body frame (meters left).')
    parser.add_argument('--dyaw', default=0, type=float,
                        help='Position offset in body frame (degrees ccw).')
    parser.add_argument('--frame', choices=[VISION_FRAME_NAME, ODOM_FRAME_NAME],
                        default=ODOM_FRAME_NAME, help='Send the command in this frame.')
    parser.add_argument('--stairs', action='store_true', help='Move the robot in stairs mode.')
    options = parser.parse_args()
    bosdyn.client.util.setup_logging(options.verbose)

    # Create robot object.
    sdk = bosdyn.client.create_standard_sdk('RobotCommandMaster')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    # Check that an estop is connected with the robot so that the robot commands can be executed.
    assert not robot.is_estopped(), "Robot is estopped. Please use an external E-Stop client, " \
                                    "such as the estop SDK example, to configure E-Stop."

    # Create the lease client.
    lease_client = robot.ensure_client(LeaseClient.default_service_name)

    # Setup clients for the robot state and robot command services.
    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    robot_command_client = robot.ensure_client(RobotCommandClient.default_service_name)

    with LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Power on the robot and stand it up.
        robot.time_sync.wait_for_sync()
        robot.power_on()
        blocking_stand(robot_command_client)

        try:
            return relative_move(options.dx, options.dy, math.radians(options.dyaw), options.frame,
                                 robot_command_client, robot_state_client, stairs=options.stairs)
        finally:
            # Send a Stop at the end, regardless of what happened.
            robot_command_client.robot_command(RobotCommandBuilder.stop_command())


def relative_move(dx, dy, dyaw, frame_name, robot_command_client, robot_state_client, stairs=False):
    transforms = robot_state_client.get_robot_state().kinematic_state.transforms_snapshot

    # Build the transform for where we want the robot to be relative to where the body currently is.
    body_tform_goal = math_helpers.SE2Pose(x=dx, y=dy, angle=dyaw)
    # We do not want to command this goal in body frame because the body will move, thus shifting
    # our goal. Instead, we transform this offset to get the goal position in the output frame
    # (which will be either odom or vision).
    out_tform_body = get_se2_a_tform_b(transforms, frame_name, BODY_FRAME_NAME)
    out_tform_goal = out_tform_body * body_tform_goal

    # Command the robot to go to the goal point in the specified frame. The command will stop at the
    # new position.
    robot_cmd = RobotCommandBuilder.synchro_se2_trajectory_point_command(
        goal_x=out_tform_goal.x, goal_y=out_tform_goal.y, goal_heading=out_tform_goal.angle,
        frame_name=frame_name, params=RobotCommandBuilder.mobility_params(stair_hint=stairs))
    end_time = 10.0
    cmd_id = robot_command_client.robot_command(lease=None, command=robot_cmd,
                                                end_time_secs=time.time() + end_time)
    # Wait until the robot has reached the goal.
    while True:
        feedback = robot_command_client.robot_command_feedback(cmd_id)
        mobility_feedback = feedback.feedback.synchronized_feedback.mobility_command_feedback
        if mobility_feedback.status != RobotCommandFeedbackStatus.STATUS_PROCESSING:
            print("Failed to reach the goal")
            return False
        traj_feedback = mobility_feedback.se2_trajectory_feedback
        if (traj_feedback.status == traj_feedback.STATUS_AT_GOAL and
                traj_feedback.body_movement_status == traj_feedback.BODY_STATUS_SETTLED):
            print("Arrived at the goal.")
            return True
        time.sleep(1)

    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
