# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tests for the power command client."""

import time
from concurrent import futures

import pytest

from bosdyn.api import license_pb2, power_pb2, robot_state_pb2
from bosdyn.client import (InternalServerError, InvalidRequestError, LeaseUseError, LicenseError,
                           ResponseError, UnsetStatusError, power)
from bosdyn.client.power import (_power_command_error_from_response,
                                 _power_feedback_error_from_response)

# For coverage report, run with...
# python -m pytest --cov bosdyn.client.power --cov-report term-missing tests/test_power.py


def test_power_command_error():
    # Test unset header error
    response = power_pb2.PowerCommandResponse()
    response.license_status = license_pb2.LicenseInfo.STATUS_VALID
    assert isinstance(_power_command_error_from_response(response), UnsetStatusError)
    # Test header internal server error
    response.header.error.code = response.header.error.CODE_INTERNAL_SERVER_ERROR
    assert isinstance(_power_command_error_from_response(response), InternalServerError)
    # Test header invalid request error
    response.header.error.code = response.header.error.CODE_INVALID_REQUEST
    assert isinstance(_power_command_error_from_response(response), InvalidRequestError)
    # Test lease use error
    response.header.error.code = response.header.error.CODE_OK
    response.lease_use_result.status = response.lease_use_result.STATUS_INVALID_LEASE
    assert isinstance(_power_command_error_from_response(response), LeaseUseError)
    # Test unset status
    response.lease_use_result.status = response.lease_use_result.STATUS_OK
    assert isinstance(_power_command_error_from_response(response), UnsetStatusError)
    # Test status error
    response.status = power_pb2.STATUS_SHORE_POWER_CONNECTED
    assert isinstance(_power_command_error_from_response(response), ResponseError)
    # Test unknown status
    response.status = 1337
    assert isinstance(_power_command_error_from_response(response), ResponseError)
    # Test status processing
    response.status = power_pb2.STATUS_IN_PROGRESS
    assert not _power_command_error_from_response(response)
    # Test status OK
    response.status = power_pb2.STATUS_SUCCESS
    assert not _power_command_error_from_response(response)
    # Test lease error even when response status is OK.
    response.lease_use_result.status = response.lease_use_result.STATUS_INVALID_LEASE
    assert isinstance(_power_command_error_from_response(response), LeaseUseError)
    # Test license error even when response status is OK.
    response.license_status = license_pb2.LicenseInfo.STATUS_NO_LICENSE
    response.lease_use_result.status = response.lease_use_result.STATUS_OK
    response.status = power_pb2.STATUS_LICENSE_ERROR
    assert isinstance(_power_command_error_from_response(response), LicenseError)

    # test backwards compatibility with old clients
    response.license_status = license_pb2.LicenseInfo.STATUS_NO_LICENSE
    response.status = power_pb2.STATUS_SUCCESS
    assert not _power_command_error_from_response(response)


def test_power_feedback_error():
    # Test unset header error
    response = power_pb2.PowerCommandFeedbackResponse()
    assert isinstance(_power_feedback_error_from_response(response), UnsetStatusError)
    # Test header internal server error
    response.header.error.code = response.header.error.CODE_INTERNAL_SERVER_ERROR
    assert isinstance(_power_feedback_error_from_response(response), InternalServerError)
    # Test header invalid request error
    response.header.error.code = response.header.error.CODE_INVALID_REQUEST
    assert isinstance(_power_feedback_error_from_response(response), InvalidRequestError)
    # Test unset status
    response.header.error.code = response.header.error.CODE_OK
    assert isinstance(_power_feedback_error_from_response(response), UnsetStatusError)
    # Test status error
    response.status = power_pb2.STATUS_SHORE_POWER_CONNECTED
    assert not _power_feedback_error_from_response(response)
    # Test unknown status. This is NOT an error -- user will decide what to do in this case.
    response.status = 1337
    assert _power_feedback_error_from_response(response) is None
    # Test status processing
    response.status = power_pb2.STATUS_IN_PROGRESS
    assert not _power_feedback_error_from_response(response)
    # Test status OK
    response.status = power_pb2.STATUS_SUCCESS
    assert not _power_feedback_error_from_response(response)


