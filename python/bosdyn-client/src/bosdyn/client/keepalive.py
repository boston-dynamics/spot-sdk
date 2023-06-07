# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client implementation of the Keepalive service."""

from __future__ import print_function

import collections
import logging
import threading
import time
from typing import Callable, List, Union

import bosdyn.client.lease
import bosdyn.util
from bosdyn.api.keepalive import keepalive_pb2, keepalive_service_pb2_grpc
from bosdyn.client.common import (BaseClient, common_header_errors, error_factory, error_pair,
                                  handle_common_header_errors, handle_unset_status_error)
from bosdyn.client.exceptions import ResponseError, RetryableRpcError


class KeepaliveResponseError(ResponseError):
    """Error in Keepalive RPC"""


class InvalidLeaseError(KeepaliveResponseError):
    """A policy's associated lease was not the same, super, or sub lease of the active lease."""


class InvalidPolicyError(KeepaliveResponseError):
    """The specified policy ID was not valid."""


class Policy():
    """Helper class for API Policy."""

    def __init__(self, proto: Union[None, 'keepalive_pb2.Policy'] = None):
        """Constructor"""
        self.policy_proto = proto or keepalive_pb2.Policy()

    @property
    def name(self) -> str:
        """Get or set the name of the Policy"""
        return self.policy_proto.name

    @name.setter
    def name(self, _name: str):
        self.policy_proto.name = _name

    def add_associated_lease(self, lease: Union['bosdyn.client.lease.Lease', 'lease_pb2.Lease']):
        if isinstance(lease, bosdyn.client.lease.Lease):
            self.policy_proto.associated_leases.append(lease.lease_proto)
        else:
            self.policy_proto.associated_leases.append(lease)

    def add_controlled_motors_off_action(self, after: float):
        """Add a 'controlled motors off' action that triggers after specified time (seconds)."""
        self._configure_action(after, lambda action: action.controlled_motors_off.SetInParent())

    def add_immediate_robot_off_action(self, after: float):
        """Add an 'immediate robot off' action that triggers after specified time (seconds)."""
        self._configure_action(after, lambda action: action.immediate_robot_off.SetInParent())

    def add_record_event_action(self, events: List['bosdyn.api.Event'], after: float):
        """Add a 'record event' action that triggers after specified time (seconds)."""

        def copy_events(action):
            for event in events:
                action.record_event.events.add().CopyFrom(event)

        self._configure_action(after, copy_events)

    def add_auto_return_action(self, leases: List['bosdyn.client.lease.Lease'],
                               params: 'bosdyn.api.auto_return.Params', after: float):
        """Add an 'auto return' action that triggers after specified time (seconds)."""

        def copy_params_and_leases(action):
            action.auto_return.leases.extend(lease.lease_proto for lease in leases)
            action.auto_return.params.CopyFrom(params)

        self._configure_action(after, copy_params_and_leases)

    def add_lease_stale_action(self, leases: List['bosdyn.client.lease.Lease'], after: float):
        """Add a 'mark lease stale' action that triggers after specified time (seconds)."""

        def copy_leases(action):
            action.lease_stale.leases.extend(lease.lease_proto for lease in leases)

        self._configure_action(after, copy_leases)

    def shortest_action_delay(self) -> Union[None, float]:
        """Get the shortest delay on an action, or None if no actions are set.

        For example:
        pol = Policy()
        pol.add_controlled_motors_off_action(2.5)
        pol.add_immediate_robot_off_action(1.2)
        assert pol.shortest_action_delay() == 1.2
        """
        delay = None
        for actionafter in self.policy_proto.actions:
            tmp = bosdyn.util.duration_to_seconds(actionafter.after)
            if delay is None or tmp < delay:
                delay = tmp
        return delay

    def _configure_action(self, after: float, set_action: Callable[['keepalive_pb2.ActionAfter'],
                                                                   None]):
        """Helper function to reduce boilerplate of adding an action."""
        action = self.policy_proto.actions.add()
        action.after.CopyFrom(bosdyn.util.seconds_to_duration(after))
        set_action(action)


