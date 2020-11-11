# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Lease clients"""

import collections
import enum
import logging
import threading
import time

from bosdyn.api.lease_pb2 import Lease as LeaseProto
from bosdyn.api.lease_pb2 import AcquireLeaseRequest
from bosdyn.api.lease_pb2 import AcquireLeaseResponse
from bosdyn.api.lease_pb2 import ListLeasesRequest
from bosdyn.api.lease_pb2 import RetainLeaseRequest
from bosdyn.api.lease_pb2 import ReturnLeaseRequest
from bosdyn.api.lease_pb2 import ReturnLeaseResponse
from bosdyn.api.lease_pb2 import TakeLeaseRequest
from bosdyn.api.lease_pb2 import TakeLeaseResponse
from bosdyn.api.lease_service_pb2_grpc import LeaseServiceStub

from . import common
from .exceptions import ResponseError


class LeaseResponseError(ResponseError):
    """General class of errors for LeaseResponseError service."""


class InvalidLeaseError(LeaseResponseError):
    """The provided lease is invalid."""


class DisplacedLeaseError(LeaseResponseError):
    """Lease is older than the current lease."""


class InvalidResourceError(LeaseResponseError):
    """Resource is not known to the LeaseService."""


class NotAuthoritativeServiceError(LeaseResponseError):
    """LeaseService is not authoritative so Acquire should not work."""


class ResourceAlreadyClaimedError(LeaseResponseError):
    """Use TakeLease method to forcefully grab the already claimed lease."""


class RevokedLeaseError(LeaseResponseError):
    """Lease is stale cause lease holder did not check in regularly enough."""


class UnmanagedResourceError(LeaseResponseError):
    """LeaseService does not manage this resource."""


class WrongEpochError(LeaseResponseError):
    """Lease is for the wrong epoch."""


class NotActiveLeaseError(LeaseResponseError):
    """Lease is not the active lease."""


class Error(Exception):
    """Base non-response error for lease module."""


class NoSuchLease(Error):
    """The requested lease does not exist."""
    def __init__(self, resource):
        self.resource = resource

    def __str__(self):
        return 'No lease for resource "{}"'.format(self.resource)


class LeaseNotOwnedByWallet(Error):
    """The lease is not owned by the wallet."""
    def __init__(self, resource, lease_state):
        self.resource = resource
        self.lease_state = lease_state

    def __str__(self):
        try:
            state = self.lease_state.lease_status
        except AttributeError:
            state = '<unknown>'
        return 'Lease on "{}" has state ({})'.format(self.resource, state)


_ACQUIRE_LEASE_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_ACQUIRE_LEASE_STATUS_TO_ERROR.update({
    AcquireLeaseResponse.STATUS_OK: (None, None),
    AcquireLeaseResponse.STATUS_RESOURCE_ALREADY_CLAIMED: (ResourceAlreadyClaimedError,
                                                           ResourceAlreadyClaimedError.__doc__),
    AcquireLeaseResponse.STATUS_INVALID_RESOURCE: (InvalidResourceError,
                                                   InvalidResourceError.__doc__),
    AcquireLeaseResponse.STATUS_NOT_AUTHORITATIVE_SERVICE: (NotAuthoritativeServiceError,
                                                            NotAuthoritativeServiceError.__doc__),
})

_TAKE_LEASE_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_TAKE_LEASE_STATUS_TO_ERROR.update({
    TakeLeaseResponse.STATUS_OK: (None, None),
    TakeLeaseResponse.STATUS_INVALID_RESOURCE: (InvalidResourceError, InvalidResourceError.__doc__),
    TakeLeaseResponse.STATUS_NOT_AUTHORITATIVE_SERVICE: (NotAuthoritativeServiceError,
                                                         NotAuthoritativeServiceError.__doc__),
})

_RETURN_LEASE_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_RETURN_LEASE_STATUS_TO_ERROR.update({
    ReturnLeaseResponse.STATUS_OK: (None, None),
    ReturnLeaseResponse.STATUS_INVALID_RESOURCE: (InvalidResourceError,
                                                  InvalidResourceError.__doc__),
    ReturnLeaseResponse.STATUS_NOT_ACTIVE_LEASE: (NotActiveLeaseError, NotActiveLeaseError.__doc__),
    ReturnLeaseResponse.STATUS_NOT_AUTHORITATIVE_SERVICE: (NotAuthoritativeServiceError,
                                                           NotAuthoritativeServiceError.__doc__),
})


