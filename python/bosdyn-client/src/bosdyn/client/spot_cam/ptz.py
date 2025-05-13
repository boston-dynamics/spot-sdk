# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Spot CAM Ptz service."""

import logging

_LOGGER = logging.getLogger(__name__)

from google.protobuf.wrappers_pb2 import FloatValue, Int32Value

from bosdyn.api.spot_cam import ptz_pb2, service_pb2_grpc
from bosdyn.client.common import BaseClient, common_header_errors, handle_common_header_errors
from bosdyn.client.math_helpers import recenter_value_mod


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
                         common_header_errors, copy_request=False, **kwargs)

    def list_ptz_async(self, **kwargs):
        """Async version of list_ptz()"""
        request = ptz_pb2.ListPtzRequest()
        return self.call_async(self._stub.ListPtz, request, self._list_ptz_from_response,
                               common_header_errors, copy_request=False, **kwargs)

    def get_ptz_position(self, ptz_desc, **kwargs):
        """Position of the specified ptz"""
        request = ptz_pb2.GetPtzPositionRequest(ptz=ptz_desc)
        return self.call(self._stub.GetPtzPosition, request, self._get_ptz_position_from_response,
                         common_header_errors, copy_request=False, **kwargs)

    def get_ptz_position_async(self, ptz_desc, **kwargs):
        """Async version of get_ptz_position()"""
        request = ptz_pb2.GetPtzPositionRequest(ptz=ptz_desc)
        return self.call_async(self._stub.GetPtzPosition, request,
                               self._get_ptz_position_from_response, common_header_errors,
                               copy_request=False, **kwargs)

    def get_ptz_velocity(self, ptz_desc, **kwargs):
        """Velocity of the specified ptz"""
        request = ptz_pb2.GetPtzVelocityRequest(ptz=ptz_desc)
        return self.call(self._stub.GetPtzVelocity, request, self._get_ptz_velocity_from_response,
                         common_header_errors, copy_request=False, **kwargs)

    def get_ptz_velocity_async(self, ptz_desc, **kwargs):
        """Async version of get_ptz_velocity()"""
        request = ptz_pb2.GetPtzVelocityRequest(ptz=ptz_desc)
        return self.call_async(self._stub.GetPtzVelocity, request,
                               self._get_ptz_velocity_from_response, common_header_errors,
                               copy_request=False, **kwargs)

    def set_ptz_position(self, ptz_desc, pan, tilt, zoom, **kwargs):
        """Set position of the specified ptz in PTZ-space"""
        p = FloatValue(value=pan)
        t = FloatValue(value=tilt)
        z = FloatValue(value=zoom)
        ptz_position = ptz_pb2.PtzPosition(ptz=ptz_desc, pan=p, tilt=t, zoom=z)
        request = ptz_pb2.SetPtzPositionRequest(position=ptz_position)
        return self.call(self._stub.SetPtzPosition, request, self._set_ptz_position_from_response,
                         common_header_errors, copy_request=False, **kwargs)

    def set_ptz_position_async(self, ptz_desc, pan, tilt, zoom, **kwargs):
        """Async version of set_ptz_position()"""
        p = FloatValue(value=pan)
        t = FloatValue(value=tilt)
        z = FloatValue(value=zoom)
        ptz_position = ptz_pb2.PtzPosition(ptz=ptz_desc, pan=p, tilt=t, zoom=z)
        request = ptz_pb2.SetPtzPositionRequest(position=ptz_position)
        return self.call_async(self._stub.SetPtzPosition, request,
                               self._set_ptz_position_from_response, common_header_errors,
                               copy_request=False, **kwargs)

    def set_ptz_velocity(self, ptz_desc, pan, tilt, zoom, **kwargs):
        """Set velocity of the specified ptz in PTZ-space"""
        p = FloatValue(value=pan)
        t = FloatValue(value=tilt)
        z = FloatValue(value=zoom)
        ptz_velocity = ptz_pb2.PtzVelocity(ptz=ptz_desc, pan=p, tilt=t, zoom=z)
        request = ptz_pb2.SetPtzVelocityRequest(velocity=ptz_velocity)
        return self.call(self._stub.SetPtzVelocity, request, self._set_ptz_velocity_from_response,
                         common_header_errors, copy_request=False, **kwargs)

    def set_ptz_velocity_async(self, ptz_desc, pan, tilt, zoom, **kwargs):
        """Async version of set_ptz_velocity()"""
        p = FloatValue(value=pan)
        t = FloatValue(value=tilt)
        z = FloatValue(value=zoom)
        ptz_velocity = ptz_pb2.PtzVelocity(ptz=ptz_desc, pan=p, tilt=t, zoom=z)
        request = ptz_pb2.SetPtzVelocityRequest(velocity=ptz_velocity)
        return self.call_async(self._stub.SetPtzVelocity, request,
                               self._set_ptz_velocity_from_response, common_header_errors,
                               copy_request=False, **kwargs)

    def initialize_lens(self, **kwargs):
        """Initializes the PTZ autofocus or resets it if already initialized"""
        request = ptz_pb2.InitializeLensRequest()
        return self.call(self._stub.InitializeLens, request, self._initialize_lens_from_response,
                         common_header_errors, copy_request=False, **kwargs)

    def initialize_lens_async(self, **kwargs):
        """Async version of initialize_lens()"""
        request = ptz_pb2.InitializeLensRequest()
        return self.call_async(self._stub.InitializeLens, request,
                               self._initialize_lens_from_response, common_header_errors,
                               copy_request=False, **kwargs)

    # Manual Focus RPCs

    def get_ptz_focus_state(self, **kwargs):
        """Retrieve focus of the mechanical ptz

        Args:
            focus_mode (PtzFocusMode): Enum indicating whether to autofocus or manually focus
            distance (float): Approximate distance to focus on, most accurate between 1.2m and 20m,
                only settable in PTZ_FOCUS_MANUAL mode
            focus_position (int32): Precise lens position for the camera for repeatable operations,
                overrides distance if specified, only settable in PTZ_FOCUS_MANUAL mode

        Returns:
            PtzFocusState containing the current focus mode and position
        """
        request = ptz_pb2.GetPtzFocusStateRequest()
        return self.call(self._stub.GetPtzFocusState, request,
                         self._get_ptz_focus_state_from_response, common_header_errors,
                         copy_request=False, **kwargs)

    def get_ptz_focus_state_async(self, **kwargs):
        """Async version of get_ptz_focus_state()"""
        request = ptz_pb2.GetPtzFocusStateRequest()
        return self.call_async(self._stub.GetPtzFocusState, request,
                               self._get_ptz_focus_state_from_response, common_header_errors,
                               copy_request=False, **kwargs)

    def set_ptz_focus_state(self, focus_mode, distance=None, focus_position=None, **kwargs):
        """Set focus of the mechanical ptz

        Args:
            focus_mode (PtzFocusMode): Enum indicating whether to autofocus or manually focus
            distance (float): Approximate distance to focus on, most accurate between 1.2m and 20m,
                only settable in PTZ_FOCUS_MANUAL mode
            focus_position (int32): Precise lens position for the camera for repeatable operations,
                overrides distance if specified, only settable in PTZ_FOCUS_MANUAL mode

        Returns:
            SetPtzFocusStateResponse indicating whether the call was successful
        """
        ptz_focus_state = create_focus_state(focus_mode, distance, focus_position)
        request = ptz_pb2.SetPtzFocusStateRequest(focus_state=ptz_focus_state)
        return self.call(self._stub.SetPtzFocusState, request,
                         self._set_ptz_focus_state_from_response, common_header_errors,
                         copy_request=False, **kwargs)

    def set_ptz_focus_state_async(self, focus_mode, distance=None, focus_position=None, **kwargs):
        """Async version of set_ptz_focus_state()"""
        ptz_focus_state = create_focus_state(focus_mode, distance, focus_position)
        request = ptz_pb2.SetPtzFocusStateRequest(focus_state=ptz_focus_state)
        return self.call_async(self._stub.SetPtzFocusState, request,
                               self._set_ptz_focus_state_from_response, common_header_errors,
                               copy_request=False, **kwargs)

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
    def _initialize_lens_from_response(response):
        return response

    # Focus methods
    @staticmethod
    def _get_ptz_focus_state_from_response(response):
        return response.focus_state

    @staticmethod
    def _set_ptz_focus_state_from_response(response):
        return response


def shift_pan_angle(pan):
    """Shift the pan angle (degrees) so that it is in the [0,360] range."""
    return recenter_value_mod(pan, 180, 360)


def create_focus_state(focus_mode, distance=None, focus_position=None):
    """Generate a focus state proto."""
    approx_distance = None
    focus_position_val = None
    if focus_mode == ptz_pb2.PtzFocusState.PTZ_FOCUS_MANUAL:
        if focus_position is not None:
            focus_position_val = Int32Value(value=focus_position)
            approx_distance = None
        elif distance is not None:
            approx_distance = FloatValue(value=distance)
            focus_position_val = None
        else:
            raise ValueError("One of distance or focus_position must be specified.")

    return ptz_pb2.PtzFocusState(mode=focus_mode, approx_distance=approx_distance,
                                 focus_position=focus_position_val)