class KeepaliveClient(BaseClient):
    """A client for the Keepalive service.

    This client is in BETA and may undergo changes in future releases.
    """

    default_service_name = 'keepalive'
    service_type = 'bosdyn.api.keepalive.KeepaliveService'

    def __init__(self):
        super().__init__(keepalive_service_pb2_grpc.KeepaliveServiceStub)
        self._timesync_endpoint = None

    def modify_policy(self, to_add: Union['Policy', 'keepalive_pb2.Policy'] = None,
                      policy_ids_to_remove: List[int] = None, **kwargs):
        """Add given policy and remove policies with given ids."""
        request = self._modify_policy_request(to_add, policy_ids_to_remove)
        return self.call(self._stub.ModifyPolicy, request, None, modify_policy_error, **kwargs)

    def modify_policy_async(self, to_add: Union['Policy', 'keepalive_pb2.Policy'] = None,
                            policy_ids_to_remove: List[int] = None, **kwargs):
        """Async version of the modify_policy() RPC."""
        request = self._modify_policy_request(to_add, policy_ids_to_remove)
        return self.call_async(self._stub.ModifyPolicy, request, None, modify_policy_error,
                               **kwargs)

    def check_in(self, policy_id: int, **kwargs):
        """Check in for given policy_id, refreshing that policy's timer."""
        request = self._check_in_request(policy_id)
        return self.call(self._stub.CheckIn, request, None, check_in_error, **kwargs)

    def check_in_async(self, policy_id: int, **kwargs):
        """Async version of the check_in() RPC."""
        request = self._check_in_request(policy_id)
        return self.call_async(self._stub.CheckIn, request, None, check_in_error, **kwargs)

    def get_status(self, **kwargs):
        """Get status on all policies."""
        request = keepalive_pb2.GetStatusRequest()
        return self.call(self._stub.GetStatus, request, None, common_header_errors, **kwargs)

    def get_status_async(self, **kwargs):
        """Async version of the get_status() RPC."""
        request = keepalive_pb2.GetStatusRequest()
        return self.call_async(self._stub.GetStatus, request, None, common_header_errors, **kwargs)

    @staticmethod
    def _modify_policy_request(to_add: Union['Policy', 'keepalive_pb2.Policy'],
                               policy_ids_to_remove):
        if isinstance(to_add, Policy):
            request = keepalive_pb2.ModifyPolicyRequest(to_add=to_add.policy_proto,
                                                        policy_ids_to_remove=policy_ids_to_remove)
        else:
            request = keepalive_pb2.ModifyPolicyRequest(to_add=to_add,
                                                        policy_ids_to_remove=policy_ids_to_remove)
        return request

    @staticmethod
    def _check_in_request(policy_id):
        request = keepalive_pb2.CheckInRequest(policy_id=policy_id)
        return request


_MODIFY_POLICY_STATUS_TO_ERROR = collections.defaultdict(lambda: (None, None))
_MODIFY_POLICY_STATUS_TO_ERROR.update({
    keepalive_pb2.ModifyPolicyResponse.STATUS_INVALID_LEASE: error_pair(InvalidLeaseError),
    keepalive_pb2.ModifyPolicyResponse.STATUS_INVALID_POLICY_ID: error_pair(InvalidPolicyError)
})

_CHECK_IN_STATUS_TO_ERROR = collections.defaultdict(lambda: (None, None))
_CHECK_IN_STATUS_TO_ERROR.update(
    {keepalive_pb2.CheckInResponse.STATUS_INVALID_POLICY_ID: error_pair(InvalidPolicyError)})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def modify_policy_error(response):
    """ModifyPolicy response to exception."""
    return error_factory(response, response.status,
                         status_to_string=keepalive_pb2.ModifyPolicyResponse.Status.Name,
                         status_to_error=_MODIFY_POLICY_STATUS_TO_ERROR)


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def check_in_error(response):
    """CheckIn response to exception."""
    return error_factory(response, response.status,
                         status_to_string=keepalive_pb2.CheckInResponse.Status.Name,
                         status_to_error=_CHECK_IN_STATUS_TO_ERROR)