class MockPowerClient(object):

    def __init__(self):
        self.request = None
        self.response = power_pb2.STATUS_IN_PROGRESS
        self.feedback_fn = None
        self.executor = futures.ThreadPoolExecutor(max_workers=2)

    def power_command(self, request, lease=None, **kwargs):
        self.request = request
        return power_pb2.PowerCommandResponse(power_command_id=1337)

    def power_command_feedback(self, power_command_id, **kwargs):
        if self.feedback_fn:
            self.feedback_fn()
        return self.response

    def power_command_feedback_async(self, power_command_id, **kwargs):
        return self.executor.submit(self.power_command_feedback, power_command_id, **kwargs)


class MockRobotCommandClient(object):

    def __init__(self):
        pass

    def robot_command(self, command, end_times_sec=None, lease=None, **kwargs):
        return 1337  # Robot command ID.


class MockRobotStateClient(object):

    def __init__(self):
        self.power_state = robot_state_pb2.PowerState.MOTOR_POWER_STATE_ON
        self.feedback_fn = None
        self.executor = futures.ThreadPoolExecutor(max_workers=2)

    def get_robot_state(self, **kwargs):
        if self.feedback_fn:
            self.feedback_fn()
        power_state = robot_state_pb2.PowerState(motor_power_state=self.power_state)
        return robot_state_pb2.RobotState(power_state=power_state)

    def get_robot_state_async(self, **kwargs):
        return self.executor.submit(self.get_robot_state, **kwargs)


def test_power_on_success():
    mock_client = MockPowerClient()
    timeout = 1.0
    mock_client.feedback_fn = lambda: time.sleep(timeout / 2.0)
    mock_client.response = power_pb2.STATUS_SUCCESS
    power.power_on(mock_client, timeout_sec=timeout, update_frequency=100)


def test_power_on_failure():
    mock_client = MockPowerClient()
    timeout = 1.0
    mock_client.feedback_fn = lambda: time.sleep(timeout / 2.0)
    mock_client.response = power_pb2.STATUS_FAULTED
    with pytest.raises(power.FaultedError, match=r".* Cannot power on due to a fault.*"):
        power.power_on(mock_client, timeout_sec=timeout, update_frequency=100)


@pytest.mark.parametrize('feedback_fn', [None, lambda: time.sleep(3.0)])
def test_power_on_timeout(feedback_fn):
    mock_client = MockPowerClient()
    mock_client.feedback_fn = feedback_fn
    start = time.time()
    timeout = 1.0
    with pytest.raises(power.CommandTimedOutError):
        power.power_on(mock_client, timeout_sec=timeout, update_frequency=100)
    dt = time.time() - start
    assert abs(dt - timeout) < 0.1


def test_emergency_power_off_success():
    mock_client = MockPowerClient()
    timeout = 1.0
    mock_client.feedback_fn = lambda: time.sleep(timeout / 2.0)
    mock_client.response = power_pb2.STATUS_SUCCESS
    power.power_off(mock_client, timeout_sec=timeout, update_frequency=100)


@pytest.mark.parametrize('feedback_fn', [None, lambda: time.sleep(3.0)])
def test_emergency_power_off_timeout(feedback_fn):
    mock_client = MockPowerClient()
    mock_client.feedback_fn = feedback_fn
    start = time.time()
    timeout = 1.0
    with pytest.raises(power.CommandTimedOutError):
        power.power_off(mock_client, timeout_sec=timeout, update_frequency=100)
    dt = time.time() - start
    assert abs(dt - timeout) < 0.1


def test_safe_power_off_success():
    mock_command_client = MockRobotCommandClient()
    mock_state_client = MockRobotStateClient()
    mock_state_client.power_state = robot_state_pb2.PowerState.MOTOR_POWER_STATE_OFF
    timeout = 1.0
    mock_command_client.feedback_fn = lambda: time.sleep(timeout / 2.0)
    mock_command_client.response = power_pb2.STATUS_SUCCESS
    power.safe_power_off(mock_command_client, mock_state_client, timeout, update_frequency=100)


@pytest.mark.parametrize('feedback_fn', [None, lambda: time.sleep(3.0)])
def test_safe_power_off_timeout(feedback_fn):
    mock_command_client = MockRobotCommandClient()
    mock_state_client = MockRobotStateClient()
    mock_state_client.feedback_fn = feedback_fn
    start = time.time()
    timeout = 1.0
    with pytest.raises(power.CommandTimedOutError):
        power.safe_power_off(mock_command_client, mock_state_client, timeout, update_frequency=100)
    dt = time.time() - start
    assert abs(dt - timeout) < 0.1


