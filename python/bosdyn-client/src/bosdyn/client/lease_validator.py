# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Lease validator tracks lease usage in intermediate services."""

import copy
import logging
import threading

from bosdyn.api import lease_pb2
from bosdyn.client.exceptions import Error
from bosdyn.client.lease import Lease, LeaseClient
from bosdyn.client.lease_resource_hierarchy import ResourceHierarchy

_LOGGER = logging.getLogger(__name__)


class LeaseValidator:
    """Lease validator tracks lease usage in intermediate services.

    Track the most recent leases seen for each lease resource and test incoming leases against this
    state.

    Args:
        robot (Robot): The robot object for which leases are associated to.
    """

    def __init__(self, robot):
        # Map tracking the lease resource and the current active lease.
        self.active_lease_map = {}

        # Lock for the active lease map.
        self.active_lease_map_lock = threading.Lock()

        # Blocking call to determine the lease resource tree from the robot.
        self.hierarchy = None
        if robot is not None:
            try:
                lease_client = robot.ensure_client(LeaseClient.default_service_name)
                list_leases_response = lease_client.list_leases_full()
            except Exception:
                # TODO should we be catching exceptions here? Is this the right exception to catch?
                # Some unit testing depends on this behavior.
                _LOGGER.exception(
                    "Unable to set the resource hierarchy for robot %s's LeaseValidator.",
                    robot.host)
            else:
                # Resource hierarchy found from the robot! Use it for better validation of incoming
                # leases.
                self.hierarchy = ResourceHierarchy(list_leases_response.resource_tree)

    def get_active_lease(self, resource):
        """Get the latest active lease.

        Args:
            resource(string): the resource for the specific lease to be returned.

        Returns:
            A Lease class object representing the most recent lease for the
            requested resource, or None if no lease has been seen.
        """
        with self.active_lease_map_lock:
            return self._get_active_lease_locked(resource)

    def test_active_lease(self, incoming_lease, allow_super_leases, allow_different_epoch=False):
        """Compare an incoming lease to the latest active lease.

        Args:
            incoming_lease(Lease object or lease_pb2.Lease): The incoming lease to test.
            allow_super_leases(boolean): Should the comparison function consider a super lease as
                ok.

        Returns:
            The LeaseUseResult proto message representing if the incoming lease is ok.
        """
        lease_use_results = lease_pb2.LeaseUseResult()
        with self.active_lease_map_lock:
            status, previous_lease = self._test_active_lease_helper(incoming_lease,
                                                                    allow_super_leases,
                                                                    allow_different_epoch)
            lease_use_results.status = status
            self._populate_base_lease_use_results_locked(incoming_lease, previous_lease,
                                                         lease_use_results)
        return lease_use_results

    def test_and_set_active_lease(self, incoming_lease, allow_super_leases,
                                  allow_different_epoch=False):
        """Compare an incoming lease to the latest active lease, and if it is ok then set it as
        the latest lease.

        Args:
            incoming_lease(Lease object or lease_pb2.Lease): The incoming lease to test.
            allow_super_leases(boolean): Should the comparison function consider a super lease as
                ok.

        Returns:
            The LeaseUseResult proto message representing if the incoming lease is ok. Additionally,
            if the result is STATUS_OK, then update the latest active lease to this incoming lease.
        """
        lease_use_results = lease_pb2.LeaseUseResult()
        with self.active_lease_map_lock:
            status, previous_lease = self._test_active_lease_helper(incoming_lease,
                                                                    allow_super_leases,
                                                                    allow_different_epoch)
            if status == lease_pb2.LeaseUseResult.STATUS_OK:
                self._set_active_lease_locked(incoming_lease)
            lease_use_results.status = status
            self._populate_base_lease_use_results_locked(incoming_lease, previous_lease,
                                                         lease_use_results)
        return lease_use_results

    def _get_active_lease_locked(self, resource):
        """Locked method to get the active lease for a resource.

        Note: The active_lease_map_lock must be locked!
        """
        assert self.active_lease_map_lock.locked(), "Must have active_lease_map_lock locked."
        if self.hierarchy is not None and not self.hierarchy.has_resource(resource):
            return None
        if resource not in self.active_lease_map:
            return None
        return self.active_lease_map[resource]

    def _test_active_lease_helper(self, incoming_lease, allow_super_lease,
                                  allow_different_epoch=False):  # pylint: disable=too-many-return-statements,too-many-branches
        """Helper function to validate the lease and compare it to the active lease.

        Returns:
            A tuple with the LeaseUseResult.Status and the Lease object representing the
            previous/last active lease.
        """
        # Convert the lease into a Lease class object.
        if isinstance(incoming_lease, lease_pb2.Lease):
            if not Lease.is_valid_proto(incoming_lease):
                return lease_pb2.LeaseUseResult.STATUS_INVALID_LEASE, None
            incoming_lease = Lease(incoming_lease)
        else:
            if not incoming_lease.is_valid_lease():
                return lease_pb2.LeaseUseResult.STATUS_INVALID_LEASE, None

        # Check if the lease resource is in the hierarchy.
        resc_of_interest = incoming_lease.lease_proto.resource
        if self.hierarchy is not None:
            if not self.hierarchy.has_resource(resc_of_interest):
                return lease_pb2.LeaseUseResult.STATUS_UNMANAGED, None

            # Determine the latest maximum lease.
            current_lease_proto = self._maximum_lease(
                self.hierarchy.get_hierarchy(resc_of_interest))
            if not Lease.is_valid_proto(current_lease_proto):
                # If the current lease proto is invalid/empty, then we will accept the incoming
                # lease so mark it as ok!
                return lease_pb2.LeaseUseResult.STATUS_OK, None
            current_lease = Lease(current_lease_proto)
        else:
            # If for some reason we don't have the hierarchy, then fall back on just the active
            # lease map.
            if resc_of_interest not in self.active_lease_map:
                # If the current lease proto is invalid/empty, then we will accept the incoming
                # lease so mark it as ok!
                return lease_pb2.LeaseUseResult.STATUS_OK, None
            current_lease = self.active_lease_map[resc_of_interest]

        compare_result = incoming_lease.compare(current_lease)
        assert compare_result != Lease.CompareResult.DIFFERENT_RESOURCES, \
            "Mismatched resources (%s vs %s) when comparing leases in the LeaseValidator." % (
                incoming_lease.lease_proto.resource, current_lease.lease_proto.resource
            )
        if compare_result is Lease.CompareResult.DIFFERENT_EPOCHS:  # pylint: disable=no-else-return
            if allow_different_epoch:
                return lease_pb2.LeaseUseResult.STATUS_OK, current_lease
            else:
                return lease_pb2.LeaseUseResult.STATUS_WRONG_EPOCH, current_lease

        elif compare_result is Lease.CompareResult.SUPER_LEASE:
            if allow_super_lease:  # pylint: disable=no-else-return
                return lease_pb2.LeaseUseResult.STATUS_OK, current_lease
            else:
                # If super leases are not allowed, then mark this as older.
                return lease_pb2.LeaseUseResult.STATUS_OLDER, current_lease
        elif compare_result is Lease.CompareResult.OLDER:
            return lease_pb2.LeaseUseResult.STATUS_OLDER, current_lease
        elif compare_result in (Lease.CompareResult.SUB_LEASE, Lease.CompareResult.SAME,
                                Lease.CompareResult.NEWER):
            return lease_pb2.LeaseUseResult.STATUS_OK, current_lease

        # We should not end up here since all compare results should be enumerated.
        assert False, ("The compare_result case [%s] is unhandled by the LeaseValidator." %
                       compare_result)

    def _set_active_lease(self, incoming_lease):
        """Helper set the active lease tracked for the specific lease resource."""
        with self.active_lease_map_lock:
            self._set_active_lease_locked(incoming_lease)

    def _set_active_lease_locked(self, incoming_lease):
        """Locked helper which updates the active lease tracked for the specific lease resource.

        Note: The active_lease_map_lock must be locked!
        """
        assert self.active_lease_map_lock.locked(), "Must have active_lease_map_lock locked."
        # Convert the lease into a Lease class object.
        if isinstance(incoming_lease, lease_pb2.Lease):
            incoming_lease = Lease(incoming_lease)
        self.active_lease_map[incoming_lease.lease_proto.resource] = incoming_lease
        if self.hierarchy is not None:
            for leaf in self.hierarchy.leaf_resources():
                leaf_lease_proto = copy.deepcopy(incoming_lease.lease_proto)
                leaf_lease_proto.resource = leaf
                self.active_lease_map[leaf] = Lease(leaf_lease_proto)

    def _populate_base_lease_use_results_locked(self, attempted_lease, previous_lease,
                                                mutable_lease_use_results):
        """Updates a mutable copy of the LeaseUseResult to fill out the debug fields.

        Note: The active_lease_map_lock must be locked!

        Args:
            attempted_lease (Lease class object): The incoming/requested lease.
            previous_lease (Lease class object): Optional previous lease that was last considered
                the latest active lease.
            mutable_lease_use_results(lease_pb2.LeaseUseResult):
        """
        assert self.active_lease_map_lock.locked(), "Must have active_lease_map_lock locked."
        if isinstance(attempted_lease, Lease):
            attempted_lease = attempted_lease.lease_proto

        mutable_lease_use_results.attempted_lease.CopyFrom(attempted_lease)

        if previous_lease is not None:
            mutable_lease_use_results.previous_lease.CopyFrom(previous_lease.lease_proto)

        latest_known_lease = self._get_active_lease_locked(attempted_lease.resource)
        if latest_known_lease is not None:
            mutable_lease_use_results.latest_known_lease.CopyFrom(latest_known_lease.lease_proto)

        if self.hierarchy is not None:
            for leaf in self.hierarchy.leaf_resources():
                if leaf in self.active_lease_map:
                    mutable_lease_use_results.latest_resources.extend(
                        [self.active_lease_map[leaf].lease_proto])

    def _maximum_lease(self, hierarchy):
        lease_proto = lease_pb2.Lease()
        lease_proto.resource = hierarchy.get_resource()

        # Determine the epoch for the maximum lease proto.
        for leaf in hierarchy.leaf_resources():
            if leaf in self.active_lease_map:
                leaf_lease = self.active_lease_map[leaf]
                if not leaf_lease.is_valid_lease():
                    continue
                # Set the epoch if it is not yet set.
                if lease_proto.epoch == "":
                    lease_proto.epoch = leaf_lease.lease_proto.epoch

                result = Lease(lease_proto,
                               ignore_is_valid_check=True).compare(leaf_lease,
                                                                   ignore_resources=True)
                if result in (Lease.CompareResult.OLDER, Lease.CompareResult.SUPER_LEASE):
                    lease_proto.client_names[:] = leaf_lease.lease_proto.client_names
                    lease_proto.sequence[:] = leaf_lease.lease_proto.sequence
        return lease_proto


class LeaseValidatorResponseProcessor:  # pylint: disable=too-few-public-methods
    """LeaseValidatorResponseProcessor updates the lease validator using the
    latest_known_lease from the response's LeaseUseResult."""

    def __init__(self, lease_validator):
        """
        Args:
            lease_validator (LeaseValidator): validator for a specific robot to be updated.
        """
        self.lease_validator = lease_validator

    def mutate(self, response):
        """Update the lease validator if a response has a lease_use_result."""
        try:
            # AttributeError will occur if the response does not have a field named
            # 'lease_use_result'
            lease_use_results = [response.lease_use_result]
        except AttributeError:
            try:
                # AttributeError will occur if the request class does not have a field named
                # 'lease_use_results'
                lease_use_results = response.lease_use_results
            except AttributeError:
                # If we get here, there's no 'lease' field nor a 'leases' field for usage results.
                # There are responses that do not have either field, so just return.
                return

        for result in lease_use_results:
            if result.status == lease_pb2.LeaseUseResult.STATUS_UNKNOWN:
                continue

            self.lease_validator.test_and_set_active_lease(result.latest_known_lease,
                                                           allow_super_leases=False)
