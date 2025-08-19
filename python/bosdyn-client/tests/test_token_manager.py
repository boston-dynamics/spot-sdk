# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the token_manager module."""
import datetime
import threading
import time
from unittest.mock import patch

import pytest

import bosdyn.client.token_manager
from bosdyn.client.auth import InvalidTokenError
from bosdyn.client.error_callback_result import ErrorCallbackResult
from bosdyn.client.exceptions import Error, RpcError
from bosdyn.client.token_manager import (USER_TOKEN_REFRESH_TIME_DELTA,
                                         USER_TOKEN_RETRY_INTERVAL_START, TokenManager,
                                         WriteFailedError)
from bosdyn.client.util import cli_auth, cli_login_prompt

from .error_callback_helpers import MockTime, PolicySwitchingCallback, SimpleCallback, diff


def fail_with_invalid_token(token):
    raise InvalidTokenError(None)


class MockRobot:

    def __init__(self, token=None):
        self.user_token = token
        self.address = 'mock-address'
        self.token_refresh_error_callback = None

    def authenticate(self, username, password):
        if not (username == 'user' and password == 'password'):
            raise Error('mock exception')

        self.user_token = 'mock-token-auth'

    def authenticate_with_token(self, token):
        self.user_token = 'mock-token-refresh'


class TokenManagerModifiedInit(bosdyn.client.token_manager.TokenManager):
    """
    Slightly modified version of TokenManager to install MockTime as a stand-in for
    the thread exit event.

    Args:
        robot (MockRobot): The mocked robot object.
        mock_time (MockTime): The mocked time/Event object.
        timestamp (datetime): The initial timestamp for the token manager.
        refresh_interval (datetime.timedelta): The interval for refreshing the token.
        initial_retry_interval (datetime.timedelta): The initial retry interval for token refresh.
    """

    def __init__(self, robot, mock_time, timestamp=None,
                 refresh_interval=USER_TOKEN_REFRESH_TIME_DELTA,
                 initial_retry_interval=USER_TOKEN_RETRY_INTERVAL_START):
        self.robot = robot

        self._last_timestamp = timestamp or datetime.datetime.now()
        self._refresh_interval = refresh_interval
        self._initial_retry_seconds = initial_retry_interval

        self._exit_thread = mock_time

        self.th = threading.Thread(name='token_manager', target=self.update)
        self.th.start()


def _run_token_refresh_test(mock_time, callback, test_duration,
                            refresh_interval=USER_TOKEN_REFRESH_TIME_DELTA,
                            initial_retry_interval=USER_TOKEN_RETRY_INTERVAL_START):
    robot = MockRobot(token='mock-token-default')
    robot.authenticate_with_token = fail_with_invalid_token
    robot.token_refresh_error_callback = callback

    with patch('bosdyn.client.token_manager.datetime.datetime', mock_time):
        tm = TokenManagerModifiedInit(robot, mock_time, refresh_interval=refresh_interval,
                                      initial_retry_interval=initial_retry_interval)
        mock_time.run(test_duration)

        # make sure that the thread has finished executing its logic before the test
        # method removes the datetime patch and evaluates the results
        tm.th.join()


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

    robot.authenticate_with_token = fail_with_invalid_token
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


def test_token_refresh_token_error_resume_normal_operation():
    mt = MockTime()
    callback = SimpleCallback(ErrorCallbackResult.RESUME_NORMAL_OPERATION, mock_time=mt)

    _run_token_refresh_test(mt, callback, USER_TOKEN_REFRESH_TIME_DELTA.seconds * 2.5)

    assert len(callback.times) == 2
    assert callback.times[0] == pytest.approx(USER_TOKEN_REFRESH_TIME_DELTA.seconds)
    t_diff = diff(callback.times)
    assert t_diff[0] == pytest.approx(USER_TOKEN_REFRESH_TIME_DELTA.seconds)


def test_token_refresh_token_error_invokes_callback_and_retries_immediately():
    mt = MockTime()
    callback = PolicySwitchingCallback(ErrorCallbackResult.RETRY_IMMEDIATELY,
                                       ErrorCallbackResult.RESUME_NORMAL_OPERATION, 3, mock_time=mt)

    _run_token_refresh_test(mt, callback, USER_TOKEN_REFRESH_TIME_DELTA.seconds * 2.5)

    assert len(callback.times) == 5
    assert callback.times[0] == pytest.approx(USER_TOKEN_REFRESH_TIME_DELTA.seconds)
    t_diff = diff(callback.times)
    assert t_diff == pytest.approx((0.0, 0.0, 0.0, USER_TOKEN_REFRESH_TIME_DELTA.seconds))


