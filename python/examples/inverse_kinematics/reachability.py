# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

""" Tutorial for how to use the spot inverse kinematics service for reachability queries.

This tutorial demonstrates how to use the inverse kinematics (IK) service to check the reachability
of desired tool poses:
 - First it defines desired tool poses uniformly distributed across a rectangle in front of the
   robot, and a small distance above the ground.
 - Then, it defines a tool frame at the tip of the lower jaw, oriented such that the opening of the
   gripper will point down  when the tool is at one of the desired tool poses.
 - Next, it formulates an InverseKinematicsRequest for each desired tool pose, such that a solution
   will provide a configuration that places the tool frame at the desired tool pose, while keeping
   the feet in their current positions.
 - Next, it checks the results returned by the IK service:
    - For desired tool poses that the IK service deemed reachable, it issues an arm Cartesian move
      command with the desired body pose set to the one provided by IK.
    - For desired tool poses that the IK service deemed un-reachable, it issues an arm Cartesian
      move with `enable_hip_height_assist` and `enable_body_yaw_assist` both set to `True`.
 - Finally, it plots the (x, y) positions of the true and false positive/negative results.
"""
import math
import sys

import numpy as np
from matplotlib import pyplot as plt

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.api import robot_command_pb2
from bosdyn.api.spot import robot_command_pb2 as spot_command_pb2
from bosdyn.api.spot.inverse_kinematics_pb2 import (InverseKinematicsRequest,
                                                    InverseKinematicsResponse)
from bosdyn.client.frame_helpers import (BODY_FRAME_NAME, GRAV_ALIGNED_BODY_FRAME_NAME,
                                         GROUND_PLANE_FRAME_NAME, ODOM_FRAME_NAME, get_a_tform_b)
from bosdyn.client.inverse_kinematics import InverseKinematicsClient
from bosdyn.client.math_helpers import Quat, SE3Pose
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                         block_until_arm_arrives, blocking_stand)
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.util import seconds_to_duration


def plot_results(*, foot_coords, reachable_ik, reachable_cmd, x_rt_task, y_rt_task):
    # Classify the IK service reachability results as true positives, true negatives, false
    # positives, or false negatives.
    true_positives = np.logical_and(reachable_ik, reachable_cmd)
    true_negatives = np.logical_and(np.logical_not(reachable_ik), np.logical_not(reachable_cmd))
    false_positives = np.logical_and(reachable_ik, np.logical_not(reachable_cmd))
    false_negatives = np.logical_and(np.logical_not(reachable_ik), reachable_cmd)
    # Compute the false positive and negative rates.
    false_positive_rate = np.sum(false_positives) / (np.sum(false_positives) +
                                                     np.sum(true_negatives))
    false_negative_rate = np.sum(false_negatives) / (np.sum(false_negatives) +
                                                     np.sum(true_positives))
    # Plot the reachability results in x and y relative to the task frame.
    fig, ax = plt.subplots()
    ax.scatter(x_rt_task[true_positives], y_rt_task[true_positives], c='g', marker='o',
               label="true positives")
    ax.scatter(x_rt_task[true_negatives], y_rt_task[true_negatives], c='r', marker='o',
               label="true negatives")
    ax.scatter(x_rt_task[false_positives], y_rt_task[false_positives], c='m', marker='o',
               label=f"false positives ({false_positive_rate * 100:.0f}%)")
    ax.scatter(x_rt_task[false_negatives], y_rt_task[false_negatives], c='c', marker='o',
               label=f"false negatives ({false_negative_rate * 100:.0f}%)")
    # Add the footprint of the robot for context.
    ax.add_patch(plt.Polygon(foot_coords, label="footprint"))
    plt.axis('equal')
    ax.legend(loc='lower left')
    plt.show()