#pylint: disable=too-many-instance-attributes
class PolicyKeepalive():
    """Specify a keepalive Policy that should be held to.

    Meant to be used as a context manager. For example:

    client = robot.ensure_client(KeepaliveClient.default_service_name)
    pol = Policy()
    # After 30 seconds of not hearing from this process, turn the robot motors off.
    pol.add_controlled_motors_off_action(30)
    with PolicyKeepalive(client, pol, rpc_interval_seconds=3) as policy_keepalive:
        # A thread will attempt a CheckIn every 3 seconds.
        run_my_code()
    """

    #pylint: disable=too-many-arguments
    def __init__(self, client: KeepaliveClient, policy: Policy, rpc_timeout_seconds: float = None,
                 rpc_interval_seconds: float = None, logger: 'logging.Logger' = None,
                 remove_policy_on_exit: bool = False):

        self.logger = logger or logging.getLogger()
        self.remove_policy_on_exit = remove_policy_on_exit

        self._client = client
        self._policy = policy
        self._policy_id = None
        # If the interval isn't specified manually, try to get the interval from the policy,
        # assuming the user wants to check in a few times before the earliest action.
        # This will raise an exception if there's no action at all.
        self._rpc_interval_seconds = rpc_interval_seconds or policy.shortest_action_delay() / 3
        self._rpc_timeout_seconds = rpc_timeout_seconds

        self._end_check_in_signal = threading.Event()
        self._thread = threading.Thread(target=self._periodic_check_in)
        self._thread.daemon = True

    def __enter__(self):
        """Add this instance's policy and begin checking in."""
        self._policy_id = self._client.modify_policy(to_add=self._policy).added_policy.policy_id
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop checking in, and optionally remove the policy."""
        self.shutdown()
        if self.remove_policy_on_exit:
            self.remove_policy()

    def remove_policy(self):
        """Remove this instance's policy, if it did manage to add one."""
        if self._policy_id:
            self._client.modify_policy(policy_ids_to_remove=[self._policy_id])
            self._policy_id = None

    def start(self):
        """Start the checkin thread."""
        self._thread.start()

    def shutdown(self):
        """Stop the checkin thread and block until it ends."""
        self._end_periodic_check_in()
        self._thread.join()

    def _check_in(self):
        self._client.check_in(self._policy_id, timeout=self._rpc_timeout_seconds)

    def _end_periodic_check_in(self):
        self._end_check_in_signal.set()

    def _periodic_check_in(self):
        while True:
            exec_start = time.time()

            try:
                self._check_in()
            except RetryableRpcError as exc:
                self.logger.warning('exception during check-in:\n%s\n', exc)
                self.logger.info('continuing check-in')

            # How long did the RPC and processing of said RPC take?
            exec_seconds = time.time() - exec_start

            # Block and wait for the stop signal. If we receive it within the check-in period,
            # leave the loop. This check must be at the end of the loop!
            # Wait up to self._check_in_period seconds, minus the RPC processing time.
            # (values < 0 are OK and will return immediately)
            if self._end_check_in_signal.wait(self._rpc_interval_seconds - exec_seconds):
                break
        self.logger.info('Policy check-in stopped')


def remove_all_policies(keepalive_client, attempts=1):
    """Remove all policies on the robot.

    Optionally do this over a few attempts, in case other things are also removing policies.
    """
    last_exc = None
    for i in range(attempts):
        if last_exc:
            time.sleep(0.5)
            last_exc = None

        all_policy_ids = [p.policy_id for p in keepalive_client.get_status().status]
        if all_policy_ids:
            try:
                keepalive_client.modify_policy(policy_ids_to_remove=all_policy_ids)
            except InvalidPolicyError as exc:
                last_exc = exc
            else:
                break
        else:
            break
    if last_exc:
        raise last_exc
