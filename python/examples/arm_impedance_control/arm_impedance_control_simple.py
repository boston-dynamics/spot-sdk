# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
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

from arm_impedance_control_helpers import (apply_force_at_current_position,
                                           get_impedance_mobility_params, get_root_T_ground_body)

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.client.frame_helpers import ODOM_FRAME_NAME
from bosdyn.client.math_helpers import Quat, SE3Pose, Vec3
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                         block_until_arm_arrives, blocking_stand)
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.util import seconds_to_duration

ENABLE_STAND_HIP_ASSIST = True
ENABLE_STAND_YAW_ASSIST = False


def impedance_command(config):
    """Sending an impedance command with the spot arm"""

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('ArmImpedanceClient')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    assert robot.has_arm(), 'Robot requires an arm to run this example.'

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    assert not robot.is_estopped(), 'Robot is estopped. Please use an external E-Stop client, ' \
                                    'such as the estop SDK example, to configure E-Stop.'

    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    command_client = robot.ensure_client(RobotCommandClient.default_service_name)
    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)

    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Power the robot on, and get it into a stand.
        power_on_and_stand(robot, command_client)

        # Unstow the arm.
        unstow_arm(robot, command_client)

        # Pick a task frame that is beneath the robot body center, on the ground.
        odom_T_task = get_root_T_ground_body(robot_state=robot_state_client.get_robot_state(),
                                             root_frame_name=ODOM_FRAME_NAME)

        # Set our tool frame to be the tip of the robot's bottom jaw. Flip the orientation so that
        # when the hand is pointed downwards, the tool's z-axis is pointed upward.
        wr1_T_tool = SE3Pose(0.23589, 0, -0.03943, Quat.from_pitch(-math.pi / 2))

        # Now, do a Cartesian move to get the hand pointed downward 20cm above and 60cm in front of
        # the task frame.
        task_T_tool_desired = SE3Pose(0.6, 0, 0.2, Quat(1, 0, 0, 0))
        move_to_cartesian_pose_rt_task(robot, command_client, task_T_tool_desired, odom_T_task,
                                       wr1_T_tool)

        # Now, let's hold this pose in all other axes while pushing downward against the ground.
        # Request a force be generated at the current position, in the negative-Z direction in the
        # task frame.
        force_dir_rt_task = Vec3(0, 0, -1)
        robot_cmd = apply_force_at_current_position(
            force_dir_rt_task_in=force_dir_rt_task, force_magnitude=8,
            robot_state=robot_state_client.get_robot_state(), root_frame_name=ODOM_FRAME_NAME,
            root_T_task=odom_T_task, wr1_T_tool_nom=wr1_T_tool)

        # Execute the impedance command
        cmd_id = command_client.robot_command(robot_cmd)
        robot.logger.info('Impedance command issued')
        # This might report STATUS_TRAJECTORY_COMPLETE or STATUS_TRAJECTORY_STALLED, depending on
        # the floor. STATUS_TRAJECTORY_STALLED is reported if the arm has stopped making progress to
        # the goal and the measured tool frame is far from the `desired_tool` along directions where
        # we expect good tracking. Since the robot can't push past the floor, the trajectory might
        # stop making progress, even though we will still be pushing against the floor. Unless the
        # floor has high friction (like carpet) we'd expect to have good tracking in all directions
        # except z. Because we have requested a feedforward force in z, we don't expect good
        # tracking in that direction. So we would expect the robot to report
        # STATUS_TRAJECTORY_COMPLETE in this case once arm motion settles.
        success = block_until_arm_arrives(command_client, cmd_id, 10.0)
        if success:
            robot.logger.info('Impedance move succeeded.')
        else:
            robot.logger.info('Impedance move didn\'t complete because it stalled or timed out.')

        # Stow the arm
        stow_arm(robot, command_client)

        # Done! When we leave this function, we'll return the lease, and the robot will
        # automatically sit and power off


def power_on_and_stand(robot, command_client):
    # Now, we are ready to power on the robot. This call will block until the power is on. Commands
    # would fail if this did not happen. We can also check that the robot is powered at any point.
    robot.logger.info('Powering on robot... This may take a several seconds.')
    robot.power_on(timeout_sec=20)
    assert robot.is_powered_on(), 'Robot power on failed.'
    robot.logger.info('Robot powered on.')

    # Tell the robot to stand up, parameterized to enable the body to adjust its height to assist
    # manipulation. For this demo, that means the robot's base will descend, enabling the hand to
    # reach the ground. The command service is used to issue commands to a robot. The set of valid
    # commands for a robot depends on hardware configuration. See SpotCommandHelper for more
    # detailed examples on command building. The robot command service requires timesync between the
    # robot and the client.
    robot.logger.info('Commanding robot to stand...')
    blocking_stand(command_client, timeout_sec=10, params=get_impedance_mobility_params())
    robot.logger.info('Robot standing.')


def unstow_arm(robot, command_client):
    stand_command = RobotCommandBuilder.synchro_stand_command(
        params=get_impedance_mobility_params())
    unstow = RobotCommandBuilder.arm_ready_command(build_on_command=stand_command)
    unstow_command_id = command_client.robot_command(unstow)
    robot.logger.info('Unstow command issued.')
    block_until_arm_arrives(command_client, unstow_command_id, 3.0)


def stow_arm(robot, command_client):
    stow_cmd = RobotCommandBuilder.arm_stow_command()
    stow_command_id = command_client.robot_command(stow_cmd)
    robot.logger.info('Stow command issued.')
    block_until_arm_arrives(command_client, stow_command_id, 3.0)


def move_to_cartesian_pose_rt_task(robot, command_client, task_T_desired, root_T_task, wr1_T_tool):
    robot_cmd = RobotCommandBuilder.synchro_stand_command(params=get_impedance_mobility_params())
    arm_cart_cmd = robot_cmd.synchronized_command.arm_command.arm_cartesian_command

    # Set up our root frame, task frame, and tool frame.
    arm_cart_cmd.root_frame_name = ODOM_FRAME_NAME
    arm_cart_cmd.root_tform_task.CopyFrom(root_T_task.to_proto())
    arm_cart_cmd.wrist_tform_tool.CopyFrom(wr1_T_tool.to_proto())

    # Do a single point goto to a desired pose in the task frame.
    cartesian_traj = arm_cart_cmd.pose_trajectory_in_task
    traj_pt = cartesian_traj.points.add()
    traj_pt.time_since_reference.CopyFrom(seconds_to_duration(2.0))
    traj_pt.pose.CopyFrom(task_T_desired.to_proto())

    # Execute the Cartesian command.
    cmd_id = command_client.robot_command(robot_cmd)
    robot.logger.info('Arm cartesian command issued.')
    block_until_arm_arrives(command_client, cmd_id, 3.0)


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
        logger.exception('Threw an exception')
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
