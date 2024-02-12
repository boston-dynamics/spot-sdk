# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging

import bosdyn.client.util
import bosdyn.geometry
from bosdyn.api.graph_nav import area_callback_pb2
from bosdyn.api.graph_nav.area_callback_pb2 import UpdateCallbackResponse
from bosdyn.client.area_callback_region_handler_base import AreaCallbackRegionHandlerBase
from bosdyn.client.area_callback_service_runner import run_service
from bosdyn.client.area_callback_service_servicer import AreaCallbackServiceServicer
from bosdyn.client.area_callback_service_utils import AreaCallbackServiceConfig
from bosdyn.client.robot import Robot


class AreaCallbackDummy(AreaCallbackRegionHandlerBase):
    """An example implementation which does nothing.
    """

    def __init__(self, config: AreaCallbackServiceConfig, robot: Robot):
        super().__init__(config, robot)
        # Set the policy for start & end of the area callback region
        self.continue_past_start()
        # self.stop_at_start()
        # self.control_at_start()

        self.continue_past_end()
        # self.stop_at_end()
        # self.control_at_end()

    def begin(
        self, request: area_callback_pb2.BeginCallbackRequest
    ) -> area_callback_pb2.BeginCallbackResponse.Status:
        return area_callback_pb2.BeginCallbackResponse.STATUS_OK

    def run(self):
        # self.block_until_arrived_at_start()
        # self.block_until_control()
        # self.continue_past_start()
        # self.block_until_arrived_at_end()
        # self.block_until_control()
        # self.continue_past_end()
        self.safe_sleep(1)

    def end(self):
        logging.info('End() called')


def main():
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    options = parser.parse_args()
    bosdyn.client.util.setup_logging(options.verbose)

    # Initialize robot object.
    sdk = bosdyn.client.create_standard_sdk('AreaCallbackDummy')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.start_time_sync()
    robot.time_sync.wait_for_sync()

    # Configure the area callback service.
    service_name = 'area-callback-dummy'
    config = AreaCallbackServiceConfig(service_name)
    info = config.area_callback_information

    # This callback does not do anything special to get past obstacles, so we should allow
    # Graph Nav to identify blockages in the region.
    info.blockage = info.BLOCKAGE_CHECK
    # This callback does not control the robot, but if it did Graph Nav should still check for
    # impairment and be able to interrupt this callback.
    info.impairment_check = info.IMPAIRMENT_CHECK
    # Graph Nav should still wait for entities as normal when crossing this region.
    info.entity_waiting = info.ENTITY_WAITING_ENABLE
    # The robot should face along the route it is going to cross.
    info.default_stop.face_direction = info.default_stop.FACE_DIRECTION_ALONG_ROUTE

    servicer = AreaCallbackServiceServicer(robot, config, AreaCallbackDummy)

    # Run the area callback service.
    service_runner, keep_alive = run_service(robot, servicer, options.port, options.host_ip)
    with keep_alive:
        service_runner.run_until_interrupt()


if __name__ == '__main__':
    main()
