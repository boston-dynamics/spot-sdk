# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

# pylint: disable=missing-module-docstring
from bosdyn.api.graph_nav import area_callback_service_pb2_grpc
from bosdyn.client.area_callback_service_servicer import AreaCallbackServiceServicer
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.robot import Robot
from bosdyn.client.server_util import GrpcServiceRunner


def run_service(robot: Robot, service: AreaCallbackServiceServicer, port: int, host_ip: str):
    """Helper function to start AreaCallback service and register it with directory keep alive.

    Args:
        robot (Robot): Robot object to use for directory registration.
        service (AreaCallbackServiceServicer): The AreaCallbackService implementation
        port (int): Port the AreaCallback service should connect to.
        host_ip (str): The IP address of the computer hosting this endpoint.

    Returns:
        (GrpcServiceRunner, DirectoryRegistrationKeepAlive)
    """
    add_servicer_to_server_fn = area_callback_service_pb2_grpc.add_AreaCallbackServiceServicer_to_server

    service_runner = GrpcServiceRunner(service, add_servicer_to_server_fn, port, max_workers=1)

    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client)
    service_name = service.area_callback_service_config.service_name
    keep_alive.start(service_name, service.SERVICE_TYPE, service_name, host_ip, service_runner.port)

    return (service_runner, keep_alive)
