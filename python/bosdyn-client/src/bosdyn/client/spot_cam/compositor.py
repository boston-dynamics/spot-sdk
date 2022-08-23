# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Spot CAM Compositor service."""

from google.protobuf.wrappers_pb2 import BoolValue

from bosdyn.api.spot_cam import compositor_pb2, service_pb2_grpc
from bosdyn.client.common import BaseClient, handle_common_header_errors


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
                         self._compositor_error_from_response, copy_request=False, **kwargs)

    def set_screen_async(self, name, **kwargs):
        """Async version of set_screen()"""
        request = compositor_pb2.SetScreenRequest(name=name)
        return self.call_async(self._stub.SetScreen, request, self._name_from_response,
                               self._compositor_error_from_response, copy_request=False, **kwargs)

    def get_screen(self, **kwargs):
        """Get the currently selected screen"""
        request = compositor_pb2.GetScreenRequest()
        return self.call(self._stub.GetScreen, request, self._name_from_response,
                         self._compositor_error_from_response, copy_request=False, **kwargs)

    def get_screen_async(self, **kwargs):
        """Async version of get_screen()"""
        request = compositor_pb2.GetScreenRequest()
        return self.call_async(self._stub.GetScreen, request, self._name_from_response,
                               self._compositor_error_from_response, copy_request=False, **kwargs)

    def list_screens(self, **kwargs):
        """List available screens"""
        request = compositor_pb2.ListScreensRequest()
        return self.call(self._stub.ListScreens, request, self._screens_from_response,
                         self._compositor_error_from_response, copy_request=False, **kwargs)

    def list_screens_async(self, **kwargs):
        """Async version of list_screens()"""
        request = compositor_pb2.ListScreensRequest()
        return self.call_async(self._stub.ListScreens, request, self._screens_from_response,
                               self._compositor_error_from_response, copy_request=False, **kwargs)

    def get_visible_cameras(self, **kwargs):
        """List cameras on Spot CAM"""
        request = compositor_pb2.GetVisibleCamerasRequest()
        return self.call(self._stub.GetVisibleCameras, request, self._streams_from_response,
                         self._compositor_error_from_response, copy_request=False, **kwargs)

    def get_visible_cameras_async(self, **kwargs):
        """Async version of get_visible_cameras()"""
        request = compositor_pb2.GetVisibleCamerasRequest()
        return self.call_async(self._stub.GetVisibleCameras, request, self._streams_from_response,
                               self._compositor_error_from_response, copy_request=False, **kwargs)

    def set_ir_colormap(self, colormap, min_temp, max_temp, auto_scale, **kwargs):
        """Set IR colormap to use on Spot CAM

        Args:
            colormap (bosdyn.api.spot_cam.compositor_pb2.IrColorMap.ColorMap): IR display colormap
            min_temp (Float): minimum temperature on the temperature scale
            max_temp (Float): maximum temperature on the temperature scale
            auto_scale (Boolean): Auto-scale the color map. This is the most human-understandable
                option. min_temp and max_temp are ignored if this is set to True
            kwargs: extra arguments for controlling RPC details.
        """
        scale = compositor_pb2.IrColorMap.ScalingPair(min=min_temp, max=max_temp)
        auto = BoolValue(value=auto_scale)
        ir_colormap = compositor_pb2.IrColorMap(colormap=colormap, scale=scale, auto_scale=auto)
        request = compositor_pb2.SetIrColormapRequest(map=ir_colormap)
        return self.call(self._stub.SetIrColormap, request, self._return_response,
                         self._compositor_error_from_response, copy_request=False, **kwargs)

    def set_ir_colormap_async(self, colormap, min_temp, max_temp, auto_scale, **kwargs):
        """Async version of set_ir_colormap()"""
        scale = compositor_pb2.IrColorMap.ScalingPair(min=min_temp, max=max_temp)
        auto = BoolValue(value=auto_scale)
        ir_colormap = compositor_pb2.IrColorMap(colormap=colormap, scale=scale, auto_scale=auto)
        request = compositor_pb2.SetIrColormapRequest(map=ir_colormap)
        return self.call_async(self._stub.SetIrColormap, request, self._return_response,
                               self._compositor_error_from_response, copy_request=False, **kwargs)

    def get_ir_colormap(self, **kwargs):
        """Get currently selected IR colormap on Spot CAM"""
        request = compositor_pb2.GetIrColormapRequest()
        return self.call(self._stub.GetIrColormap, request, self._colormap_from_response,
                         self._compositor_error_from_response, copy_request=False, **kwargs)

    def get_ir_colormap_async(self, **kwargs):
        """Async version of get_ir_colormap()"""
        request = compositor_pb2.GetIrColormapRequest()
        return self.call_async(self._stub.GetIrColormap, request, self._colormap_from_response,
                               self._compositor_error_from_response, copy_request=False, **kwargs)

    def set_ir_meter_overlay(self, x, y, enable, **kwargs):
        """Set IR reticle position to use on Spot CAM IR

        Args:
            x (Float): (0,1) horizontal coordinate of reticle
            y (Float): (0,1) vertical coordinate of reticle
            enable (Boolean): Enable the reticle on the display
            kwargs: extra arguments for controlling RPC details.
        """
        coords = compositor_pb2.IrMeterOverlay.NormalizedCoordinates(x=x, y=y)
        overlay = compositor_pb2.IrMeterOverlay(enable=enable, coords=coords)
        request = compositor_pb2.SetIrMeterOverlayRequest(overlay=overlay)
        return self.call(self._stub.SetIrMeterOverlay, request, self._return_response,
                         self._compositor_error_from_response, copy_request=False, **kwargs)

    def set_ir_meter_overlay_async(self, x, y, enable, **kwargs):
        """Async version of set_ir_meter_overlay()"""
        coords = compositor_pb2.IrMeterOverlay.NormalizedCoordinates(x=x, y=y)
        overlay = compositor_pb2.IrMeterOverlay(enable=enable, coords=coords)
        request = compositor_pb2.SetIrMeterOverlayRequest(overlay=overlay)
        return self.call_async(self._stub.SetIrMeterOverlay, request, self._return_response,
                               self._compositor_error_from_response, copy_request=False, **kwargs)

    @staticmethod
    def _return_response(response):
        return response

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
    def _colormap_from_response(response):
        return response.map

    @staticmethod
    @handle_common_header_errors
    def _compositor_error_from_response(response):  # pylint: disable=unused-argument
        return None
