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
from bosdyn.client.exceptions import InvalidRequestError
from bosdyn.client.keepalive import (InvalidLeaseError, InvalidPolicyError, KeepaliveClient, Policy,
                                     PolicyKeepalive)
from bosdyn.client.lease import Lease

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


