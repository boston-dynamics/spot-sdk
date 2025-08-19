# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tests for the payload registration client."""

from unittest.mock import patch

# import helpers
import pytest

import bosdyn.api.header_pb2 as HeaderProto
import bosdyn.api.payload_pb2 as payload_protos
import bosdyn.api.payload_registration_pb2 as payload_registration_protos
import bosdyn.api.payload_registration_service_pb2_grpc as payload_registration_service
import bosdyn.client.payload_registration
from bosdyn.api.robot_id_pb2 import SoftwareVersion
from bosdyn.client import InternalServerError, UnsetStatusError
from bosdyn.client.error_callback_result import ErrorCallbackResult
from bosdyn.client.payload_registration import (PayloadAlreadyExistsError,
                                                PayloadRegistrationClient,
                                                _payload_registration_error)

from . import error_callback_helpers, helpers

# default registration interval
INTERVAL_SECONDS = 30.0
# default initial retry time for exponential backoff
INITIAL_RETRY_SECONDS = 1.0


def test_payload_registration_error():
    # Test unset header error
    response = payload_registration_protos.RegisterPayloadResponse()
    assert isinstance(_payload_registration_error(response), UnsetStatusError)
    # Test header error
    response.header.error.code = response.header.error.CODE_INTERNAL_SERVER_ERROR
    assert isinstance(_payload_registration_error(response), InternalServerError)
    response.header.error.code = response.header.error.CODE_OK
    # Test unset status error
    assert isinstance(_payload_registration_error(response), UnsetStatusError)
    # Test status error
    response.status = response.STATUS_ALREADY_EXISTS
    assert isinstance(_payload_registration_error(response), PayloadAlreadyExistsError)
    # Test OK
    response.status = response.STATUS_OK
    assert not _payload_registration_error(response)


class MockPayloadRegistrationServicer(
        payload_registration_service.PayloadRegistrationServiceServicer):
    """
    MockPayloadRegistrationServicer provides a basic registry for testing.
    """

    def __init__(self):
        """Create mock that is a pretend payload registry."""
        super(MockPayloadRegistrationServicer, self).__init__()
        self.payloads = {}
        self.error_code = HeaderProto.CommonError.CODE_OK
        self.error_message = None
        self.use_unspecified_status = False
        self.simulate_service_error = False

    def RegisterPayload(self, request, context):
        """Register a payload."""
        response = payload_registration_protos.RegisterPayloadResponse()
        if self.simulate_service_error:
            return None
        helpers.add_common_header(response, request, self.error_code, self.error_message)
        if self.error_code != HeaderProto.CommonError.CODE_OK:
            return response
        if request.payload.GUID not in self.payloads.keys():
            self.payloads[request.payload.GUID] = request.payload
            response.status = payload_registration_protos.RegisterPayloadResponse.STATUS_OK
        else:
            response.status = payload_registration_protos.RegisterPayloadResponse.STATUS_ALREADY_EXISTS
        return response

    def UpdatePayloadVersion(self, request, context):
        """Update the payload version."""
        response = payload_registration_protos.UpdatePayloadVersionResponse()
        if self.simulate_service_error:
            return None
        helpers.add_common_header(response, request, self.error_code, self.error_message)
        if self.error_code != HeaderProto.CommonError.CODE_OK:
            return response
        if request.payload.GUID in self.payloads.keys():
            self.payloads[request.payload.GUID].version.CopyFrom(request.payload.version)
            response.status = payload_registration_protos.UpdatePayloadVersionResponse.STATUS_OK
        else:
            response.status = payload_registration_protos.UpdatePayloadVersionResponse.STATUS_DOES_NOT_EXIST
        return response

    def GetPayloadAuthToken(self, request, context):
        """Get the payload auth token."""
        response = payload_registration_protos.GetPayloadAuthTokenResponse()
        if self.simulate_service_error:
            return None
        helpers.add_common_header(response, request, self.error_code, self.error_message)
        if self.error_code != HeaderProto.CommonError.CODE_OK:
            return response
        if request.payload.GUID in self.payloads.keys():
            response.status = payload_registration_protos.GetPayloadAuthTokenResponse.STATUS_OK
            response.token = 'asdf'
        else:
            response.status = payload_registration_protos.GetPayloadAuthTokenResponse.STATUS_INVALID_CREDENTIALS
        return response

    def UpdatePayloadAttached(self, request, context):
        """Update the payload attached status."""
        response = payload_registration_protos.UpdatePayloadAttachedResponse()
        if self.simulate_service_error:
            return None
        helpers.add_common_header(response, request, self.error_code, self.error_message)
        if self.error_code != HeaderProto.CommonError.CODE_OK:
            return response
        if request.payload.GUID in self.payloads.keys():
            self.payloads[request.payload.GUID].is_enabled = \
                request.request == payload_registration_protos.UpdatePayloadAttachedRequest.REQUEST_ATTACH
            response.status = payload_registration_protos.UpdatePayloadAttachedResponse.STATUS_OK
        else:
            response.status = payload_registration_protos.UpdatePayloadAttachedResponse.STATUS_DOES_NOT_EXIST
        return response


