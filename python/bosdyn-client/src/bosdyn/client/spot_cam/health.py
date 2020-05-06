# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Spot CAM Health service."""

import logging

_LOGGER = logging.getLogger(__name__)

from bosdyn.client.common import (BaseClient, common_header_errors, handle_common_header_errors)
from bosdyn.api.spot_cam import service_pb2_grpc
from bosdyn.api.spot_cam import health_pb2

class HealthClient(BaseClient):
    """A client calling Spot CAM Health service.
    """
    default_service_name = 'spot-cam-health'
    service_type = 'bosdyn.api.spot_cam.HealthService'

    def __init__(self):
        super(HealthClient, self).__init__(service_pb2_grpc.HealthServiceStub)

    def clear_bit_events(self, **kwargs):
        """Clear out the events list of the BITStatus structure."""
        request = health_pb2.ClearBITEventsRequest()
        return self.call(self._stub.ClearBITEvents, request, self._clear_bit_events_from_response,
                         self._health_error_from_response, **kwargs)

    def clear_bit_events_async(self, **kwargs):
        """Async version of clear_bit_events()."""
        request = health_pb2.ClearBITEventsRequest()
        return self.call_async(self._stub.ClearBITEvents, request, self._clear_bit_events_from_response,
                               self._health_error_from_response, **kwargs)

    def get_bit_status(self, **kwargs):
        """Retrieve (system events, degradations) as a tuple of two lists."""
        request = health_pb2.GetBITStatusRequest()
        return self.call(self._stub.GetBITStatus, request, self._get_bit_status_from_response,
                         self._health_error_from_response, **kwargs)

    def get_bit_status_async(self, **kwargs):
        """Async version of get_bit_status()."""
        request = health_pb2.GetBITStatusRequest()
        return self.call_async(self._stub.GetBITStatus, request, self._get_bit_status_from_response,
                               self._health_error_from_response, **kwargs)

    def get_temperature(self, **kwargs):
        """Retrieve a list of thermometers measuring the temperature (mC) of corresponding on-board devices."""
        request = health_pb2.GetTemperatureRequest()
        return self.call(self._stub.GetTemperature, request, self._get_temperature_from_response,
                         self._health_error_from_response, **kwargs)

    def get_temperature_async(self, **kwargs):
        """Async version of get_temperature()."""
        request = health_pb2.GetTemperatureRequest()
        return self.call_async(self._stub.GetTemperature, request, self._get_temperature_from_response,
                               self._health_error_from_response, **kwargs)

    @staticmethod
    def _clear_bit_events_from_response(response):
        pass

    @staticmethod
    def _get_bit_status_from_response(response):
        return response.events, response.degradations

    @staticmethod
    def _get_temperature_from_response(response):
        return response.temps

    @staticmethod
    @handle_common_header_errors
    def _health_error_from_response(response):  # pylint: disable=unused-argument
        return None
