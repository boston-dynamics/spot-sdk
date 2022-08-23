# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from __future__ import print_function

import logging
import time

import google.protobuf.json_format as json_format

import bosdyn.client.util
from bosdyn.api import (data_acquisition_pb2, data_acquisition_plugin_service_pb2_grpc,
                        network_compute_bridge_pb2, world_object_pb2)
from bosdyn.client.data_acquisition import DataAcquisitionClient
from bosdyn.client.data_acquisition_plugin_service import (Capability, DataAcquisitionPluginService,
                                                           RequestCancelledError, make_error)
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.network_compute_bridge_client import (ExternalServerError,
                                                         ExternalServiceNotFoundError,
                                                         NetworkComputeBridgeClient)
from bosdyn.client.util import GrpcServiceRunner, setup_logging

# from bosdyn.client.server_util import

AUTHORITY = 'data-acquisition-ncb-plugin'

_LOGGER = logging.getLogger(__name__)

kCapabilityImage = "image"
kCapabilityObjectInImage = "object_in_image"
kCapabilityNames = [kCapabilityImage, kCapabilityObjectInImage]


def get_directory_name(network_compute_bridge_worker_name):
    return '{}-{}-plugin'.format(DataAcquisitionClient.default_service_name,
                                 network_compute_bridge_worker_name)


class NetworkComputeBrideAdapter:
    """Provide access to the latest data from a network compute bridge worker.

    Args:
        robot (bosdyn.client.Robot): Robot instance to use for creating NetworkComputeBridgeClient.
        network_compute_bridge_worker_name (string): Name as listed in the directory of the worker.
    """

    def __init__(self, robot, network_compute_bridge_worker_name):
        self._network_compute_bridge_client = robot.ensure_client(
            NetworkComputeBridgeClient.default_service_name)
        self._worker_name = network_compute_bridge_worker_name

    def get_capabilities(self):
        """Get list of available data capture options for the network compute bridge worker.

        Returns:
            Array with list of Capabilities corresponding to the available data capture options.
        """

        # Try to get a list of models available from the worker to see if this service is alive.
        while True:
            try:
                server_data = network_compute_bridge_pb2.NetworkComputeServerConfiguration(
                    service_name=self._worker_name)
                list_req = network_compute_bridge_pb2.ListAvailableModelsRequest(
                    server_config=server_data)
                response = self._network_compute_bridge_client.list_available_models_command(
                    list_req)
                break
            except (ExternalServiceNotFoundError, ExternalServerError):
                _LOGGER.exception('Network compute bridge worker is still unavailable:\n')
                time.sleep(2)
        if response.header.error.message:
            _LOGGER.error("List available models from %s returned with error: %s",
                          self._worker_name, response.header.error.message)
        else:
            _LOGGER.info('Available models from %s:', self._worker_name)
            for model in response.available_models:
                _LOGGER.info('   %s', model)

        # Compose the list of data capture options.
        capabilities = []
        _LOGGER.info('Available data capture options:')
        for name in kCapabilityNames:
            _LOGGER.info('   %s', name)
            capabilities.append(
                Capability(name=name,
                           description="Processed {} from {}.".format(name, self._worker_name),
                           channel_name="{}--{}".format(self._worker_name, name)))

        return capabilities

    def get_network_compute_data(self, request, store_helper):
        """Make the RPC to the network compute bridge worker and save results to the data store.

        Args:
            request (bosdyn.api.AcquirePluginDataRequest): Plugin request.
            store_helper (bosdyn.client.DataAcquisitionStoreHelper): Helper used to manage storage
                of objects in data acquisition store service.
        """

        try:
            _LOGGER.info("Requesting data from %s...", self._worker_name)
            network_compute_bridge_metadata = request.metadata.data["network_compute_bridge"]
            response = self._request_data(request, network_compute_bridge_metadata, store_helper)

            for capture in request.acquisition_requests.data_captures:
                data_id = self._get_data_id(request, capture.name)

                if capture.name == kCapabilityImage:
                    store_helper.cancel_check()
                    _LOGGER.info("Storing image with data id %s...", data_id)
                    store_helper.state.set_status(
                        data_acquisition_pb2.GetStatusResponse.STATUS_SAVING)
                    store_helper.store_image(response.image_response.shot, data_id)

                elif capture.name == kCapabilityObjectInImage:
                    store_helper.cancel_check()
                    _LOGGER.info("Storing detection info with data id %s...", data_id)

                    detection_info = world_object_pb2.ListWorldObjectResponse(
                        world_objects=response.object_in_image)
                    detection_metadata = data_acquisition_pb2.Metadata()
                    detection_metadata.data.update(json_format.MessageToDict(detection_info))
                    reference_id = self._get_data_id(request, kCapabilityImage)
                    associated_metadata = data_acquisition_pb2.AssociatedMetadata(
                        reference_id=reference_id, metadata=detection_metadata)
                    store_helper.store_metadata(associated_metadata, data_id)
                else:
                    errMsg = "Unknown capability {}.".format(capture.name)
                    store_helper.state.add_errors([make_error(data_id, errMsg)])
                    _LOGGER.error(errMsg)

        except ValueError:
            errMsg = "Unable to get network compute bridge info."
            store_helper.state.add_errors([make_error(data_id, errMsg)])
            _LOGGER.error(errMsg)
        except RequestCancelledError:
            _LOGGER.info("Capture canceled.")

    def _get_data_id(self, request, capability_name):
        """Get a data id for the given capability.

        Args:
            request (bosdyn.api.AcquirePluginDataRequest): Plugin request.
            capability_name (string):  Name of the capability to get data id for.

        Returns:
            The data id associated with the given capability name.
        """
        data_id = data_acquisition_pb2.DataIdentifier(
            action_id=request.action_id, channel="{}--{}".format(self._worker_name,
                                                                 capability_name))
        return data_id

    def _request_data(self, request, network_compute_bridge_metadata, store_helper):
        """Make the RPC to the network compute bridge worker.

        Args:
            request (bosdyn.api.AcquirePluginDataRequest): Plugin request.
            network_compute_bridge_metadata (google.protobuf.Struct): Metadata containing
                information needed for the request
            store_helper (bosdyn.client.DataAcquisitionStoreHelper): Helper used to manage storage
                of objects in data acquisition store service.

        Returns:
            The response from the compute request or None if error occurs
        """

        server_config = network_compute_bridge_pb2.NetworkComputeServerConfiguration(
            service_name=self._worker_name)

        try:
            image_service = network_compute_bridge_metadata["image_service"]
            image_source = network_compute_bridge_metadata["image_source"]
        except ValueError:
            errMsg = "Unable to get image service and source info."
            data_id = self._get_data_id(request, kCapabilityImage)
            store_helper.state.add_errors([make_error(data_id, errMsg)])
            _LOGGER.error(errMsg)

        service_source = network_compute_bridge_pb2.ImageSourceAndService(
            image_service=image_service, image_source=image_source)

        try:
            model_name = network_compute_bridge_metadata["model_name"]
            min_confidence = network_compute_bridge_metadata["min_confidence"]
        except ValueError:
            errMsg = "Unable to get model name or confidence value."
            data_id = self._get_data_id(request, kCapabilityObjectInImage)
            store_helper.state.add_errors([make_error(data_id, errMsg)])
            _LOGGER.error(errMsg)

        input_data = network_compute_bridge_pb2.NetworkComputeInputData(
            image_source_and_service=service_source, model_name=model_name,
            min_confidence=min_confidence)
        network_compute_request = network_compute_bridge_pb2.NetworkComputeRequest(
            server_config=server_config, input_data=input_data)

        response = self._network_compute_bridge_client.network_compute_bridge_command(
            network_compute_request)
        return response