def test_safe_power_off_motors_success():
    mock_command_client = MockRobotCommandClient()
    mock_state_client = MockRobotStateClient()
    mock_state_client.power_state = robot_state_pb2.PowerState.MOTOR_POWER_STATE_OFF
    timeout = 1.0
    mock_command_client.feedback_fn = lambda: time.sleep(timeout / 2.0)
    mock_command_client.response = power_pb2.STATUS_SUCCESS
    power.safe_power_off_motors(mock_command_client, mock_state_client, timeout,
                                update_frequency=100)


@pytest.mark.parametrize('feedback_fn', [None, lambda: time.sleep(3.0)])
def test_safe_power_off_motors_timeout(feedback_fn):
    mock_command_client = MockRobotCommandClient()
    mock_state_client = MockRobotStateClient()
    mock_state_client.feedback_fn = feedback_fn
    start = time.time()
    timeout = 1.0
    with pytest.raises(power.CommandTimedOutError):
        power.safe_power_off_motors(mock_command_client, mock_state_client, timeout,
                                    update_frequency=100)
    dt = time.time() - start
    assert abs(dt - timeout) < 0.1


def test_safe_power_off_robot_success():
    mock_command_client = MockRobotCommandClient()
    mock_state_client = MockRobotStateClient()
    mock_power_client = MockPowerClient()
    mock_state_client.power_state = robot_state_pb2.PowerState.MOTOR_POWER_STATE_OFF
    timeout = 1.0
    mock_command_client.feedback_fn = lambda: time.sleep(timeout / 4.0)
    mock_command_client.response = power_pb2.STATUS_SUCCESS
    mock_power_client.feedback_fn = lambda: time.sleep(timeout / 4.0)
    mock_power_client.response = power_pb2.STATUS_SUCCESS
    power.safe_power_off_robot(mock_command_client, mock_state_client, mock_power_client, 20,
                               update_frequency=100)


@pytest.mark.parametrize('feedback_fn', [None, lambda: time.sleep(3.0)])
def test_safe_power_off_robot_timeout(feedback_fn):
    mock_command_client = MockRobotCommandClient()
    mock_state_client = MockRobotStateClient()
    mock_power_client = MockPowerClient()
    mock_state_client.feedback_fn = feedback_fn
    timeout = 1.0
    start = time.time()
    with pytest.raises(power.CommandTimedOutError):
        power.safe_power_off_robot(mock_command_client, mock_state_client, mock_power_client,
                                   timeout, update_frequency=100)
    dt = time.time() - start
    assert abs(dt - timeout) < 0.1


def test_safe_power_cycle_robot_success():
    mock_command_client = MockRobotCommandClient()
    mock_state_client = MockRobotStateClient()
    mock_power_client = MockPowerClient()
    mock_state_client.power_state = robot_state_pb2.PowerState.MOTOR_POWER_STATE_OFF
    timeout = 1.0
    mock_command_client.feedback_fn = lambda: time.sleep(timeout / 4.0)
    mock_command_client.response = power_pb2.STATUS_SUCCESS
    mock_power_client.feedback_fn = lambda: time.sleep(timeout / 4.0)
    mock_power_client.response = power_pb2.STATUS_SUCCESS
    power.safe_power_cycle_robot(mock_command_client, mock_state_client, mock_power_client, 20,
                                 update_frequency=100)


@pytest.mark.parametrize('feedback_fn', [None, lambda: time.sleep(3.0)])
def test_safe_power_cycle_robot_timeout(feedback_fn):
    mock_command_client = MockRobotCommandClient()
    mock_state_client = MockRobotStateClient()
    mock_power_client = MockPowerClient()
    mock_state_client.feedback_fn = feedback_fn
    timeout = 1.0
    start = time.time()
    with pytest.raises(power.CommandTimedOutError):
        power.safe_power_cycle_robot(mock_command_client, mock_state_client, mock_power_client,
                                     timeout, update_frequency=100)
    dt = time.time() - start
    assert abs(dt - timeout) < 0.1
