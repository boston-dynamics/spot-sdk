# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Spot CAM Lighting service."""

import logging

_LOGGER = logging.getLogger(__name__)

from bosdyn.client.common import (BaseClient, common_header_errors, handle_common_header_errors)
from bosdyn.api.spot_cam import service_pb2_grpc
from bosdyn.api.spot_cam import LED_pb2


class LightingClient(BaseClient):
    """A client calling Spot CAM Lighting service.
    """
    default_service_name = 'spot-cam-lighting'
    service_type = 'bosdyn.api.spot_cam.LightingService'

    def __init__(self):
        super(LightingClient, self).__init__(service_pb2_grpc.LightingServiceStub)

    def get_led_brightness(self, **kwargs):
        """Retrieve the brightness value [0, 1] of each LED at indices [0, max)."""
        request = LED_pb2.GetLEDBrightnessRequest()
        return self.call(self._stub.GetLEDBrightness, request,
                         self._get_led_brightness_from_response, self._lighting_error_from_response,
                         **kwargs)

    def get_led_brightness_async(self, **kwargs):
        """Async version of get_led_brightness()"""
        request = LED_pb2.GetLEDBrightnessRequest()
        return self.call_async(self._stub.GetLEDBrightness, request,
                               self._get_led_brightness_from_response,
                               self._lighting_error_from_response, **kwargs)

    def set_led_brightness(self, brightnesses, **kwargs):
        """Set the brightness value [0, 1] of each LED at indices [0, max)."""
        request = LED_pb2.SetLEDBrightnessRequest()
        for i, brightness in enumerate(brightnesses):
            if i >= 4:
                break

            request.brightnesses[i] = brightness

        return self.call(self._stub.SetLEDBrightness, request,
                         self._set_led_brightness_from_response, self._lighting_error_from_response,
                         **kwargs)

    def set_led_brightness_async(self, brightnesses, **kwargs):
        """Async version of set_led_brightness()"""
        request = LED_pb2.SetLEDBrightnessRequest()
        for i, brightness in enumerate(brightnesses):
            if i >= 4:
                break

            request.brightnesses[i] = brightness
        return self.call_async(self._stub.SetLEDBrightness, request,
                               self._set_led_brightness_from_response,
                               self._lighting_error_from_response, **kwargs)

    @staticmethod
    def _get_led_brightness_from_response(response):
        return response.brightnesses

    @staticmethod
    def _set_led_brightness_from_response(response):
        pass

    @staticmethod
    @handle_common_header_errors
    def _lighting_error_from_response(response):  # pylint: disable=unused-argument
        return None