def make_service(robot, network_compute_bridge_worker_name, logger=None):
    adapter = NetworkComputeBrideAdapter(robot, network_compute_bridge_worker_name)
    capabilities = adapter.get_capabilities()
    return DataAcquisitionPluginService(robot, capabilities, adapter.get_network_compute_data)


def run_service(bosdyn_sdk_robot, port, network_compute_bridge_worker_name, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = data_acquisition_plugin_service_pb2_grpc.add_DataAcquisitionPluginServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = make_service(bosdyn_sdk_robot, network_compute_bridge_worker_name,
                                    logger=logger)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


def add_network_compute_bridge_plugin_arguments(parser):
    parser.add_argument('--worker-name',
                        help="Name of the network compute bridge worker to get data from.",
                        required=True)


if __name__ == '__main__':
    # Define all arguments used by this service.
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    default_port = 50052
    parser.add_argument('-p', '--port', help=f'Server\'s port number, default: {default_port}',
                        default=default_port)
    add_network_compute_bridge_plugin_arguments(parser)
    options = parser.parse_args()

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.
    self_ip = bosdyn.client.common.get_self_ip(options.hostname)
    print('Detected IP address as: ' + self_ip)
    sdk = bosdyn.client.create_standard_sdk("PointcloudPluginServiceSDK")
    robot = sdk.create_robot(options.hostname)
    robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(options))
    robot.sync_with_directory()

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options.port, options.worker_name, logger=_LOGGER)

    # Set up the directory name.  The name must have the pattern data-acquisition-XXX-plugin.
    directory_name = get_directory_name(options.worker_name)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(directory_name, DataAcquisitionPluginService.service_type, AUTHORITY, self_ip,
                     service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()
