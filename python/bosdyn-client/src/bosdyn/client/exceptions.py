# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

class Error(Exception):
    """Base exception that all public api exceptions are derived from."""


class ResponseError(Error):
    """Exception triggered by a server response whose rpc succeeded."""

    def __init__(self, response, error_message=None):
        super(ResponseError, self).__init__()
        self.response = response
        if error_message is not None:
            self.error_message = error_message
        elif response is not None:
            self.error_message = response.header.error.message
        else:
            self.error_message = ""

    def __str__(self):
        if self.response is not None:
            full_classname = self.response.DESCRIPTOR.full_name
        else:
            full_classname = "Error"
        return '{} ({}): {}'.format(full_classname, self.__class__.__name__, self.error_message)


class InvalidRequestError(ResponseError):
    """The provided request arguments are ill-formed or invalid, independent of the system state."""


class LeaseUseError(ResponseError):
    """Request was rejected due to using an invalid lease."""


class LicenseError(ResponseError):
    """Request was rejected due to using an invalid license."""


class ServerError(ResponseError):
    """Service encountered an unrecoverable error."""


class InternalServerError(ServerError):
    """Service experienced an unexpected error state."""


class UnsetStatusError(ServerError):
    """Response's status field (in either message or common header) was UNKNOWN value."""


class RpcError(Error):
    """An error occurred trying to reach a service on the robot."""

    def __init__(self, original_error, error_message=None):
        super(RpcError, self).__init__()
        self.error = original_error
        self.error_message = error_message or str(original_error)

    def __str__(self):
        return '{}: {}'.format(self.__class__.__name__, self.error_message)


class RetryableRpcError(RpcError):
    """An RpcError that denotes the same request may succeed if retried."""


class PersistentRpcError(RpcError):
    """An RpcError that will almost certainly continue to keep failing if retried"""


class ClientCancelledOperationError(PersistentRpcError):
    """The user cancelled the rpc request."""


class InvalidAppTokenError(PersistentRpcError):
    """The provided app token is invalid."""


class InvalidClientCertificateError(PersistentRpcError):
    """The provided client certificate is invalid."""


class NonexistentAuthorityError(PersistentRpcError):
    """The app token's authority field names a nonexistent service."""


class PermissionDeniedError(PersistentRpcError):
    """The rpc request was denied access."""


class ProxyConnectionError(RetryableRpcError):
    """The proxy on the robot could not be reached."""


class ResponseTooLargeError(RetryableRpcError):
    """The rpc response was larger than allowed max size."""


class ServiceUnavailableError(RetryableRpcError):
    """The proxy could not find the (possibly unregistered) service."""


class TooManyRequestsError(RetryableRpcError):
    """The remote procedure call did not go through the proxy due to rate limiting."""


class ServiceFailedDuringExecutionError(RetryableRpcError):
    """The service encountered an unexpected failure."""


class TimedOutError(RetryableRpcError):
    """The remote procedure call did not terminate within the allotted time."""


class UnableToConnectToRobotError(RetryableRpcError):
    """The robot may be offline or otherwise unreachable."""


class RetryableUnavailableError(UnableToConnectToRobotError):
    """Service unavailable or channel reset. Likely transient and can be resolved by retrying."""


class UnauthenticatedError(PersistentRpcError):
    """The user needs to authenticate or does not have permission to access requested service."""


class UnknownDnsNameError(PersistentRpcError):
    """The system is unable to translate the domain name."""


class NotFoundError(PersistentRpcError):
    """The backend system could not be found."""


class UnimplementedError(PersistentRpcError):
    """The API does not recognize the request and is unable to complete the request."""


class TransientFailureError(RetryableRpcError):
    """The channel is in state TRANSIENT_FAILURE, often caused by a connection failure."""


class TimeSyncRequired(Error):
    """Time synchronization is required but none seems to be established."""
