# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the mission service."""

from builtins import str as text
import collections

from google.protobuf import timestamp_pb2

from bosdyn.client.common import BaseClient
from bosdyn.client.common import (common_header_errors, handle_common_header_errors,
                                  handle_unset_status_error, error_factory)

from bosdyn.api.mission import mission_pb2
from bosdyn.api.mission import mission_service_pb2_grpc

from bosdyn.client.exceptions import ResponseError, TimeSyncRequired


class MissionResponseError(ResponseError):
    """General class of errors for mission service."""


class InvalidQuestionId(MissionResponseError):
    """The indicated question is unknown."""


class InvalidAnswerCode(MissionResponseError):
    """The indicated answer code is invalid for the specified question."""


class QuestionAlreadyAnswered(MissionResponseError):
    """The indicated question was already answered."""


class CompilationError(MissionResponseError):
    """Mission could not be compiled."""


class ValidationError(MissionResponseError):
    """Mission could not be validated."""

    def __init__(self, response, error_message=None):
        super(ValidationError, self).__init__(self, response)
        self.failed_nodes = response.failed_nodes

    def __str__(self):
        return 'Mission validation failed with: {}'.format('; '.join(
            [n.error for n in self.failed_nodes]))


class NoMissionError(MissionResponseError):
    """There is no mission to be played/restarted."""


class NoMissionPlayingError(MissionResponseError):
    """There is no mission to be paused."""


