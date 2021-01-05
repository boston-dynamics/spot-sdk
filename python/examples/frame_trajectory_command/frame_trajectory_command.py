# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Simple robot command capture tutorial."""

import argparse
import math
import sys
import time
import bosdyn.client
import bosdyn.client.util
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.robot_command import RobotCommandClient, RobotCommandBuilder, blocking_stand
from bosdyn.api import geometry_pb2 as geo
from bosdyn.client import math_helpers
from bosdyn.client.frame_helpers import ODOM_FRAME_NAME, VISION_FRAME_NAME, get_odom_tform_body, get_vision_tform_body
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive


def main():
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    options = parser.parse_args()

    # Create robot object.
    sdk = bosdyn.client.create_standard_sdk('RobotCommandMaster')
    robot = sdk.create_robot(options.hostname)
    robot.authenticate(options.username, options.password)

    # Check that an estop is connected with the robot so that the robot commands can be executed.
    assert not robot.is_estopped(), "Robot is estopped. Please use an external E-Stop client, " \
                                    "such as the estop SDK example, to configure E-Stop."

    # Create the lease client.
    lease_client = robot.ensure_client(LeaseClient.default_service_name)
    lease = lease_client.acquire()
    robot.time_sync.wait_for_sync()
    lk = bosdyn.client.lease.LeaseKeepAlive(lease_client)

    # Setup clients for the robot state and robot command services.
    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    robot_command_client = robot.ensure_client(RobotCommandClient.default_service_name)

    # Power on the robot and stand it up.
    robot.power_on()
    blocking_stand(robot_command_client)

    # Get robot state information. Specifically, we are getting the vision_tform_body transform to understand
    # the robot's current position in the vision frame.
    vision_tform_body = get_vision_tform_body(
        robot_state_client.get_robot_state().kinematic_state.transforms_snapshot)

    # We want to command a trajectory to go forward one meter in the x-direction of the body.
    # It is simple to define this trajectory relative to the body frame, since we know that will be
    # just 1 meter forward in the x-axis of the body.
    # Note that the rotation is just math_helpers.Quat(), which is the identity quaternion. We want the
    # rotation of the body at the goal to match the rotation of the body currently, so we do not need
    # to transform the rotation.
    body_tform_goal = math_helpers.SE3Pose(x=1, y=0, z=0, rot=math_helpers.Quat())
    # We can then transform this transform to get the goal position relative to the vision frame.
    vision_tform_goal = vision_tform_body * body_tform_goal

    # Command the robot to go to the goal point in the vision frame. The command will stop at the new
    # position in the vision frame.
    robot_cmd = RobotCommandBuilder.synchro_se2_trajectory_point_command(goal_x=vision_tform_goal.x,
                                                     goal_y=vision_tform_goal.y,
                                                     goal_heading=vision_tform_goal.rot.to_yaw(),
                                                     frame_name=VISION_FRAME_NAME)
    end_time = 2.0
    robot_command_client.robot_command(lease=None, command=robot_cmd,
                                       end_time_secs=time.time() + end_time)
    time.sleep(end_time)

    # Get new robot state information after moving the robot. Here we are getting the transform odom_tform_body,
    # which describes the robot body's position in the odom frame.
    odom_tform_body = get_odom_tform_body(
        robot_state_client.get_robot_state().kinematic_state.transforms_snapshot)

    # We want to command a trajectory to go backwards one meter and to the left one meter.
    # It is simple to define this trajectory relative to the body frame, since we know that will be
    # just 1 meter backwards (negative-value) in the x-axis of the body and one meter left (positive-value)
    # in the y-axis of the body.
    body_tform_goal = math_helpers.SE3Pose(x=-1, y=1, z=0, rot=math_helpers.Quat())
    # We can then transform this transform to get the goal position relative to the odom frame.
    odom_tform_goal = odom_tform_body * body_tform_goal

    # Command the robot to go to the goal point in the odom frame. The command will stop at the new
    # position in the odom frame.
    robot_cmd = RobotCommandBuilder.synchro_se2_trajectory_point_command(goal_x=odom_tform_goal.x,
                                                     goal_y=odom_tform_goal.y,
                                                     goal_heading=odom_tform_goal.rot.to_yaw(),
                                                     frame_name=ODOM_FRAME_NAME)
    end_time = 5.0
    robot_command_client.robot_command(lease=None, command=robot_cmd,
                                       end_time_secs=time.time() + end_time)
    time.sleep(end_time)

    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