def test_token_refresh_token_error_invokes_callback_and_aborts_on_abort_policy():
    mt = MockTime()
    callback = SimpleCallback(ErrorCallbackResult.ABORT, mock_time=mt)

    _run_token_refresh_test(mt, callback, USER_TOKEN_REFRESH_TIME_DELTA.seconds * 2.5)

    assert len(callback.times) == 1
    assert callback.times[0] == pytest.approx(USER_TOKEN_REFRESH_TIME_DELTA.seconds)


def test_token_refresh_token_error_invokes_callback_and_backs_off():
    mt = MockTime()
    callback = SimpleCallback(ErrorCallbackResult.RETRY_WITH_EXPONENTIAL_BACK_OFF, mock_time=mt)
    refresh_interval = datetime.timedelta(hours=1)
    initial_retry = datetime.timedelta(seconds=1)

    # 3600 + 1 + 2 + 4 + 8 + 16 = 3631
    # + 0.75 * 32 => 3655
    _run_token_refresh_test(mt, callback, 3655, refresh_interval=refresh_interval,
                            initial_retry_interval=initial_retry)

    assert len(callback.times) == 6
    assert callback.times[0] == pytest.approx(refresh_interval.seconds)
    t_diff = diff(callback.times)
    assert t_diff == pytest.approx(tuple(initial_retry.seconds * (2**count) for count in range(5)))


def test_token_refresh_token_error_default_policy_is_exponential_back_off():
    mt = MockTime()
    callback = SimpleCallback(mock_time=mt)
    refresh_interval = datetime.timedelta(hours=1)
    initial_retry = datetime.timedelta(seconds=1)

    # 3600 + 1 + 2 + 4 + 8 + 16 = 3631
    # + 0.75 * 32 => 3655
    _run_token_refresh_test(mt, callback, 3655, refresh_interval=refresh_interval,
                            initial_retry_interval=initial_retry)

    assert len(callback.times) == 6
    assert callback.times[0] == pytest.approx(refresh_interval.seconds)
    t_diff = diff(callback.times)
    assert t_diff == pytest.approx(tuple(initial_retry.seconds * (2**count) for count in range(5)))


def test_token_refresh_token_error_invokes_callback_and_backs_off_and_levels_off():
    mt = MockTime()
    callback = SimpleCallback(ErrorCallbackResult.RETRY_WITH_EXPONENTIAL_BACK_OFF, mock_time=mt)

    refresh_interval = datetime.timedelta(seconds=120)
    initial_retry = datetime.timedelta(seconds=2)
    # 120 + 2 + 4 + 8 + 16 + 32 + 64 + 120 + 120 = 486
    # + 0.5 * 120 => 546
    _run_token_refresh_test(mt, callback, 546, refresh_interval=refresh_interval,
                            initial_retry_interval=initial_retry)

    assert len(callback.times) == 9
    assert callback.times[0] == pytest.approx(refresh_interval.seconds)
    t_diff = diff(callback.times)
    assert t_diff == pytest.approx(
        tuple(initial_retry.seconds * (2**count) for count in range(6)) +
        (refresh_interval.seconds, refresh_interval.seconds))


def _patch(value):

    def patched(*args, **kwargs):
        return value

    return patched


def test_cli_login(monkeypatch):
    real_login = ('user', 'password')
    monkeypatch.setattr('builtins.input', _patch(real_login[0]))
    monkeypatch.setattr('getpass.getpass', _patch(real_login[1]))
    login = cli_login_prompt()
    assert login == real_login


def test_cli_login_with_username(monkeypatch):
    real_login = ('bad_user', 'bad_password')
    monkeypatch.setattr('builtins.input', _patch(real_login[0]))
    monkeypatch.setattr('getpass.getpass', _patch(real_login[1]))
    login = cli_login_prompt('mock-user')
    assert login == real_login


def test_cli_authentication(monkeypatch):
    robot = MockRobot(token='mock-token-default')

    monkeypatch.setattr('builtins.input', _patch('user'))
    monkeypatch.setattr('getpass.getpass', _patch('password'))
    cli_auth(robot)

    assert robot.user_token == 'mock-token-auth'
