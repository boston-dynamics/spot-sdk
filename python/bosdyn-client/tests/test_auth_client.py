# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the auth module."""
import logging
import time

import grpc
import pytest

import bosdyn.api.auth_pb2
import bosdyn.api.auth_service_pb2_grpc as auth_service
import bosdyn.client
from bosdyn.client.exceptions import TimedOutError

from . import helpers


class MockAuthServicer(auth_service.AuthServiceServicer):
    USERNAME = 'spam'
    PASSWORD = 'eggs'
    USERNAME_TO_TRIGGER_UNKNOWN = 'blackknight'
    TOKEN_TO_REMINT = 'not-real-jwt'
    RETURN_TOKEN = 'the-token-to-expect'
    VALID_APP_TEST_TOKEN = 'valid-app-token'
    INVALID_APP_TEST_TOKEN = 'invalid-app-token'
    EXPIRED_APP_TEST_TOKEN = 'expired-app-token'

    def __init__(self, rpc_delay=0, use_app_token=False):
        """Create mock that returns specific token after optional delay."""
        super(MockAuthServicer, self).__init__()
        self._rpc_delay = rpc_delay
        self._use_app_token = use_app_token  # For testing compatibility

    def GetAuthToken(self, request, context):
        """Implement the GetAuthToken function of the service.

        This does not mirror the actual behavior of the real AuthService. It
        is only intended to trigger all branches of the AuthClient.
        """
        resp = bosdyn.api.auth_pb2.GetAuthTokenResponse()
        helpers.add_common_header(resp, request)

        if self._use_app_token and request.application_token != self.VALID_APP_TEST_TOKEN:
            if request.application_token == self.EXPIRED_APP_TEST_TOKEN:
                resp.status = resp.STATUS_EXPIRED_APPLICATION_TOKEN
            else:
                resp.status = resp.STATUS_INVALID_APPLICATION_TOKEN
            return resp

        if request.username:
            if request.username == self.USERNAME and request.password == self.PASSWORD:
                resp.token = self.RETURN_TOKEN
                resp.status = resp.STATUS_OK
            elif request.username == self.USERNAME_TO_TRIGGER_UNKNOWN:
                pass
            else:
                resp.status = resp.STATUS_INVALID_LOGIN
        elif request.token:
            if request.token == self.TOKEN_TO_REMINT:
                resp.token = self.RETURN_TOKEN
                resp.status = resp.STATUS_OK
            else:
                resp.status = resp.STATUS_INVALID_TOKEN
        else:
            pass
        time.sleep(self._rpc_delay)
        return resp


def _setup(rpc_delay=0, use_app_token=False):
    client = bosdyn.client.AuthClient()
    service = MockAuthServicer(rpc_delay, use_app_token)
    server = helpers.setup_client_and_service(client, service,
                                              auth_service.add_AuthServiceServicer_to_server)
    return client, service, server


def test_async_valid():
    client, service, server = _setup()
    fut = client.auth_async(MockAuthServicer.USERNAME, MockAuthServicer.PASSWORD)
    assert MockAuthServicer.RETURN_TOKEN == fut.result()


def test_async_invalid():
    client, service, server = _setup()
    with pytest.raises(bosdyn.client.InvalidLoginError):
        client.auth_async('parrot', '').result()


def test_async_timeout():
    timeout = 0.1
    client, service, server = _setup(rpc_delay=(timeout * 2))
    fut = client.auth_async(MockAuthServicer.USERNAME, MockAuthServicer.PASSWORD, timeout=timeout)
    with pytest.raises(TimedOutError):
        fut.result()


def test_async_expired_app_token():
    client, service, server = _setup(use_app_token=True)
    fut = client.auth_async(MockAuthServicer.USERNAME, MockAuthServicer.PASSWORD,
                            MockAuthServicer.EXPIRED_APP_TEST_TOKEN)
    with pytest.raises(bosdyn.client.ExpiredApplicationTokenError):
        fut.result()


def test_async_invalid_app_token():
    client, service, server = _setup(use_app_token=True)
    fut = client.auth_async(MockAuthServicer.USERNAME, MockAuthServicer.PASSWORD,
                            MockAuthServicer.INVALID_APP_TEST_TOKEN)
    with pytest.raises(bosdyn.client.InvalidApplicationTokenError):
        fut.result()


def test_async_token_valid():
    client, service, server = _setup()
    fut = client.auth_with_token_async(MockAuthServicer.TOKEN_TO_REMINT)
    assert MockAuthServicer.RETURN_TOKEN == fut.result()


