# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the Spot CAM's HealthClient."""
import time

import grpc
import pytest

import bosdyn.client.spot_cam.health
from bosdyn.api.spot_cam import health_pb2, service_pb2_grpc

from . import helpers


class MockHealthService(service_pb2_grpc.HealthServiceServicer):

    def __init__(self, rpc_delay=0):
        """Create mock that returns fake health status."""
        super(MockHealthService, self).__init__()
        self._rpc_delay = rpc_delay

    def ClearBITEvents(self, request, context):
        time.sleep(self._rpc_delay)

        response = health_pb2.ClearBITEventsResponse()
        helpers.add_common_header(response, request)
        return response

    def GetBITStatus(self, request, context):
        time.sleep(self._rpc_delay)

        response = health_pb2.GetBITStatusResponse()
        response.degradations.extend([
            health_pb2.GetBITStatusResponse.Degradation(
                type=health_pb2.GetBITStatusResponse.Degradation.STORAGE, description='cool')
        ])
        helpers.add_common_header(response, request)
        return response

    def GetTemperature(self, request, context):
        time.sleep(self._rpc_delay)

        response = health_pb2.GetTemperatureResponse()
        response.temps.extend([health_pb2.Temperature(channel_name='hi', temperature=100)])
        helpers.add_common_header(response, request)
        return response


def _setup(rpc_delay=0):
    client = bosdyn.client.spot_cam.health.HealthClient()
    service = MockHealthService(rpc_delay=rpc_delay)
    server = helpers.setup_client_and_service(client, service,
                                              service_pb2_grpc.add_HealthServiceServicer_to_server)
    return client, service, server


def test_clear_bit_events():
    client, service, server = _setup()
    client.clear_bit_events()


def test_clear_bit_events_async():
    client, service, server = _setup()
    client.clear_bit_events_async().result()


def test_get_bit_status():
    client, service, server = _setup()
    events, degradations = client.get_bit_status()
    assert len(events) == 0
    assert len(degradations) == 1


def test_get_bit_status_async():
    client, service, server = _setup()
    events, degradations = client.get_bit_status_async().result()
    assert len(events) == 0
    assert len(degradations) == 1


def test_get_temperature():
    client, service, server = _setup()
    temp = client.get_temperature()
    assert len(temp) == 1


def test_get_temperature_async():
    client, service, server = _setup()
    temp = client.get_temperature()
    assert len(temp) == 1
