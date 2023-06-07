# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the robot_id client."""
import logging
import time

import grpc
import pytest

import bosdyn.api.robot_id_pb2 as robot_id_protos
import bosdyn.api.robot_id_service_pb2_grpc as robot_id_service
import bosdyn.client.robot_id
from bosdyn.client.exceptions import TimedOutError

from . import helpers


class MockRobotIdServicer(robot_id_service.RobotIdServiceServicer):

    def __init__(self, rpc_delay=0, robot_id=None):
        """Create mock that returns specific token after optional delay."""
        super(MockRobotIdServicer, self).__init__()
        self._rpc_delay = rpc_delay
        self._robot_id = robot_id or robot_id_protos.RobotId()

    def GetRobotId(self, request, context):
        resp = robot_id_protos.RobotIdResponse()
        helpers.add_common_header(resp, request)
        resp.robot_id.MergeFrom(self._robot_id)
        time.sleep(self._rpc_delay)
        return resp


def _setup(rpc_delay=0, robot_id=None):
    client = bosdyn.client.robot_id.RobotIdClient()
    service = MockRobotIdServicer(rpc_delay=rpc_delay, robot_id=robot_id)
    server = helpers.setup_client_and_service(client, service,
                                              robot_id_service.add_RobotIdServiceServicer_to_server)
    return client, service, server


def _create_fake_robot_id():
    robot_id = robot_id_protos.RobotId()
    robot_id.serial_number = 'B12313'
    robot_id.species = 'spot'
    robot_id.version = '1.1.12'
    robot_id.software_release.version.major_version = 1
    robot_id.software_release.version.minor_version = 1
    robot_id.software_release.version.patch_level = 12
    robot_id.nickname = 'goofball'
    robot_id.computer_serial_number = 'fdafds'
    return robot_id


def _check_robot_id(robot_id):
    assert robot_id.serial_number == 'B12313'
    assert robot_id.species == 'spot'


def test_get_robot_id():
    client, service, server = _setup(robot_id=_create_fake_robot_id())
    robot_id = client.get_id()
    _check_robot_id(robot_id)


def test_get_robot_id_async():
    client, service, server = _setup(robot_id=_create_fake_robot_id())
    fut = client.get_id_async()
    robot_id = fut.result()
    _check_robot_id(robot_id)


def test_get_robot_id_timeout():
    timeout = 0.1
    client, service, server = _setup(rpc_delay=(2.0 * timeout), robot_id=_create_fake_robot_id())
    with pytest.raises(TimedOutError):
        result = client.get_id(timeout=timeout)


def test_get_robot_id_async_timeout():
    timeout = 0.1
    client, service, server = _setup(rpc_delay=(2.0 * timeout), robot_id=_create_fake_robot_id())
    fut = client.get_id_async(timeout=timeout)
    with pytest.raises(TimedOutError):
        result = fut.result()


def test_version_tuple():
    client, service, server = _setup(robot_id=_create_fake_robot_id())
    robot_id = client.get_id()
    bosdyn.client.robot_id.version_tuple(robot_id.software_release.version) == (1, 1, 12)