class Lease(object):
    """Leases are used to coordinate access to shared resources on a Boston Dynamics robot.

    A service will grant access to the shared resource if the lease which accompanies a request is
    "more recent" than any previously seen leases. Recency is determined using a sequence of
    monotonically increasing numbers, similar to a Lamport logical clock.

    Args:
        lease_proto: bosdyn.api.Lease protobuf object.
    """

    def __init__(self, lease_proto):
        """Initializes a Lease object.

        Raises:
            ValueError if lease_proto is not present or valid.
        """
        if not self.is_valid_proto(lease_proto):
            raise ValueError('invalid lease_proto: {}'.format(lease_proto))
        self.lease_proto = lease_proto

    class CompareResult(enum.Enum):
        """Enum for comparison results between two leases."""
        SAME = 1
        SUPER_LEASE = 2
        SUB_LEASE = 3
        OLDER = 4
        NEWER = 5
        DIFFERENT_RESOURCES = 6
        DIFFERENT_EPOCHS = 7

    def compare(self, other_lease):
        """Compare two different lease objects.

        Args:
            other_lease: The lease to compare this lease with.

        Returns:
            * CompareResult.SAME if this lease is exactly the same as other_lease.
            * CompareResult.SUPER_LEASE if this lease is a "super-lease" of the other
              lease - in other words, the other lease is a sublease of this lease.
            * CompareResult.SUB_LEASE if this lease is a "sub-lease" of the other lease.
            * CompareResult.OLDER if this lease is older than other_lease.
              other_lease may be a sublease of this lease.
            * CompareResult.NEWER if this is lease is newer than other_lease. This
              lease may be a sublease of other_lease.
            * CompareResult.DIFFERENT_RESOURCES if this lease is for a different
              resource than other_lease. There is no way to compare recency/time of
              Leases for two different resources.
            * CompareResult.DIFFERENT_EPOCHS if this lease is for a different
              epoch than other_lease. There is no way to compare recency/time of
              Leases for two different epochs.
            * CompareResult.INVALID if either this or other_lease is invalid.
        """
        # Sequences are only valid for leases with the same resource and epoch.
        if not (self.lease_proto.resource == other_lease.lease_proto.resource):
            return self.CompareResult.DIFFERENT_RESOURCES
        if not (self.lease_proto.epoch == other_lease.lease_proto.epoch):
            return self.CompareResult.DIFFERENT_EPOCHS

        # If any sequence numbers are different within the common subset of sequence lengths, then one
        # Lease is newer than the other.
        sequence_size = len(self.lease_proto.sequence)
        other_sequence_size = len(other_lease.lease_proto.sequence)
        common_sequence_size = min(sequence_size, other_sequence_size)
        for i in range(common_sequence_size):
            sequence_num = self.lease_proto.sequence[i]
            other_sequence_num = other_lease.lease_proto.sequence[i]
            if sequence_num < other_sequence_num:
                return self.CompareResult.OLDER
            elif sequence_num > other_sequence_num:
                return self.CompareResult.NEWER

        # At this point, the sequence numbers are different within the common subset. If one Lease has
        # more sequence numbers than the other Lease, it is a sublease of that lease and considered
        # newer.
        if sequence_size < other_sequence_size:
            return self.CompareResult.SUPER_LEASE
        elif sequence_size > other_sequence_size:
            return self.CompareResult.SUB_LEASE

        # Lease are the same
        return self.CompareResult.SAME

    def create_newer(self):
        """Creates a new Lease which is newer than this Lease.

        Returns:
            A new Lease object where self.compare(returned_lease) would return OLDER.
        """
        incr_lease_proto = LeaseProto()
        incr_lease_proto.CopyFrom(self.lease_proto)
        incr_lease_proto.sequence[-1] = self.lease_proto.sequence[-1] + 1
        return Lease(incr_lease_proto)

    def create_sublease(self):
        """Creates a sublease of this lease.

        Returns:
            A new Lease object where self.compare(returned_lease) would return SUB_LEASE.
        """
        sub_lease_proto = LeaseProto()
        sub_lease_proto.CopyFrom(self.lease_proto)
        sub_lease_proto.sequence.append(0)
        return Lease(sub_lease_proto)

    @staticmethod
    def is_valid_proto(lease_proto):
        """Checks whether this lease is valid.

        Returns:
           bool indicating that this lease has a valid resource and sequence.
        """
        return lease_proto and lease_proto.resource and lease_proto.sequence


