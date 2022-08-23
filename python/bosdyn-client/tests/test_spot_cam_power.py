# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the Spot CAM's PowerClient."""
import time

import grpc
import pytest

import bosdyn.client.spot_cam.power
from bosdyn.api.spot_cam import power_pb2, service_pb2_grpc

from . import helpers


class MockPowerService(service_pb2_grpc.PowerServiceServicer):

    def __init__(self, rpc_delay=0):
        """Create mock that returns fake power statuses."""
        super(MockPowerService, self).__init__()
        self._rpc_delay = rpc_delay

    def GetPowerStatus(self, request, context):
        time.sleep(self._rpc_delay)

        response = power_pb2.GetPowerStatusResponse()
        response.status.ptz.value = True
        response.status.aux1.value = True
        response.status.aux2.value = False
        helpers.add_common_header(response, request)
        return response

    def SetPowerStatus(self, request, context):
        time.sleep(self._rpc_delay)

        response = power_pb2.SetPowerStatusResponse()
        response.status.CopyFrom(request.status)
        helpers.add_common_header(response, request)
        return response


def _setup(rpc_delay=0):
    client = bosdyn.client.spot_cam.power.PowerClient()
    service = MockPowerService(rpc_delay=rpc_delay)
    server = helpers.setup_client_and_service(client, service,
                                              service_pb2_grpc.add_PowerServiceServicer_to_server)
    return client, service, server


def test_get_power_status():
    client, service, server = _setup()
    ps = client.get_power_status()
    assert ps.ptz.value
    assert ps.aux1.value
    assert not ps.aux2.value


def test_get_power_status_async():
    client, service, server = _setup()
    ps = client.get_power_status_async().result()
    assert ps.ptz.value
    assert ps.aux1.value
    assert not ps.aux2.value


def test_set_power_status():
    client, service, server = _setup()
    ps = client.set_power_status(ptz=True, aux1=False)
    assert ps.ptz.value
    assert not ps.aux1.value
    assert not ps.aux2.value


def test_set_power_status_async():
    client, service, server = _setup()
    ps = client.set_power_status_async(ptz=True, aux1=False).result()
    assert ps.ptz.value
    assert not ps.aux1.value
    assert not ps.aux2.value
