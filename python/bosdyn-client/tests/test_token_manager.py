# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the token_manager module."""
import datetime
import time

import pytest

from bosdyn.client.auth import InvalidTokenError
from bosdyn.client.exceptions import Error, RpcError
from bosdyn.client.token_manager import TokenManager, WriteFailedError
from bosdyn.client.util import cli_auth, cli_login_prompt


class MockRobot:

    def __init__(self, token=None):
        self.user_token = token
        self.address = 'mock-address'

    def authenticate(self, username, password):
        if not (username == 'user' and password == 'password'):
            raise Error('mock exception')

        self.user_token = 'mock-token-auth'

    def authenticate_with_token(self, token):
        self.user_token = 'mock-token-refresh'


def test_token_refresh():
    robot = MockRobot(token='mock-token-default')

    assert robot.user_token == 'mock-token-default'

    local = datetime.datetime.now() + datetime.timedelta(hours=-2)
    tm = TokenManager(robot, timestamp=local)

    time.sleep(0.1)
    assert robot.user_token == 'mock-token-refresh'

    tm.stop()


def test_token_refresh_rpc_error():
    robot = MockRobot(token='mock-token-default')

    def fail_with_rpc(token):
        fail_with_rpc.count += 1
        raise RpcError("Fake Rpc Error")

    fail_with_rpc.count = 0
    robot.authenticate_with_token = fail_with_rpc
    assert robot.user_token == 'mock-token-default'
    local = datetime.datetime.now() + datetime.timedelta(hours=-2)
    tm = TokenManager(robot, timestamp=local)
    time.sleep(0.1)
    assert fail_with_rpc.count == 1  # If the TokenManager immediately retries, count ends up as several hundred.
    assert tm.is_alive()


def test_token_refresh_token_error():
    robot = MockRobot(token='mock-token-default')

    def fail_with_rpc(token):
        raise InvalidTokenError(None)

    robot.authenticate_with_token = fail_with_rpc
    assert robot.user_token == 'mock-token-default'
    local = datetime.datetime.now() + datetime.timedelta(hours=-2)
    tm = TokenManager(robot, timestamp=local)
    time.sleep(0.1)
    assert tm.is_alive(
    )  # For now we keep the tokenmanager retrying, so if the user does re-auth it
    # will start updating the new token.


def test_token_refresh_write_error():
    robot = MockRobot(token='mock-token-default')
    original_auth = robot.authenticate_with_token

    def fail_write(token):
        original_auth(token)
        raise WriteFailedError("Fake write failure")

    robot.authenticate_with_token = fail_write
    assert robot.user_token == 'mock-token-default'
    local = datetime.datetime.now() + datetime.timedelta(hours=-2)
    tm = TokenManager(robot, timestamp=local)
    time.sleep(0.1)
    assert robot.user_token == 'mock-token-refresh'
    assert tm.is_alive()
    tm.stop()


def _patch(value):

    def patched(*args, **kwargs):
        return value

    return patched


def test_cli_login(monkeypatch):
    real_login = ('user', 'password')
    monkeypatch.setattr('six.moves.input', _patch(real_login[0]))
    monkeypatch.setattr('getpass.getpass', _patch(real_login[1]))
    login = cli_login_prompt()
    assert login == real_login


def test_cli_login_with_username(monkeypatch):
    real_login = ('bad_user', 'bad_password')
    monkeypatch.setattr('six.moves.input', _patch(real_login[0]))
    monkeypatch.setattr('getpass.getpass', _patch(real_login[1]))
    login = cli_login_prompt('mock-user')
    assert login == real_login


def test_cli_authentication(monkeypatch):
    robot = MockRobot(token='mock-token-default')

    monkeypatch.setattr('six.moves.input', _patch('user'))
    monkeypatch.setattr('getpass.getpass', _patch('password'))
    cli_auth(robot)

    assert robot.user_token == 'mock-token-auth'
