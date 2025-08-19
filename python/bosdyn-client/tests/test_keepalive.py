# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import time
from unittest import mock

import pytest
from google.protobuf.timestamp_pb2 import Timestamp

from bosdyn.api import header_pb2, lease_pb2
from bosdyn.api.auto_return import auto_return_pb2
from bosdyn.api.keepalive import keepalive_pb2
from bosdyn.api.keepalive.keepalive_service_pb2_grpc import (KeepaliveServiceServicer,
                                                             add_KeepaliveServiceServicer_to_server)
from bosdyn.client.error_callback_result import ErrorCallbackResult
from bosdyn.client.exceptions import InvalidRequestError
from bosdyn.client.keepalive import InvalidLeaseError, KeepaliveClient, Policy, PolicyKeepalive
from bosdyn.client.lease import Lease

from . import helpers
from .error_callback_helpers import MockTime, PolicySwitchingCallback, SimpleCallback, diff
from .util import mock_stub_response, set_common_response_header

MOCK_CHECK_IN_CLIENT_NAME = 'mock-client'
MOCK_POLICY_ID = 12345
MOCK_LAST_CHECK_IN = Timestamp(seconds=1600000000, nanos=54321)


def default_present_policy():
    policy = Policy()
    policy.name = 'default policy'
    policy.add_associated_lease(lease_pb2.Lease(sequence=[0], resource='resource'))
    policy.add_immediate_robot_off_action(1)
    policy.add_controlled_motors_off_action(2)
    return policy


def build_mocked_stub_client(modify_policy_resp=None, check_in_resp=None, get_status_resp=None):
    client = KeepaliveClient()
    if modify_policy_resp is None:
        modify_policy_resp = keepalive_pb2.ModifyPolicyResponse()
        modify_policy_resp.status = keepalive_pb2.ModifyPolicyResponse.STATUS_OK
        modify_policy_resp.added_policy.policy_id = MOCK_POLICY_ID
        set_common_response_header(modify_policy_resp.header)
    if check_in_resp is None:
        check_in_resp = keepalive_pb2.CheckInResponse()
        check_in_resp.status = keepalive_pb2.CheckInResponse.STATUS_OK
        set_common_response_header(check_in_resp.header)
    if get_status_resp is None:
        get_status_resp = keepalive_pb2.GetStatusResponse()
        set_common_response_header(get_status_resp.header)
        status = get_status_resp.status.add()
        status.policy_id = MOCK_POLICY_ID
        status.policy.CopyFrom(default_present_policy().policy_proto)
        status.last_checkin.CopyFrom(MOCK_LAST_CHECK_IN)
        status.client_name = MOCK_CHECK_IN_CLIENT_NAME

    client._stub = mock.Mock('keepalive-client-stub-mock')
    client._stub.ModifyPolicy = mock.Mock()
    client._stub.CheckIn = mock.Mock()
    client._stub.GetStatus = mock.Mock()
    mock_stub_response(client._stub.ModifyPolicy, modify_policy_resp)
    mock_stub_response(client._stub.CheckIn, check_in_resp)
    mock_stub_response(client._stub.GetStatus, get_status_resp)

    return client


def test_policy():
    policy = Policy()

    policy.name = 'default policy'
    assert policy.policy_proto.name == policy.name

    lease = Lease(lease_pb2.Lease(sequence=[0], resource='resource'))
    policy.add_associated_lease(lease)
    assert policy.policy_proto.associated_leases[0] == lease.lease_proto

    assert policy.shortest_action_delay() is None

    policy.add_controlled_motors_off_action(1)
    assert policy.policy_proto.actions[0].WhichOneof('action') == 'controlled_motors_off'
    policy.add_immediate_robot_off_action(2)
    assert policy.policy_proto.actions[0].WhichOneof('action') == 'controlled_motors_off'
    assert policy.policy_proto.actions[1].WhichOneof('action') == 'immediate_robot_off'

    assert policy.shortest_action_delay() == 1

    auto_return_params = auto_return_pb2.Params(max_displacement=10)
    policy.add_auto_return_action([lease], auto_return_params, 0.2)
    assert policy.policy_proto.actions[2].WhichOneof('action') == 'auto_return'
    assert (policy.policy_proto.actions[2].auto_return.leases[0].SerializeToString() ==
            lease.lease_proto.SerializeToString())
    assert (policy.policy_proto.actions[2].auto_return.params.SerializeToString() ==
            auto_return_params.SerializeToString())
    assert policy.shortest_action_delay() == 0.2


@pytest.mark.timeout(1)
def test_context_mgr_basic():
    client = build_mocked_stub_client()
    policy = default_present_policy()
    logger = mock.Mock()
    with PolicyKeepalive(client, policy, logger=logger) as pka:
        # Policy should be added immediately.
        client._stub.ModifyPolicy.assert_called_once()
        assert pka._policy_id == MOCK_POLICY_ID
        assert pka._rpc_interval_seconds < policy.shortest_action_delay()
        while client._stub.CheckIn.call_count < 0:
            time.sleep(0.05)


