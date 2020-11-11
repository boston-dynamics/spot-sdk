# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
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
    """The provided request arguments are ill-formed or invalid.

       This is programmer error, hence it should be fixed and not ignored.
       This error does not depend on the state of the system."""


class LeaseUseError(ResponseError):
    """Request was rejected due to using an invalid lease.

       This is thrown by services outside of LeaseService."""

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
        full_classname = self.error.__class__.__name__
        return '{}: {}'.format(full_classname, self.error_message)


class ClientCancelledOperationError(RpcError):
    """The user cancelled the rpc request."""


class InvalidAppTokenError(RpcError):
    """The provided app token is invalid."""


class InvalidClientCertificateError(RpcError):
    """The provided client certificate is invalid."""


class NonexistentAuthorityError(RpcError):
    """The app token's authority field names a nonexistent service."""


class PermissionDeniedError(RpcError):
    """The rpc request was denied access."""


class ProxyConnectionError(RpcError):
    """The proxy on the robot could not be reached."""


class ResponseTooLargeError(RpcError):
    """The rpc response was larger than allowed max size."""


class ServiceUnavailableError(RpcError):
    """The proxy could not find the (possibly unregistered) service."""


class ServiceFailedDuringExecutionError(RpcError):
    """The service encountered an unexpected failure."""


class TimedOutError(RpcError):
    """The remote procedure call did not terminate within the allotted time."""


class UnableToConnectToRobotError(RpcError):
    """The robot may be offline or otherwise unreachable."""


class UnauthenticatedError(RpcError):
    """The user needs to authenticate or does not have permission to access requested service."""


class UnknownDnsNameError(RpcError):
    """The system is unable to translate the domain name."""


class NotFoundError(RpcError):
    """The backend system could not be found."""


class UnimplementedError(RpcError):
    """The API does not recognize the request and is unable to complete the request."""


class TransientFailureError(RpcError):
    """The channel is in state TRANSIENT_FAILURE, often caused by a connection failure."""


class TimeSyncRequired(Error):
    """Time synchronization is required but none seems to be established."""