class LeaseState(object):

    class Status(enum.Enum):
        UNOWNED = 0
        REVOKED = 1
        SELF_OWNER = 2
        OTHER_OWNER = 3
        NOT_MANAGED = 4

    # Deprecated. Provided for backwards compatibility.
    STATUS_UNOWNED = Status.UNOWNED
    STATUS_REVOKED = Status.REVOKED
    STATUS_SELF_OWNER = Status.SELF_OWNER
    STATUS_OTHER_OWNER = Status.OTHER_OWNER
    STATUS_NOT_MANAGED = Status.NOT_MANAGED

    def __init__(self, lease_status, lease_owner=None, lease=None, lease_current=None):
        self.lease_status = lease_status
        self.lease_owner = lease_owner
        self.lease_original = lease
        if lease_current:
            self.lease_current = lease_current
        elif lease:
            self.lease_current = self.lease_original.create_sublease()
        else:
            self.lease_current = None

    def create_newer(self):
        """Create newer version of the Lease.

        Returns:
            Instance of itself if lease_current was not passed, or a new LeaseState.
        """
        if not self.lease_current:
            return self
        return LeaseState(self.lease_status, self.lease_owner, self.lease_original,
                          self.lease_current.create_newer())

    def update_from_lease_use_result(self, lease_use_result):
        """Update internal instance of LeaseState from given lease.

        Args:
            lease_use_result: LeaseUseResult from the server.

        Returns:
            Updated internal instance of LeaseState.
        """
        if lease_use_result.status == lease_use_result.STATUS_OLDER:
            if self.lease_current:
                attempted_lease = Lease(lease_use_result.attempted_lease)
                if attempted_lease.compare(self.lease_current) is Lease.CompareResult.SAME:
                    return LeaseState(LeaseState.Status.OTHER_OWNER,
                                      lease_owner=lease_use_result.owner)
        elif lease_use_result.status == lease_use_result.STATUS_WRONG_EPOCH:
            if self.lease_current:
                attempted_lease = Lease(lease_use_result.attempted_lease)
                if attempted_lease.compare(self.lease_current) is Lease.CompareResult.SAME:
                    return LeaseState(LeaseState.Status.UNOWNED)
        elif lease_use_result.status == lease_use_result.STATUS_REVOKED:
            if self.lease_current:
                attempted_lease = Lease(lease_use_result.attempted_lease)
                if attempted_lease.compare(self.lease_current) is Lease.CompareResult.SAME:
                    return LeaseState(LeaseState.Status.REVOKED)
        # The LeaseState is not modified
        return self


_RESOURCE_BODY = 'body'


