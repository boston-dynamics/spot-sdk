# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Example to show how to use Boston Dynamics' joint control API"""

import argparse
import sys
import time
from threading import Thread

from constants import DEFAULT_LEG_K_Q_P, DEFAULT_LEG_K_QD_P, DOF
from joint_api_helper import JointAPIInterface

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
import bosdyn.geometry
from bosdyn.client.robot_command import (RobotCommandClient, RobotCommandStreamingClient,
                                         blocking_stand)
from bosdyn.client.robot_state import RobotStateStreamingClient


def run_joint_control(config):
    """An example of using joint control to command a Spot robot through the Boston Dynamics API.
    This example will,
    1. Power on the robot
    2. Stand the robot up
    3. Start streaming joint control state messages
    4. Start streaming joint control command messages
        a. Doing squat twice
    5. Activate joint control
    6. Sit down and power off the robot
    """
    # The Boston Dynamics Python library uses Python's logging module to
    # generate output.
    bosdyn.client.util.setup_logging(config.verbose)

    # The SDK object is the primary entry point to the Boston Dynamics API.
    # create_standard_sdk will initialize an SDK object with typical default
    # parameters. The argument passed in is a string identifying the client.
    sdk = bosdyn.client.create_standard_sdk('JointControlClient')

    # Register the non-standard api clients
    sdk.register_service_client(RobotCommandStreamingClient)
    sdk.register_service_client(RobotStateStreamingClient)

    # A Robot object represents a single robot.
    robot = sdk.create_robot(config.hostname)

    # Clients need to authenticate to a robot before being able to use it.
    bosdyn.client.util.authenticate(robot)

    # Establish time sync with the robot. This kicks off a background thread to establish time sync.
    # Time sync is required to issue commands to the robot. After starting time sync thread, block
    # until sync is established.
    robot.time_sync.wait_for_sync()

    # Verify the robot is not estopped and that an external application has registered and holds
    # an estop endpoint.
    assert not robot.is_estopped(), 'Robot is estopped. Please use an external E-Stop client, ' \
                                    'such as the estop SDK example, to configure E-Stop.'

    # Acquire the lease
    lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
    with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
        # Now, we are ready to power on the robot. This call will block until the power
        # is on. Commands would fail if this did not happen. We can also check that the robot is
        # powered at any point.
        robot.logger.info('Powering on robot... This may take several seconds.')
        robot.power_on(timeout_sec=20)
        assert robot.is_powered_on(), 'Robot power on failed.'
        robot.logger.info('Robot powered on.')

        # The robot state streaming client will allow us to get the robot's joint and imu information.
        robot_state_streaming_client = robot.ensure_client(
            RobotStateStreamingClient.default_service_name)

        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        command_streaming_client = robot.ensure_client(
            RobotCommandStreamingClient.default_service_name)

        # Stand the robot
        blocking_stand(command_client)
        # Extra delay to make sure
        time.sleep(2)

        # JointControlAPI class definition
        joint_api_interface = JointAPIInterface(robot, DOF.N_DOF_LEGS)

        state_thread = None
        try:
            # Start state streaming
            robot.logger.info("Starting state stream")
            state_thread = Thread(target=joint_api_interface.handle_state_streaming,
                                  args=(robot_state_streaming_client,))
            state_thread.start()

            # Activate joint control mode
            activate_thread = Thread(target=joint_api_interface.activate, args=(command_client,))
            activate_thread.start()

            # Once state streaming has started and before we take control, cache the joint positions
            # and loads.
            curr_pose, curr_load = joint_api_interface.get_latest_pos_and_load_state()
            squatty_pose = [
                0.15, 1.3, -2.25, -0.15, 1.3, -2.25, 0.15, 1.3, -2.25, -0.15, 1.3, -2.25
            ]
            cmd_poses = [curr_pose, squatty_pose, curr_pose, squatty_pose, curr_pose]

            duration_bw_pose = 2

            # Stream commands to the robot by passing an iterator
            robot.logger.info("Starting command stream")
            response = command_streaming_client.send_joint_control_commands(
                joint_api_interface.generate_joint_pos_interp_commands(
                    cmd_poses, curr_load, duration_bw_pose, DEFAULT_LEG_K_Q_P, DEFAULT_LEG_K_QD_P))
            # print(response)

        finally:
            joint_api_interface.set_should_stop(True)
            if state_thread:
                state_thread.join()
            if activate_thread:
                activate_thread.join()

        # Power the robot off. By specifying "cut_immediately=False", a safe power off command
        # is issued to the robot. This will attempt to sit the robot before powering off.
        robot.power_off(cut_immediately=False, timeout_sec=20)
        assert not robot.is_powered_on(), 'Robot power off failed.'
        robot.logger.info('Robot safely powered off.')


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()
    try:
        run_joint_control(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception('Hello, Spot! threw an exception: %r', exc)
        return False


if __name__ == '__main__':
    if not main():
        sys.exit(1)
