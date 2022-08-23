# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging

from google.protobuf import json_format

import bosdyn.client.util
from bosdyn.api import data_acquisition_pb2, data_acquisition_plugin_service_pb2_grpc
from bosdyn.client.data_acquisition_plugin_service import (Capability, DataAcquisitionPluginService,
                                                           DataAcquisitionStoreHelper)
from bosdyn.client.data_acquisition_store import DataAcquisitionStoreClient
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.server_util import GrpcServiceRunner
from bosdyn.client.util import setup_logging

DIRECTORY_NAME = 'data-acquisition-battery'
AUTHORITY = 'data-acquisition-battery'
CAPABILITY = Capability(name='battery', description='Battery level', channel_name='battery')

_LOGGER = logging.getLogger('battery_plugin')


class BatteryAdapter:
    """Basic plugin for reporting battery level"""

    def __init__(self, sdk_robot):
        self.client = sdk_robot.ensure_client(RobotStateClient.default_service_name)

    def get_battery_data(self, request: data_acquisition_pb2.AcquirePluginDataRequest,
                         store_helper: DataAcquisitionStoreHelper):
        """Save the latest battery data to the data store."""
        data_id = data_acquisition_pb2.DataIdentifier(action_id=request.action_id,
                                                      channel=CAPABILITY.channel_name)

        state = self.client.get_robot_state(timeout=1)

        # Check if the request has been cancelled.
        store_helper.cancel_check()

        # All the data we need is now collected, so we can tell clients that we have moved on to
        # saving the data.
        store_helper.state.set_status(data_acquisition_pb2.GetStatusResponse.STATUS_SAVING)

        # Populate data acquisition store message.
        message = data_acquisition_pb2.AssociatedMetadata()
        message.reference_id.action_id.CopyFrom(request.action_id)
        message.metadata.data.update({
            "battery_percentage":
                state.power_state.locomotion_charge_percentage.value,
            "battery_runtime":
                json_format.MessageToJson(state.power_state.locomotion_estimated_runtime)
        })
        _LOGGER.info("Retrieving battery data: {}".format(message.metadata.data))

        # Store the data and manage store state.
        store_helper.store_metadata(message, data_id)


def make_servicer(sdk_robot):
    """Create the data acquisition servicer for the battery data."""
    adapter = BatteryAdapter(sdk_robot)
    return DataAcquisitionPluginService(sdk_robot, [CAPABILITY], adapter.get_battery_data,
                                        logger=_LOGGER)


def run_service(sdk_robot, port):
    """Create and run the battery plugin service."""
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = data_acquisition_plugin_service_pb2_grpc.add_DataAcquisitionPluginServiceServicer_to_server

    # Instance of the servicer to be run.
    return GrpcServiceRunner(make_servicer(sdk_robot), add_servicer_to_server_fn, port,
                             logger=_LOGGER)


if __name__ == '__main__':
    # Define all arguments used by this service.
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    options = parser.parse_args()

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk("BatteryPlugin")
    robot = sdk.create_robot(options.hostname)
    robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(options))

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options.port)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, DataAcquisitionPluginService.service_type, AUTHORITY,
                     options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()