def test_async_token_invalid():
    client, service, server = _setup()
    fut = client.auth_with_token_async('not-a-valid-token')
    with pytest.raises(bosdyn.client.InvalidTokenError):
        fut.result()


def test_async_token_timeout():
    timeout = 0.1
    client, service, server = _setup(rpc_delay=(timeout * 2))
    fut = client.auth_with_token_async(MockAuthServicer.TOKEN_TO_REMINT, timeout=timeout)
    with pytest.raises(TimedOutError):
        fut.result()


def test_async_token_expired_app_token():
    client, service, server = _setup(use_app_token=True)
    fut = client.auth_with_token_async(MockAuthServicer.TOKEN_TO_REMINT,
                                       MockAuthServicer.EXPIRED_APP_TEST_TOKEN)
    with pytest.raises(bosdyn.client.ExpiredApplicationTokenError):
        fut.result()


def test_async_token_invalid_app_token():
    client, service, server = _setup(use_app_token=True)
    fut = client.auth_with_token_async(MockAuthServicer.TOKEN_TO_REMINT,
                                       MockAuthServicer.INVALID_APP_TEST_TOKEN)
    with pytest.raises(bosdyn.client.InvalidApplicationTokenError):
        fut.result()


def test_sync_valid():
    client, service, server = _setup()
    token = client.auth(MockAuthServicer.USERNAME, MockAuthServicer.PASSWORD)
    assert MockAuthServicer.RETURN_TOKEN == token


def test_sync_invalid():
    client, service, server = _setup()
    with pytest.raises(bosdyn.client.InvalidLoginError) as excinfo:
        token = client.auth('parrot', '')
    assert isinstance(excinfo.value.response, bosdyn.api.auth_pb2.GetAuthTokenResponse)


def test_sync_timeout():
    timeout = 0.1
    client, service, server = _setup(rpc_delay=(timeout * 2))
    with pytest.raises(TimedOutError):
        token = client.auth(MockAuthServicer.USERNAME, MockAuthServicer.PASSWORD, timeout=timeout)


def test_sync_unset():
    client, service, server = _setup()
    with pytest.raises(bosdyn.client.UnsetStatusError) as excinfo:
        token = client.auth(MockAuthServicer.USERNAME_TO_TRIGGER_UNKNOWN, '')
    assert isinstance(excinfo.value.response, bosdyn.api.auth_pb2.GetAuthTokenResponse)


def test_sync_expired_app_token():
    client, service, server = _setup(use_app_token=True)
    with pytest.raises(bosdyn.client.ExpiredApplicationTokenError):
        client.auth(MockAuthServicer.USERNAME, MockAuthServicer.PASSWORD,
                    MockAuthServicer.EXPIRED_APP_TEST_TOKEN)


def test_sync_invalid_app_token():
    client, service, server = _setup(use_app_token=True)
    with pytest.raises(bosdyn.client.InvalidApplicationTokenError):
        client.auth(MockAuthServicer.USERNAME, MockAuthServicer.PASSWORD,
                    MockAuthServicer.INVALID_APP_TEST_TOKEN)


def test_sync_token_valid():
    client, service, server = _setup()
    token = client.auth_with_token(MockAuthServicer.TOKEN_TO_REMINT)
    assert MockAuthServicer.RETURN_TOKEN == token


def test_sync_token_invalid():
    client, service, server = _setup()
    with pytest.raises(bosdyn.client.InvalidTokenError):
        token = client.auth_with_token('not-a-valid-token')


def test_sync_token_timeout():
    timeout = 0.1
    client, service, server = _setup(rpc_delay=(timeout * 2))
    with pytest.raises(TimedOutError):
        token = client.auth_with_token(MockAuthServicer.TOKEN_TO_REMINT, timeout=timeout)


def test_sync_token_expired_app_token():
    client, service, server = _setup(use_app_token=True)
    with pytest.raises(bosdyn.client.ExpiredApplicationTokenError):
        client.auth_with_token(MockAuthServicer.TOKEN_TO_REMINT,
                               MockAuthServicer.EXPIRED_APP_TEST_TOKEN)


def test_sync_token_invalid_app_token():
    client, service, server = _setup(use_app_token=True)
    with pytest.raises(bosdyn.client.InvalidApplicationTokenError):
        client.auth_with_token(MockAuthServicer.TOKEN_TO_REMINT,
                               MockAuthServicer.INVALID_APP_TEST_TOKEN)
