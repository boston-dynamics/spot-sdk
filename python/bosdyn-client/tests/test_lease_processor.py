# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import pytest

from bosdyn.api import lease_pb2, robot_command_pb2
from bosdyn.api.graph_nav import graph_nav_pb2
from bosdyn.client import lease
from bosdyn.client.lease import LeaseWalletRequestProcessor


def test_get_lease_state():
    """Check the LeaseWalletRequestProcessor.get_lease_state() method"""
    single_lease_unset_request = robot_command_pb2.RobotCommandRequest()
    single_lease_set_request = robot_command_pb2.RobotCommandRequest(lease=lease_pb2.Lease())
    no_lease_request = robot_command_pb2.RobotCommandFeedbackRequest()

    multi_lease, skip_mut = LeaseWalletRequestProcessor.get_lease_state(single_lease_unset_request)
    assert not multi_lease
    assert not skip_mut

    multi_lease, skip_mut = LeaseWalletRequestProcessor.get_lease_state(single_lease_set_request)
    assert not multi_lease
    assert skip_mut

    multi_lease, skip_mut = LeaseWalletRequestProcessor.get_lease_state(no_lease_request)
    assert multi_lease is None
    assert skip_mut


def test_resource_list():
    """Test that using the resource list does the right thing."""

    # Set up a lease wallet with an imaginary resource
    resource_name = 'test_resource'
    wallet = lease.LeaseWallet()
    wallet.client_name = 'test'
    lease_proto = lease.LeaseProto(resource=resource_name)
    lease_proto.sequence.append(1)
    lease_proto.client_names.append('root')
    lease_obj = lease.Lease(lease_proto)
    wallet.add(lease_obj)

    proc = LeaseWalletRequestProcessor(wallet, resource_list=(resource_name,))

    # Processor defaults to using our lease resource.
    request = graph_nav_pb2.NavigateToRequest()
    proc.mutate(request)

    assert len(request.leases) == 1
    assert request.leases[0].resource == resource_name
    assert request.leases[0].sequence == [1, 1]

    # Intentionally tell it that we *don't* want leases set.
    request = graph_nav_pb2.NavigateToRequest()
    proc.mutate(request, resource_list=())

    assert len(request.leases) == 0

    # Request a lease we don't have in the wallet.
    request = graph_nav_pb2.NavigateToRequest()
    with pytest.raises(lease.NoSuchLease):
        proc.mutate(request, resource_list=('body',))

    # Explicit lease overrides resource_list
    request = graph_nav_pb2.NavigateToRequest()
    request.leases.add().CopyFrom(lease_proto)
    proc.mutate(request, resource_list=('body',))

    assert len(request.leases) == 1
    assert request.leases[0] == lease_proto
