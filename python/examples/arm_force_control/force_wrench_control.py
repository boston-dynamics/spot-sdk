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

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import (arm_command_pb2, geometry_pb2, robot_command_pb2, synchronized_command_pb2,
                        trajectory_pb2)
from bosdyn.api.spot import robot_command_pb2 as spot_command_pb2
from bosdyn.client import math_helpers
from bosdyn.client.frame_helpers import (BODY_FRAME_NAME, GRAV_ALIGNED_BODY_FRAME_NAME,
                                         ODOM_FRAME_NAME, get_a_tform_b)
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                         block_until_arm_arrives, blocking_stand)
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.util import seconds_to_duration


def force_wrench(config):
    """Commanding a force / wrench with Spot's arm."""

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('ForceWrenchClient')
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

        # Tell the robot to stand up, parameterized to enable the body to adjust its height to assist manipulation.
        # For this demo, that means the robot's base will lower enabling the hand to reach the ground.
        # The command service is used to issue commands to a robot.
        # The set of valid commands for a robot depends on hardware configuration. See
        # RobotCommandBuilder for more detailed examples on command building. The robot
        # command service requires timesync between the robot and the client.
        robot.logger.info("Commanding robot to stand...")
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)

        body_control = spot_command_pb2.BodyControlParams(
            body_assist_for_manipulation=spot_command_pb2.BodyControlParams.
            BodyAssistForManipulation(enable_hip_height_assist=True, enable_body_yaw_assist=True))
        blocking_stand(command_client, timeout_sec=10,
                       params=spot_command_pb2.MobilityParams(body_control=body_control))
        robot.logger.info("Robot standing.")

        # Unstow the arm
        unstow = RobotCommandBuilder.arm_ready_command()

        # Issue the command via the RobotCommandClient
        unstow_command_id = command_client.robot_command(unstow)
        robot.logger.info("Unstow command issued.")

        block_until_arm_arrives(command_client, unstow_command_id, 3.0)

        # Start in gravity-compensation mode (but zero force)
        f_x = 0  # Newtons
        f_y = 0
        f_z = 0

        # We won't have any rotational torques
        torque_x = 0
        torque_y = 0
        torque_z = 0

        # Duration in seconds.
        seconds = 1000

        # Use the helper function to build a single wrench
        command = RobotCommandBuilder.arm_wrench_command(f_x, f_y, f_z, torque_x, torque_y,
                                                         torque_z, BODY_FRAME_NAME, seconds)

        # Send the request
        command_client.robot_command(command)
        robot.logger.info('Zero force commanded...')

        time.sleep(5.0)

        # Drive the arm into the ground with a specified force:
        f_z = -5  # Newtons

        # Convert the location from the moving base frame to the world frame.  If we left the command
        # expressed in the body frame, then the body assist would not work.
        robot_state = robot_state_client.get_robot_state()
        odom_T_body = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot,
                                    ODOM_FRAME_NAME, BODY_FRAME_NAME)

        force_in_odom = odom_T_body.rotation.transform_point(x=f_x, y=f_y, z=f_z)
        torque_in_odom = odom_T_body.rotation.transform_point(x=torque_x, y=torque_y, z=torque_z)

        command = RobotCommandBuilder.arm_wrench_command(force_in_odom[0], force_in_odom[1],
                                                         force_in_odom[2], torque_in_odom[0],
                                                         torque_in_odom[1], torque_in_odom[2],
                                                         ODOM_FRAME_NAME, seconds)

        # Send the request
        command_client.robot_command(command)

        time.sleep(5.0)

        # --------------- #

        # Hybrid position-force mode and trajectories.
        #
        # We'll move the arm in an X/Y trajectory while maintaining some force on the ground.
        # Hand will start to the left and move to the right.

        hand_x = 0.75  # in front of the robot.
        hand_y_start = 0.25  # to the left
        hand_y_end = -0.25  # to the right
        hand_z = 0  # will be ignored since we'll have a force in the Z axis.

        f_z = -5  # Newtons

        hand_vec3_start = geometry_pb2.Vec3(x=hand_x, y=hand_y_start, z=hand_z)
        hand_vec3_end = geometry_pb2.Vec3(x=hand_x, y=hand_y_end, z=hand_z)

        qw = 1
        qx = 0
        qy = 0
        qz = 0
        quat = geometry_pb2.Quaternion(w=qw, x=qx, y=qy, z=qz)

        # Build a position trajectory
        hand_pose1_in_flat_body = geometry_pb2.SE3Pose(position=hand_vec3_start, rotation=quat)
        hand_pose2_in_flat_body = geometry_pb2.SE3Pose(position=hand_vec3_end, rotation=quat)

        # Convert the poses to the odometry frame.
        robot_state = robot_state_client.get_robot_state()
        odom_T_flat_body = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot,
                                         ODOM_FRAME_NAME, GRAV_ALIGNED_BODY_FRAME_NAME)
        hand_pose1 = odom_T_flat_body * math_helpers.SE3Pose.from_obj(hand_pose1_in_flat_body)
        hand_pose2 = odom_T_flat_body * math_helpers.SE3Pose.from_obj(hand_pose2_in_flat_body)

        traj_time = 5.0
        time_since_reference = seconds_to_duration(traj_time)

        traj_point1 = trajectory_pb2.SE3TrajectoryPoint(pose=hand_pose1.to_proto(),
                                                        time_since_reference=seconds_to_duration(0))
        traj_point2 = trajectory_pb2.SE3TrajectoryPoint(pose=hand_pose2.to_proto(),
                                                        time_since_reference=time_since_reference)

        hand_traj = trajectory_pb2.SE3Trajectory(points=[traj_point1, traj_point2])

        # We'll use a constant wrench here.  Build a wrench trajectory with a single point.
        # Note that we only need to fill out Z-force because that is the only axis that will
        # be in force mode.
        force_tuple = odom_T_flat_body.rotation.transform_point(x=0, y=0, z=f_z)
        force = geometry_pb2.Vec3(x=force_tuple[0], y=force_tuple[1], z=force_tuple[2])
        torque = geometry_pb2.Vec3(x=0, y=0, z=0)

        wrench = geometry_pb2.Wrench(force=force, torque=torque)

        # We set this point to happen at 0 seconds.  The robot will hold the wrench past that
        # time, so we'll end up with a constant value.
        duration = seconds_to_duration(0)

        traj_point = trajectory_pb2.WrenchTrajectoryPoint(wrench=wrench,
                                                          time_since_reference=duration)
        trajectory = trajectory_pb2.WrenchTrajectory(points=[traj_point])

        arm_cartesian_command = arm_command_pb2.ArmCartesianCommand.Request(
            pose_trajectory_in_task=hand_traj, root_frame_name=ODOM_FRAME_NAME,
            wrench_trajectory_in_task=trajectory,
            x_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_POSITION,
            y_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_POSITION,
            z_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_FORCE,
            rx_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_POSITION,
            ry_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_POSITION,
            rz_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_POSITION)
        arm_command = arm_command_pb2.ArmCommand.Request(
            arm_cartesian_command=arm_cartesian_command)
        synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
            arm_command=arm_command)
        robot_command = robot_command_pb2.RobotCommand(synchronized_command=synchronized_command)

        # Send the request
        command_client.robot_command(robot_command)
        robot.logger.info('Running mixed position and force mode.')

        time.sleep(traj_time + 5.0)

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
        force_wrench(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception("Threw an exception")
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