@pytest.fixture(scope='function')
def default_payload_entry():
    return payload_protos.Payload(
        name='test_payload', GUID='test_guid',
        version=SoftwareVersion(major_version=1, minor_version=2, patch_level=3))


def _setup(payload, interval_seconds=INTERVAL_SECONDS, initial_retry_seconds=INITIAL_RETRY_SECONDS,
           callback=None):
    client = PayloadRegistrationClient()
    service = MockPayloadRegistrationServicer()
    server = helpers.setup_client_and_service(
        client, service,
        payload_registration_service.add_PayloadRegistrationServiceServicer_to_server)
    keepalive = bosdyn.client.payload_registration.PayloadRegistrationKeepAlive(
        client, payload, 'asdf', registration_interval_secs=interval_seconds,
        initial_retry_seconds=initial_retry_seconds)
    keepalive.reregistration_error_callback = callback

    return client, service, server, keepalive


def test_keep_alive(default_payload_entry):
    client, service, server, keepalive = _setup(default_payload_entry)

    guid = default_payload_entry.GUID
    assert guid not in service.payloads

    with keepalive.start():
        assert guid in service.payloads

        # Just have some statement inside the "with" context.
        assert service.payloads[guid] == default_payload_entry

    # Now that we've exited the "with" block, the internal thread should have ended, but this
    # this doesn't de-register the payload...
    assert not keepalive.is_alive()
    assert guid in service.payloads


def _run_keepalive_test(payload, mock_time, callback, test_time, interval_seconds=INTERVAL_SECONDS,
                        initial_retry_seconds=INITIAL_RETRY_SECONDS):
    with patch('bosdyn.client.payload_registration.time', mock_time):
        client, service, server, keepalive = _setup(payload, interval_seconds=interval_seconds,
                                                    initial_retry_seconds=initial_retry_seconds,
                                                    callback=callback)
        keepalive._end_reregister_signal = mock_time

        with keepalive.start():
            service.simulate_service_error = True
            mock_time.run(test_time)


def test_keep_alive_update_error_callback_is_invoked_on_rpc_error(default_payload_entry):
    mt = error_callback_helpers.MockTime()
    callback = error_callback_helpers.SimpleCallback(mock_time=mt)

    _run_keepalive_test(default_payload_entry, mt, callback, test_time=INTERVAL_SECONDS * 3.5)

    assert len(callback.times) == 3
    assert callback.times[0] == pytest.approx(INTERVAL_SECONDS)
    t_diff = error_callback_helpers.diff(callback.times)
    assert t_diff == pytest.approx((INTERVAL_SECONDS, INTERVAL_SECONDS))


