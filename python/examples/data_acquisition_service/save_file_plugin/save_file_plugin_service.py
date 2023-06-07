# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Data Acquisition plugin for saving a file to the robot.
"""

import argparse
import logging
import pathlib

import bosdyn.client.util
from bosdyn.api import data_acquisition_pb2, data_acquisition_plugin_service_pb2_grpc
from bosdyn.client.data_acquisition_plugin_service import Capability, DataAcquisitionPluginService
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.server_util import GrpcServiceRunner
from bosdyn.client.util import setup_logging

_LOGGER = logging.getLogger(__name__)

DIRECTORY_NAME = 'data-acquisition-save-file-plugin'
AUTHORITY = 'data-acquisition-save-file-plugin'
CAPABILITY = Capability(name='data', description='Example data loaded from a file',
                        channel_name='data')


class SaveFileAdapter:
    """Provide access to a file loaded from disk.

    Args:
        save_file_service_name: Name for this service.
    """

    def __init__(self, save_file_service_name, file_path):
        self._service_name = save_file_service_name
        self._file_extension = pathlib.Path(file_path).suffix
        with open(file_path, "rb") as f:
            self._file_data = f.read()

    def get_file_data(self, request, store_helper):
        """Save the file data to the data store."""
        data_id = data_acquisition_pb2.DataIdentifier(action_id=request.action_id,
                                                      channel=CAPABILITY.channel_name)
        store_helper.store_data(self._file_data, data_id, file_extension=self._file_extension)
        store_helper.state.set_status(data_acquisition_pb2.GetStatusResponse.STATUS_SAVING)


def make_service(robot, save_file_service_name, file_path, logger=None):
    adapter = SaveFileAdapter(save_file_service_name, file_path)
    return DataAcquisitionPluginService(robot, [CAPABILITY], adapter.get_file_data)


def run_service(bosdyn_sdk_robot, port, save_file_service_name, file_path, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = data_acquisition_plugin_service_pb2_grpc.add_DataAcquisitionPluginServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = make_service(bosdyn_sdk_robot, save_file_service_name, file_path,
                                    logger=logger)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


def add_save_file_arguments(parser):
    parser.add_argument('--file-path', help='Full path to the file on disk.', required=True)


def main():
    # Define all arguments used by this service.
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    add_save_file_arguments(parser)
    options = parser.parse_args()

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk('SaveFilePluginServiceSDK')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    robot.sync_with_directory()

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options.port, "save_file_service", options.file_path,
                                 logger=_LOGGER)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, DataAcquisitionPluginService.service_type, AUTHORITY,
                     options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()


if __name__ == "__main__":
    main()
