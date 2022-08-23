# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import time

import bosdyn.client.util
from bosdyn.api.graph_nav import area_callback_pb2
from bosdyn.api.graph_nav.area_callback_pb2 import UpdateCallbackRequest, UpdateCallbackResponse
from bosdyn.client.area_callback import AreaCallbackClient
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.robot_command import RobotCommandClient, blocking_stand

WALK_TO_END_DURATION = 3


def run_callback(robot, area_callback_client, area_callback_info, control_needed, walk_duration):
    # Start the callback.
    end_time = robot.time_sync.robot_timestamp_from_local_secs(time.time() + 10)
    begin_callback_request = area_callback_pb2.BeginCallbackRequest(end_time=end_time)
    begin_callback_response = area_callback_client.begin_callback(begin_callback_request)
    command_id = begin_callback_response.command_id
    robot.logger.info("Callback has started.")

    callback_is_running = True
    stage = UpdateCallbackRequest.STAGE_TO_START
    given_control = False

    # Run the callback until complete. During each loop, call the UpdateCallback RPC and act on it. If
    # the callback requests control, give the callback the required resources.
    reached_end_time = None

    def set_stage(s):
        nonlocal stage
        robot.logger.info('Stage set to %s', UpdateCallbackRequest.Stage.Name(s))
        stage = s

    try:
        while callback_is_running:
            end_time = robot.time_sync.robot_timestamp_from_local_secs(time.time() + 10)
            update_callback_request = UpdateCallbackRequest(stage=stage, end_time=end_time,
                                                            command_id=command_id)
            update_callback_response = area_callback_client.update_callback(update_callback_request)

            if update_callback_response.HasField("policy"):
                policy = update_callback_response.policy
                assert policy.at_start != UpdateCallbackResponse.NavPolicy.OPTION_UNKNOWN
                assert policy.at_end != UpdateCallbackResponse.NavPolicy.OPTION_UNKNOWN
                if stage <= UpdateCallbackRequest.STAGE_AT_START:
                    if policy.at_start == UpdateCallbackResponse.NavPolicy.OPTION_STOP:
                        set_stage(UpdateCallbackRequest.STAGE_AT_START)
                    elif policy.at_start == UpdateCallbackResponse.NavPolicy.OPTION_CONTROL and not given_control:
                        assert control_needed, 'Callback requested control at the start when it specified no lease resources'
                        set_stage(UpdateCallbackRequest.STAGE_AT_START)
                        lease_wallet = robot.lease_wallet
                        leases_proto_list = []
                        for resource in area_callback_info.info.required_lease_resources:
                            lease_proto = lease_wallet.get_lease(
                                resource).create_sublease().lease_proto
                            leases_proto_list.append(lease_proto)
                        begin_control_request = area_callback_pb2.BeginControlRequest(
                            leases=leases_proto_list, command_id=command_id)
                        area_callback_client.begin_control(begin_control_request)
                        robot.logger.info("Gave control to callback.")
                        given_control = True
                    elif policy.at_start == UpdateCallbackResponse.NavPolicy.OPTION_CONTINUE:
                        set_stage(UpdateCallbackRequest.STAGE_TO_END)
                        given_control = False
                        if reached_end_time is None:
                            robot.logger.info("Continuing to the end of the region.")
                            reached_end_time = time.time() + walk_duration

                elif stage == UpdateCallbackRequest.STAGE_TO_END:
                    if reached_end_time is not None and time.time() > reached_end_time:
                        set_stage(UpdateCallbackRequest.STAGE_AT_END)
                elif stage == UpdateCallbackRequest.STAGE_AT_END:
                    if policy.at_end == UpdateCallbackResponse.NavPolicy.OPTION_CONTROL and not given_control:
                        assert control_needed, 'Callback requested control at the end when it specified no lease resources'
                        lease_wallet = robot.lease_wallet
                        leases_proto_list = []
                        for resource in area_callback_info.info.required_lease_resources:
                            lease_proto = lease_wallet.get_lease(
                                resource).create_sublease().lease_proto
                            leases_proto_list.append(lease_proto)
                        begin_control_request = area_callback_pb2.BeginControlRequest(
                            leases=leases_proto_list, command_id=command_id)
                        area_callback_client.begin_control(begin_control_request)
                        robot.logger.info("Gave control to callback.")
                        given_control = True
                    elif policy.at_end == UpdateCallbackResponse.NavPolicy.OPTION_CONTINUE:
                        robot.logger.info("Passed end waypoint.")
                        callback_is_running = False

            elif update_callback_response.HasField("error"):
                robot.logger.error("Error occurred while running callback.")
                robot.logger.error(update_callback_response)
                callback_is_running = False
            elif update_callback_response.HasField("complete"):
                robot.logger.info("Callback completed successfully.")
                callback_is_running = False

            time.sleep(0.1)

    finally:
        # End the callback.
        end_callback_request = area_callback_pb2.EndCallbackRequest(command_id=command_id)
        area_callback_client.end_callback(end_callback_request)
        robot.logger.info("Callback has ended.")


def main():
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('--service-name', '-s', type=str,
                        help='Service name of the AreaCallback to test')
    parser.add_argument(
        '--walk-duration', type=float, default=WALK_TO_END_DURATION,
        help='Amount of time to wait between starting to "walk" to the end '
        'and reaching the end of the region.')
    options = parser.parse_args()
    bosdyn.client.util.setup_logging(options.verbose)

    # Initialize robot object.
    sdk = bosdyn.client.create_standard_sdk('AreaCallbackTester', [AreaCallbackClient])
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.start_time_sync(time_sync_interval_sec=0.01)
    robot.time_sync.wait_for_sync()

    area_callback_client = robot.ensure_client(options.service_name)
    nav_info = area_callback_client.area_callback_information()
    control_needed = bool(nav_info.info.required_lease_resources)

    try:
        if control_needed:
            assert not robot.is_estopped(), "Robot is estopped. Please use an external E-Stop client, "\
                                            "such as the estop SDK example, to configure E-Stop."

            lease_client = robot.ensure_client(LeaseClient.default_service_name)
            with LeaseKeepAlive(lease_client, must_acquire=True, return_at_exit=True):
                robot.power_on(timeout_sec=20)
                command_client = robot.ensure_client(RobotCommandClient.default_service_name)
                blocking_stand(command_client, timeout_sec=10)
                run_callback(robot, area_callback_client, nav_info, control_needed,
                             options.walk_duration)
        else:
            run_callback(robot, area_callback_client, nav_info, control_needed,
                         options.walk_duration)
    except AssertionError as exc:
        robot.logger.error('%s', exc)


if __name__ == "__main__":
    main()
