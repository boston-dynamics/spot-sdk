# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

""" Tutorial for how to use the arm impedance command
"""
import argparse
import math
import sys
import time

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import (arm_command_pb2, geometry_pb2, robot_command_pb2, synchronized_command_pb2,
                        trajectory_pb2)
from bosdyn.api.spot import robot_command_pb2 as spot_command_pb2
from bosdyn.client import math_helpers
from bosdyn.client.frame_helpers import (BODY_FRAME_NAME, GRAV_ALIGNED_BODY_FRAME_NAME,
                                         GROUND_PLANE_FRAME_NAME, ODOM_FRAME_NAME, get_a_tform_b)
from bosdyn.client.math_helpers import Quat, SE3Pose
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                         block_until_arm_arrives, blocking_stand)
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.util import seconds_to_duration


def impedance_command(config):
    """Sending an impedance command with the spot arm"""

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('ArmImpedanceClient')
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

        # Tell the robot to stand up, parameterized to enable the body to adjust its height to
        # assist manipulation. For this demo, that means the robot's base will descend, enabling
        # the hand to reach the ground.
        # The command service is used to issue commands to a robot.
        # The set of valid commands for a robot depends on hardware configuration. See
        # RobotCommandBuilder for more detailed examples on command building. The robot
        # command service requires timesync between the robot and the client.
        robot.logger.info("Commanding robot to stand...")
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)

        body_control = spot_command_pb2.BodyControlParams(
            body_assist_for_manipulation=spot_command_pb2.BodyControlParams.
            BodyAssistForManipulation(enable_hip_height_assist=True, enable_body_yaw_assist=False))
        blocking_stand(command_client, timeout_sec=10,
                       params=spot_command_pb2.MobilityParams(body_control=body_control))
        robot.logger.info("Robot standing.")

        # Define a stand command that we'll send with the rest of our arm commands so we keep
        # adjusting the body for the arm
        stand_command = RobotCommandBuilder.synchro_stand_command(
            params=spot_command_pb2.MobilityParams(body_control=body_control))

        # First, let's pick a task frame that is in front of the robot on the ground.
        robot_state = robot_state_client.get_robot_state()
        odom_T_grav_body = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot,
                                         ODOM_FRAME_NAME, GRAV_ALIGNED_BODY_FRAME_NAME)

        odom_T_gpe = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot, ODOM_FRAME_NAME,
                                   GROUND_PLANE_FRAME_NAME)

        # Get the frame on the ground right underneath the center of the body.
        odom_T_ground_body = odom_T_grav_body
        odom_T_ground_body.z = odom_T_gpe.z

        # Now, get the frame that is 60cm in front of this frame, right in front of the robot.
        odom_T_task = odom_T_ground_body * SE3Pose(x=0.6, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0))

        # Now, let's set our tool frame to be the tip of the robot's bottom jaw. Flip the
        # orientation so that when the hand is pointed downwards, the tool's z-axis is
        # pointed upward.
        wr1_T_tool = SE3Pose(0.23589, 0, -0.03943, Quat.from_pitch(-math.pi / 2))

        # Unstow the arm
        unstow = RobotCommandBuilder.arm_ready_command(build_on_command=stand_command)

        # Issue the command via the RobotCommandClient
        unstow_command_id = command_client.robot_command(unstow)
        robot.logger.info("Unstow command issued.")
        block_until_arm_arrives(command_client, unstow_command_id, 3.0)

        # Now, do a Cartesian move with the hand pointed downward a little above the task frame.
        robot_cmd = robot_command_pb2.RobotCommand()
        robot_cmd.CopyFrom(stand_command)  # Make sure we keep adjusting the body for the arm
        arm_cart_cmd = robot_cmd.synchronized_command.arm_command.arm_cartesian_command
        # Set up our root frame, task frame, and tool frame.
        arm_cart_cmd.root_frame_name = ODOM_FRAME_NAME
        arm_cart_cmd.root_tform_task.CopyFrom(odom_T_task.to_proto())
        arm_cart_cmd.wrist_tform_tool.CopyFrom(wr1_T_tool.to_proto())

        # Do a single point goto to 20cm above the task frame.
        cartesian_traj = arm_cart_cmd.pose_trajectory_in_task
        traj_pt = cartesian_traj.points.add()
        traj_pt.time_since_reference.CopyFrom(seconds_to_duration(2.0))
        traj_pt.pose.CopyFrom(SE3Pose(0, 0, 0.2, Quat(1, 0, 0, 0)).to_proto())

        # Execute the Cartesian command.
        cmd_id = command_client.robot_command(robot_cmd)
        block_until_arm_arrives(command_client, cmd_id, 3.0)

        # First, let's do an impedance command where we set all of our stiffnesses high and
        # move around. This will act similar to a position command, but be slightly less stiff.
        robot_cmd = robot_command_pb2.RobotCommand()
        robot_cmd.CopyFrom(stand_command)  # Make sure we keep adjusting the body for the arm
        impedance_cmd = robot_cmd.synchronized_command.arm_command.arm_impedance_command

        # Set up our root frame, task frame, and tool frame.
        impedance_cmd.root_frame_name = ODOM_FRAME_NAME
        impedance_cmd.root_tform_task.CopyFrom(odom_T_task.to_proto())
        impedance_cmd.wrist_tform_tool.CopyFrom(wr1_T_tool.to_proto())

        # Set up stiffness and damping matrices. Note: if these values are set too high,
        # the arm can become unstable. Currently, these are the max stiffness and
        # damping values that can be set.
        impedance_cmd.diagonal_stiffness_matrix.CopyFrom(
            geometry_pb2.Vector(values=[500, 500, 500, 60, 60, 60]))
        impedance_cmd.diagonal_damping_matrix.CopyFrom(
            geometry_pb2.Vector(values=[2.5, 2.5, 2.5, 1.0, 1.0, 1.0]))

        # Set up our `desired_tool` trajectory. This is where we want the tool to be with respect
        # to the task frame. The stiffness we set will drag the tool towards `desired_tool`.
        traj = impedance_cmd.task_tform_desired_tool
        pt1 = traj.points.add()
        pt1.time_since_reference.CopyFrom(seconds_to_duration(2.0))
        pt1.pose.CopyFrom(SE3Pose(0, 0.2, 0.2, Quat(1, 0, 0, 0)).to_proto())
        pt2 = traj.points.add()
        pt2.time_since_reference.CopyFrom(seconds_to_duration(4.0))
        pt2.pose.CopyFrom(SE3Pose(0, 0, 0, Quat(1, 0, 0, 0)).to_proto())

        # Execute the impedance command.
        cmd_id = command_client.robot_command(robot_cmd)
        time.sleep(5.0)

        # Now, let's move along the surface of the ground, exerting a downward force while
        # dragging the arm sideways.
        robot_cmd = robot_command_pb2.RobotCommand()
        robot_cmd.CopyFrom(stand_command)  # Make sure we keep adjusting the body for the arm
        impedance_cmd = robot_cmd.synchronized_command.arm_command.arm_impedance_command

        # Set up our root frame, task frame, and tool frame.
        impedance_cmd.root_frame_name = ODOM_FRAME_NAME
        impedance_cmd.root_tform_task.CopyFrom(odom_T_task.to_proto())
        impedance_cmd.wrist_tform_tool.CopyFrom(wr1_T_tool.to_proto())

        # Set up downward force.
        impedance_cmd.feed_forward_wrench_at_tool_in_desired_tool.force.x = 0
        impedance_cmd.feed_forward_wrench_at_tool_in_desired_tool.force.y = 0
        impedance_cmd.feed_forward_wrench_at_tool_in_desired_tool.force.z = -8.0  # Newtons
        impedance_cmd.feed_forward_wrench_at_tool_in_desired_tool.torque.x = 0
        impedance_cmd.feed_forward_wrench_at_tool_in_desired_tool.torque.y = 0
        impedance_cmd.feed_forward_wrench_at_tool_in_desired_tool.torque.z = 0

        # Set up stiffness and damping matrices. Note that we've set the stiffness in the z-axis
        # to 0 since we're commanding a constant downward force, regardless of where the tool
        # is in z relative to our `desired_tool` frame.
        impedance_cmd.diagonal_stiffness_matrix.CopyFrom(
            geometry_pb2.Vector(values=[500, 500, 0, 60, 60, 60]))
        impedance_cmd.diagonal_damping_matrix.CopyFrom(
            geometry_pb2.Vector(values=[2.5, 2.5, 2.5, 1.0, 1.0, 1.0]))

        # Set up our `desired_tool` trajectory. This is where we want the tool to be with respect to
        # the task frame. The stiffness we set will drag the tool towards `desired_tool`.
        traj = impedance_cmd.task_tform_desired_tool
        pt1 = traj.points.add()
        pt1.time_since_reference.CopyFrom(seconds_to_duration(2.0))
        pt1.pose.CopyFrom(SE3Pose(0, -0.2, 0, Quat(1, 0, 0, 0)).to_proto())
        pt2 = traj.points.add()
        pt2.time_since_reference.CopyFrom(seconds_to_duration(4.0))
        pt2.pose.CopyFrom(SE3Pose(0, 0, 0, Quat(1, 0, 0, 0)).to_proto())

        # Execute the impedance command
        cmd_id = command_client.robot_command(robot_cmd)
        time.sleep(5.0)

        # Stow the arm
        stow_cmd = RobotCommandBuilder.arm_stow_command()
        stow_command_id = command_client.robot_command(stow_cmd)
        robot.logger.info("Stow command issued.")
        block_until_arm_arrives(command_client, stow_command_id, 3.0)

        # Done! When we leave this function, we'll return the lease, and the robot
        # will automatically sit and power off


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args(argv)
    try:
        impedance_command(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception("Threw an exception")
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
