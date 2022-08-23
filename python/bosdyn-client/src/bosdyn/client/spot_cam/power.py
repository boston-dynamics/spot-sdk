# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Spot CAM Power service."""

import logging

_LOGGER = logging.getLogger(__name__)

from google.protobuf.wrappers_pb2 import BoolValue

from bosdyn.api.spot_cam import power_pb2, service_pb2_grpc
from bosdyn.client.common import BaseClient, common_header_errors, handle_common_header_errors


class PowerClient(BaseClient):
    """A client calling Spot CAM Power service.
    """
    default_service_name = 'spot-cam-power'
    service_type = 'bosdyn.api.spot_cam.PowerService'

    def __init__(self):
        super(PowerClient, self).__init__(service_pb2_grpc.PowerServiceStub)

    def get_power_status(self, **kwargs):
        """Retrieve on/off state of device."""
        request = power_pb2.GetPowerStatusRequest()
        return self.call(self._stub.GetPowerStatus, request, self._get_power_status_from_response,
                         self._power_error_from_response, copy_request=False, **kwargs)

    def get_power_status_async(self, **kwargs):
        """Async version of get_power_status()"""
        request = power_pb2.GetPowerStatusRequest()
        return self.call_async(self._stub.GetPowerStatus, request,
                               self._get_power_status_from_response,
                               self._power_error_from_response, copy_request=False, **kwargs)

    def set_power_status(self, ptz=None, aux1=None, aux2=None, external_mic=None, **kwargs):
        """Turn on/off the desire device.
        Should not be used on PTZ for non-IR units as it can cause the stream to crash.
        If the intent is to reset the PTZ autofocus, try PtzClient.initialize_lens instead.
        If the intent is to recover the PTZ stream in another way, you may need to power cycle the robot.
        """
        request = self._build_SetPowerStatusRequest(ptz, aux1, aux2, external_mic)

        return self.call(self._stub.SetPowerStatus, request, self._set_power_status_from_response,
                         self._power_error_from_response, copy_request=False, **kwargs)

    def set_power_status_async(self, ptz=None, aux1=None, aux2=None, external_mic=None, **kwargs):
        """Async version of set_power_status()"""
        request = self._build_SetPowerStatusRequest(ptz, aux1, aux2, external_mic)

        return self.call_async(self._stub.SetPowerStatus, request,
                               self._set_power_status_from_response,
                               self._power_error_from_response, copy_request=False, **kwargs)

    def cycle_power(self, ptz=None, aux1=None, aux2=None, external_mic=None, **kwargs):
        """Turn power off then back on for the desired devices.
        Should not be used on PTZ for non-IR units as it can cause the stream to crash.
        If the intent is to reset the PTZ autofocus, try PtzClient.initialize_lens instead.
        If the intent is to recover the PTZ stream in another way, you may need to power cycle the robot.
        """
        request = self._build_CyclePowerRequest(ptz, aux1, aux2, external_mic)

        return self.call(self._stub.CyclePower, request, self._cycle_power_from_response,
                         self._power_error_from_response, copy_request=False, **kwargs)

    def cycle_power_async(self, ptz=None, aux1=None, aux2=None, external_mic=None, **kwargs):
        """Async version of cycle_power()"""
        request = self._build_CyclePowerRequest(ptz, aux1, aux2, external_mic)

        return self.call_async(self._stub.CyclePower, request, self._cycle_power_from_response,
                               self._power_error_from_response, copy_request=False, **kwargs)

    @staticmethod
    def _build_SetPowerStatusRequest(ptz, aux1, aux2, external_mic):
        request = power_pb2.SetPowerStatusRequest()

        if ptz:
            request.status.ptz.value = ptz

        if aux1:
            request.status.aux1.value = aux1

        if aux2:
            request.status.aux2.value = aux2

        if external_mic:
            request.status.external_mic.value = external_mic

        return request

    @staticmethod
    def _build_CyclePowerRequest(ptz, aux1, aux2, external_mic):
        request = power_pb2.CyclePowerRequest()

        if ptz:
            request.status.ptz.value = ptz

        if aux1:
            request.status.aux1.value = aux1

        if aux2:
            request.status.aux2.value = aux2

        if external_mic:
            request.status.external_mic.value = external_mic

        return request

    @staticmethod
    def _get_power_status_from_response(response):
        return response.status

    @staticmethod
    def _set_power_status_from_response(response):
        return response.status

    @staticmethod
    def _cycle_power_from_response(response):
        return response.status

    @staticmethod
    @handle_common_header_errors
    def _power_error_from_response(response):  # pylint: disable=unused-argument
        return None
