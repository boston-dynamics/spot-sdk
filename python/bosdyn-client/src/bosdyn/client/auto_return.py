# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client implementation of the AutoReturn service."""

from __future__ import print_function

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

    def configure(self, params, leases, **kwargs):
        """Set the configuration of the AutoReturn system.

        Args:
          params (bosdyn.api.auto_return.auto_return_pb2.Params): Parameters to use.
          leases (list of bosdyn.client.Lease)

        Raises:
          AutoReturnResponseError: An invalid request was received by the service.
          RpcError: Problem communicating with the service.

        Returns:
            The bosdyn.api.auto_return_pb2.ConfigureResponse.
        """

        request = self._configure_request(params, leases)
        return self.call(self._stub.Configure, request, None, configure_error, copy_request=False,
                         **kwargs)

    def configure_async(self, params, leases, **kwargs):
        """Async version of the configure() RPC."""
        request = self._configure_request(params, leases)
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

    def start(self, **kwargs):
        """Start AutoReturn now.
        Raises:
          RpcError: Problem communicating with the service.

        Returns:
            The bosdyn.api.auto_return_pb2.GetConfigurationResponse.
        """
        request = auto_return_pb2.StartRequest()
        return self.call(self._stub.Start, request, None, None, copy_request=False, **kwargs)

    def start_async(self, **kwargs):
        """Async version of the start() RPC."""
        request = auto_return_pb2.StartRequest()
        return self.call_async(self._stub.Start, request, None, None, copy_request=False, **kwargs)

    def _configure_request(self, params, leases):
        request = auto_return_pb2.ConfigureRequest(params=params)
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