def test_modify_policy_invalid_lease():
    modify_policy_resp = keepalive_pb2.ModifyPolicyResponse()
    modify_policy_resp.status = keepalive_pb2.ModifyPolicyResponse.STATUS_INVALID_LEASE
    set_common_response_header(modify_policy_resp.header)
    client = build_mocked_stub_client(modify_policy_resp=modify_policy_resp)
    with pytest.raises(InvalidLeaseError):
        client.modify_policy(keepalive_pb2.Policy())
    with pytest.raises(InvalidLeaseError):
        client.modify_policy_async(keepalive_pb2.Policy()).result()


def test_modify_policy_invalid_request():
    modify_policy_resp = keepalive_pb2.ModifyPolicyResponse()
    set_common_response_header(modify_policy_resp.header,
                               header_pb2.CommonError.CODE_INVALID_REQUEST)
    client = build_mocked_stub_client(modify_policy_resp=modify_policy_resp)
    with pytest.raises(InvalidRequestError):
        client.modify_policy(keepalive_pb2.Policy())
    with pytest.raises(InvalidRequestError):
        client.modify_policy_async(keepalive_pb2.Policy()).result()




class MockKeepaliveServicer(KeepaliveServiceServicer):

    def __init__(self):
        self.simulate_service_error = False
        self.error_code = header_pb2.CommonError.CODE_OK
        self.error_message = None
        self.id_counter = 1
        self.live_policies = {}
        self.modify_count = 0
        self.checkin_count = 0

    def CheckIn(self, request, context):
        self.checkin_count += 1
        if self.simulate_service_error:
            return None
        response = keepalive_pb2.CheckInResponse()
        helpers.add_common_header(response, request, self.error_code, self.error_message)
        if self.error_code != header_pb2.CommonError.CODE_OK:
            return response
        if request.policy_id in self.live_policies:
            response.status = keepalive_pb2.CheckInResponse.STATUS_OK
        else:
            response.status = keepalive_pb2.CheckInResponse.STATUS_INVALID_POLICY_ID
        return response

    def ModifyPolicy(self, request, context):
        self.modify_count += 1
        response = keepalive_pb2.ModifyPolicyResponse()
        helpers.add_common_header(response, request, self.error_code, self.error_message)
        if self.error_code != header_pb2.CommonError.CODE_OK:
            return response
        response.status = keepalive_pb2.ModifyPolicyResponse.STATUS_OK
        if request.HasField('to_add'):
            policy_id = self.id_counter
            self.id_counter += 1
            live_policy = keepalive_pb2.LivePolicy(policy_id=policy_id, policy=request.to_add)
            self.live_policies[policy_id] = live_policy
            response.added_policy.CopyFrom(live_policy)
        for policy_id in request.policy_ids_to_remove:
            if policy_id in self.live_policies:
                del self.live_policies[policy_id]
            else:
                response.status = keepalive_pb2.ModifyPolicyResponse.STATUS_INVALID_POLICY_ID
        return response

    def GetStatus(self, request, context):
        response = keepalive_pb2.GetStatusResponse()
        helpers.add_common_header(response, request, self.error_code, self.error_message)
        if self.error_code != header_pb2.CommonError.CODE_OK:
            return response
        response.status.extend(self.live_policies.values())
        return response


@pytest.fixture(scope='function')
def default_policy():
    return Policy(keepalive_pb2.Policy(name='default policy'))


INTERVAL_SECONDS = 10.0
INITIAL_RETRY_SECONDS = 1.0


def _setup(policy, interval_seconds=INTERVAL_SECONDS, initial_retry_seconds=INITIAL_RETRY_SECONDS,
           callback=None, remove_policy_on_exit=False):
    client = KeepaliveClient()
    service = MockKeepaliveServicer()
    server = helpers.setup_client_and_service(client, service,
                                              add_KeepaliveServiceServicer_to_server)
    keepalive = PolicyKeepalive(client, policy, rpc_interval_seconds=interval_seconds,
                                initial_retry_seconds=initial_retry_seconds,
                                remove_policy_on_exit=remove_policy_on_exit)
    keepalive.keepalive_error_callback = callback

    return client, service, server, keepalive


def test_periodic_checkin_setup(default_policy):
    client, service, server, keepalive = _setup(default_policy)

    assert service.modify_count == 0
    assert service.checkin_count == 0
    with keepalive:
        assert service.modify_count == 1
        assert service.checkin_count == 0

    # Now that we've exited the "with" block, the internal thread should have ended, but this
    # this doesn't de-register the policy...
    current_policies = client.get_status().status
    assert len(current_policies) == 1
    assert current_policies[0].policy_id == keepalive._policy_id


def test_periodic_checkin_setup_with_cleanup(default_policy):
    client, service, server, keepalive = _setup(default_policy, remove_policy_on_exit=True)

    assert service.modify_count == 0
    assert service.checkin_count == 0
    with keepalive:
        assert service.modify_count == 1
        assert service.checkin_count == 0
        assert keepalive._policy_id is not None

    # Now that we've exited the "with" block, the internal thread should have ended, but this
    # this doesn't de-register the policy...
    current_policies = client.get_status().status
    assert len(current_policies) == 0
    assert keepalive._policy_id is None


