# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Spot CAM Compositor service."""

from bosdyn.client.common import (BaseClient, handle_common_header_errors)
from bosdyn.api.spot_cam import service_pb2_grpc
from bosdyn.api.spot_cam import compositor_pb2


class CompositorClient(BaseClient):
    """A client calling Spot CAM Compositor services.
    """
    default_service_name = 'spot-cam-compositor'
    service_type = 'bosdyn.api.spot_cam.CompositorService'

    def __init__(self):
        super(CompositorClient, self).__init__(service_pb2_grpc.CompositorServiceStub)

    def set_screen(self, name, **kwargs):
        """Change the current view that is being streamed over the network"""
        request = compositor_pb2.SetScreenRequest(name=name)
        return self.call(self._stub.SetScreen, request, self._name_from_response,
                         self._compositor_error_from_response, **kwargs)

    def set_screen_async(self, name, **kwargs):
        """Async version of set_screen()"""
        request = compositor_pb2.SetScreenRequest(name=name)
        return self.call_async(self._stub.SetScreen, request, self._name_from_response,
                               self._compositor_error_from_response, **kwargs)

    def get_screen(self, **kwargs):
        """Get the currently selected screen"""
        request = compositor_pb2.GetScreenRequest()
        return self.call(self._stub.GetScreen, request, self._name_from_response,
                         self._compositor_error_from_response, **kwargs)

    def get_screen_async(self, **kwargs):
        """Async version of get_screen()"""
        request = compositor_pb2.GetScreenRequest()
        return self.call_async(self._stub.GetScreen, request, self._name_from_response,
                               self._compositor_error_from_response, **kwargs)

    def list_screens(self, **kwargs):
        """List available screens"""
        request = compositor_pb2.ListScreensRequest()
        return self.call(self._stub.ListScreens, request, self._screens_from_response,
                         self._compositor_error_from_response, **kwargs)

    def list_screens_async(self, **kwargs):
        """Async version of list_screens()"""
        request = compositor_pb2.ListScreensRequest()
        return self.call_async(self._stub.ListScreens, request, self._screens_from_response,
                               self._compositor_error_from_response, **kwargs)

    def get_visible_cameras(self, **kwargs):
        """List cameras on Spot CAM"""
        request = compositor_pb2.GetVisibleCamerasRequest()
        return self.call(self._stub.GetVisibleCameras, request, self._streams_from_response,
                         self._compositor_error_from_response, **kwargs)

    def get_visible_cameras_async(self, **kwargs):
        """Async version of get_visible_cameras()"""
        request = compositor_pb2.GetVisibleCamerasRequest()
        return self.call_async(self._stub.GetVisibleCameras, request, self._streams_from_response,
                               self._compositor_error_from_response, **kwargs)

    @staticmethod
    def _name_from_response(response):
        return response.name

    @staticmethod
    def _screens_from_response(response):
        return response.screens

    @staticmethod
    def _streams_from_response(response):
        return response.streams

    @staticmethod
    @handle_common_header_errors
    def _compositor_error_from_response(response):  # pylint: disable=unused-argument
        return None
