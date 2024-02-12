# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Example to show how usage of the Boston Dynamics joint control API"""

import argparse
import sys
import time
from math import cos, pi, sin
from threading import Thread

from constants import DEFAULT_K_Q_P, DEFAULT_K_QD_P, DOF

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
import bosdyn.geometry
from bosdyn.api import robot_command_pb2
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                         RobotCommandStreamingClient, blocking_stand)
from bosdyn.client.robot_state import RobotStateStreamingClient
from bosdyn.util import set_timestamp_from_now


class JointPlan:

    def __init__(self, period, pos_offset, amplitude):
        self.period = period
        self.pos_offset = pos_offset
        self.amplitude = amplitude

    def calculate_command(self, time):
        pos = self.pos_offset + self.amplitude * sin(time / self.period * 2 * pi)
        vel = self.amplitude * (2 * pi / self.period) * cos(time / self.period * 2 * pi)
        return pos, vel


def run_joint_control(config):
    """An example of using joint control to command a Spot robot through the Boston Dynamics API.
    This example will,
    1. Power on the robot
    2. Stand the robot up
    3. Start streaming joint control state messages
    4. Start streaming joint control command messages
        a. Move WR0 and gripper (F1X) in a sinusoidal pattern
        b. Lock all other joints in their initial position, including using the initial torque as a
            feed forward torque to mimic gravity compensation.
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

    # The robot state streaming client will allow us to get the robot's joint and imu information.
    robot_state_streaming_client = robot.ensure_client(
        RobotStateStreamingClient.default_service_name)

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

        command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        command_streaming_client = robot.ensure_client(
            RobotCommandStreamingClient.default_service_name)

        # Stand the robot
        blocking_stand(command_client)
        # Stabilize
        time.sleep(2)

        init_kin_pos_state = [0] * DOF.N_DOF
        init_kin_load_state = [0] * DOF.N_DOF
        latest_state_stream_data = None

        # Set up a space to track sent commands and their user_key's
        cmd_history = {}
        should_stop = False
        started_streaming = False

        # Continually receive state data until told to stop
        def handle_state_streaming():
            nonlocal latest_state_stream_data

            for state in robot_state_streaming_client.get_robot_state_stream():
                receive_time = time.time()
                latest_state_stream_data = state

                if should_stop:
                    return

                if (state.last_command.user_command_key != 0 and
                        state.last_command.user_command_key in cmd_history.keys()):
                    sent_time = cmd_history[state.last_command.user_command_key]
                    received_time = robot.time_sync.get_robot_time_converter(
                    ).local_seconds_from_robot_timestamp(state.last_command.received_timestamp)
                    latency_ms = (received_time - sent_time) * 1000
                    roundtrip_ms = (receive_time - sent_time) * 1000
                    # Note that the latency measurement here has the receive time converted from
                    # robot time, so it's not very accurate
                    robot.logger.info(f"Latency {latency_ms:.3f}\tRoundtrip {roundtrip_ms:.3f}")
                else:
                    robot.logger.info(f"No key: {state.last_command.user_command_key}")

        # Cache the initial joint positions and loads so they can be reissued for locking joints
        def update_initial_conditions():
            nonlocal init_kin_pos_state
            nonlocal init_kin_load_state

            # Wait for first data to cache. This should happend synchronously in normal stand before
            # joint control is activated.
            while not latest_state_stream_data:
                time.sleep(0.1)

            # Cache current joint state
            starting_state = latest_state_stream_data
            init_kin_pos_state = starting_state.joint_states.position
            init_kin_load_state = starting_state.joint_states.load

        # Sinusoidal plan paramaters
        period = 2
        dt = 1 / 333
        duration = 5

        # Generate plans
        joints_to_control = {}
        joints_to_control[DOF.A0_WR0] = JointPlan(period, pos_offset=0, amplitude=1)
        joints_to_control[DOF.A0_F1X] = JointPlan(period, pos_offset=-0.7, amplitude=0.5)

        # Set joint PD gains
        k_q_p = DEFAULT_K_Q_P
        k_qd_p = DEFAULT_K_QD_P

        # Method to generate commands at the configured interval
        def generate_commands():
            nonlocal started_streaming

            update_proto = robot_command_pb2.JointControlStreamRequest()

            pos_cmd = [0] * DOF.N_DOF
            vel_cmd = [0] * DOF.N_DOF
            load_cmd = [0] * DOF.N_DOF

            starting_time = time.time()
            previous_dt_time = starting_time
            count = 0
            while time.time() < (starting_time + duration):
                count += 1

                if should_stop:
                    return

                # Want to send next command no sooner than `dt` after the previous one
                this_dt_time_d = max(previous_dt_time + dt, time.time())
                sleep_time = max(0, this_dt_time_d - time.time())
                time.sleep(sleep_time)

                this_dt_time_actual = time.time()
                plan_time = this_dt_time_actual - starting_time

                for joint_ind in range(DOF.N_DOF):
                    if joint_ind in joints_to_control:
                        # Execute plan
                        spec = joints_to_control[joint_ind]
                        pos, vel = spec.calculate_command(plan_time)
                        pos_cmd[joint_ind] = pos
                        vel_cmd[joint_ind] = vel
                        load_cmd[joint_ind] = 0

                    else:
                        # Hold in original position
                        pos_cmd[joint_ind] = init_kin_pos_state[joint_ind]
                        vel_cmd[joint_ind] = 0
                        load_cmd[joint_ind] = init_kin_load_state[joint_ind]

                # Construct proto
                update_proto.Clear()
                set_timestamp_from_now(update_proto.header.request_timestamp)
                update_proto.header.client_name = "streaming_example_client"

                # Fill in gains the first dt
                if count == 1:
                    update_proto.joint_command.gains.k_q_p.extend(k_q_p)
                    update_proto.joint_command.gains.k_qd_p.extend(k_qd_p)

                update_proto.joint_command.position.extend(pos_cmd)
                update_proto.joint_command.velocity.extend(vel_cmd)
                update_proto.joint_command.load.extend(load_cmd)

                update_proto.joint_command.end_time.CopyFrom(
                    robot.time_sync.robot_timestamp_from_local_secs(time.time() + 0.05))

                # Let it extrapolate the command a little
                update_proto.joint_command.extrapolation_duration.nanos = int(5 * 1e6)

                # Set user key for latency tracking
                update_proto.joint_command.user_command_key = count

                # Track the actual send time
                cmd_history[count] = time.time()
                yield update_proto

                started_streaming = True
                previous_dt_time = this_dt_time_d

        # Method to activate full body joint control through RobotCommand
        def activate():
            nonlocal should_stop

            # Wait for streaming to start
            while not started_streaming:
                time.sleep(0.001)

                if should_stop:
                    return

            # Activate joint control
            robot.logger.info("Activating joint control")
            joint_command = RobotCommandBuilder.joint_command()

            try:
                cmd_id = command_client.robot_command(joint_command)
            except:
                # Signal everything else to stop too
                should_stop = True

        state_thread = None
        activate_thread = None
        try:
            # Start state streaming
            robot.logger.info("Starting state stream")
            state_thread = Thread(target=handle_state_streaming)
            state_thread.start()

            # Once state streaming has started and before we take control, cache the joint positions
            # and loads.
            update_initial_conditions()

            # Async activate once streaming has started
            activate_thread = Thread(target=activate)
            activate_thread.start()

            # Stream commands to the robot by passing an iterator
            robot.logger.info("Starting command stream")
            response = command_streaming_client.send_joint_control_commands(generate_commands())
            # print(response)

        finally:
            should_stop = True
            if state_thread:
                state_thread.join()
            if activate_thread:
                activate_thread.join()

        # Power the robot off. By specifying "cut_immediately=False", a safe power off command
        # is issued to the robot. This will attempt to sit the robot before powering off.
        robot.power_off(cut_immediately=False, timeout_sec=20)
        assert not robot.is_powered_on(), 'Robot power off failed.'
        robot.logger.info('Robot safely powered off.')


# Used to visualize plans and make sure they look right.
def draw_plan(options):
    import matplotlib.pyplot as plt

    dt = 1 / 333
    duration = 10
    period = 2 * pi
    pos_offset = 0
    amplitude = 0.5
    spec = JointPlan(period, pos_offset, amplitude)

    times = []
    positions = []
    velocities = []
    time_d = 0
    while time_d < duration:
        times.append(time_d)
        pos, vel = spec.calculate_command(time_d)
        positions.append(pos)
        velocities.append(vel)
        time_d += dt

    plt.plot(times, positions, label='pos')
    plt.plot(times, velocities, '-.', label='vel')
    plt.axhline(y=0, color='r')

    plt.xlabel("Time")
    plt.ylabel("Pos/Vel")
    plt.legend()
    plt.show()


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()
    try:
        # draw_plan(options)
        run_joint_control(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.exception('Hello, Spot! threw an exception: %r', exc)
        return False


if __name__ == '__main__':
    if not main():
        sys.exit(1)