def test_periodic_checkin_periodically_checks_in(default_policy):
    mt = MockTime()
    callback = SimpleCallback(mock_time=mt)

    with mock.patch('bosdyn.client.keepalive.time', mt):
        client, service, server, keepalive = _setup(default_policy, callback=callback)
        keepalive._end_check_in_signal = mt

        with keepalive:
            mt.run(INTERVAL_SECONDS * 10.5)

    assert service.modify_count == 1
    assert service.checkin_count == 10


def _run_periodic_checkin_test(policy, mock_time, callback, test_time,
                               interval_seconds=INTERVAL_SECONDS,
                               initial_retry_seconds=INITIAL_RETRY_SECONDS):
    with mock.patch('bosdyn.client.keepalive.time', mock_time):
        client, service, server, keepalive = _setup(policy, interval_seconds=interval_seconds,
                                                    initial_retry_seconds=initial_retry_seconds,
                                                    callback=callback)
        keepalive._end_check_in_signal = mock_time

        with keepalive:
            service.simulate_service_error = True
            mock_time.run(test_time)


def test_update_error_callback_is_invoked_on_rpc_error(default_policy):
    mt = MockTime()
    callback = SimpleCallback(mock_time=mt)

    _run_periodic_checkin_test(default_policy, mt, callback, test_time=INTERVAL_SECONDS * 3.5)

    assert len(callback.times) == 3
    assert callback.times[0] == pytest.approx(INTERVAL_SECONDS)
    t_diff = diff(callback.times)
    assert t_diff == pytest.approx((INTERVAL_SECONDS, INTERVAL_SECONDS))


def test_periodic_checkin_error_callback_resume_normal_operation(default_policy):
    mt = MockTime()
    callback = SimpleCallback(ErrorCallbackResult.RESUME_NORMAL_OPERATION, mock_time=mt)

    _run_periodic_checkin_test(default_policy, mt, callback, test_time=INTERVAL_SECONDS * 3.5)

    assert len(callback.times) == 3
    assert callback.times[0] == pytest.approx(INTERVAL_SECONDS)
    t_diff = diff(callback.times)
    assert t_diff == pytest.approx((INTERVAL_SECONDS, INTERVAL_SECONDS))


def test_periodic_checkin_error_callback_retry_immediately(default_policy):
    mt = MockTime()
    callback = PolicySwitchingCallback(ErrorCallbackResult.RETRY_IMMEDIATELY,
                                       ErrorCallbackResult.RESUME_NORMAL_OPERATION, 3, mock_time=mt)

    _run_periodic_checkin_test(default_policy, mt, callback, test_time=INTERVAL_SECONDS * 2.5)

    assert len(callback.times) == 5
    assert callback.times[0] == pytest.approx(INTERVAL_SECONDS)
    t_diff = diff(callback.times)
    assert t_diff == pytest.approx((0.0, 0.0, 0.0, INTERVAL_SECONDS))


def test_keep_alive_update_error_callback_abort(default_policy):
    mt = MockTime()
    callback = SimpleCallback(ErrorCallbackResult.ABORT, mock_time=mt)

    _run_periodic_checkin_test(default_policy, mt, callback, test_time=INTERVAL_SECONDS * 1.5)

    assert len(callback.times) == 1
    assert callback.times[0] == pytest.approx(INTERVAL_SECONDS)


def test_keep_alive_update_error_callback_exponential_backoff(default_policy):
    mt = MockTime()
    callback = SimpleCallback(ErrorCallbackResult.RETRY_WITH_EXPONENTIAL_BACK_OFF, mock_time=mt)
    interval_seconds = 30.0
    initial_retry_seconds = 1.0

    # 30 + 1 + 2 + 4 + 8 + 16 = 61
    # + 0.5 * interval_seconds => 76
    _run_periodic_checkin_test(default_policy, mt, callback, test_time=76,
                               interval_seconds=interval_seconds,
                               initial_retry_seconds=initial_retry_seconds)

    assert len(callback.times) == 6
    assert callback.times[0] == pytest.approx(interval_seconds)
    t_diff = diff(callback.times)
    assert t_diff == pytest.approx(tuple(initial_retry_seconds * (2**count) for count in range(5)))


def test_keep_alive_update_error_callback_exponential_backoff_levels_off(default_policy):
    interval_seconds = 30.0
    initial_retry_seconds = 2.0
    mt = MockTime()
    callback = SimpleCallback(ErrorCallbackResult.RETRY_WITH_EXPONENTIAL_BACK_OFF, mock_time=mt)

    # 30 + 2 + 4 + 8 + 16 + 30 + 30 = 120
    # + 0.5 * interval_seconds => 135
    _run_periodic_checkin_test(default_policy, mt, callback, interval_seconds=interval_seconds,
                               initial_retry_seconds=initial_retry_seconds, test_time=135)

    assert len(callback.times) == 7
    assert callback.times[0] == pytest.approx(interval_seconds)
    t_diff = diff(callback.times)
    assert t_diff == pytest.approx(
        tuple(initial_retry_seconds * (2**count) for count in range(4)) +
        (interval_seconds, interval_seconds))
