# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client for the RemoteMission service."""

import collections

from bosdyn.api.mission import remote_pb2, remote_service_pb2_grpc

from bosdyn.client.common import BaseClient
from bosdyn.client.common import (common_header_errors, error_factory, handle_unset_status_error,
                                  handle_common_header_errors, handle_lease_use_result_errors)
from bosdyn.client.exceptions import ResponseError

from bosdyn.mission import constants


class Error(Exception):
    pass


class InvalidSessionId(ResponseError):
    """Provided session ID was not valid on the server."""


class MissingInputs(ResponseError):
    """Missing required inputs."""


class MissingLeases(ResponseError):
    """Missing leases on required resources."""


def tree_status_from_tick_status(tick_status):
    if tick_status == remote_pb2.TickResponse.STATUS_FAILURE:
        return constants.Result.FAILURE
    elif tick_status == remote_pb2.TickResponse.STATUS_RUNNING:
        return constants.Result.RUNNING
    elif tick_status == remote_pb2.TickResponse.STATUS_SUCCESS:
        return constants.Result.SUCCESS
    raise Error('No corresponding tree status for tick status "{}"'.format(tick_status))


class RemoteClient(BaseClient):

    default_service_name = None
    service_type = 'bosdyn.api.mission.RemoteMissionService'

    def __init__(self):
        super(RemoteClient, self).__init__(remote_service_pb2_grpc.RemoteMissionServiceStub)

    def establish_session(self, leases, inputs, **kwargs):
        """Establish a session.

        Args:
          leases: List of lease protobufs to establish session with.
        """
        req = _build_establish_session_request(inputs=inputs, leases=leases)
        return self.call(self._stub.EstablishSession, req,
                         value_from_response=_session_id_from_response,
                         error_from_response=_establish_error_from_response, **kwargs)

    def establish_session_async(self, leases, inputs, **kwargs):
        req = _build_establish_session_request(inputs=inputs, leases=leases)
        return self.call_async(self._stub.EstablishSession, req,
                               value_from_response=_session_id_from_response,
                               error_from_response=_establish_error_from_response, **kwargs)

    def tick(self, session_id, leases, inputs, **kwargs):
        req = _build_tick_request(inputs=inputs, leases=leases, session_id=session_id)
        return self.call(self._stub.Tick, req, value_from_response=None,
                         error_from_response=_tick_error_from_response, **kwargs)

    def tick_async(self, session_id, leases, inputs, **kwargs):
        req = _build_tick_request(inputs=inputs, leases=leases, session_id=session_id)
        return self.call_async(self._stub.Tick, req, value_from_response=None,
                               error_from_response=_tick_error_from_response, **kwargs)

    def stop(self, session_id, **kwargs):
        req = remote_pb2.StopRequest(session_id=session_id)
        return self.call(self._stub.Stop, req, value_from_response=None,
                         error_from_response=_stop_error_from_response, **kwargs)

    def stop_async(self, session_id, **kwargs):
        req = remote_pb2.StopRequest(session_id=session_id)
        return self.call_async(self._stub.Stop, req, value_from_response=None,
                               error_from_response=_stop_error_from_response, **kwargs)

    def teardown_session(self, session_id, **kwargs):
        req = remote_pb2.TeardownSessionRequest(session_id=session_id)
        return self.call(self._stub.TeardownSession, req, value_from_response=None,
                         error_from_response=_teardown_error_from_response, **kwargs)

    def teardown_session_async(self, session_id, **kwargs):
        req = remote_pb2.TeardownSessionRequest(session_id=session_id)
        return self.call_async(self._stub.TeardownSession, req, value_from_response=None,
                               error_from_response=_teardown_error_from_response, **kwargs)


def _copy_leases(req, leases):
    """Modify req.leases in place to contain lease_pb2.Lease objects"""
    # Assume that the "leases" iterable contains lease_pb2.Lease protobuf objects.
    for proto in leases:
        try:
            # Try to access the lease_proto, in case the "leases" argument isn't a protobuf.
            # For example it could be a bosdyn.client.lease.Lease.
            proto = proto.lease_proto
        except AttributeError:
            # If that didn't work, do nothing.
            # Either it's a lease_pb2.Lease, or we'll get an error in the CopyFrom step.
            pass
        req.leases.add().CopyFrom(proto)


def _build_establish_session_request(inputs, leases):
    req = remote_pb2.EstablishSessionRequest(inputs=inputs)
    _copy_leases(req, leases)
    return req


def _build_tick_request(inputs, leases, session_id):
    req = remote_pb2.TickRequest(inputs=inputs, session_id=session_id)
    _copy_leases(req, leases)
    return req


def _session_id_from_response(response):
    return response.session_id


_ESTABLISH_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_ESTABLISH_STATUS_TO_ERROR.update({
    remote_pb2.EstablishSessionResponse.STATUS_OK: (None, None),
    remote_pb2.EstablishSessionResponse.STATUS_MISSING_LEASES: (MissingLeases,
                                                                MissingLeases.__doc__),
    remote_pb2.EstablishSessionResponse.STATUS_MISSING_INPUTS: (MissingInputs,
                                                                MissingInputs.__doc__),
})


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _establish_error_from_response(response):
    return error_factory(response, response.status,
                         status_to_string=remote_pb2.TickResponse.Status.Name,
                         status_to_error=_ESTABLISH_STATUS_TO_ERROR)


_TICK_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_TICK_STATUS_TO_ERROR.update({
    remote_pb2.TickResponse.STATUS_FAILURE: (None, None),
    remote_pb2.TickResponse.STATUS_RUNNING: (None, None),
    remote_pb2.TickResponse.STATUS_SUCCESS: (None, None),
    remote_pb2.TickResponse.STATUS_MISSING_LEASES: (MissingLeases, MissingLeases.__doc__),
    remote_pb2.TickResponse.STATUS_MISSING_INPUTS: (MissingInputs, MissingInputs.__doc__),
    remote_pb2.TickResponse.STATUS_INVALID_SESSION_ID: (InvalidSessionId, InvalidSessionId.__doc__),
})


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _tick_error_from_response(response):
    return error_factory(response, response.status,
                         status_to_string=remote_pb2.TickResponse.Status.Name,
                         status_to_error=_TICK_STATUS_TO_ERROR)


_STOP_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_STOP_STATUS_TO_ERROR.update({
    remote_pb2.StopResponse.STATUS_OK: (None, None),
    remote_pb2.StopResponse.STATUS_INVALID_SESSION_ID: (InvalidSessionId, InvalidSessionId.__doc__),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _stop_error_from_response(response):
    return error_factory(response, response.status,
                         status_to_string=remote_pb2.StopResponse.Status.Name,
                         status_to_error=_STOP_STATUS_TO_ERROR)


_TEARDOWN_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_TEARDOWN_STATUS_TO_ERROR.update({
    remote_pb2.TeardownSessionResponse.STATUS_OK: (None, None),
    remote_pb2.TeardownSessionResponse.STATUS_INVALID_SESSION_ID: (InvalidSessionId,
                                                                   InvalidSessionId.__doc__),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _teardown_error_from_response(response):
    return error_factory(response, response.status,
                         status_to_string=remote_pb2.TeardownSessionResponse.Status.Name,
                         status_to_error=_TEARDOWN_STATUS_TO_ERROR)
