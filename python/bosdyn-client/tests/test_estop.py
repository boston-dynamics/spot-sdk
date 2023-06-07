# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import concurrent.futures
import logging
import time

import grpc
import pytest

import bosdyn.api.estop_pb2
import bosdyn.api.estop_service_pb2_grpc
import bosdyn.client.estop
from bosdyn.client import InternalServerError


class MockEstopServicer(bosdyn.api.estop_service_pb2_grpc.EstopServiceServicer):
    VALID_STOP_LEVEL = 1
    NAME_FOR_ENDPOINT_UNKNOWN = 'mystery'
    NAME_FOR_SERVER_ERROR = 'little-bobby-drop-tables'
    STATUSES_THAT_DO_NOT_PROVIDE_CHALLENGE = \
        set([bosdyn.api.estop_pb2.EstopCheckInResponse.STATUS_UNKNOWN])

    def __init__(self, rpc_delay=0):
        """Create mock that returns specific token after optional delay."""
        super(MockEstopServicer, self).__init__()
        self._rpc_delay = rpc_delay
        self._challenge = 0

    def RegisterEstopEndpoint(self, request, context):
        """Create mock."""

    def EstopCheckIn(self, request, context):
        """Implement the EstopCheckIn function of the service.

        This does not mirror the actual behavior of the real service. It
        is only intended to trigger all branches of the client.
        """
        resp = bosdyn.api.estop_pb2.EstopCheckInResponse()
        resp.header.error.code = bosdyn.api.header_pb2.CommonError.CODE_OK
        if request.endpoint.name == self.NAME_FOR_SERVER_ERROR:
            resp.header.error.code = bosdyn.api.header_pb2.CommonError.CODE_INTERNAL_SERVER_ERROR
        elif request.endpoint.name == self.NAME_FOR_ENDPOINT_UNKNOWN:
            resp.status = resp.STATUS_ENDPOINT_UNKNOWN
        else:
            if not request.challenge:
                resp.status = resp.STATUS_INCORRECT_CHALLENGE_RESPONSE
            elif request.response != bosdyn.client.estop.response_from_challenge(request.challenge):
                resp.status = resp.STATUS_INCORRECT_CHALLENGE_RESPONSE
            else:
                resp.status = resp.STATUS_OK
        if resp.status not in self.STATUSES_THAT_DO_NOT_PROVIDE_CHALLENGE:
            if request.challenge is not None:
                self._challenge = request.challenge + 1
            else:
                self._challenge = 0
            resp.challenge = self._challenge
        time.sleep(self._rpc_delay)
        return resp


def _setup_server_and_client(rpc_delay=0, endpoint_name='test-endpoint'):
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    bosdyn.api.estop_service_pb2_grpc.add_EstopServiceServicer_to_server(
        MockEstopServicer(rpc_delay), server)
    port = server.add_insecure_port('localhost:0')
    server.start()
    channel = grpc.insecure_channel('localhost:{}'.format(port))
    client = bosdyn.client.estop.EstopClient()
    client.channel = channel
    endpoint = bosdyn.client.estop.EstopEndpoint(client, endpoint_name, estop_timeout=1)
    return client, endpoint


def test_check_in():
    client, endpoint = _setup_server_and_client()
    challenge = 100
    response = bosdyn.client.estop.response_from_challenge(challenge)
    client.check_in(stop_level=MockEstopServicer.VALID_STOP_LEVEL, endpoint=endpoint,
                    challenge=challenge, response=response)


def test_check_in_incorrect_1():
    client, endpoint = _setup_server_and_client()
    challenge = 22
    response = 2 + bosdyn.client.estop.response_from_challenge(challenge)
    with pytest.raises(bosdyn.client.estop.IncorrectChallengeResponseError):
        client.check_in(stop_level=MockEstopServicer.VALID_STOP_LEVEL, endpoint=endpoint,
                        challenge=challenge, response=challenge)


def test_check_in_incorrect_2():
    client, endpoint = _setup_server_and_client()
    challenge = None
    response = None
    with pytest.raises(bosdyn.client.estop.IncorrectChallengeResponseError):
        client.check_in(stop_level=MockEstopServicer.VALID_STOP_LEVEL, endpoint=endpoint,
                        challenge=challenge, response=response)


def test_check_in_incorrect_3():
    client, endpoint = _setup_server_and_client()
    challenge = None
    response = None
    client.check_in(stop_level=MockEstopServicer.VALID_STOP_LEVEL, endpoint=endpoint,
                    challenge=challenge, response=response, suppress_incorrect=True)


def test_server_error_check_in():
    """Test that when we ignore incorrect chal/resp, we still get InternalServerError"""
    client, endpoint = _setup_server_and_client(
        endpoint_name=MockEstopServicer.NAME_FOR_SERVER_ERROR)
    challenge = 100
    response = bosdyn.client.estop.response_from_challenge(challenge)
    with pytest.raises(InternalServerError):
        client.check_in(stop_level=MockEstopServicer.VALID_STOP_LEVEL, endpoint=endpoint,
                        challenge=challenge, response=challenge, suppress_incorrect=True)


def test_endpoint_unknown_check_in():
    """Test that when we ignore incorrect chal/resp, we still get EndpointUnknownError"""
    client, endpoint = _setup_server_and_client(
        endpoint_name=MockEstopServicer.NAME_FOR_ENDPOINT_UNKNOWN)
    challenge = 100
    response = bosdyn.client.estop.response_from_challenge(challenge)
    with pytest.raises(bosdyn.client.estop.EndpointUnknownError):
        client.check_in(stop_level=MockEstopServicer.VALID_STOP_LEVEL, endpoint=endpoint,
                        challenge=challenge, response=challenge, suppress_incorrect=True)


def test_challenge():
    client, endpoint = _setup_server_and_client()

    old_challenge = 0
    endpoint.set_challenge(old_challenge)
    print(endpoint.get_challenge())
    endpoint.allow()
    # We should have gotten the next challenge from that RPC.
    assert old_challenge + 1 == endpoint.get_challenge()


def test_challenge_exc():
    # Make an endpoint unknown by the system.
    _, endpoint = _setup_server_and_client(
        endpoint_name=MockEstopServicer.NAME_FOR_ENDPOINT_UNKNOWN)

    old_challenge = 0
    endpoint.set_challenge(old_challenge)
    with pytest.raises(bosdyn.client.estop.EndpointUnknownError):
        endpoint.allow()
    assert old_challenge + 1 == endpoint.get_challenge()


def test_challenge_exc_async():
    # Make an endpoint unknown by the system.
    _, endpoint = _setup_server_and_client(
        endpoint_name=MockEstopServicer.NAME_FOR_ENDPOINT_UNKNOWN)

    old_challenge = 0
    endpoint.set_challenge(old_challenge)
    fut = endpoint.allow_async()
    with pytest.raises(bosdyn.client.estop.EndpointUnknownError):
        fut.result()
    time.sleep(0.1)
    assert old_challenge + 1 == endpoint.get_challenge()
