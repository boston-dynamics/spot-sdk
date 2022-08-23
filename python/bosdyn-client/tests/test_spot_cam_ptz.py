# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the Spot CAM's PtzClient."""
import time

import grpc
import pytest
from pytest import approx

import bosdyn.client.spot_cam.ptz
from bosdyn.api.spot_cam import ptz_pb2, service_pb2_grpc

from . import helpers


class MockPtzService(service_pb2_grpc.PtzServiceServicer):

    def __init__(self, rpc_delay=0):
        """Create mock that returns fake ptz responses."""
        super(MockPtzService, self).__init__()
        self._rpc_delay = rpc_delay

    def ListPtz(self, request, context):
        time.sleep(self._rpc_delay)

        response = ptz_pb2.ListPtzResponse()
        response.ptzs.add().name = 'digi'
        response.ptzs.add().name = 'full_digi'
        response.ptzs.add().name = 'mech'
        response.ptzs.add().name = 'overlay_digi'
        response.ptzs.add().name = 'full_pano'
        response.ptzs.add().name = 'overlay_pano'
        helpers.add_common_header(response, request)
        return response

    def GetPtzPosition(self, request, context):
        time.sleep(self._rpc_delay)

        response = ptz_pb2.GetPtzPositionResponse()
        response.position.ptz.CopyFrom(request.ptz)
        response.position.pan.value = 1.0
        response.position.tilt.value = 2.0
        response.position.zoom.value = 3.0
        helpers.add_common_header(response, request)
        return response

    def GetPtzVelocity(self, request, context):
        time.sleep(self._rpc_delay)

        response = ptz_pb2.GetPtzVelocityResponse()
        response.velocity.ptz.CopyFrom(request.ptz)
        response.velocity.pan.value = 1.0
        response.velocity.tilt.value = 2.0
        response.velocity.zoom.value = 3.0
        helpers.add_common_header(response, request)
        return response

    def SetPtzPosition(self, request, context):
        time.sleep(self._rpc_delay)

        response = ptz_pb2.SetPtzPositionResponse()
        response.position.CopyFrom(request.position)
        helpers.add_common_header(response, request)
        return response

    def SetPtzVelocity(self, request, context):
        time.sleep(self._rpc_delay)

        response = ptz_pb2.SetPtzVelocityResponse()
        response.velocity.CopyFrom(request.velocity)
        helpers.add_common_header(response, request)
        return response


def _setup(rpc_delay=0):
    client = bosdyn.client.spot_cam.ptz.PtzClient()
    service = MockPtzService(rpc_delay=rpc_delay)
    server = helpers.setup_client_and_service(client, service,
                                              service_pb2_grpc.add_PtzServiceServicer_to_server)
    return client, service, server


def _create_fake_ptz_desc(name='fake-ptz'):
    desc = ptz_pb2.PtzDescription()
    desc.name = name
    return desc


def test_list_ptz():
    client, service, server = _setup()
    ptzs = client.list_ptz()
    assert len(ptzs) == 6


def test_list_ptz_async():
    client, service, server = _setup()
    ptzs = client.list_ptz_async().result()
    assert len(ptzs) == 6


def test_get_ptz_position():
    client, service, server = _setup()
    desc = _create_fake_ptz_desc()
    position = client.get_ptz_position(desc)
    assert position.ptz.name == desc.name
    assert position.pan.value == approx(1.0)
    assert position.tilt.value == approx(2.0)
    assert position.zoom.value == approx(3.0)


def test_get_ptz_position_async():
    client, service, server = _setup()
    desc = _create_fake_ptz_desc()
    position = client.get_ptz_position_async(desc).result()
    assert position.ptz.name == desc.name
    assert position.pan.value == approx(1.0)
    assert position.tilt.value == approx(2.0)
    assert position.zoom.value == approx(3.0)


def test_get_ptz_velocity():
    client, service, server = _setup()
    desc = _create_fake_ptz_desc()
    velocity = client.get_ptz_velocity(desc)
    assert velocity.ptz.name == desc.name
    assert velocity.pan.value == approx(1.0)
    assert velocity.tilt.value == approx(2.0)
    assert velocity.zoom.value == approx(3.0)


def test_get_ptz_velocity_async():
    client, service, server = _setup()
    desc = _create_fake_ptz_desc()
    velocity = client.get_ptz_velocity_async(desc).result()
    assert velocity.ptz.name == desc.name
    assert velocity.pan.value == approx(1.0)
    assert velocity.tilt.value == approx(2.0)
    assert velocity.zoom.value == approx(3.0)


def test_set_ptz_position():
    client, service, server = _setup()
    desc = _create_fake_ptz_desc()
    position = client.set_ptz_position(desc, 1.0, 2.0, 3.0)
    assert position.ptz.name == desc.name
    assert position.pan.value == approx(1.0)
    assert position.tilt.value == approx(2.0)
    assert position.zoom.value == approx(3.0)


def test_set_ptz_position_async():
    client, service, server = _setup()
    desc = _create_fake_ptz_desc()
    position = client.set_ptz_position_async(desc, 1.0, 2.0, 3.0).result()
    assert position.ptz.name == desc.name
    assert position.pan.value == approx(1.0)
    assert position.tilt.value == approx(2.0)
    assert position.zoom.value == approx(3.0)


def test_set_ptz_velocity():
    client, service, server = _setup()
    desc = _create_fake_ptz_desc()
    velocity = client.set_ptz_velocity(desc, 1.0, 2.0, 3.0)
    assert velocity.ptz.name == desc.name
    assert velocity.pan.value == approx(1.0)
    assert velocity.tilt.value == approx(2.0)
    assert velocity.zoom.value == approx(3.0)


def test_set_ptz_velocity_async():
    client, service, server = _setup()
    desc = _create_fake_ptz_desc()
    velocity = client.set_ptz_velocity_async(desc, 1.0, 2.0, 3.0).result()
    assert velocity.ptz.name == desc.name
    assert velocity.pan.value == approx(1.0)
    assert velocity.tilt.value == approx(2.0)
    assert velocity.zoom.value == approx(3.0)
