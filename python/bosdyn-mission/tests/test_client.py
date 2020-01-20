# Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import concurrent
import grpc
import pytest
import time

from bosdyn.api.mission import mission_service_pb2_grpc
from bosdyn.api.mission import mission_pb2
import bosdyn.api.header_pb2 as HeaderProto

import bosdyn.mission.client
from bosdyn.mission import server_util

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

    def GetState(self, request, context):
        response = mission_pb2.GetStateResponse()
        with server_util.ResponseContext(response, request):
            q = response.state.questions.add()
            q.id = self.question_id
            q.source = self.source
            q.text = 'Answer me these questions three'
            i = 0
            for t in ('What is your name', 'What is your quest', 'What is the air-speed velocity of an unladen swallow'):
                o = q.options.add()
                o.answer_code = i
                i += 1

            self.active_questions[q.id] = q
            self.question_id += 1
        return response

    def AnswerQuestion(self, request, context):
        response = mission_pb2.AnswerQuestionResponse()
        with server_util.ResponseContext(response, request):
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

    def reset_answered_questions(self):
        self.answered_questions = {}

@pytest.fixture(scope='function')
def client():
    return bosdyn.mission.client.MissionClient()

@pytest.fixture(scope='function')
def service():
    return MockMissionServicer()

@pytest.fixture(scope='function')
def server(client, service):
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=1))
    mission_service_pb2_grpc.add_MissionServiceServicer_to_server(service, server)
    port = server.add_insecure_port('localhost:0')
    channel = grpc.insecure_channel('localhost:{}'.format(port))
    client.channel = channel
    server.start()
    return server

def test_simple(client, server, service):
    client.get_state()
    resp = client.get_state_async().result()
    assert len(resp.questions) == 1
    assert len(resp.questions[0].options) == 3

    resp = client.answer_question(resp.questions[0].id, resp.questions[0].options[2].answer_code)
    assert resp.status == mission_pb2.AnswerQuestionResponse.STATUS_OK

def test_errors(client, server, service):
    resp = client.get_state()

    question_id = resp.questions[0].id
    answer_code = resp.questions[0].options[2].answer_code

    with pytest.raises(bosdyn.mission.client.InvalidAnswerCode):
        client.answer_question(question_id, INVALID_ANSWER_CODE)

    with pytest.raises(bosdyn.mission.client.InvalidQuestionId):
        # Doesn't matter what the answer code is
        client.answer_question(INVALID_QUESTION_ID, 0)

    client.answer_question(question_id, answer_code)

    with pytest.raises(bosdyn.mission.client.QuestionAlreadyAnswered):
        # Doesn't matter what the answer code is
        client.answer_question(question_id, 0)
