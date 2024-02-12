# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging

from build_signal import build_signals
from core_io_auth import PASSWORD, USERNAME
from core_io_helpers import CoreIOHelper

import bosdyn.client
from bosdyn.api import data_acquisition_pb2, data_acquisition_plugin_service_pb2_grpc
from bosdyn.client.data_acquisition_plugin_service import (Capability, DataAcquisitionPluginService,
                                                           DataAcquisitionStoreHelper)
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.server_util import GrpcServiceRunner
from bosdyn.client.signals_helpers import build_capability_live_data, build_live_data_response
from bosdyn.client.util import setup_logging

DIRECTORY_NAME = 'data-acquisition-modem'
AUTHORITY = 'data-acquisition-modem'
CAPABILITY = Capability(name='modem', description="Core I/O Telit modem stats",
                        channel_name='modem', has_live_data=True)
CLIENT_NAME = 'ModemPlugin'
_LOGGER = logging.getLogger('Modem_plugin')


class ModemAdapter:
    """Modem DAQ plugin adapter."""

    def __init__(self, options):
        # Using host_ip with the assumption that this DAQ plugin is run on the COREIO.
        self.coreio = CoreIOHelper(options.host_ip, USERNAME, PASSWORD, _LOGGER)
        self.coreio.login()

    def get_signals_data(self, request: data_acquisition_pb2.AcquirePluginDataRequest,
                         store_helper: DataAcquisitionStoreHelper):
        """Save the latest battery data to the data store."""
        data_id = data_acquisition_pb2.DataIdentifier(action_id=request.action_id,
                                                      channel=CAPABILITY.channel_name)

        # Collect the data from the modem
        data = self.coreio.get_modem_stats()

        # Check if the request has been cancelled.
        store_helper.cancel_check()

        # All the data we need is now collected, so we can tell clients that we have moved on to
        # saving the data.
        store_helper.state.set_status(data_acquisition_pb2.GetStatusResponse.STATUS_SAVING)

        # Populate data acquisition store message.
        message = data_acquisition_pb2.AssociatedMetadata()
        message.reference_id.action_id.CopyFrom(request.action_id)
        message.metadata.data.update({
            'signal_quality': data['signalQuality'],
            'SINR': int(data['sinr']) / 12.5,
            'RSRP': data['rsrp'],
            'RSRQ': data['rsrq']
        })
        _LOGGER.info('Retrieving modem stats: %s', message.metadata.data)

        # Store the data and manage store state.
        store_helper.store_metadata(message, data_id)

    def get_live_data(self, request: data_acquisition_pb2.LiveDataRequest):
        """Handler for a GetLiveData RPC."""
        request_capabilities = ", ".join(
            data_capture.name for data_capture in request.data_captures)
        _LOGGER.info("Get_live_data called, request_capabilities: %s", request_capabilities)
        data = self.coreio.get_modem_stats()
        signals = build_signals(data)
        return build_live_data_response([build_capability_live_data(signals, CAPABILITY.name)])


def make_servicer(sdk_robot, options):
    """Create the data acquisition servicer for the data."""
    adapter = ModemAdapter(options)
    return DataAcquisitionPluginService(sdk_robot, [CAPABILITY], adapter.get_signals_data,
                                        live_response_fn=adapter.get_live_data, logger=_LOGGER)


def run_service(sdk_robot, options):
    """Create and run the plugin service."""
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = data_acquisition_plugin_service_pb2_grpc.add_DataAcquisitionPluginServiceServicer_to_server

    # Instance of the servicer to be run.
    return GrpcServiceRunner(make_servicer(sdk_robot, options), add_servicer_to_server_fn,
                             options.port, logger=_LOGGER)


if __name__ == '__main__':
    # Define all arguments used by this service.
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser, required=False)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    options = parser.parse_args()

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk(CLIENT_NAME)
    robot = sdk.create_robot(options.hostname)
    # Authenticate robot before being able to use it
    if options.payload_credentials_file:
        robot.authenticate_from_payload_credentials(
            *bosdyn.client.util.get_guid_and_secret(options))
    else:
        bosdyn.client.util.authenticate(robot)

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, DataAcquisitionPluginService.service_type, AUTHORITY,
                     options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()