def reachability_queries(config):
    """Making reachability requests using the InverseKinematics service"""

    # See hello_spot.py for an explanation of these lines.
    bosdyn.client.util.setup_logging(config.verbose)

    sdk = bosdyn.client.create_standard_sdk('ReachabilitySDK')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    assert robot.has_arm(), 'Robot requires an arm to run this example.'

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    assert not robot.is_estopped(), 'Robot is estopped. Please use an external E-Stop client, ' \
                                    'such as the estop SDK example, to configure E-Stop.'

    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)

    # The desired tool poses are defined relative to a task frame in front of the robot and slightly
    # above the ground. The task frame is aligned with the "gravity aligned body frame", such that
    # the positive-x direction is to the front of the robot, the positive-y direction is to the left
    # of the robot, and the positive-z direction is opposite to gravity.
    rng = np.random.RandomState(0)
    x_size = 0.7  # m
    y_size = 0.8  # m
    x_rt_task = x_size * rng.random(config.num_poses)
    y_rt_task = -y_size / 2 + y_size * rng.random(config.num_poses)
    task_T_desired_tools = [
        SE3Pose(xi_rt_task, yi_rt_task, 0.0, Quat())
        for (xi_rt_task, yi_rt_task) in zip(x_rt_task.flatten(), y_rt_task.flatten())
    ]

    # These arrays store the reachability results as determined by the IK responses (`reachable_ik`)
    # or by trying to move to the desired tool pose (`reachable_cmd`).
    reachable_ik = np.full(x_rt_task.shape, False)
    reachable_cmd = np.full(x_rt_task.shape, False)

    # This list will store the (x, y) coordinates of the feet relative to the task frame, so that
    # the support polygon can be drawn in the output plot for reference.
    foot_coords = []

    # Create a lease client to allow us to control the robot.
    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Now, we are ready to power on the robot. This call will block until the power
        # is on. Commands would fail if this did not happen. We can also check that the robot is
        # powered at any point.
        robot.logger.info('Powering on robot... This may take a several seconds.')
        robot.power_on(timeout_sec=20)
        assert robot.is_powered_on(), 'Robot power on failed.'
        robot.logger.info('Robot powered on.')
        # The command service is used to issue commands to a robot.
        # The set of valid commands for a robot depends on hardware configuration. See
        # RobotCommandBuilder for more detailed examples on command building. The robot
        # command service requires timesync between the robot and the client.
        command_client = robot.ensure_client(RobotCommandClient.default_service_name)

        # Tell the robot to stand up
        robot.logger.info('Commanding robot to stand...')
        blocking_stand(command_client, timeout_sec=10)
        robot.logger.info('Robot standing.')

        # Define a stand command that we'll send if the IK service does not find a solution.
        body_control = spot_command_pb2.BodyControlParams(
            body_assist_for_manipulation=spot_command_pb2.BodyControlParams.
            BodyAssistForManipulation(enable_hip_height_assist=True, enable_body_yaw_assist=True))
        body_assist_enabled_stand_command = RobotCommandBuilder.synchro_stand_command(
            params=spot_command_pb2.MobilityParams(body_control=body_control))

        # Define the task frame to be in front of the robot and near the ground
        robot_state = robot_state_client.get_robot_state()
        odom_T_grav_body = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot,
                                         ODOM_FRAME_NAME, GRAV_ALIGNED_BODY_FRAME_NAME)

        odom_T_gpe = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot, ODOM_FRAME_NAME,
                                   GROUND_PLANE_FRAME_NAME)

        # Construct the frame on the ground right underneath the center of the body.
        odom_T_ground_body = odom_T_grav_body
        odom_T_ground_body.z = odom_T_gpe.z

        # Now, construct a task frame slightly above the ground, in front of the robot.
        odom_T_task = odom_T_ground_body * SE3Pose(x=0.4, y=0, z=0.05, rot=Quat(w=1, x=0, y=0, z=0))

        # Now, let's set our tool frame to be the tip of the robot's bottom jaw. Flip the
        # orientation so that when the hand is pointed downwards, the tool's z-axis is
        # pointed upward.
        wr1_T_tool = SE3Pose(0.23589, 0, -0.03943, Quat.from_pitch(-math.pi / 2))

        # Populate the foot positions relative to the task frame for plotting later.
        odom_T_body = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot,
                                    ODOM_FRAME_NAME, BODY_FRAME_NAME)
        task_T_body = odom_T_task.inverse() * odom_T_body
        for foot_index in [0, 1, 3, 2]:
            foot_state = robot_state.foot_state[foot_index]
            foot_position_rt_task = task_T_body.transform_vec3(foot_state.foot_position_rt_body)
            foot_coords.append((foot_position_rt_task.x, foot_position_rt_task.y))

        # Unstow the arm
        ready_command = RobotCommandBuilder.arm_ready_command(
            build_on_command=body_assist_enabled_stand_command)
        ready_command_id = command_client.robot_command(ready_command)
        robot.logger.info('Going to "ready" pose')
        block_until_arm_arrives(command_client, ready_command_id, 3.0)

        # Create a client for the IK service.
        ik_client = robot.ensure_client(InverseKinematicsClient.default_service_name)
        ik_responses = []
        for i, task_T_desired_tool in enumerate(task_T_desired_tools):
            # Query the IK service for the reachability of the desired tool pose.
            # Construct the IK request for this reachability problem. Note that since
            # `root_tform_scene` is unset, the "scene" frame is the same as the "root" frame in this
            # case.
            ik_request = InverseKinematicsRequest(
                root_frame_name=ODOM_FRAME_NAME,
                scene_tform_task=odom_T_task.to_proto(),
                wrist_mounted_tool=InverseKinematicsRequest.WristMountedTool(
                    wrist_tform_tool=wr1_T_tool.to_proto()),
                tool_pose_task=InverseKinematicsRequest.ToolPoseTask(
                    task_tform_desired_tool=task_T_desired_tool.to_proto()),
            )
            ik_responses.append(ik_client.inverse_kinematics(ik_request))
            reachable_ik[i] = (ik_responses[i].status == InverseKinematicsResponse.STATUS_OK)

            # Attempt to move to each of the desired tool pose to check the IK results.
            stand_command = None
            if ik_responses[i].status == InverseKinematicsResponse.STATUS_OK:
                odom_T_desired_body = get_a_tform_b(
                    ik_responses[i].robot_configuration.transforms_snapshot, ODOM_FRAME_NAME,
                    BODY_FRAME_NAME)
                mobility_params = spot_command_pb2.MobilityParams(
                    body_control=spot_command_pb2.BodyControlParams(
                        body_pose=RobotCommandBuilder.body_pose(ODOM_FRAME_NAME,
                                                                odom_T_desired_body.to_proto())))
                stand_command = RobotCommandBuilder.synchro_stand_command(params=mobility_params)
            else:
                stand_command = body_assist_enabled_stand_command
            arm_command = RobotCommandBuilder.arm_pose_command_from_pose(
                (odom_T_task * task_T_desired_tool).to_proto(), ODOM_FRAME_NAME, 1,
                build_on_command=stand_command)
            arm_command.synchronized_command.arm_command.arm_cartesian_command.wrist_tform_tool.CopyFrom(
                wr1_T_tool.to_proto())
            arm_command_id = command_client.robot_command(arm_command)
            reachable_cmd[i] = block_until_arm_arrives(command_client, arm_command_id, 2)

        # Done! When we leave this block, we'll return the lease, and the robot
        # will automatically sit and power off

    plot_results(foot_coords=foot_coords, reachable_ik=reachable_ik, reachable_cmd=reachable_cmd,
                 x_rt_task=x_rt_task, y_rt_task=y_rt_task)


def main():
    """Command line interface."""
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('-n', '--num_poses', default=50, type=int,
                        help="Number of desired tool poses to query.")
    options = parser.parse_args()
    try:
        reachability_queries(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception('Threw an exception')
        return False


if __name__ == '__main__':
    if not main():
        sys.exit(1)