class LeaseWallet(object):
    """Thread-safe storage of Leases."""

    def __init__(self):
        self._lease_state_map = {}
        self._lock = threading.Lock()

    def add(self, lease):
        """Add lease in the wallet.

        Args:
            lease: Lease to add in the wallet.
        """
        with self._lock:
            self._lease_state_map[lease.lease_proto.resource] = LeaseState(
                LeaseState.Status.SELF_OWNER, lease=lease)

    def remove(self, lease):
        """Remove lease from the wallet.

        Args:
            lease: Lease to remove from the wallet.
        """
        with self._lock:
            self._lease_state_map.pop(lease.lease_proto.resource, None)

    def advance(self, resource=_RESOURCE_BODY):
        """Advance the lease for a specific resource.

        Args:
            resource: The resource that the Lease is for.
        Returns:
            Advanced lease for the resource.
        Raises:
            LeaseNotOwnedByWallet: The lease is not owned by the wallet.
        """

        with self._lock:
            lease_state = self._get_owned_lease_state_locked(resource)
            new_lease = lease_state.create_newer()
            self._lease_state_map[resource] = new_lease
            return new_lease.lease_current

    def get_lease(self, resource=_RESOURCE_BODY):
        """Get the lease for a specific resource.

        Args:
            resource: The resource that the Lease is for.
        Returns:
            Lease for the resource.
        Raises:
            LeaseNotOwnedByWallet: The lease is not owned by the wallet.
        """

        with self._lock:
            return self._get_owned_lease_state_locked(resource).lease_current

    def get_lease_state(self, resource=_RESOURCE_BODY):
        """Get the lease state for a specific resource.

        Args:
            resource: The resource that the Lease is for.
        Returns:
            Lease state for the resource.
        Raises:
            NoSuchLease: The requested lease does not exist.
        """

        with self._lock:
            return self._get_lease_state_locked(resource)

    def _get_lease_state_locked(self, resource):
        """Get the lease state for a specific resource or raise an NoSuchLease exception if lease
        is not found.

        Args:
            resource: The resource that the Lease is for.
        Returns:
            Lease state for the resource.
        Raises:
            NoSuchLease: The requested lease does not exist.
        """
        try:
            return self._lease_state_map[resource]
        except KeyError:
            raise NoSuchLease(resource)

    def _get_owned_lease_state_locked(self, resource):
        """Get the lease for a specific resource or raise an LeaseNotOwnedByWallet exception if
        lease is not found.

        Args:
            resource: The resource that the Lease is for.
        Returns:
            Lease state for the resource.
        Raises:
            LeaseNotOwnedByWallet: The lease is not owned by the wallet.
        """
        lease_state = self._get_lease_state_locked(resource)
        if lease_state.lease_status != LeaseState.Status.SELF_OWNER:
            raise LeaseNotOwnedByWallet(resource, lease_state)
        return lease_state

    def on_lease_use_result(self, lease_use_result, resource=None):
        """Update the lease state based on result of using the lease.

        Args:
          lease_use_result: LeaseUseResult from the server.
          resource: Resource to update, e.g. 'body'. Default to None to use the resource specified
                          by the lease_use_result.
        """
        resource = resource or lease_use_result.attempted_lease.resource
        with self._lock:
            lease_state = self._lease_state_map.get(resource, None)
            if not lease_state:
                return
            new_lease_state = lease_state.update_from_lease_use_result(lease_use_result)
            self._lease_state_map[resource] = new_lease_state


