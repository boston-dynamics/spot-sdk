# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the Spot CAM's CompositorClient."""
import time

import grpc
import pytest

import bosdyn.client.spot_cam.compositor
from bosdyn.api.spot_cam import camera_pb2, compositor_pb2, service_pb2_grpc

from . import helpers


class MockCompositorService(service_pb2_grpc.CompositorServiceServicer):

    def __init__(self, rpc_delay=0):
        """Create mock that returns fake compositor queries."""
        super(MockCompositorService, self).__init__()
        self._rpc_delay = rpc_delay

    def SetScreen(self, request, context):
        time.sleep(self._rpc_delay)

        response = compositor_pb2.SetScreenResponse()
        response.name = request.name
        helpers.add_common_header(response, request)
        return response

    def GetScreen(self, request, context):
        time.sleep(self._rpc_delay)

        response = compositor_pb2.GetScreenResponse()
        response.name = 'good'
        helpers.add_common_header(response, request)
        return response

    def ListScreens(self, request, context):
        time.sleep(self._rpc_delay)

        response = compositor_pb2.ListScreensResponse()
        response.screens.extend([compositor_pb2.ScreenDescription(name='good')])
        helpers.add_common_header(response, request)
        return response

    def GetVisibleCameras(self, request, context):
        time.sleep(self._rpc_delay)

        response = compositor_pb2.GetVisibleCamerasResponse()
        response.streams.extend([_mock_stream()])
        helpers.add_common_header(response, request)
        return response


def _setup(rpc_delay=0):
    client = bosdyn.client.spot_cam.compositor.CompositorClient()
    service = MockCompositorService(rpc_delay=rpc_delay)
    server = helpers.setup_client_and_service(
        client, service, service_pb2_grpc.add_CompositorServiceServicer_to_server)
    return client, service, server


def _mock_stream(name='good', x_offset=0, y_offset=0, width=2, height=1):
    stream = compositor_pb2.GetVisibleCamerasResponse.Stream()
    stream.window.CopyFrom(
        compositor_pb2.GetVisibleCamerasResponse.Stream.Window(xoffset=x_offset, yoffset=y_offset,
                                                               width=width, height=height))
    stream.camera.CopyFrom(camera_pb2.Camera(name=name))
    return stream


def test_set_screen():
    client, service, server = _setup()
    result = client.set_screen('good')
    assert result == 'good'


def test_set_screen_async():
    client, service, server = _setup()
    result = client.set_screen_async('good').result()
    assert result == 'good'


def test_get_screen():
    client, service, server = _setup()
    result = client.get_screen()
    assert result == 'good'


def test_get_screen_async():
    client, service, server = _setup()
    result = client.get_screen_async().result()
    assert result == 'good'


def test_list_screens():
    client, service, server = _setup()
    result = client.list_screens()
    assert len(result) == 1
    assert result[0].name == 'good'


def test_list_screens_async():
    client, service, server = _setup()
    result = client.list_screens_async().result()
    assert len(result) == 1
    assert result[0].name == 'good'


def test_get_visible_cameras():
    client, service, server = _setup()
    result = client.get_visible_cameras()
    assert len(result) == 1
    mock = _mock_stream()
    assert result[0].camera.name == mock.camera.name
    assert result[0].window.xoffset == mock.window.xoffset
    assert result[0].window.yoffset == mock.window.yoffset
    assert result[0].window.width == mock.window.width
    assert result[0].window.height == mock.window.height
