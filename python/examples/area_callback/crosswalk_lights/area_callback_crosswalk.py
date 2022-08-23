# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging
import threading

import bosdyn.client.util
import bosdyn.geometry
from bosdyn.api.graph_nav import area_callback_pb2
from bosdyn.api.graph_nav.area_callback_pb2 import UpdateCallbackResponse
from bosdyn.client import spot_cam
from bosdyn.client.area_callback_region_handler_base import AreaCallbackRegionHandlerBase
from bosdyn.client.area_callback_service_runner import run_service
from bosdyn.client.area_callback_service_servicer import AreaCallbackServiceServicer
from bosdyn.client.area_callback_service_utils import AreaCallbackServiceConfig
from bosdyn.client.robot import Robot
from bosdyn.client.spot_cam.lights_helper import LightsHelper


class AreaCallbackCrossWalkService(AreaCallbackRegionHandlerBase):
    """An example implementation which lets the robot to check for forklift while crossing the road.
    """

    def __init__(self, config: AreaCallbackServiceConfig, robot: Robot):
        super().__init__(config, robot)
        # Set the policies at the start & end of the Area Callback region
        self.robot = robot
        self.logger = logging.getLogger(__name__)

        self.stop_at_start()
        self.continue_past_end()

    def begin(
        self, request: area_callback_pb2.BeginCallbackRequest
    ) -> area_callback_pb2.BeginCallbackResponse.Status:
        # Unpack any configuration settings
        return area_callback_pb2.BeginCallbackResponse.STATUS_OK

    def run(self):
        # Actions to be executed while approaching the Area Callback region
        self.block_until_arrived_at_start()  # block the code until the robot reaches the start

        # Pass in robot object, desired light frequency (Hz), and desired light brightness for waiting
        # Lights will flash at 0.5Hz with brightness of 20%
        with LightsHelper(self.robot, 0.5, 0.2):
            self.safe_sleep(5.0)
        # Lights will be turned off upon exiting from LightsHelper

        # proceed walking to the end of the Area callback region
        self.continue_past_start()

        # Pass in robot object, desired light frequency (Hz), and desired light brightness for crossing
        # Lights will flash at 3Hz with brightness of 80%
        with LightsHelper(self.robot, 3, 0.8):
            self.block_until_arrived_at_end()  # block the code until the robot reaches the end
        # Lights will be turned off upon exiting from LightsHelper

    def end(self):
        # Actions that need to be executed after the robot goes past Area Callback region
        # Actions to be executed at the end of the Area Callback region
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
    sdk = bosdyn.client.create_standard_sdk('AreaCallbackCrosswalkLightsService')
    spot_cam.register_all_service_clients(sdk)  # register service client for spotcam light
    robot = sdk.create_robot(options.hostname)
    robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(options))
    #bosdyn.client.util.authenticate(robot)
    robot.start_time_sync(time_sync_interval_sec=0.01)
    robot.time_sync.wait_for_sync()

    # Configure the area callback service.
    service_name = "crosswalk-lights"
    # required_lease_resources = ["body"] # we do not need body lease for forklift detection & spotcam lights
    config = AreaCallbackServiceConfig(service_name)
    servicer = AreaCallbackServiceServicer(robot, config, AreaCallbackCrossWalkService)

    # Run the area callback service.
    service_runner, keep_alive = run_service(robot, servicer, options.port, self_ip)
    with keep_alive:
        service_runner.run_until_interrupt()


if __name__ == "__main__":
    main()