class LeaseClient(common.BaseClient):
    """Client to the lease service.

    Args:
        lease_wallet: Lease wallet to use.
    """
    default_service_name = 'lease'
    service_type = 'bosdyn.api.LeaseService'

    def __init__(self, lease_wallet=None):
        super(LeaseClient, self).__init__(LeaseServiceStub)
        self.lease_wallet = lease_wallet

    def acquire(self, resource=_RESOURCE_BODY, **kwargs):
        """Acquire a lease for the given resource.

        Args:
            resorce: Resource for the lease.

        Returns:
            Acquired Lease object.

        Raises:
            ResourceAlreadyClaimedError: Use TakeLease method to forcefully grab the already
                                         claimed lease.
            InvalidResourceError: Resource is not known to the LeaseService.
            NotAuthoritativeServiceError: LeaseService is not authoritative so Acquire should not work.
        """
        req = self._make_acquire_request(resource)
        return self.call(self._stub.AcquireLease, req, self._handle_acquire_success,
                         self._handle_acquire_errors, **kwargs)

    def acquire_async(self, resource=_RESOURCE_BODY, **kwargs):
        """Async version of acquire() function."""
        req = self._make_acquire_request(resource)
        return self.call_async(self._stub.AcquireLease, req, self._handle_acquire_success,
                               self._handle_acquire_errors, **kwargs)

    def take(self, resource=_RESOURCE_BODY, **kwargs):
        """Take the lease for the given resource.

        Args:
            resorce: Resource for the lease.

        Returns:
            Taken Lease object.

        Raises:
            InvalidResourceError: Resource is not known to the LeaseService.
            NotAuthoritativeServiceError: LeaseService is not authoritative so Acquire should not
                                          work.
        """
        req = self._make_take_request(resource)
        return self.call(self._stub.TakeLease, req, self._handle_acquire_success,
                         self._handle_take_errors, **kwargs)

    def take_async(self, resource=_RESOURCE_BODY, **kwargs):
        """Async version of the take() function."""
        req = self._make_take_request(resource)
        return self.call_async(self._stub.TakeLease, req, self._handle_acquire_success,
                               self._handle_take_errors, **kwargs)

    def return_lease(self, lease, **kwargs):
        """Return an acquired lease.

        Args:
            lease: Lease to return.

        Raises:
            InvalidResourceError: Resource is not known to the LeaseService.
            NotActiveLeaseError: Lease is not the active lease.
            NotAuthoritativeServiceError: LeaseService is not authoritative so Acquire should not
                                          work.
        """
        if self.lease_wallet:
            self.lease_wallet.remove(lease)
        req = self._make_return_request(lease)
        return self.call(self._stub.ReturnLease, req, None, self._handle_return_errors, **kwargs)

    def return_lease_async(self, lease, **kwargs):
        """Async version of the return_lease() function."""
        if self.lease_wallet:
            self.lease_wallet.remove(lease)
        req = self._make_return_request(lease)
        return self.call(self._stub.ReturnLease, req, None, self._handle_return_errors, **kwargs)

    def retain_lease(self, lease, **kwargs):
        """Retain the lease.

        Args:
            lease: Lease to retain.

        Raises:
            InternalServerError: Service experienced an unexpected error state.
            LeaseUseError: Request was rejected due to using an invalid lease.
        """
        req = self._make_retain_request(lease)
        return self.call(self._stub.RetainLease, req, None, common.common_lease_errors, **kwargs)

    def retain_lease_async(self, lease, **kwargs):
        """Async version of the retain_lease() function."""
        req = self._make_retain_request(lease)
        return self.call_async(self._stub.RetainLease, req, None, common.common_lease_errors,
                               **kwargs)

    def list_leases(self, **kwargs):
        """Get a list of the leases.

        Returns:
            List of lease resources.

        Raises:
            InternalServerError: Service experienced an unexpected error state.
            LeaseUseError: Request was rejected due to using an invalid lease.
        """
        req = self._make_list_leases_request()
        return self.call(self._stub.ListLeases, req, self._list_leases_success,
                         common.common_header_errors, **kwargs)

    def list_leases_async(self, **kwargs):
        """Async version of the list_leases() function."""
        req = self._make_list_leases_request()
        return self.call_async(self._stub.ListLeases, req, self._list_leases_success,
                               common.common_header_errors, **kwargs)

    @staticmethod
    def _make_acquire_request(resource):
        """Return AcquireLeaseRequest message with the given resource."""
        return AcquireLeaseRequest(resource=resource)

    def _handle_acquire_success(self, response):
        """Return lease in an AcquireLeaseResponse message."""
        lease = Lease(response.lease)
        if self.lease_wallet:
            self.lease_wallet.add(lease)
        return lease

    @staticmethod
    @common.handle_common_header_errors
    def _handle_acquire_errors(response):
        """Return a custom exception based on response, None if no error."""
        return common.error_factory(response, response.status,
                                    status_to_string=AcquireLeaseResponse.Status.Name,
                                    status_to_error=_ACQUIRE_LEASE_STATUS_TO_ERROR)

    @staticmethod
    def _make_take_request(resource):
        """Return TakeLeaseRequest message with the given resource."""
        return TakeLeaseRequest(resource=resource)

    @staticmethod
    @common.handle_common_header_errors
    def _handle_take_errors(response):
        """Return a custom exception based on response, None if no error."""
        return common.error_factory(response, response.status,
                                    status_to_string=TakeLeaseResponse.Status.Name,
                                    status_to_error=_TAKE_LEASE_STATUS_TO_ERROR)

    @staticmethod
    def _make_return_request(lease):
        return ReturnLeaseRequest(lease=lease.lease_proto)

    @staticmethod
    @common.handle_common_header_errors
    def _handle_return_errors(response):
        """Return a custom exception based on response, None if no error."""
        return common.error_factory(response, response.status,
                                    status_to_string=ReturnLeaseResponse.Status.Name,
                                    status_to_error=_RETURN_LEASE_STATUS_TO_ERROR)

    @staticmethod
    def _make_retain_request(lease):
        req = RetainLeaseRequest(lease=lease.lease_proto)
        return req

    @staticmethod
    def _make_list_leases_request():
        return ListLeasesRequest()

    @staticmethod
    def _list_leases_success(response):
        return response.resources