class MissionClient(BaseClient):
    """Client for the Mission service."""
    default_service_name = 'robot-mission'
    service_type = 'bosdyn.api.mission.MissionService'

    def __init__(self):
        super(MissionClient, self).__init__(mission_service_pb2_grpc.MissionServiceStub)
        self._timesync_endpoint = None

    def update_from(self, other):
        super(MissionClient, self).update_from(other)

        # Grab a timesync endpoint if it is available.
        try:
            self._timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    @property
    def timesync_endpoint(self):
        """Accessor for timesync endpoint that was grabbed via 'update_from()'."""
        if not self._timesync_endpoint:
            raise TimeSyncRequired
        return self._timesync_endpoint

    def get_state(self, upper_tick_bound=None, lower_tick_bound=None, past_ticks=None, **kwargs):
        """Obtain current mission state.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_state_request(upper_tick_bound, lower_tick_bound, past_ticks)
        return self.call(self._stub.GetState, req, _get_state_value, common_header_errors, **kwargs)

    def get_state_async(self, upper_tick_bound=None, lower_tick_bound=None, past_ticks=None,
                        **kwargs):
        """Async version of get_state()"""
        req = self._get_state_request(upper_tick_bound, lower_tick_bound, past_ticks)
        return self.call_async(self._stub.GetState, req, _get_state_value, common_header_errors,
                               **kwargs)

    def answer_question(self, question_id, code, **kwargs):
        """Specify an answer to the question asked by the mission.
        Args:
            question_id (int): Id of the question to answer.
            code (int): Answer code.

        Raises:
            RpcError: Problem communicating with the robot.
            InvalidQuestionId: question_id was not a valid id.
            InvalidAnswerCode: code was not valid for the question.
            QuestionAlreadyAnswered: The question for question_id was already answered.
        """
        req = self._answer_question_request(question_id, code)
        return self.call(self._stub.AnswerQuestion, req, None, _answer_question_error_from_response,
                         **kwargs)

    def answer_question_async(self, question_id, code, **kwargs):
        """Async version of answer_question()"""
        req = self._answer_question_request(question_id, code)
        return self.call_async(self._stub.AnswerQuestion, req, None,
                               _answer_question_error_from_response, **kwargs)

    def load_mission(self, root, leases, **kwargs):
        """Load a mission onto the robot.
        Args:
            root: Root node in a mission.
            leases: All leases necessary to initialize a mission.
        Raises:
            RpcError: Problem communicating with the robot.
            CompilationError: The mission failed to compile.
            bosdyn.mission.client.ValidationError: The mission failed to validate.
        """
        req = self._load_mission_request(root, leases)
        return self.call(self._stub.LoadMission, req, None, _load_mission_error_from_response,
                         **kwargs)

    def load_mission_async(self, root, leases, **kwargs):
        """Async version of load_mission"""
        req = self._load_mission_request(root, leases)
        return self.call_async(self._stub.LoadMission, req, None, _load_mission_error_from_response,
                               **kwargs)

    def play_mission(self, pause_time_secs, leases, settings=None, **kwargs):
        """Play the loaded mission.

        Args:
          pause_time_secs: Absolute time when the mission should pause execution. Subsequent RPCs
              will override this value, so you can use this to say "if you don't hear from me again,
              stop running the mission at this time."
          leases: Leases the mission service will need to use. Unlike other clients, these MUST
              be specified.
        Raises:
            RpcError: Problem communicating with the robot.
            NoMissionError: No mission Loaded.
        """
        req = self._play_mission_request(pause_time_secs, leases, settings)
        return self.call(self._stub.PlayMission, req, None, _play_mission_error_from_response,
                         **kwargs)

    def play_mission_async(self, pause_time_secs, leases, settings=None, **kwargs):
        """Async version of play_mission."""
        req = self._play_mission_request(pause_time_secs, leases, settings)
        return self.call_async(self._stub.PlayMission, req, None, _play_mission_error_from_response,
                               **kwargs)

    def restart_mission(self, pause_time_secs, leases, settings=None, **kwargs):
        """Restart the loaded mission.

        Args:
          pause_time_secs: Absolute time when the mission should pause execution. Subsequent RPCs
              to RestartMission will override this value, so you can use this to say "if you don't hear
              from me again, stop running the mission at this time."
          leases: Leases the mission service will need to use. Unlike other clients, these MUST
              be specified.
        Raises:
            RpcError: Problem communicating with the robot.
            NoMissionError: No Mission Loaded.
            bosdyn.mission.client.ValidationError: The mission failed to validate.
        """
        req = self._restart_mission_request(pause_time_secs, leases, settings)
        return self.call(self._stub.RestartMission, req, None, _restart_mission_error_from_response,
                         **kwargs)

    def restart_mission_async(self, pause_time_secs, leases, settings=None, **kwargs):
        """Async version of restart_mission."""
        req = self._restart_mission_request(pause_time_secs, leases, settings)
        return self.call_async(self._stub.RestartMission, req, None,
                               _restart_mission_error_from_response, **kwargs)

    def pause_mission(self, **kwargs):
        """Pause the running mission.

        Raises:
            RpcError: Problem communicating with the robot.
            NoMissionPlayingError: No mission playing.
        """
        req = self._pause_mission_request()
        return self.call(self._stub.PauseMission, req, None, _pause_mission_error_from_response,
                         **kwargs)

    def pause_mission_async(self, **kwargs):
        """Async version of pause_mission()."""
        req = self._pause_mission_request()
        return self.call_async(self._stub.PauseMission, req, None,
                               _pause_mission_error_from_response, **kwargs)

    def get_info(self, **kwargs):
        """Get static information about the loaded mission.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_info_request()
        return self.call(self._stub.GetInfo, req, _get_info_value, common_header_errors, **kwargs)

    def get_info_async(self, **kwargs):
        """Async version of get_info."""
        req = self._get_info_request()
        return self.call_async(self._stub.GetInfo, req, _get_info_value, common_header_errors,
                               **kwargs)

    def get_mission(self, **kwargs):
        """Get the loaded mission.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_mission_request()
        return self.call(self._stub.GetMission, req, None, common_header_errors, **kwargs)

    def get_mission_async(self, **kwargs):
        """Async version of get_mission()."""
        req = self._get_mission_request()
        return self.call_async(self._stub.GetMission, req, None, common_header_errors, **kwargs)

    @staticmethod
    def _get_state_request(upper_tick_bound, lower_tick_bound, past_ticks):
        if lower_tick_bound is not None and past_ticks is not None:
            raise ValueError('Cannot specify both lower_tick_bound and past_ticks')
        request = mission_pb2.GetStateRequest(history_lower_tick_bound=lower_tick_bound,
                                              history_past_ticks=past_ticks)
        if upper_tick_bound is not None:
            request.history_upper_tick_bound.value = upper_tick_bound
        return request

    @staticmethod
    def _answer_question_request(question_id, code):
        return mission_pb2.AnswerQuestionRequest(question_id=question_id, code=code)

    @staticmethod
    def _load_mission_request(root, leases):
        request = mission_pb2.LoadMissionRequest(root=root)
        for lease in leases:
            request.leases.add().CopyFrom(lease.lease_proto)
        return request

    def _play_mission_request(self, pause_time_secs, leases, settings):
        request = mission_pb2.PlayMissionRequest(
            pause_time=self.timesync_endpoint.robot_timestamp_from_local_secs(pause_time_secs),
            settings=settings)
        for lease in leases:
            request.leases.add().CopyFrom(lease.lease_proto)
        return request

    def _restart_mission_request(self, pause_time_secs, leases, settings):
        request = mission_pb2.RestartMissionRequest(
            pause_time=self.timesync_endpoint.robot_timestamp_from_local_secs(pause_time_secs),
            settings=settings)
        for lease in leases:
            request.leases.add().CopyFrom(lease.lease_proto)
        return request

    @staticmethod
    def _pause_mission_request():
        return mission_pb2.PauseMissionRequest()

    @staticmethod
    def _get_info_request():
        return mission_pb2.GetInfoRequest()

    @staticmethod
    def _get_mission_request():
        return mission_pb2.GetMissionRequest()


def _get_state_value(response):
    return response.state


def _get_info_value(response):
    if response.HasField(text('mission_info')):
        return response.mission_info
    return None


_ANSWER_QUESTION_STATUS_TO_ERROR = collections.defaultdict(lambda: (MissionResponseError, None))
_ANSWER_QUESTION_STATUS_TO_ERROR.update({
    mission_pb2.AnswerQuestionResponse.STATUS_OK: (None, None),
    mission_pb2.AnswerQuestionResponse.STATUS_INVALID_QUESTION_ID: (InvalidQuestionId,
                                                                    InvalidQuestionId.__doc__),
    mission_pb2.AnswerQuestionResponse.STATUS_INVALID_CODE: (InvalidAnswerCode,
                                                             InvalidAnswerCode.__doc__),
    mission_pb2.AnswerQuestionResponse.STATUS_ALREADY_ANSWERED: (QuestionAlreadyAnswered,
                                                                 QuestionAlreadyAnswered.__doc__),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _answer_question_error_from_response(response):
    return error_factory(response, response.status,
                         status_to_string=mission_pb2.AnswerQuestionResponse.Status.Name,
                         status_to_error=_ANSWER_QUESTION_STATUS_TO_ERROR)


_LOAD_MISSION_STATUS_TO_ERROR = collections.defaultdict(lambda: (MissionResponseError, None))
_LOAD_MISSION_STATUS_TO_ERROR.update({
    mission_pb2.LoadMissionResponse.STATUS_OK: (None, None),
    mission_pb2.LoadMissionResponse.STATUS_VALIDATE_ERROR: (ValidationError, None),
    mission_pb2.LoadMissionResponse.STATUS_COMPILE_ERROR: (CompilationError, None),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _load_mission_error_from_response(response):
    return error_factory(response, response.status,
                         status_to_string=mission_pb2.LoadMissionResponse.Status.Name,
                         status_to_error=_LOAD_MISSION_STATUS_TO_ERROR)


_PLAY_MISSION_STATUS_TO_ERROR = collections.defaultdict(lambda: (MissionResponseError, None))
_PLAY_MISSION_STATUS_TO_ERROR.update({
    mission_pb2.PlayMissionResponse.STATUS_OK: (None, None),
    mission_pb2.PlayMissionResponse.STATUS_NO_MISSION: (NoMissionError, None),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _play_mission_error_from_response(response):
    return error_factory(response, response.status,
                         status_to_string=mission_pb2.PlayMissionResponse.Status.Name,
                         status_to_error=_PLAY_MISSION_STATUS_TO_ERROR)


_PAUSE_MISSION_STATUS_TO_ERROR = collections.defaultdict(lambda: (MissionResponseError, None))
_PAUSE_MISSION_STATUS_TO_ERROR.update({
    mission_pb2.PauseMissionResponse.STATUS_OK: (None, None),
    mission_pb2.PauseMissionResponse.STATUS_NO_MISSION_PLAYING: (NoMissionPlayingError, None),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _pause_mission_error_from_response(response):
    return error_factory(response, response.status,
                         status_to_string=mission_pb2.PauseMissionResponse.Status.Name,
                         status_to_error=_PAUSE_MISSION_STATUS_TO_ERROR)


_RESTART_MISSION_STATUS_TO_ERROR = collections.defaultdict(lambda: (MissionResponseError, None))
_RESTART_MISSION_STATUS_TO_ERROR.update({
    mission_pb2.RestartMissionResponse.STATUS_OK: (None, None),
    mission_pb2.RestartMissionResponse.STATUS_NO_MISSION: (NoMissionError, None),
    mission_pb2.RestartMissionResponse.STATUS_VALIDATE_ERROR: (ValidationError, None),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _restart_mission_error_from_response(response):
    return error_factory(response, response.status,
                         status_to_string=mission_pb2.RestartMissionResponse.Status.Name,
                         status_to_error=_RESTART_MISSION_STATUS_TO_ERROR)
