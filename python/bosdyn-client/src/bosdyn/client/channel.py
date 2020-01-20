# Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging

import grpc

from .exceptions import (RpcError, ClientCancelledOperationError, InvalidAppTokenError,
                         InvalidClientCertificateError, NonexistentAuthorityError,
                         ProxyConnectionError, ServiceFailedDuringExecutionError,
                         ServiceUnavailableError, TimedOutError, UnableToConnectToRobotError,
                         UnauthenticatedError, UnknownDnsNameError, UnimplementedError)

TransportError = grpc.RpcError

_LOGGER = logging.getLogger(__name__)


class RefreshingAccessTokenAuthMetadataPlugin(grpc.AuthMetadataPlugin):

    def __init__(self, token_cb):
        """Constructor.

        Args:
            token_cb -- Callable that returns a tuple of (app token, user token)
        """
        self._token_cb = token_cb

    def __call__(self, context, callback):
        app_token, user_token = self._token_cb()
        user_token_metadata = ('authorization', 'Bearer {}'.format(user_token))
        metadata = (user_token_metadata, ('x-bosdyn-apptoken', app_token))
        error = None
        callback(metadata, error)


def create_secure_channel_creds(cert, token_cb):
    """Returns credentials for establishing a secure channel
    Uses previously set values on the linked Sdk and self.
    """
    transport_creds = grpc.ssl_channel_credentials(root_certificates=cert)
    plugin = RefreshingAccessTokenAuthMetadataPlugin(token_cb)
    # Encrypted connections carry either just transport credentials sufficient to
    # establish TLS or both transport and authorization credentials. The auth
    # credentials provide the token with every GRPC call on this channel.
    auth_creds = grpc.metadata_call_credentials(plugin)
    return grpc.composite_channel_credentials(transport_creds, auth_creds)


def create_secure_channel(address, port, creds, authority):
    """Create a secure channel to given host:port"""
    socket = '{}:{}'.format(address, port)
    options = (('grpc.ssl_target_name_override', authority),)
    return grpc.secure_channel(socket, creds, options)


def translate_exception(rpc_error):
    code = rpc_error.code()
    details = rpc_error.details()

    if code is grpc.StatusCode.CANCELLED:
        if str(401) in details:
            return UnauthenticatedError(rpc_error, UnauthenticatedError.__doc__)
        elif str(403) in details:
            return InvalidAppTokenError(rpc_error, InvalidAppTokenError.__doc__)
        elif str(404) in details:
            return UnimplementedError(rpc_error, UnimplementedError.__doc__)
        elif str(502) in details:
            return ServiceUnavailableError(rpc_error, ServiceUnavailableError.__doc__)
        elif str(504) in details:
            return TimedOutError(rpc_error, TimedOutError.__doc__)

        return ClientCancelledOperationError(rpc_error, ClientCancelledOperationError.__doc__)
    elif code is grpc.StatusCode.DEADLINE_EXCEEDED:
        return TimedOutError(rpc_error, TimedOutError.__doc__)
    elif code is grpc.StatusCode.UNIMPLEMENTED:
        return UnimplementedError(rpc_error, UnimplementedError.__doc__)

    debug = rpc_error.debug_error_string()
    if 'is not in peer certificate' in debug:
        return NonexistentAuthorityError(rpc_error, NonexistentAuthorityError.__doc__)
    elif 'Failed to connect to remote host' in debug or 'Failed to create subchannel' in debug:
        return ProxyConnectionError(rpc_error, ProxyConnectionError.__doc__)
    elif 'Exception calling application' in debug:
        return ServiceFailedDuringExecutionError(rpc_error,
                                                 ServiceFailedDuringExecutionError.__doc__)
    elif 'Handshake failed' in debug:
        return InvalidClientCertificateError(rpc_error, InvalidClientCertificateError.__doc__)
    elif 'Name resolution failure' in debug:
        return UnknownDnsNameError(rpc_error, UnknownDnsNameError.__doc__)
    elif 'Connect Failed' in debug:
        # This error should be checked last because a lot of grpc errors contain said substring.
        return UnableToConnectToRobotError(rpc_error, UnableToConnectToRobotError.__doc__)

    _LOGGER.warning('Unclassified exception: %s', rpc_error)

    return RpcError(rpc_error, RpcError.__doc__)
