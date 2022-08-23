# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the Spot CAM's LightingClient."""
import time

import grpc
import pytest

import bosdyn.client.spot_cam.lighting
from bosdyn.api.spot_cam import LED_pb2, service_pb2_grpc

from . import helpers


class MockLightingService(service_pb2_grpc.LightingServiceServicer):

    def __init__(self, rpc_delay=0):
        """Create mock that returns fake LED brightnesses."""
        super(MockLightingService, self).__init__()
        self._rpc_delay = rpc_delay

    def GetLEDBrightness(self, request, context):
        time.sleep(self._rpc_delay)

        response = LED_pb2.GetLEDBrightnessResponse()
        response.brightnesses.extend([
            0.004999999888241291, 0.004999999888241291, 0.004999999888241291, 0.004999999888241291
        ])
        helpers.add_common_header(response, request)
        return response

    def SetLEDBrightness(self, request, context):
        time.sleep(self._rpc_delay)

        response = LED_pb2.SetLEDBrightnessResponse()
        helpers.add_common_header(response, request)
        return response


def _setup(rpc_delay=0):
    client = bosdyn.client.spot_cam.lighting.LightingClient()
    service = MockLightingService(rpc_delay=rpc_delay)
    server = helpers.setup_client_and_service(
        client, service, service_pb2_grpc.add_LightingServiceServicer_to_server)
    return client, service, server


def test_get_led_brightness():
    client, service, server = _setup()
    brightnesses = client.get_led_brightness()
    assert len(brightnesses) == 4
    for brightness in brightnesses:
        assert brightness < 0.01


def test_get_led_brightness_async():
    client, service, server = _setup()
    brightnesses = client.get_led_brightness_async().result()
    assert len(brightnesses) == 4
    for brightness in brightnesses:
        assert brightness < 0.01


def test_set_led_brightness():
    client, service, server = _setup()
    client.set_led_brightness([1.0])


def test_set_led_brightness_async():
    client, service, server = _setup()
    client.set_led_brightness_async([1.0, 2.0, 3.0, 4.0, 5.0]).result()
