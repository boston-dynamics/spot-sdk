# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from __future__ import print_function

import logging
import signal
import time

import bosdyn.client.util
from bosdyn.api import data_acquisition_pb2, data_acquisition_plugin_service_pb2_grpc
from bosdyn.api.point_cloud_pb2 import PointCloud
from bosdyn.client.data_acquisition_plugin_service import Capability, DataAcquisitionPluginService
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.exceptions import ServiceUnavailableError
from bosdyn.client.point_cloud import PointCloudClient
from bosdyn.client.server_util import GrpcServiceRunner
from bosdyn.client.util import setup_logging

DIRECTORY_NAME = 'data-acquisition-pointcloud-plugin'
AUTHORITY = 'data-acquisition-pc-plugin'

_LOGGER = logging.getLogger(__name__)


class PointCloudAdapter:
    """Provide access to the latest data from a point-cloud service.

    Args:
        robot(bosdyn.client.Robot): Robot instance to use for creating PointCloudClient.
    """

    def __init__(self, robot, point_cloud_service_name):
        self._point_cloud_client = robot.ensure_client(point_cloud_service_name)
        self._service_name = point_cloud_service_name

    def get_capabilities(self):
        """Get list of available capabilities to capture point-clouds.

        The capabilities available will vary depending on what sources of pointclouds are
        available. This method blocks until it communicates with the SpotCAM MediaLog service.

        Returns:
            Array with list of Capabilities corresponding to the available point-cloud sensors.
        """

        while True:
            try:
                sources = self._point_cloud_client.list_point_cloud_sources()
                break
            except ServiceUnavailableError:
                _LOGGER.exception('PointCloud service is still unavailable:\n')
                time.sleep(2)

        capabilities = []
        for source in sources:
            name = source.name
            capabilities.append(
                Capability(name=name,
                           description="Point-clouds from a {} LIDAR sensor.".format(name),
                           channel_name="{}--{}".format(self._service_name, name)))
        return capabilities

    def get_point_cloud_data(self, request, store_helper):
        """Save the latest point-cloud data to the data store."""
        point_cloud_responses = self._point_cloud_client.get_point_cloud_from_sources(
            [capture.name for capture in request.acquisition_requests.data_captures])
        for point_cloud_response in point_cloud_responses:
            data_id = data_acquisition_pb2.DataIdentifier(
                action_id=request.action_id, channel=point_cloud_response.point_cloud.source.name)
            store_helper.store_data(point_cloud_response.point_cloud.SerializeToString(), data_id)
        store_helper.state.set_status(data_acquisition_pb2.GetStatusResponse.STATUS_SAVING)


def make_service(robot, point_cloud_service_name, logger=None):
    adapter = PointCloudAdapter(robot, point_cloud_service_name)
    capabilities = adapter.get_capabilities()
    return DataAcquisitionPluginService(robot, capabilities, adapter.get_point_cloud_data)


def run_service(bosdyn_sdk_robot, port, point_cloud_service_name, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = data_acquisition_plugin_service_pb2_grpc.add_DataAcquisitionPluginServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = make_service(bosdyn_sdk_robot, point_cloud_service_name, logger=logger)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


def add_pointcloud_plugin_arguments(parser):
    parser.add_argument('--pointcloud-service',
                        help="Name of the point-cloud service to get data from.", required=True)


if __name__ == '__main__':
    # Define all arguments used by this service.
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    add_pointcloud_plugin_arguments(parser)
    options = parser.parse_args()

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk("PointcloudPluginServiceSDK")
    robot = sdk.create_robot(options.hostname)
    robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(options))
    robot.sync_with_directory()

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options.port, options.pointcloud_service, logger=_LOGGER)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, DataAcquisitionPluginService.service_type, AUTHORITY,
                     options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()
