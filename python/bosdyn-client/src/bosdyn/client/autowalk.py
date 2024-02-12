# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Autowalk service."""

import collections

from bosdyn.api.autowalk import autowalk_pb2, autowalk_service_pb2_grpc
from bosdyn.client import data_chunk
from bosdyn.client.common import BaseClient, error_factory, error_pair
from bosdyn.client.exceptions import ResponseError
from bosdyn.client.lease import add_lease_wallet_processors

from .data_chunk import chunk_message


class AutowalkResponseError(ResponseError):
    """General class of errors for autowalk service."""


class CompilationError(AutowalkResponseError):
    """Provided Walk could not be compiled because the Walk was malformed.
    """


class ValidationError(AutowalkResponseError):
    """Provided Walk could not be validated because some part of the Walk was unable to initialize.
    """


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
        """Send the input walk file to the autowalk service for compilation.

        Args:
            walk: a walks_pb2.Walk input to be compiled by the autowalk service
            data_chunk_byte_size: max size of each streamed message
        Raises:
            RpcError: Problem communicating with the robot.
            bosdyn.client.autowalk.CompilationError: The walk failed to compile because it was malformed.
            bosdyn.client.autowalk.ValidationError: The walk failed to validate because some part of it was unable to initialize.
        """
        request = self._compile_autowalk_request(walk)
        self._apply_request_processors(request, copy_request=False)
        return self.call(self._stub.CompileAutowalk,
                         data_chunk.chunk_message(request, data_chunk_byte_size),
                         error_from_response=_compile_autowalk_error_from_response,
                         assemble_type=autowalk_pb2.CompileAutowalkResponse, copy_request=False,
                         **kwargs)

    def load_autowalk(self, walk, leases=[], data_chunk_byte_size=1000 * 1000, **kwargs):
        """Send the input walk file to the autowalk service for compilation and
        load resulting mission to the Mission Service on the robot.

        Args:
            walk: a walks_pb2.Walk input to be loaded onto the robot by the autowalk service
            leases: Leases the autowalk service will need to use. Unlike other clients, these MUST
              be specified.
            data_chunk_byte_size: max size of each streamed message
        Raises:
            RpcError: Problem communicating with the robot.
            bosdyn.client.autowalk.CompilationError: The walk failed to compile because it was malformed.
            bosdyn.client.autowalk.ValidationError: The walk failed to validate because some part of it was unable to initialize.
        """
        request = self._load_autowalk_request(walk, leases)
        self._apply_request_processors(request, copy_request=False)
        return self.call(self._stub.LoadAutowalk,
                         data_chunk.chunk_message(request, data_chunk_byte_size),
                         error_from_response=_load_autowalk_error_from_response,
                         assemble_type=autowalk_pb2.LoadAutowalkResponse, copy_request=False,
                         **kwargs)

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
    autowalk_pb2.CompileAutowalkResponse.STATUS_COMPILE_ERROR: error_pair(CompilationError),
})


def _compile_autowalk_error_from_response(response):
    return error_factory(response, response.status,
                         status_to_string=autowalk_pb2.CompileAutowalkResponse.Status.Name,
                         status_to_error=_COMPILE_AUTOWALK_STATUS_TO_ERROR)


_LOAD_AUTOWALK_STATUS_TO_ERROR = collections.defaultdict(lambda: (AutowalkResponseError, None))
_LOAD_AUTOWALK_STATUS_TO_ERROR.update({
    autowalk_pb2.LoadAutowalkResponse.STATUS_OK: (None, None),
    autowalk_pb2.LoadAutowalkResponse.STATUS_COMPILE_ERROR: error_pair(CompilationError),
    autowalk_pb2.LoadAutowalkResponse.STATUS_VALIDATE_ERROR: error_pair(ValidationError),
})


def _load_autowalk_error_from_response(response):
    return error_factory(response, response.status,
                         status_to_string=autowalk_pb2.LoadAutowalkResponse.Status.Name,
                         status_to_error=_LOAD_AUTOWALK_STATUS_TO_ERROR)
