# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client implementation of the AutoReturn service."""

import collections

from bosdyn.api.auto_return import auto_return_pb2, auto_return_service_pb2_grpc
from bosdyn.client.common import (BaseClient, error_factory, error_pair,
                                  handle_common_header_errors, handle_unset_status_error)
from bosdyn.client.exceptions import ResponseError


class AutoReturnResponseError(ResponseError):
    """Error in Auto Return RPC"""


class InvalidParameterError(AutoReturnResponseError):
    """One or more parameters were invalid."""


class AutoReturnClient(BaseClient):
    """A client for configuring automatic AutoReturn behavior."""

    default_service_name = 'auto-return'
    service_type = 'bosdyn.api.auto_return.AutoReturnService'

    def __init__(self):
        super(AutoReturnClient, self).__init__(auto_return_service_pb2_grpc.AutoReturnServiceStub)
        self._timesync_endpoint = None

    def configure(self, params, leases, clear_buffer=False, **kwargs):
        """Set the configuration of the AutoReturn system.

        Args:
          params (bosdyn.api.auto_return.auto_return_pb2.Params): Parameters to use.
          leases (list of bosdyn.client.Lease)
          clear_buffer (bool): Set True to forget any currently buffered locations.

        Raises:
          InvalidParameterError: An invalid request was received by the service.
          RpcError: Problem communicating with the service.

        Returns:
            The bosdyn.api.auto_return_pb2.ConfigureResponse.
        """

        request = self._configure_request(params, leases, clear_buffer)
        return self.call(self._stub.Configure, request, None, configure_error, copy_request=False,
                         **kwargs)

    def configure_async(self, params, leases, clear_buffer=False, **kwargs):
        """Async version of the configure() RPC."""
        request = self._configure_request(params, leases, clear_buffer)
        return self.call(self._stub.Configure, request, None, configure_error, copy_request=False,
                         **kwargs)

    def get_configuration(self, **kwargs):
        """Get the configuration of the AutoReturn system.

        Raises:
          RpcError: Problem communicating with the service.

        Returns:
            The bosdyn.api.auto_return_pb2.GetConfigurationResponse.
        """
        request = auto_return_pb2.GetConfigurationRequest()
        return self.call(self._stub.GetConfiguration, request, None, None, copy_request=False,
                         **kwargs)

    def get_configuration_async(self, **kwargs):
        """Async version of the get_configuration() RPC."""
        request = auto_return_pb2.GetConfigurationRequest()
        return self.call_async(self._stub.GetConfiguration, request, None, None, copy_request=False,
                               **kwargs)

    def start(self, params=None, leases=[], **kwargs):
        """Start AutoReturn now.
        Raises:
          InvalidParameterError: An invalid request was received by the service.
          RpcError: Problem communicating with the service.

        Returns:
            The bosdyn.api.auto_return_pb2.StartResponse.
        """
        request = self._start_request(params, leases)
        return self.call(self._stub.Start, request, None, start_error, copy_request=False, **kwargs)

    def start_async(self, params=None, leases=[], **kwargs):
        """Async version of the start() RPC."""
        request = self._start_request(params, leases)
        return self.call_async(self._stub.Start, request, None, start_error, copy_request=False,
                               **kwargs)

    @staticmethod
    def _configure_request(params, leases, clear_buffer):
        request = auto_return_pb2.ConfigureRequest(params=params, clear_buffer=clear_buffer)
        for lease in leases:
            request.leases.add().CopyFrom(lease.lease_proto)
        return request

    @staticmethod
    def _start_request(params, leases):
        request = auto_return_pb2.StartRequest(params=params)
        for lease in leases:
            request.leases.add().CopyFrom(lease.lease_proto)
        return request


_CONFIGURE_STATUS_TO_ERROR = collections.defaultdict(lambda: (None, None))
_CONFIGURE_STATUS_TO_ERROR.update(
    {auto_return_pb2.ConfigureResponse.STATUS_INVALID_PARAMS: error_pair(InvalidParameterError)})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def configure_error(response):
    """Return a custom exception based on the Configure response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=auto_return_pb2.ConfigureResponse.Status.Name,
                         status_to_error=_CONFIGURE_STATUS_TO_ERROR)


_START_STATUS_TO_ERROR = collections.defaultdict(lambda: (None, None))
_START_STATUS_TO_ERROR.update(
    {auto_return_pb2.StartResponse.STATUS_INVALID_PARAMS: error_pair(InvalidParameterError)})


@handle_common_header_errors
def start_error(response):
    """Return a custom exception based on the Start response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=auto_return_pb2.StartResponse.Status.Name,
                         status_to_error=_START_STATUS_TO_ERROR)
