# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to acquire a user token from the authentication service.

AuthClient -- Wrapper around service stub.
InvalidLoginError -- Raised when authentication response indicates invalid login.
InvalidTokenError -- Raised when authentication response indicates invalid token.
"""

import collections
import logging

from bosdyn.api import auth_pb2
from bosdyn.api import auth_service_pb2_grpc

from .common import BaseClient
from .common import error_factory, handle_common_header_errors, handle_unset_status_error
from .exceptions import ResponseError

_LOGGER = logging.getLogger(__name__)


class AuthResponseError(ResponseError):
    """General class of errors for AuthResponseError service."""


class InvalidLoginError(AuthResponseError):
    """Provided username/password is invalid."""


class InvalidTokenError(AuthResponseError):
    """Provided user token is invalid or cannot be re-minted."""


class TemporarilyLockedOutError(AuthResponseError):
    """User is temporarily locked out of authentication."""


class ExpiredApplicationTokenError(AuthResponseError):
    """Application token has expired. Please contact support@bostondynamics.com to receive a new one."""


class InvalidApplicationTokenError(AuthResponseError):
    """The Application Token is invalid."""


_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_STATUS_TO_ERROR.update({
    auth_pb2.GetAuthTokenResponse.STATUS_OK: (None, None),
    auth_pb2.GetAuthTokenResponse.STATUS_INVALID_LOGIN: (InvalidLoginError,
                                                         InvalidLoginError.__doc__),
    auth_pb2.GetAuthTokenResponse.STATUS_INVALID_TOKEN: (InvalidTokenError,
                                                         InvalidTokenError.__doc__),
    auth_pb2.GetAuthTokenResponse.STATUS_TEMPORARILY_LOCKED_OUT:
    (TemporarilyLockedOutError, TemporarilyLockedOutError.__doc__),
    auth_pb2.GetAuthTokenResponse.STATUS_INVALID_APPLICATION_TOKEN:
    (InvalidApplicationTokenError, InvalidApplicationTokenError.__doc__),
    auth_pb2.GetAuthTokenResponse.STATUS_EXPIRED_APPLICATION_TOKEN:
    (ExpiredApplicationTokenError, ExpiredApplicationTokenError.__doc__)
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _error_from_response(response):
    """Return a custom exception based on response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=auth_pb2.GetAuthTokenResponse.Status.Name,
                         status_to_error=_STATUS_TO_ERROR)


def _token_from_response(response):
    return response.token


def _build_auth_request(username, password, app_token=None):
    return auth_pb2.GetAuthTokenRequest(username=username, password=password,
                                        application_token=app_token)


def _build_auth_token_request(token, app_token=None):
    return auth_pb2.GetAuthTokenRequest(token=token, application_token=app_token)


class AuthClient(BaseClient):
    """Client to authenticate to the robot."""

    # Typical name of the service in the robot's directory listing.
    default_service_name = 'auth'
    # gRPC service proto definition implemented by this service
    service_type = 'bosdyn.api.AuthService'

    def __init__(self, name=None):
        super(AuthClient, self).__init__(auth_service_pb2_grpc.AuthServiceStub, name=name)

    def auth(self, username, password, app_token=None, **kwargs):
        """Authenticate to the robot with a username/password combo.

        Args:
            username: username on the robot.
            password: password for the username on the robot.
            app_token: Deprecated.  Only include for robots with old software.
            kwargs: extra arguments for controlling RPC details.

        Returns:
            User token from the server as a string.

        Raises:
            InvalidLoginError: If username and/or password are not valid.
        """
        req = _build_auth_request(username, password, app_token)
        return self.call(self._stub.GetAuthToken, req, _token_from_response, _error_from_response,
                         **kwargs)

    def auth_async(self, username, password, app_token=None, **kwargs):
        """Asynchronously authenticate to the robot with a username/password combo.

        See auth documentation for more details.
        """
        req = _build_auth_request(username, password, app_token)
        return self.call_async(self._stub.GetAuthToken, req, _token_from_response,
                               _error_from_response, **kwargs)

    def auth_with_token(self, token, app_token=None, **kwargs):
        """Authenticate to the robot using a previously created user token.

        Args:
            token: a user token previously issued by the robot.
            app_token: Deprecated.  Only include for robots with old software.
            kwargs: extra arguments for controlling RPC details.

        Returns:
            A new user token from the server. The new token will generally be valid further in
            the future than the passed in token. A client can use auth_with_token to regularly
            re-authenticate without needing to ask for username/password credentials.

        Raises:
            InvalidTokenError: If the token was incorrectly formed, for the wrong robot, or expired.
        """
        req = _build_auth_token_request(token, app_token)
        return self.call(self._stub.GetAuthToken, req, _token_from_response, _error_from_response,
                         **kwargs)

    def auth_with_token_async(self, token, app_token=None, **kwargs):
        """Authenticate to the robot using a previously created user token.

        See auth_with_token documentation for more details.
        """
        req = _build_auth_token_request(token, app_token)
        return self.call_async(self._stub.GetAuthToken, req, _token_from_response,
                               _error_from_response, **kwargs)
