# Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the mission service."""

import collections

from bosdyn.client.common import BaseClient
from bosdyn.client.common import (common_header_errors, handle_common_header_errors,
                                  handle_unset_status_error, error_factory)

from bosdyn.api.mission import mission_pb2
from bosdyn.api.mission import mission_service_pb2_grpc

from bosdyn.client.exceptions import ResponseError

class MissionResponseError(ResponseError):
    """General class of errors for mission service."""

class InvalidQuestionId(MissionResponseError):
    """The indicated question is unknown."""

class InvalidAnswerCode(MissionResponseError):
    """The indicated answer code is invalid for the specified question."""

class QuestionAlreadyAnswered(MissionResponseError):
    """The indicated question was already answered."""


class MissionClient(BaseClient):
    """Client for the RobotState service."""
    default_authority = 'mission.spot.robot'
    default_service_name = 'robot-mission'
    service_type = 'bosdyn.api.mission.MissionService'

    def __init__(self):
        super(MissionClient, self).__init__(mission_service_pb2_grpc.MissionServiceStub)

    def get_state(self, **kwargs):
        """ Obtain current mission state."""
        req = self._get_state_request()
        return self.call(self._stub.GetState, req, _get_state_value, common_header_errors, **kwargs)

    def get_state_async(self, **kwargs):
        """Async version of get_state()"""
        req = self._get_state_request()
        return self.call_async(self._stub.GetState, req, _get_state_value,
                               common_header_errors, **kwargs)

    def answer_question(self, question_id, code, **kwargs):
        """Specify an answer to the question asked by the mission."""
        req = self._answer_question_request(question_id, code)
        return self.call(self._stub.AnswerQuestion, req, None, _answer_question_error_from_response,
                         **kwargs)

    def answer_question_async(self, question_id, code, **kwargs):
        """Async version of answer_question()"""
        req = self._answer_question_request(question_id, code)
        return self.call_async(self._stub.AnswerQuestion, req, None,
                               _answer_question_error_from_response, **kwargs)

    @staticmethod
    def _get_state_request():
        return mission_pb2.GetStateRequest()

    @staticmethod
    def _answer_question_request(question_id, code):
        return mission_pb2.AnswerQuestionRequest(question_id=question_id, code=code)


def _get_state_value(response):
    return response.state


_ANSWER_QUESTION_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_ANSWER_QUESTION_STATUS_TO_ERROR.update({
    mission_pb2.AnswerQuestionResponse.STATUS_OK: (None, None),
    mission_pb2.AnswerQuestionResponse.STATUS_INVALID_QUESTION_ID:
    (InvalidQuestionId, InvalidQuestionId.__doc__),
    mission_pb2.AnswerQuestionResponse.STATUS_INVALID_CODE:
    (InvalidAnswerCode, InvalidAnswerCode.__doc__),
    mission_pb2.AnswerQuestionResponse.STATUS_ALREADY_ANSWERED:
    (QuestionAlreadyAnswered, QuestionAlreadyAnswered.__doc__),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _answer_question_error_from_response(response):
    return error_factory(response, response.status,
                         status_to_string=mission_pb2.AnswerQuestionResponse.Status.Name,
                         status_to_error=_ANSWER_QUESTION_STATUS_TO_ERROR)

