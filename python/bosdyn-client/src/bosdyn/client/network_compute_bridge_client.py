# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the network compute bridge service."""

import collections

from bosdyn.api import (network_compute_bridge_pb2, network_compute_bridge_service_pb2,
                        network_compute_bridge_service_pb2_grpc)
from bosdyn.client.common import (BaseClient, error_factory, error_pair,
                                  handle_common_header_errors, handle_lease_use_result_errors,
                                  handle_unset_status_error)
from bosdyn.client.exceptions import Error, InternalServerError, ResponseError, UnsetStatusError


class ExternalServiceNotFoundError(ResponseError):
    """The requested service for external computation was not found in the directory."""


class ExternalServerError(ResponseError):
    """The call to the external server did not complete successfully."""


class NetworkComputeRotationError(ResponseError):
    """The robot failed to rotate the image as requested."""


class NetworkComputeBridgeClient(BaseClient):
    """Client to either the NetworkComputeBridgeService or the NetworkComputeBridgeWorkerService."""

    default_service_name = 'network-compute-bridge'
    service_type = 'bosdyn.api.NetworkComputeBridge'

    def __init__(self):
        super(NetworkComputeBridgeClient,
              self).__init__(network_compute_bridge_service_pb2_grpc.NetworkComputeBridgeStub)

    def list_available_models(self, service_name, **kwargs):
        """List all available models that the service knows.

        Args:
            service_name (str): The service to query for models.

        Returns:
            The full ListAvailableModelsResponse, which contains any models the service or worker
            service advertise.

        Raises:
            RpcError: Problem communicating with the robot.
            ExternalServiceNotFoundError: The network compute bridge worker service was not found in
                the robot's directory.
            ExternalServerError: Either the service or worker service threw an error when responding with
                the set of all models.
        """
        request = network_compute_bridge_pb2.ListAvailableModelsRequest()
        request.server_config.service_name = service_name
        return self.list_available_models_command(request, **kwargs)

    def list_available_models_async(self, service_name, **kwargs):
        """Async version of list_available_models()."""
        request = network_compute_bridge_pb2.ListAvailableModelsRequest()
        request.server_config.service_name = service_name
        return self.list_available_models_command_async(request, **kwargs)

    def list_available_models_command(self, list_request, **kwargs):
        """List all available models that the service knows.

        Args:
            list_request (ListAvailableModelsRequest): The request to list all models.

        Returns:
            The full ListAvailableModelsResponse, which contains any models the service or worker
            service advertise.

        Raises:
            RpcError: Problem communicating with the robot.
            ExternalServiceNotFoundError: The network compute bridge worker service was not found in
                the robot's directory.
            ExternalServerError: Either the service or worker service threw an error when responding with
                the set of all models.
        """
        return self.call(self._stub.ListAvailableModels, list_request, None,
                         _list_available_models_error, **kwargs)

    def list_available_models_command_async(self, list_request, **kwargs):
        """Async version of list_available_models_command()."""
        return self.call_async(self._stub.ListAvailableModels, list_request, None,
                               _list_available_models_error, **kwargs)

    def network_compute_bridge_command(self, network_compute_request, **kwargs):
        """Issue the main network compute bridge request to run a model on specific, requested data.

        Args:
            network_compute_request (NetworkComputeRequest): The request which contains what type of data should
                be processed, and which model the server should run.

        Returns:
            The full NetworkComputeResponse, which contains the processed data.

        Raises:
            RpcError: Problem communicating with the robot.
            ExternalServiceNotFoundError: The network compute bridge worker service was not found in
                the robot's directory.
            ExternalServerError: Either the service or worker service threw an error when responding with
                the set of all models.
            NetworkComputeRotationError: For processed image data, the robot was unable to rotate the
                image as requested.

        """
        return self.call(self._stub.NetworkCompute, network_compute_request, None,
                         _network_compute_error, **kwargs)

    def network_compute_bridge_command_async(self, network_compute_request, **kwargs):
        """Async version of network_compute_bridge_command()."""
        return self.call_async(self._stub.NetworkCompute, network_compute_request, None,
                               _network_compute_error, **kwargs)


@handle_common_header_errors
def _network_compute_error(response):
    """Return a custom exception based on response, None if no error."""
    error_type, message = _NETWORK_COMPUTE_STATUS_TO_ERROR[response.status]
    # This status is not an error.
    if error_type is None:
        return None

    return error_type(response=response, error_message=message)


_NETWORK_COMPUTE_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_NETWORK_COMPUTE_STATUS_TO_ERROR.update({
    network_compute_bridge_pb2.NETWORK_COMPUTE_STATUS_UNKNOWN:
        error_pair(UnsetStatusError),
    network_compute_bridge_pb2.NETWORK_COMPUTE_STATUS_SUCCESS: (None, None),
    network_compute_bridge_pb2.NETWORK_COMPUTE_STATUS_EXTERNAL_SERVICE_NOT_FOUND:
        (ExternalServiceNotFoundError, ExternalServiceNotFoundError.__doc__),
    network_compute_bridge_pb2.NETWORK_COMPUTE_STATUS_EXTERNAL_SERVER_ERROR:
        (ExternalServerError, None),
    network_compute_bridge_pb2.NETWORK_COMPUTE_STATUS_ROTATION_ERROR:
        (NetworkComputeRotationError, None),
})


@handle_common_header_errors
def _list_available_models_error(response):
    """Return a custom exception based on response, None if no error."""
    error_type, message = _LIST_AVAILABLE_MODELS_STATUS_TO_ERROR[response.status]
    # This status is not an error.
    if error_type is None:
        return None

    return error_type(response=response, error_message=message)


_LIST_AVAILABLE_MODELS_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_LIST_AVAILABLE_MODELS_STATUS_TO_ERROR.update({
    network_compute_bridge_pb2.LIST_AVAILABLE_MODELS_STATUS_UNKNOWN:
        error_pair(UnsetStatusError),
    network_compute_bridge_pb2.LIST_AVAILABLE_MODELS_STATUS_SUCCESS: (None, None),
    network_compute_bridge_pb2.LIST_AVAILABLE_MODELS_STATUS_EXTERNAL_SERVICE_NOT_FOUND:
        (ExternalServiceNotFoundError, ExternalServiceNotFoundError.__doc__),
    network_compute_bridge_pb2.LIST_AVAILABLE_MODELS_STATUS_EXTERNAL_SERVER_ERROR:
        (ExternalServerError, None),
})