def test_keep_alive_update_error_callback_resume_normal_operation(default_payload_entry):
    mt = error_callback_helpers.MockTime()
    callback = error_callback_helpers.SimpleCallback(ErrorCallbackResult.RESUME_NORMAL_OPERATION,
                                                     mock_time=mt)

    _run_keepalive_test(default_payload_entry, mt, callback, test_time=INTERVAL_SECONDS * 3.5)

    assert len(callback.times) == 3
    assert callback.times[0] == pytest.approx(INTERVAL_SECONDS)
    t_diff = error_callback_helpers.diff(callback.times)
    assert t_diff == pytest.approx((INTERVAL_SECONDS, INTERVAL_SECONDS))


def test_keep_alive_update_error_callback_retry_immediately(default_payload_entry):
    mt = error_callback_helpers.MockTime()
    callback = error_callback_helpers.PolicySwitchingCallback(
        ErrorCallbackResult.RETRY_IMMEDIATELY, ErrorCallbackResult.RESUME_NORMAL_OPERATION, 3,
        mock_time=mt)

    _run_keepalive_test(default_payload_entry, mt, callback, test_time=INTERVAL_SECONDS * 2.5)

    assert len(callback.times) == 5
    assert callback.times[0] == pytest.approx(INTERVAL_SECONDS)
    t_diff = error_callback_helpers.diff(callback.times)
    assert t_diff == pytest.approx((0.0, 0.0, 0.0, INTERVAL_SECONDS))


def test_keep_alive_update_error_callback_abort(default_payload_entry):
    mt = error_callback_helpers.MockTime()
    callback = error_callback_helpers.SimpleCallback(ErrorCallbackResult.ABORT, mock_time=mt)

    _run_keepalive_test(default_payload_entry, mt, callback, test_time=INTERVAL_SECONDS * 1.5)

    assert len(callback.times) == 1
    assert callback.times[0] == pytest.approx(INTERVAL_SECONDS)


def test_keep_alive_update_error_callback_exponential_backoff(default_payload_entry):
    mt = error_callback_helpers.MockTime()
    callback = error_callback_helpers.SimpleCallback(
        ErrorCallbackResult.RETRY_WITH_EXPONENTIAL_BACK_OFF, mock_time=mt)
    interval_seconds = 30.0
    initial_retry_seconds = 1.0

    # 30 + 1 + 2 + 4 + 8 + 16 = 61
    # + 0.5 * interval_seconds => 76
    _run_keepalive_test(default_payload_entry, mt, callback, test_time=76,
                        interval_seconds=interval_seconds,
                        initial_retry_seconds=initial_retry_seconds)

    assert len(callback.times) == 6
    assert callback.times[0] == pytest.approx(interval_seconds)
    t_diff = error_callback_helpers.diff(callback.times)
    assert t_diff == pytest.approx(tuple(initial_retry_seconds * (2**count) for count in range(5)))


def test_keep_alive_update_error_callback_exponential_backoff_levels_off(default_payload_entry):
    interval_seconds = 30.0
    initial_retry_seconds = 2.0
    mt = error_callback_helpers.MockTime()
    callback = error_callback_helpers.SimpleCallback(
        ErrorCallbackResult.RETRY_WITH_EXPONENTIAL_BACK_OFF, mock_time=mt)

    # 30 + 2 + 4 + 8 + 16 + 30 + 30 = 120
    # + 0.5 * interval_seconds => 135
    _run_keepalive_test(default_payload_entry, mt, callback, interval_seconds=interval_seconds,
                        initial_retry_seconds=initial_retry_seconds, test_time=135)

    assert len(callback.times) == 7
    assert callback.times[0] == pytest.approx(interval_seconds)
    t_diff = error_callback_helpers.diff(callback.times)
    assert t_diff == pytest.approx(
        tuple(initial_retry_seconds * (2**count) for count in range(4)) +
        (interval_seconds, interval_seconds))
