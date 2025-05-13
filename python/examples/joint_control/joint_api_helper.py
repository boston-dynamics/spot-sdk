# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import time

from constants import DOF

from bosdyn.api import robot_command_pb2
from bosdyn.client.robot_command import RobotCommandBuilder
from bosdyn.util import seconds_to_duration, set_timestamp_from_now


class LinearInterpolator:
    # LinearInterpolator is a helper class to linearly interpolate between
    # two joint positions over a fixed duration.
    def __init__(self, duration, init_pos, target_pos):
        self.duration = duration
        self.init_pos = init_pos
        self.target_pos = target_pos

    def calculate_command(self, time):
        pos = self.init_pos + (self.target_pos - self.init_pos) * time / self.duration
        vel = (self.target_pos - self.init_pos) / self.duration
        return pos, vel


class JointAPIInterface:
    # JointAPIInterface is a helper class to help to use joint control API.
    # This class contains the way of activating joint control mode, getting lightweight
    # robot state, and sending joint pos by interpolating commanded poses as an example.
    def __init__(self, robot, n_dofs):
        self.robot = robot
        self.latest_state_stream_data = None
        self.should_stop = False
        self.started_streaming = False
        self.cmd_history = {}

        if n_dofs != DOF.N_DOF_LEGS and n_dofs != DOF.N_DOF:
            # DOF error
            self.robot.logger.warning("Incorrect number of DOF. Joint API will not be activated")
            self.should_stop = True
        self.n_dofs = n_dofs

    # should_stop is a flag to enable/disable sending/receiving command
    def set_should_stop(self, flag):
        self.should_stop = flag

    # activate function is to activate joint control mode
    def activate(self, command_client):
        # Wait for streaming to start
        while not self.started_streaming:
            time.sleep(0.001)

            if self.should_stop:
                return

        # Activate joint control
        self.robot.logger.info("Activating joint control")
        joint_command = RobotCommandBuilder.joint_command()

        try:
            cmd_id = command_client.robot_command(joint_command)
        except:
            # Signal everything else to stop too
            self.should_stop = True

    # handle_state_streaming function is to get lightweight robot state streaming message.
    def handle_state_streaming(self, robot_state_streaming_client):
        for state in robot_state_streaming_client.get_robot_state_stream():
            receive_time = time.time()
            self.latest_state_stream_data = state

            if self.should_stop:
                return

            if (state.last_command.user_command_key != 0 and
                    state.last_command.user_command_key in self.cmd_history.keys()):
                sent_time = self.cmd_history[state.last_command.user_command_key]
                received_time = self.robot.time_sync.get_robot_time_converter(
                ).local_seconds_from_robot_timestamp(state.last_command.received_timestamp)
                latency_ms = (received_time - sent_time) * 1000
                roundtrip_ms = (receive_time - sent_time) * 1000
                # Note that the latency measurement here has the receive time converted from
                # robot time, so it's not very accurate
                self.robot.logger.info(f"Latency {latency_ms:.3f}\tRoundtrip {roundtrip_ms:.3f}")
            else:
                self.robot.logger.info(f"No key: {state.last_command.user_command_key}")

    # get_latest_joints_state function is to get a latest joint state
    def get_latest_pos_and_load_state(self):
        # Wait for first data to cache. This should happened synchronously in normal stand before
        # joint control is activated.
        while not self.latest_state_stream_data:
            time.sleep(0.1)

        kin_pos_state = self.latest_state_stream_data.joint_states.position
        kin_load_state = self.latest_state_stream_data.joint_states.load
        return kin_pos_state, kin_load_state

    # generate_joint_pos_interp_commands functions is an example function to send the joint
    # command by interpolating commanded poses
    # cmd_poses : series of commanded joints poses
    # cmd_loads : commanded joint loads
    # duration : desired duration between the poses [s]
    # k_q_p : proportional gain for position control
    # k_qd_p : proportional gain for velocity control
    def generate_joint_pos_interp_commands(self, cmd_poses, cmd_load, duration, k_q_p, k_qd_p):
        update_proto = robot_command_pb2.JointControlStreamRequest()

        pos_cmd = [0] * self.n_dofs
        vel_cmd = [0] * self.n_dofs
        load_cmd = [0] * self.n_dofs

        count = 0

        # Joint plan parameter [s]
        dt = 1 / 333

        joints_to_control = {}

        for iter in range(len(cmd_poses) - 1):
            new_command = True
            starting_time = time.time()
            previous_dt_time = starting_time
            while time.time() < (starting_time + duration):
                count += 1

                if self.should_stop:
                    return

                # Want to send next command no sooner than `dt` after the previous one
                this_dt_time_d = max(previous_dt_time + dt, time.time())
                sleep_time = max(0, this_dt_time_d - time.time())
                time.sleep(sleep_time)

                this_dt_time_actual = time.time()
                plan_time = this_dt_time_actual - starting_time

                for joint_ind in range(self.n_dofs):
                    if new_command:
                        # Set up joint planner
                        joints_to_control[joint_ind] = LinearInterpolator(
                            duration, cmd_poses[iter][joint_ind], cmd_poses[iter + 1][joint_ind])

                    # Calculate joint command
                    pos, vel = joints_to_control[joint_ind].calculate_command(plan_time)
                    pos_cmd[joint_ind] = pos
                    vel_cmd[joint_ind] = vel
                load_cmd = cmd_load
                new_command = False

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
                    self.robot.time_sync.robot_timestamp_from_local_secs(time.time() + 0.05))

                # Let it extrapolate the command a little
                update_proto.joint_command.extrapolation_duration.CopyFrom(
                    seconds_to_duration(0.005))

                # Set user key for latency tracking
                update_proto.joint_command.user_command_key = count

                # Track the actual send time
                self.cmd_history[count] = time.time()
                yield update_proto

                self.started_streaming = True
                previous_dt_time = this_dt_time_d
