# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging

import bosdyn.client.util
import bosdyn.geometry
from bosdyn.api.graph_nav.area_callback_pb2 import BeginCallbackRequest, BeginCallbackResponse
from bosdyn.client.area_callback_region_handler_base import AreaCallbackRegionHandlerBase
from bosdyn.client.area_callback_service_runner import run_service
from bosdyn.client.area_callback_service_servicer import AreaCallbackServiceServicer
from bosdyn.client.area_callback_service_utils import AreaCallbackServiceConfig
from bosdyn.client.robot import Robot
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient


class AreaCallbackRegionHandlerLookBothWays(AreaCallbackRegionHandlerBase):
    """An example AreaCallbackRegionHandler implementation which looks both ways.
    """
    DEFAULT_YAW = 1

    def __init__(self, config: AreaCallbackServiceConfig, robot: Robot):
        super().__init__(config, robot)
        self.yaw = self.DEFAULT_YAW
        # Set up initial policy
        self.control_at_start()
        self.continue_past_end()

    def begin(self, request: BeginCallbackRequest) -> BeginCallbackResponse.Status:
        return BeginCallbackResponse.STATUS_OK

    def run(self):
        # In order to send a robot command, the AreaCallback requires a lease. This helper function
        # blocks until a lease is given to the callback.
        self.control_at_start()
        self.block_until_control()

        # The check function is a convenience function to check if the area callback should shut down.
        # These should be scattered throughout the run implementation to make sure the callback does
        # not accidentally keep running after a client calls end.
        self.check()

        # After control is given, issue robot commands to look both ways.
        command_client = self.robot.ensure_client(RobotCommandClient.default_service_name)
        footprint_R_body = bosdyn.geometry.EulerZXY(yaw=self.yaw, roll=0.0, pitch=0.0)
        cmd = RobotCommandBuilder.synchro_stand_command(footprint_R_body=footprint_R_body)
        command_client.robot_command(cmd)

        # The safe sleep function should be used rather than time.sleep. This safe sleep function
        # checks that the run thread should still be running and throws an exception when it should
        # shut down.
        self.safe_sleep(2.0)

        # Look the other direction.
        footprint_R_body = bosdyn.geometry.EulerZXY(yaw=-self.yaw, roll=0.0, pitch=0.0)
        cmd = RobotCommandBuilder.synchro_stand_command(footprint_R_body=footprint_R_body)
        command_client.robot_command(cmd)
        self.safe_sleep(2.0)

        # Look straight ahead.
        footprint_R_body = bosdyn.geometry.EulerZXY(yaw=0.0, roll=0.0, pitch=0.0)
        cmd = RobotCommandBuilder.synchro_stand_command(footprint_R_body=footprint_R_body)
        command_client.robot_command(cmd)
        self.safe_sleep(0.5)

        # The callback is complete. The client (graph nav) will take back control, as well as call
        # EndCallback.
        self.continue_past_start()

        self.block_until_arrived_at_end()
        # self.set_complete()

    def end(self):
        # No extra cleanup is required by this callback. For something like a callback that plays a
        # sound, the EndCallback call would be a place to stop playing the sound.
        pass


def main():
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    bosdyn.client.util.add_service_hosting_arguments(parser)
    options = parser.parse_args()
    bosdyn.client.util.setup_logging(options.verbose)

    self_ip = bosdyn.client.common.get_self_ip(options.hostname)

    # Initialize robot object.
    sdk = bosdyn.client.create_standard_sdk('AreaCallbackLookBothWaysService')
    robot = sdk.create_robot(options.hostname)
    robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(options))
    robot.start_time_sync()
    robot.time_sync.wait_for_sync()

    # Configure the area callback service.
    service_name = 'look-both-ways'
    required_lease_resources = ['body']
    config = AreaCallbackServiceConfig(service_name,
                                       required_lease_resources=required_lease_resources)
    info = config.area_callback_information

    # This callback does not do anything special to get past obstacles, so we should allow
    # Graph Nav to identify blockages in the region.
    info.blockage = info.BLOCKAGE_CHECK
    # This callback controls the robot, but only looks left and right, so it is okay for Graph Nav
    # to interrupt it if the robot becomes impaired.
    info.impairment_check = info.IMPAIRMENT_CHECK
    # Graph Nav should still wait for entities as normal when crossing this region.
    info.entity_waiting = info.ENTITY_WAITING_ENABLE
    # The robot should face along the route it is going to cross, so that we look left and
    # right of the crossing direction.
    info.default_stop.face_direction = info.default_stop.FACE_DIRECTION_ALONG_ROUTE

    servicer = AreaCallbackServiceServicer(robot, config, AreaCallbackRegionHandlerLookBothWays)

    # Run the area callback service.
    service_runner, keep_alive = run_service(robot, servicer, options.port, self_ip)
    with keep_alive:
        service_runner.run_until_interrupt()


if __name__ == '__main__':
    main()
