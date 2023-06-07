# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Test the client to the mission service."""
import concurrent
import sys
import time
from unittest import mock

import grpc
import helpers
import pytest
from google.protobuf import timestamp_pb2

import bosdyn.api.header_pb2 as HeaderProto
import bosdyn.mission.client
from bosdyn.api.mission import mission_pb2, mission_service_pb2_grpc
from bosdyn.client.server_util import ResponseContext

INVALID_ANSWER_CODE = 100
INVALID_QUESTION_ID = -1


class MockMissionServicer(mission_service_pb2_grpc.MissionServiceServicer):

    def __init__(self):
        super(MockMissionServicer, self).__init__()
        self.service_entries = []
        self.question_id = 0
        self.active_questions = {}
        self.answered_questions = {}
        self.source = 'Mock'
        self.play_mission_response_status = mission_pb2.PlayMissionResponse.STATUS_OK
        self.load_mission_response_status = mission_pb2.LoadMissionResponse.STATUS_OK
        self.restart_mission_response_status = mission_pb2.RestartMissionResponse.STATUS_OK
        self.pause_mission_response_status = mission_pb2.PauseMissionResponse.STATUS_OK

    def GetState(self, request, context):
        """Mock out GetState to produce specific state."""
        response = mission_pb2.GetStateResponse()
        with ResponseContext(response, request):
            q = response.state.questions.add()
            q.id = self.question_id
            q.source = self.source
            q.text = 'Answer me these questions three'
            i = 0
            for t in ('What is your name', 'What is your quest',
                      'What is the air-speed velocity of an unladen swallow'):
                o = q.options.add()
                o.text = 'What is your name'
                o.answer_code = i
                i += 1

            self.active_questions[q.id] = q
            self.question_id += 1
        return response

    def AnswerQuestion(self, request, context):
        """Mimic AnswerQuestion in actual servicer."""
        response = mission_pb2.AnswerQuestionResponse()
        with ResponseContext(response, request):
            self._answer_question_impl(request, response)
        return response

    def _answer_question_impl(self, request, response):
        if request.question_id in self.answered_questions:
            response.status = mission_pb2.AnswerQuestionResponse.STATUS_ALREADY_ANSWERED
            return response
        if request.question_id not in self.active_questions:
            response.status = mission_pb2.AnswerQuestionResponse.STATUS_INVALID_QUESTION_ID
            return response
        question = self.active_questions[request.question_id]
        if request.code not in [option.answer_code for option in question.options]:
            response.status = mission_pb2.AnswerQuestionResponse.STATUS_INVALID_CODE
            return response
        self.answered_questions[request.question_id] = request
        del self.active_questions[request.question_id]
        response.status = mission_pb2.AnswerQuestionResponse.STATUS_OK
        return response

    def PlayMission(self, request, context):
        response = mission_pb2.PlayMissionResponse()
        with ResponseContext(response, request):
            response.status = self.play_mission_response_status
        return response

    def RestartMission(self, request, context):
        response = mission_pb2.RestartMissionResponse()
        with ResponseContext(response, request):
            response.status = self.restart_mission_response_status
        return response

    def PauseMission(self, request, context):
        response = mission_pb2.PauseMissionResponse()
        with ResponseContext(response, request):
            response.status = self.pause_mission_response_status
        return response

    def LoadMission(self, request, context):
        response = mission_pb2.LoadMissionResponse()
        with ResponseContext(response, request):
            response.status = self.load_mission_response_status
        return response

    def reset_answered_questions(self):
        self.answered_questions = {}


@pytest.fixture(scope='function')
def client():
    cli = bosdyn.mission.client.MissionClient()
    cli._timesync_endpoint = mock.Mock()
    cli._timesync_endpoint.robot_timestamp_from_local_secs.return_value = timestamp_pb2.Timestamp(
        seconds=12345, nanos=6789)
    return cli


@pytest.fixture(scope='function')
def service():
    return MockMissionServicer()


@pytest.fixture(scope='function')
def server(client, service):
    return helpers.start_server(mission_service_pb2_grpc.add_MissionServiceServicer_to_server,
                                client, service)


def test_simple(client, server, service):
    """Test basic usage of the mission service client."""
    # Test the get_state and the async version. Should return the question state from the mock.
    client.get_state()
    resp = client.get_state_async().result()
    assert len(resp.questions) == 1
    assert len(resp.questions[0].options) == 3

    # Answer a question with a valid code.
    resp = client.answer_question(resp.questions[0].id, resp.questions[0].options[2].answer_code)
    assert resp.status == mission_pb2.AnswerQuestionResponse.STATUS_OK
    # The next two checks make sure the response context applied the necessary changes to the response header, while
    # also getting the changes from the answer question impl function.
    assert resp.header.error.code == resp.header.error.CODE_OK
    assert resp.header.request_received_timestamp.seconds + resp.header.request_received_timestamp.nanos * 1e-9 > 0


def test_errors(client, server, service):
    """Test incorrect usage of the mission service client."""
    resp = client.get_state()

    question_id = resp.questions[0].id
    answer_code = resp.questions[0].options[2].answer_code

    with pytest.raises(bosdyn.mission.client.InvalidAnswerCode):
        client.answer_question(question_id, INVALID_ANSWER_CODE)

    with pytest.raises(bosdyn.mission.client.InvalidQuestionId):
        # Doesn't matter what the answer code is
        client.answer_question(INVALID_QUESTION_ID, 0)

    # Actually answer the question so we can test answering the same question more than once.
    client.answer_question(question_id, answer_code)

    with pytest.raises(bosdyn.mission.client.QuestionAlreadyAnswered):
        # Doesn't matter what the answer code is
        client.answer_question(question_id, 0)

    # Can't specify both past_ticks and lower_tick_bound.
    with pytest.raises(ValueError):
        client.get_state(past_ticks=2, lower_tick_bound=1)

    # Run through misc error codes.
    service.play_mission_response_status = mission_pb2.PlayMissionResponse.STATUS_NO_MISSION
    with pytest.raises(bosdyn.mission.client.NoMissionError):
        client.play_mission(time.time(), leases=[])

    service.load_mission_response_status = mission_pb2.LoadMissionResponse.STATUS_COMPILE_ERROR
    with pytest.raises(bosdyn.mission.client.CompilationError):
        client.load_mission(None, leases=[])

    service.load_mission_response_status = mission_pb2.LoadMissionResponse.STATUS_VALIDATE_ERROR
    with pytest.raises(bosdyn.mission.client.ValidationError):
        client.load_mission(None, leases=[])

    service.restart_mission_response_status = mission_pb2.RestartMissionResponse.STATUS_NO_MISSION
    with pytest.raises(bosdyn.mission.client.NoMissionError):
        client.restart_mission(time.time(), leases=[])

    service.restart_mission_response_status = mission_pb2.RestartMissionResponse.STATUS_VALIDATE_ERROR
    with pytest.raises(bosdyn.mission.client.ValidationError):
        client.restart_mission(time.time(), leases=[])

    service.pause_mission_response_status = mission_pb2.PauseMissionResponse.STATUS_NO_MISSION_PLAYING
    with pytest.raises(bosdyn.mission.client.NoMissionPlayingError):
        client.pause_mission()
