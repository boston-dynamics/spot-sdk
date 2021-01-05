# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from bosdyn.api import lease_pb2
from bosdyn.api import robot_command_pb2
from bosdyn.client.lease import LeaseWalletRequestProcessor


def test_get_lease_state():
    """Check the LeaseWalletRequestProcessor.get_lease_state() method"""
    proc = LeaseWalletRequestProcessor

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
