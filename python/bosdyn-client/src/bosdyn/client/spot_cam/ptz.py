# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Spot CAM Ptz service."""

import logging

_LOGGER = logging.getLogger(__name__)

from bosdyn.client.math_helpers import recenter_angle
from bosdyn.client.common import (BaseClient, common_header_errors, handle_common_header_errors)
from bosdyn.api.spot_cam import service_pb2_grpc
from bosdyn.api.spot_cam import ptz_pb2

from google.protobuf.wrappers_pb2 import FloatValue


class PtzClient(BaseClient):
    """A client calling Spot CAM Ptz service.
    """
    default_service_name = 'spot-cam-ptz'
    service_type = 'bosdyn.api.spot_cam.PtzService'

    def __init__(self):
        super(PtzClient, self).__init__(service_pb2_grpc.PtzServiceStub)

    def list_ptz(self, **kwargs):
        """List all the available ptzs"""
        request = ptz_pb2.ListPtzRequest()
        return self.call(self._stub.ListPtz, request, self._list_ptz_from_response,
                         self._ptz_error_from_response, **kwargs)

    def list_ptz_async(self, **kwargs):
        """Async version of list_ptz()"""
        request = ptz_pb2.ListPtzRequest()
        return self.call_async(self._stub.ListPtz, request, self._list_ptz_from_response,
                               self._ptz_error_from_response, **kwargs)

    def get_ptz_position(self, ptz_desc, **kwargs):
        """Position of the specified ptz"""
        request = ptz_pb2.GetPtzPositionRequest(ptz=ptz_desc)
        return self.call(self._stub.GetPtzPosition, request, self._get_ptz_position_from_response,
                         self._ptz_error_from_response, **kwargs)

    def get_ptz_position_async(self, ptz_desc, **kwargs):
        """Async version of get_ptz_position()"""
        request = ptz_pb2.GetPtzPositionRequest(ptz=ptz_desc)
        return self.call_async(self._stub.GetPtzPosition, request,
                               self._get_ptz_position_from_response, self._ptz_error_from_response,
                               **kwargs)

    def get_ptz_velocity(self, ptz_desc, **kwargs):
        """Velocity of the specified ptz"""
        request = ptz_pb2.GetPtzVelocityRequest(ptz=ptz_desc)
        return self.call(self._stub.GetPtzVelocity, request, self._get_ptz_velocity_from_response,
                         self._ptz_error_from_response, **kwargs)

    def get_ptz_velocity_async(self, ptz_desc, **kwargs):
        """Async version of get_ptz_velocity()"""
        request = ptz_pb2.GetPtzVelocityRequest(ptz=ptz_desc)
        return self.call_async(self._stub.GetPtzVelocity, request,
                               self._get_ptz_velocity_from_response, self._ptz_error_from_response,
                               **kwargs)

    def set_ptz_position(self, ptz_desc, pan, tilt, zoom, **kwargs):
        """Set position of the specified ptz in PTZ-space"""
        p = FloatValue(value=pan)
        t = FloatValue(value=tilt)
        z = FloatValue(value=zoom)
        ptz_position = ptz_pb2.PtzPosition(ptz=ptz_desc, pan=p, tilt=t, zoom=z)
        request = ptz_pb2.SetPtzPositionRequest(position=ptz_position)
        return self.call(self._stub.SetPtzPosition, request, self._set_ptz_position_from_response,
                         self._ptz_error_from_response, **kwargs)

    def set_ptz_position_async(self, ptz_desc, pan, tilt, zoom, **kwargs):
        """Async version of set_ptz_position()"""
        p = FloatValue(value=pan)
        t = FloatValue(value=tilt)
        z = FloatValue(value=zoom)
        ptz_position = ptz_pb2.PtzPosition(ptz=ptz_desc, pan=p, tilt=t, zoom=z)
        request = ptz_pb2.SetPtzPositionRequest(position=ptz_position)
        return self.call_async(self._stub.SetPtzPosition, request,
                               self._set_ptz_position_from_response, self._ptz_error_from_response,
                               **kwargs)

    def set_ptz_velocity(self, ptz_desc, pan, tilt, zoom, **kwargs):
        """Set velocity of the specified ptz in PTZ-space"""
        p = FloatValue(value=pan)
        t = FloatValue(value=tilt)
        z = FloatValue(value=zoom)
        ptz_velocity = ptz_pb2.PtzVelocity(ptz=ptz_desc, pan=p, tilt=t, zoom=z)
        request = ptz_pb2.SetPtzVelocityRequest(velocity=ptz_velocity)
        return self.call(self._stub.SetPtzVelocity, request, self._set_ptz_velocity_from_response,
                         self._ptz_error_from_response, **kwargs)

    def set_ptz_velocity_async(self, ptz_desc, pan, tilt, zoom, **kwargs):
        """Async version of set_ptz_velocity()"""
        p = FloatValue(value=pan)
        t = FloatValue(value=tilt)
        z = FloatValue(value=zoom)
        ptz_velocity = ptz_pb2.PtzVelocity(ptz=ptz_desc, pan=p, tilt=t, zoom=z)
        request = ptz_pb2.SetPtzVelocityRequest(velocity=ptz_velocity)
        return self.call_async(self._stub.SetPtzVelocity, request,
                               self._set_ptz_velocity_from_response, self._ptz_error_from_response,
                               **kwargs)

    @staticmethod
    def _list_ptz_from_response(response):
        return response.ptzs

    @staticmethod
    def _get_ptz_position_from_response(response):
        return response.position

    @staticmethod
    def _get_ptz_velocity_from_response(response):
        return response.velocity

    @staticmethod
    def _set_ptz_position_from_response(response):
        return response.position

    @staticmethod
    def _set_ptz_velocity_from_response(response):
        return response.velocity

    @staticmethod
    @handle_common_header_errors
    def _ptz_error_from_response(response):  # pylint: disable=unused-argument
        return None


def shift_pan_angle(pan):
    """Shift the pan angle (degrees) so that it is in the [0,360] range."""
    return recenter_angle(pan, 0, 360)