class LeaseWalletRequestProcessor(object):
    """LeaseWalletRequestProcessor adds a lease from a wallet to a request.

    Args:
        lease_wallet: The LeaseWallet to read leases from.
        resource_list: List of resources this processors should add to requests. Default None
                        to use the default resource.
    """

    def __init__(self, lease_wallet, resource_list=None):
        self.lease_wallet = lease_wallet
        self.resource_list = resource_list or [_RESOURCE_BODY]
        self.logger = logging.getLogger()

    def mutate(self, request):
        """Add the leases for the necessary resources if no leases have been specified yet."""
        multiple_leases, skip_mutation = self.get_lease_state(request)

        if skip_mutation:
            return

        if multiple_leases and len(self.resource_list) <= 1:
            pass
        elif not multiple_leases and len(self.resource_list) > 1:
            self.logger.error('LeaseWalletRequestProcessor assigned multiple leases, '
                              'but request only wants one')

        if multiple_leases:
            for resource in self.resource_list:
                lease = self.lease_wallet.advance(resource)
                request.leases.add().CopyFrom(lease.lease_proto)
        else:
            lease = self.lease_wallet.advance(self.resource_list[0])
            request.lease.CopyFrom(lease.lease_proto)

    @staticmethod
    def get_lease_state(request):
        """Returns a tuple of ("are there multiple leases in request?", "are they set already?")"""
        skip_mutation = False
        multiple_leases = None

        try:
            # ValueError will occur if the request class does not have a field named 'lease'
            skip_mutation = request.HasField('lease')
        except ValueError:
            try:
                # AttributeError will occur if the request class does not have a field named 'leases'
                skip_mutation = len(request.leases) > 0
            except AttributeError:
                # If we get here, there's no 'lease' field nor a 'leases' field.
                # There are responses that do not have either field, so just return.
                skip_mutation = True
            else:
                multiple_leases = True
        else:
            # If we get here, there's only a single lease.
            multiple_leases = False
        return multiple_leases, skip_mutation


class LeaseWalletResponseProcessor(object):
    """LeaseWalletResponseProcessor updates the wallet with a LeaseUseResult.

    Args:
        lease_wallet: Lease wallet to use.
    """

    def __init__(self, lease_wallet):
        self.lease_wallet = lease_wallet

    def mutate(self, response):
        """Update the wallet if a response has a lease_use_result."""
        lease_use_results = None
        try:
            # AttributeError will occur if the response does not have a field named 'lease_use_result'
            lease_use_results = [response.lease_use_result]
        except AttributeError:
            try:
                # AttributeError will occur if the request class does not have a field named 'lease_use_results'
                lease_use_results = response.lease_use_results
            except AttributeError:
                # If we get here, there's no 'lease' field nor a 'leases' field for usage results.
                # There are responses that do not have either field, so just return.
                return

        for result in lease_use_results:
            self.lease_wallet.on_lease_use_result(result)


def add_lease_wallet_processors(client, lease_wallet, resource_list=None):
    """Adds LeaseWallet related processors to a gRPC client.

    For services which use leases for access control, this does two things:
        * Advance the lease from the LeaseWallet and attach to a request.
        * Handle the LeaseUseResult from a response and update LeaseWallet.

    Args:
        * client: BaseClient derived class for a single service.
        * lease_wallet: The LeaseWallet to track from, must be non-None.
        * resource_list: List of resources these processors should add to requests. Default None
                             to use a default resource.
    """
    client.request_processors.append(LeaseWalletRequestProcessor(lease_wallet, resource_list))
    client.response_processors.append(LeaseWalletResponseProcessor(lease_wallet))


