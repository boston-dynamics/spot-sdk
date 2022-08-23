# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Autowalk service."""

import collections

from bosdyn.api.autowalk import autowalk_pb2, autowalk_service_pb2_grpc, walks_pb2
from bosdyn.client.common import (BaseClient, common_header_errors, error_factory,
                                  handle_common_header_errors, handle_lease_use_result_errors,
                                  handle_unset_status_error)
from bosdyn.client.exceptions import ResponseError, TimeSyncRequired
from bosdyn.client.lease import add_lease_wallet_processors


class AutowalkResponseError(ResponseError):
    """General class of errors for autowalk service."""


class CompilationError(AutowalkResponseError):
    """Walk could not be compiled."""


class ValidationError(AutowalkResponseError):
    """Walk could not be validated."""


class AutowalkClient(BaseClient):
    """Client for the Autowalk service."""
    default_service_name = 'autowalk-service'
    service_type = 'bosdyn.api.autowalk.AutowalkService'

    def __init__(self):
        super(AutowalkClient, self).__init__(autowalk_service_pb2_grpc.AutowalkServiceStub)

    def update_from(self, other):
        """Update instance from another object.

        Args:
            other: The object where to copy from.
        """
        super(AutowalkClient, self).update_from(other)
        if self.lease_wallet:
            add_lease_wallet_processors(self, self.lease_wallet)

    def compile_autowalk(self, walk, data_chunk_byte_size=1000 * 1000, **kwargs):
        """
        Send the input walk file to the autowalk service for compilation.
        """
        request = self._compile_autowalk_request(walk)
        self._apply_request_processors(request, copy_request=False)
        return self.call(self._stub.CompileAutowalk,
                         BaseClient.chunk_message(request, data_chunk_byte_size),
                         _get_compile_autowalk_response_from_chunks,
                         _compile_autowalk_error_from_response, copy_request=False, **kwargs)

    def load_autowalk(self, walk, leases=[], data_chunk_byte_size=1000 * 1000, **kwargs):
        """
        Send the input walk file to the autowalk service for compilation and
        load resulting mission to the Mission Service on the robot.
        """
        request = self._load_autowalk_request(walk, leases)
        self._apply_request_processors(request, copy_request=False)
        return self.call(self._stub.LoadAutowalk,
                         BaseClient.chunk_message(request, data_chunk_byte_size),
                         _get_load_autowalk_response_from_chunks,
                         _load_autowalk_error_from_response, copy_request=False, **kwargs)

    @staticmethod
    def _compile_autowalk_request(walk):
        request = autowalk_pb2.CompileAutowalkRequest(walk=walk)
        return request

    @staticmethod
    def _load_autowalk_request(walk, leases):
        request = autowalk_pb2.LoadAutowalkRequest(walk=walk)
        for lease in leases:
            request.leases.add().CopyFrom(lease.lease_proto)
        return request


_COMPILE_AUTOWALK_STATUS_TO_ERROR = collections.defaultdict(lambda: (AutowalkResponseError, None))
_COMPILE_AUTOWALK_STATUS_TO_ERROR.update({
    autowalk_pb2.CompileAutowalkResponse.STATUS_OK: (None, None),
    autowalk_pb2.CompileAutowalkResponse.STATUS_COMPILE_ERROR: (CompilationError, None),
})


def _compile_autowalk_error_from_response(response):
    response = _get_compile_autowalk_response_from_chunks(response)
    return error_factory(response, response.status,
                         status_to_string=autowalk_pb2.CompileAutowalkResponse.Status.Name,
                         status_to_error=_COMPILE_AUTOWALK_STATUS_TO_ERROR)


_LOAD_AUTOWALK_STATUS_TO_ERROR = collections.defaultdict(lambda: (AutowalkResponseError, None))
_LOAD_AUTOWALK_STATUS_TO_ERROR.update({
    autowalk_pb2.LoadAutowalkResponse.STATUS_OK: (None, None),
    autowalk_pb2.LoadAutowalkResponse.STATUS_COMPILE_ERROR: (CompilationError, None),
    autowalk_pb2.LoadAutowalkResponse.STATUS_VALIDATE_ERROR: (ValidationError, None),
})


def _load_autowalk_error_from_response(response):
    response = _get_load_autowalk_response_from_chunks(response)
    return error_factory(response, response.status,
                         status_to_string=autowalk_pb2.LoadAutowalkResponse.Status.Name,
                         status_to_error=_LOAD_AUTOWALK_STATUS_TO_ERROR)


def _get_load_autowalk_response_from_chunks(response):
    """Reads a streamed response to recreate load autowalk response."""
    data = ''
    num_chunks = 0
    for resp in response:
        if num_chunks == 0:
            data = resp.data
        else:
            data += resp.data
        num_chunks += 1
    load_autowalk_response = autowalk_pb2.LoadAutowalkResponse()
    if (num_chunks > 0):
        load_autowalk_response.ParseFromString(data)
    return load_autowalk_response


def _get_compile_autowalk_response_from_chunks(response):
    """Reads a streamed response to recreate compile autowalk response."""
    data = ''
    num_chunks = 0
    for resp in response:
        if num_chunks == 0:
            data = resp.data
        else:
            data += resp.data
        num_chunks += 1
    compile_autowalk_response = autowalk_pb2.CompileAutowalkResponse()
    if (num_chunks > 0):
        compile_autowalk_response.ParseFromString(data)
    return compile_autowalk_response
