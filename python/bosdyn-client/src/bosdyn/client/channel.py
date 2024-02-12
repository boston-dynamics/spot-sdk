# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging
import warnings

import grpc

from .exceptions import (ClientCancelledOperationError, InvalidClientCertificateError,
                         NonexistentAuthorityError, NotFoundError, PermissionDeniedError,
                         ProxyConnectionError, ResponseTooLargeError, RetryableUnavailableError,
                         RpcError, ServiceFailedDuringExecutionError, ServiceUnavailableError,
                         TimedOutError, TooManyRequestsError, TransientFailureError,
                         UnableToConnectToRobotError, UnauthenticatedError, UnimplementedError,
                         UnknownDnsNameError)

TransportError = grpc.RpcError

_LOGGER = logging.getLogger(__name__)

# Set default max message length for sending and receiving. This value is used when
# creating channels in the bosdyn.client.Robot class.
DEFAULT_MAX_MESSAGE_LENGTH = 100 * (1024**2)

# Period in milliseconds after which a keepalive ping is sent on the transport.
DEFAULT_KEEP_ALIVE_TIME_MS = 5000


class RefreshingAccessTokenAuthMetadataPlugin(grpc.AuthMetadataPlugin):
    """Plugin to refresh access token.

    Args:
        token_cb: a callback to provide a valid user token.
    """

    def __init__(self, token_cb):
        self._token_cb = token_cb

    def __call__(self, context, callback):
        user_token_metadata = ('authorization', 'Bearer {}'.format(self._token_cb()))
        metadata = (user_token_metadata,)
        error = None
        callback(metadata, error)


def create_secure_channel_creds(cert, token_cb):
    """Returns credentials for establishing a secure channel.
    Uses previously set values on the linked Sdk and self.
    """

    transport_creds = grpc.ssl_channel_credentials(root_certificates=cert)
    plugin = RefreshingAccessTokenAuthMetadataPlugin(token_cb)
    # Encrypted connections carry either just transport credentials sufficient to
    # establish TLS or both transport and authorization credentials. The auth
    # credentials provide the token with every GRPC call on this channel.
    auth_creds = grpc.metadata_call_credentials(plugin)
    return grpc.composite_channel_credentials(transport_creds, auth_creds)


def create_secure_channel(address, port, creds, authority, options=[]):
    """Create a secure channel to given host:port.

    Args:
        address: Connection host address.
        port: Connection port.
        creds: A ChannelCredentials instance.
        authority: Authority option for the channel.
        options: A list of additional parameters for the GRPC channel.

    Returns:
        A secure channel.
    """

    socket = '{}:{}'.format(address, port)
    complete_options = [('grpc.ssl_target_name_override', authority)]
    complete_options.extend(options)
    return grpc.secure_channel(socket, creds, complete_options)


def create_insecure_channel(address, port, authority=None, options=[]):
    """Create an insecure channel to given host and port.

    This method is only used for testing purposes. Applications must use secure channels to
    communicate with services running on Spot.

    Args:
        address: Connection host address.
        port: Connection port.
        authority: Authority option for the channel.
        options: A list of additional parameters for the GRPC channel.

    Returns:
        An insecure channel.
    """

    socket = '{}:{}'.format(address, port)
    complete_options = []
    if authority:
        complete_options.extend([('grpc.ssl_target_name_override', authority)])
    if options:
        complete_options.extend(options)
    return grpc.insecure_channel(socket, options=complete_options)


def translate_exception(rpc_error):
    """Translated a GRPC error into an SDK RpcError.

    Args:
        rpc_error: RPC error to translate.

    Returns:
        Specific sub-type of RpcError.
    """
    code = rpc_error.code()
    details = rpc_error.details()

    if code is grpc.StatusCode.CANCELLED:
        if str(401) in details:
            return UnauthenticatedError(rpc_error, UnauthenticatedError.__doc__)
        elif str(404) in details:
            return NotFoundError(rpc_error, NotFoundError.__doc__)
        elif str(429) in details:
            return TooManyRequestsError(rpc_error, TooManyRequestsError.__doc__)
        elif str(502) in details:
            return ServiceUnavailableError(rpc_error, ServiceUnavailableError.__doc__)
        elif str(504) in details:
            return TimedOutError(rpc_error, TimedOutError.__doc__)

        return ClientCancelledOperationError(rpc_error, ClientCancelledOperationError.__doc__)
    elif code is grpc.StatusCode.DEADLINE_EXCEEDED:
        return TimedOutError(rpc_error, TimedOutError.__doc__)
    elif code is grpc.StatusCode.UNIMPLEMENTED:
        return UnimplementedError(rpc_error, UnimplementedError.__doc__)
    elif code is grpc.StatusCode.PERMISSION_DENIED:
        return PermissionDeniedError(rpc_error, PermissionDeniedError.__doc__)
    elif code is grpc.StatusCode.RESOURCE_EXHAUSTED:
        if "Received message larger than max" in details:
            return ResponseTooLargeError(rpc_error, ResponseTooLargeError.__doc__)
    elif code is grpc.StatusCode.UNAUTHENTICATED:
        return UnauthenticatedError(rpc_error, UnauthenticatedError.__doc__)

    debug = rpc_error.debug_error_string()
    if debug is not None:
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
        elif 'channel is in state TRANSIENT_FAILURE' in debug:
            return TransientFailureError(rpc_error, TransientFailureError.__doc__)
        elif 'Connect Failed' in debug or 'Failed to pick subchannel' in debug:
            # This error should be checked last because a lot of grpc errors contain said substrings.
            return UnableToConnectToRobotError(rpc_error, UnableToConnectToRobotError.__doc__)

    if code is grpc.StatusCode.UNAVAILABLE:
        if 'Socket closed' in debug or 'Connection reset by peer' in debug:
            return RetryableUnavailableError(rpc_error, RetryableUnavailableError.__doc__)
        if str(502) in details:
            return ServiceUnavailableError(rpc_error, ServiceUnavailableError.__doc__)
        if str(429) in details:
            return TooManyRequestsError(rpc_error, TooManyRequestsError.__doc__)
        return UnableToConnectToRobotError(rpc_error, UnableToConnectToRobotError.__doc__)

    _LOGGER.warning('Unclassified exception: %s', rpc_error)

    return RpcError(rpc_error, RpcError.__doc__)


def generate_channel_options(max_send_message_length=None, max_receive_message_length=None,
                             keep_alive_ping_time_ms=None):
    """Generate the array of options to specify in the creation of a client channel or server.

    The list contains the values for max allowed message length for both sending and
    receiving. If no values are provided, the default values of 100 MB are used. It also contains a
    value for time between keep_alive pings, which default to 5s.

    Args:
        max_send_message_length (int): Max message length allowed for message to send.
        max_receive_message_length (int):  Max message length allowed for message to receive.
        keep_alive_ping_time_ms (int):  Period in milliseconds after which a keepalive ping is sent
        on the transport.

    Returns:
        Array with values for channel options.
    """

    return [('grpc.max_send_message_length', max_send_message_length or DEFAULT_MAX_MESSAGE_LENGTH),
            ('grpc.max_receive_message_length', max_receive_message_length or
             DEFAULT_MAX_MESSAGE_LENGTH),
            ('grpc.keepalive_time_ms', keep_alive_ping_time_ms or DEFAULT_KEEP_ALIVE_TIME_MS)]
