# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use Spot's arm.
"""
import argparse
import sys

import bosdyn.client
import bosdyn.client.estop
import bosdyn.client.lease
import bosdyn.client.util

from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient, blocking_stand
from bosdyn.client.frame_helpers import *
from bosdyn.api import geometry_pb2
from bosdyn.api import robot_command_pb2
from bosdyn.api import synchronized_command_pb2

from bosdyn.api import trajectory_pb2
from google.protobuf import duration_pb2
from bosdyn.util import seconds_to_duration
from bosdyn.api import arm_command_pb2

import traceback
import time
from bosdyn.util import seconds_to_duration


def force_wrench(config):
    """Commanding a force / wrench with Spot's arm."""

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('ForceTrajectoryClient')
    robot = sdk.create_robot(config.hostname)
    robot.authenticate(config.username, config.password)
    robot.time_sync.wait_for_sync()

    assert robot.has_arm(), "Robot requires an arm to run this example."

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    assert not robot.is_estopped(), "Robot is estopped. Please use an external E-Stop client, " \
                                    "such as the estop SDK example, to configure E-Stop."

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

            # Unstow the arm
            unstow = RobotCommandBuilder.arm_ready_command()

            # Issue the command via the RobotCommandClient
            command_client.robot_command(unstow)

            robot.logger.info("Unstow command issued.")
            time.sleep(3.0)

            # Demonstrate an example force trajectory by ramping up and down a vertical force over
            # 10 seconds

            f_x0 = 0  # Newtons
            f_y0 = 0
            f_z0 = 0

            f_x1 = 0  # Newtons
            f_y1 = 0
            f_z1 = -10  # push down

            # We won't have any rotational torques
            torque_x = 0
            torque_y = 0
            torque_z = 0

            # Duration in seconds.
            traj_duration = 5

            # First point on the trajectory
            force0 = geometry_pb2.Vec3(x=f_x0, y=f_y0, z=f_z0)
            torque0 = geometry_pb2.Vec3(x=torque_x, y=torque_y, z=torque_z)

            wrench0 = geometry_pb2.Wrench(force=force0, torque=torque0)
            t0 = seconds_to_duration(0)
            traj_point0 = trajectory_pb2.WrenchTrajectoryPoint(wrench=wrench0,
                                                               time_since_reference=t0)

            # Second point on the trajectory
            force1 = geometry_pb2.Vec3(x=f_x1, y=f_y1, z=f_z1)
            torque1 = geometry_pb2.Vec3(x=torque_x, y=torque_y, z=torque_z)

            wrench1 = geometry_pb2.Wrench(force=force1, torque=torque1)
            t1 = seconds_to_duration(traj_duration)
            traj_point1 = trajectory_pb2.WrenchTrajectoryPoint(wrench=wrench1,
                                                               time_since_reference=t1)

            # Build the trajectory
            trajectory = trajectory_pb2.WrenchTrajectory(points=[traj_point0, traj_point1])

            # Build the full request, putting all axes into force mode.
            arm_cartesian_command = arm_command_pb2.ArmCartesianCommand.Request(
                root_frame_name=ODOM_FRAME_NAME, wrench_trajectory_in_task=trajectory,
                x_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_FORCE,
                y_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_FORCE,
                z_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_FORCE,
                rx_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_FORCE,
                ry_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_FORCE,
                rz_axis=arm_command_pb2.ArmCartesianCommand.Request.AXIS_MODE_FORCE)
            arm_command = arm_command_pb2.ArmCommand.Request(
                arm_cartesian_command=arm_cartesian_command)
            synchronized_command = synchronized_command_pb2.SynchronizedCommand.Request(
                arm_command=arm_command)
            robot_command = robot_command_pb2.RobotCommand(
                synchronized_command=synchronized_command)

            # Send the request
            command_client.robot_command(robot_command)
            robot.logger.info('Force trajectory command issued...')

            time.sleep(5.0 + traj_duration)

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
        force_wrench(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception("Threw an exception")
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
