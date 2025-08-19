# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import collections
import math

from bosdyn.api import audio_visual_pb2, audio_visual_service_pb2_grpc
from bosdyn.client.common import (BaseClient, common_header_errors, error_factory, error_pair,
                                  handle_common_header_errors, handle_unset_status_error)

from .exceptions import Error as BaseError
from .exceptions import ResponseError


class AudioVisualResponseError(ResponseError):
    """General class of errors for AudioVisual service."""


class Error(BaseError):
    """Base class for non-response errors in this module."""


class NoTimeSyncError(BaseError):
    """Client has not done timesync with robot."""


class DoesNotExistError(AudioVisualResponseError):
    """The specified behavior does not exist."""


class PermanentBehaviorError(AudioVisualResponseError):
    """Permanent behaviors cannot be modified or deleted."""


class BehaviorExpiredError(AudioVisualResponseError):
    """The specified end_time has already expired."""


class InvalidBehaviorError(AudioVisualResponseError):
    """The request contained a behavior with invalid fields."""


class InvalidClientError(AudioVisualResponseError):
    """The behavior cannot be stopped because a different client is running it."""


class AudioVisualClient(BaseClient):
    """Client for calling the Audio Visual Service."""
    default_service_name = 'audio-visual'
    service_type = 'bosdyn.api.AudioVisualService'

    def __init__(self):
        super(AudioVisualClient,
              self).__init__(audio_visual_service_pb2_grpc.AudioVisualServiceStub)
        self.timesync_endpoint = None

    def update_from(self, other):
        """Update instance from another object.

        Args:
            other: The object where to copy from.
        """
        super(AudioVisualClient, self).update_from(other)

        # Grab a timesync endpoint if it is available.
        try:
            self.timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    def run_behavior(self, name, end_time_secs, restart=False, timesync_endpoint=None, **kwargs):
        """Run a behavior on the robot.

        Args:
            name: The name of the behavior to run.
            end_time_secs: The time that this behavior should stop.
            restart: If this behavior is already running, should we restart it from the beginning.
            timesync_endpoint: Timesync endpoint.

        Raises:
            RpcError: Problem communicating with the robot.
            DoesNotExistError: The behavior name specified has not been added to the system.
            BehaviorExpiredError: The specified end_time has already expired.
            NoTimeSyncError: Time sync has not been established with the robot yet.
        """

        end_time = self._timestamp_to_robot_time(end_time_secs, timesync_endpoint)
        req = audio_visual_pb2.RunBehaviorRequest(name=name, end_time=end_time, restart=restart)
        return self.call(self._stub.RunBehavior, req, error_from_response=_run_behavior_error,
                         copy_request=False, **kwargs)

    def run_behavior_async(self, name, end_time_secs, restart=False, timesync_endpoint=None,
                           **kwargs):
        """Async version of run_behavior().

        Args:
            name: The name of the behavior to run.
            end_time_secs: The time that this behavior should stop.
            restart: If this behavior is already running, should we restart it from the beginning.
            timesync_endpoint: Timesync endpoint.

        Raises:
            RpcError: Problem communicating with the robot.
            DoesNotExistError: The behavior name specified has not been added to the system.
            BehaviorExpiredError: The specified end_time has already expired.
            NoTimeSyncError: Time sync has not been established with the robot yet.
        """

        end_time = self._timestamp_to_robot_time(end_time_secs, timesync_endpoint)
        req = audio_visual_pb2.RunBehaviorRequest(name=name, end_time=end_time, restart=restart)
        return self.call_async(self._stub.RunBehavior, req, error_from_response=_run_behavior_error,
                               copy_request=False, **kwargs)

    def stop_behavior(self, name, **kwargs):
        """Stop a behavior that is currently running.

        Args:
            name: The name of the behavior to stop.

        Raises:
            RpcError: Problem communicating with the robot.
            InvalidClientError: A different client is running this behavior."""

        req = audio_visual_pb2.StopBehaviorRequest(behavior_name=name)

        return self.call(self._stub.StopBehavior, req, error_from_response=_stop_behavior_error,
                         copy_request=False, **kwargs)

    def stop_behavior_async(self, name, **kwargs):
        """Async version of stop_behavior().

        Args:
            name: The name of the behavior to stop.

        Raises:
            RpcError: Problem communicating with the robot.
            InvalidClientError: A different client is running this behavior."""

        req = audio_visual_pb2.StopBehaviorRequest(behavior_name=name)

        return self.call_async(self._stub.StopBehavior, req,
                               error_from_response=_stop_behavior_error, copy_request=False,
                               **kwargs)


    def list_behaviors(self, **kwargs):
        """List all currently added AudioVisualBehaviors.

        Returns:
            A list of all LiveAudioVisualBehavior protos.

        Raises:
            RpcError: Problem communicating with the robot.
        """

        req = audio_visual_pb2.ListBehaviorsRequest()
        return self.call(self._stub.ListBehaviors, req, value_from_response=_get_behavior_list,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def list_behaviors_async(self, **kwargs):
        """Async version of list_behaviors().

        Returns:
            A list of all LiveAudioVisualBehavior protos.

        Raises:
            RpcError: Problem communicating with the robot.
        """

        req = audio_visual_pb2.ListBehaviorsRequest()
        return self.call_async(self._stub.ListBehaviors, req,
                               value_from_response=_get_behavior_list,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def get_system_params(self, **kwargs):
        """Get the current system params.

        Returns:
            An AudioVisualSystemParams proto containing the current system param values.

        Raises:
            RpcError: Problem communicating with the robot.
        """

        req = audio_visual_pb2.GetSystemParamsRequest()
        return self.call(self._stub.GetSystemParams, req, error_from_response=common_header_errors,
                         copy_request=False, **kwargs)

    def get_system_params_async(self, **kwargs):
        """Async version of get_system_params().

        Returns:
            An AudioVisualSystemParams proto containing the current system param values.

        Raises:
            RpcError: Problem communicating with the robot.
        """

        req = audio_visual_pb2.GetSystemParamsRequest()
        return self.call_async(self._stub.GetSystemParams, req,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def set_system_params(self, enabled=None, max_brightness=None, buzzer_max_volume=None,
                          speaker_max_volume=None, normal_color_association=None,
                          warning_color_association=None, danger_color_association=None, **kwargs):
        """Set the system params.

        Args:
            enabled: [optional] System is enabled or disabled (boolean).
            max_brightness: [optional] New max_brightness value [0, 1].
            buzzer_max_volume: [optional] New buzzer_max_volume value [0, 1].
            speaker_max_volume: [optional] New speaker_max_volume value [0, 1].
            normal_color_association: [optional] The color to associate with the normal color preset.
            warning_color_association: [optional] The color to associate with the warning color preset.
            danger_color_association: [optional] The color to associate with the danger color preset.


        Raises:
            RpcError: Problem communicating with the robot.
        """

        req = audio_visual_pb2.SetSystemParamsRequest()
        if (enabled is not None):
            req.enabled.value = enabled
        if (max_brightness is not None):
            req.max_brightness.value = max_brightness
        if (buzzer_max_volume is not None):
            req.buzzer_max_volume.value = buzzer_max_volume
        if (speaker_max_volume is not None):
            req.speaker_max_volume.value = speaker_max_volume
        if (normal_color_association is not None):
            req.normal_color_association.CopyFrom(normal_color_association)
        if (warning_color_association is not None):
            req.warning_color_association.CopyFrom(warning_color_association)
        if (danger_color_association is not None):
            req.danger_color_association.CopyFrom(danger_color_association)
        return self.call(self._stub.SetSystemParams, req, error_from_response=common_header_errors,
                         copy_request=False, **kwargs)

    def set_system_params_async(self, enabled=None, max_brightness=None, buzzer_max_volume=None,
                                speaker_max_volume=None, normal_color_association=None,
                                warning_color_association=None, danger_color_association=None,
                                **kwargs):
        """Async version of set_system_params().

        Args:
            enabled: [optional] System is enabled or disabled (boolean).
            max_brightness: [optional] New max_brightness value [0, 1].
            buzzer_max_volume: [optional] New buzzer_max_volume value [0, 1].
            speaker_max_volume: [optional] New speaker_max_volume value [0, 1].
            normal_color_association: [optional] The color to associate with the normal color preset.
            warning_color_association: [optional] The color to associate with the warning color preset.
            danger_color_association: [optional] The color to associate with the danger color preset.

        Raises:
            RpcError: Problem communicating with the robot.
        """

        req = audio_visual_pb2.SetSystemParamsRequest()
        if (enabled is not None):
            req.enabled.value = enabled
        if (max_brightness is not None):
            req.max_brightness.value = max_brightness
        if (buzzer_max_volume is not None):
            req.buzzer_max_volume.value = buzzer_max_volume
        if (speaker_max_volume is not None):
            req.speaker_max_volume.value = speaker_max_volume
        if (normal_color_association is not None):
            req.normal_color_association.CopyFrom(normal_color_association)
        if (warning_color_association is not None):
            req.warning_color_association.CopyFrom(warning_color_association)
        if (danger_color_association is not None):
            req.danger_color_association.CopyFrom(danger_color_association)
        return self.call_async(self._stub.SetSystemParams, req,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def _timestamp_to_robot_time(self, timestamp, timesync_endpoint=None):
        # Create a time converter to convert timestamp to robot time
        time_converter = None
        if (timesync_endpoint):
            time_converter = timesync_endpoint.get_robot_time_converter()
        elif (self.timesync_endpoint):
            time_converter = self.timesync_endpoint.get_robot_time_converter()
        else:
            raise NoTimeSyncError("No timesync endpoint was passed to audio visual client.")

        return time_converter.robot_timestamp_from_local_secs(timestamp)


def _get_behavior_list(response):
    return response.behaviors


def _get_live_behavior(response):
    return response.live_behavior



_AUDIO_VISUAL_RUN_BEHAVIOR_STATUS_TO_ERROR = collections.defaultdict(
    lambda: (AudioVisualResponseError, None))
_AUDIO_VISUAL_RUN_BEHAVIOR_STATUS_TO_ERROR.update({
    audio_visual_pb2.RunBehaviorResponse.STATUS_SUCCESS: (None, None),
    audio_visual_pb2.RunBehaviorResponse.STATUS_DOES_NOT_EXIST: error_pair(DoesNotExistError),
    audio_visual_pb2.RunBehaviorResponse.STATUS_EXPIRED: error_pair(BehaviorExpiredError),
})

_AUDIO_VISUAL_STOP_BEHAVIOR_STATUS_TO_ERROR = collections.defaultdict(
    lambda: (AudioVisualResponseError, None))
_AUDIO_VISUAL_STOP_BEHAVIOR_STATUS_TO_ERROR.update({
    audio_visual_pb2.StopBehaviorResponse.STATUS_SUCCESS: (None, None),
    audio_visual_pb2.StopBehaviorResponse.STATUS_INVALID_CLIENT: error_pair(InvalidClientError)
})



@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _run_behavior_error(response):
    """RunBehaviorResponse response to exception."""
    return error_factory(response, response.status,
                         status_to_string=audio_visual_pb2.RunBehaviorResponse.Status.Name,
                         status_to_error=_AUDIO_VISUAL_RUN_BEHAVIOR_STATUS_TO_ERROR)


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _stop_behavior_error(response):
    """StopBehaviorResponse response to exception."""
    return error_factory(response, response.status,
                         status_to_string=audio_visual_pb2.StopBehaviorResponse.Status.Name,
                         status_to_error=_AUDIO_VISUAL_STOP_BEHAVIOR_STATUS_TO_ERROR)


