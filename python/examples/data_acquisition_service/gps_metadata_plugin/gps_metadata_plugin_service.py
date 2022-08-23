# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from __future__ import print_function

import logging
import math
import random
import threading
import time

import bosdyn.client.util
from bosdyn.api import data_acquisition_pb2, data_acquisition_plugin_service_pb2_grpc
from bosdyn.client.data_acquisition_plugin_service import (Capability, DataAcquisitionPluginService,
                                                           RequestState)
from bosdyn.client.data_acquisition_store import DataAcquisitionStoreClient
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.server_util import GrpcServiceRunner
from bosdyn.client.util import setup_logging

DIRECTORY_NAME = 'data-acquisition-gps-metadata-plugin'
AUTHORITY = 'data-acquisition-gps-metadata-plugin'

_LOGGER = logging.getLogger(__name__)

kName = 'GPS'
kChannel = 'GPS'
kDescription = 'GPS latitude/longitude coordinates'
kCapabilities = [Capability(name=kName, description=kDescription, channel_name=kChannel)]


class GPSData:

    def __init__(self, lat, lon, alt):
        self.lat = lat
        self.lon = lon
        self.alt = alt


class GPS_Adapter:
    """Provide access to the latest data from a fake sensor."""

    def __init__(self):
        self.data_lock = threading.Lock()
        self.data = None
        self.background_thread = threading.Thread(target=self.read_loop, daemon=True)
        self.background_thread.start()

    def read_loop(self):
        """Continually read from the sensor in a loop."""
        while True:
            self.read_GPS_from_sensor()
            time.sleep(0.5)

    def read_GPS_from_sensor(self):
        """Update the internal data with random numbers."""
        with self.data_lock:
            self.data = GPSData(random.random() * math.pi - math.pi / 2,
                                random.random() * 2 * math.pi - math.pi, 0.0)

    def get_GPS_data(self, request, store_helper):
        """Save the latest GPS data to the data store."""
        data_id = data_acquisition_pb2.DataIdentifier(action_id=request.action_id, channel=kChannel)

        # Get GPS data.
        with self.data_lock:
            data = self.data

        # Populate data acquisition store message.
        message = data_acquisition_pb2.AssociatedMetadata()
        message.reference_id.action_id.CopyFrom(request.action_id)
        message.metadata.data.update({
            "latitude": data.lat,
            "longitude": data.lon,
            "altitude": data.alt,
        })
        _LOGGER.info("Retrieving GPS data: {}".format(message.metadata.data))

        # Store the data and manage store state.
        store_helper.store_metadata(message, data_id)
        store_helper.state.set_status(data_acquisition_pb2.GetStatusResponse.STATUS_SAVING)


def make_service(bosdyn_sdk_robot, logger=None):
    adapter = GPS_Adapter()
    return DataAcquisitionPluginService(bosdyn_sdk_robot, kCapabilities, adapter.get_GPS_data,
                                        logger=logger)


def run_service(bosdyn_sdk_robot, port, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = data_acquisition_plugin_service_pb2_grpc.add_DataAcquisitionPluginServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = make_service(bosdyn_sdk_robot, logger=logger)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


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
    sdk = bosdyn.client.create_standard_sdk("GpsMetadataPluginServiceSDK")
    robot = sdk.create_robot(options.hostname)
    robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(options))

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options.port, logger=_LOGGER)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, DataAcquisitionPluginService.service_type, AUTHORITY,
                     options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()