class LeaseKeepAlive(object):
    """LeaseKeepAlive issues lease liveness checks on a background thread.

    The robot's lease system expects lease holders to check in at a regular
    cadence. If the check-ins do not happen, the robot will treat it as a
    communications loss. Typically this will result in the robot stopping,
    powering off, and the lease holder getting their lease revoked.

    Using a LeaseKeepAlive object hides most of the details of issuing the
    lease liveness check. Developers can also manage liveness checks directly
    by using the retain_lease methods on the LeaseClient object.

    Args:
        lease_client: The LeaseClient object to issue requests on.
        lease_wallet: The LeaseWallet to retrieve current leases from,
                and to handle any bad LeaseUseResults from. If not specified,
                the lease_client's lease_wallet will be used.
        resource: The resource to do liveness checks for.
        rpc_interval_seconds: Duration in seconds between liveness checks.
        keep_running_cb: If specified, should be a callable object that
                returns True if the liveness checks should proceed, False
                otherwise. LeaseKeepAlive will invoke keep_running_cb on its
                background thread. One example of where this could be used is
                in an interactive UI - keep_running_cb could stall or return
                False if the UI thread is wedged, which prevents the
                application from continuing to keep the Lease alive when it is
                no longer in a good state.
    """

    def __init__(self, lease_client, lease_wallet=None, resource=_RESOURCE_BODY,
                 rpc_interval_seconds=2, keep_running_cb=None):
        """Create a new LeaseKeepAlive object."""
        if not lease_client:
            raise ValueError("lease_client must be set")
        self._lease_client = lease_client

        if not lease_wallet:
            lease_wallet = lease_client.lease_wallet
        if not lease_wallet:
            raise ValueError("lease_wallet must be set")
        self._lease_wallet = lease_wallet

        if not resource:
            raise ValueError("resource must be set")
        self._resource = resource

        if rpc_interval_seconds <= 0.0:
            raise ValueError("rpc_interval_seconds must be > 0, was %f" % rpc_interval_seconds)
        self._rpc_interval_seconds = rpc_interval_seconds

        self.logger = logging.getLogger()

        self._keep_running = keep_running_cb or (lambda: True)

        self._end_check_in_signal = threading.Event()

        # Configure the thread to do check-ins, and begin checking in.
        self._thread = threading.Thread(target=self._periodic_check_in)
        self._thread.daemon = True
        self._thread.start()

    def shutdown(self):
        """Shut the background thread down and stop the liveness checks.

        Can be called multiple times, but subsequent calls are no-ops.
        Blocks until the background thread completes.
        """
        self.logger.debug('Shutting down')
        self._end_periodic_check_in()
        self.wait_until_done()

    def is_alive(self):
        return self._thread.is_alive()

    @property
    def lease_wallet(self):
        return self._lease_wallet

    def wait_until_done(self):
        """Waits until the background thread exits.

        Most client code should exit the background thread by using shutdown
        or by passing in a keep_running_cb callback in the constructor.

        However, this can be useful in unit tests for ensuring exits.
        """
        self._thread.join()

    def _end_periodic_check_in(self):
        """Stop checking into the Lease system."""
        self.logger.debug('Stopping check-in')
        self._end_check_in_signal.set()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def _ok(self):
        self.logger.debug('Check-in successful')

    def _check_in(self):
        """Retain lease associated with the resourse in this class."""
        lease = self._lease_wallet.get_lease(self._resource)
        if not lease:
            return None
        return self._lease_client.retain_lease(lease)

    def _periodic_check_in(self):
        """Periodically check in and retain the lease associated with the resource in this class."""
        self.logger.info('Starting lease check-in')
        while True:
            # Include the time it takes to execute keep_running, in case it takes a significant
            # portion of our check in period.
            exec_start = time.time()

            # Stop doing retention if this is not meant to keep running.
            if not self._keep_running():
                break

            try:
                self._check_in()
            # We really do want to catch anything.
            #pylint: disable=broad-except
            except Exception as exc:
                self.logger.warning('Generic exception during check-in:\n%s\n'
                                    '    (resuming check-in)', exc)
            else:
                # No errors!
                self._ok()

            # How long did the RPC and processing of said RPC take?
            exec_seconds = time.time() - exec_start

            # Block and wait for the stop signal. If we receive it within the check-in period,
            # leave the loop. This check must be at the end of the loop!
            # Wait up to self._check_in_period seconds, minus the RPC processing time.
            # (values < 0 are OK and will return immediately)
            if self._end_check_in_signal.wait(self._rpc_interval_seconds - exec_seconds):
                break
        self.logger.info('Lease check-in stopped')
