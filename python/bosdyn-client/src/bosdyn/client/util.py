# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Helper functions and classes for creating client applications."""

from __future__ import print_function

import copy
import getpass
import glob
import logging
import os
import signal
import sys
import threading
import time
from concurrent import futures

import google.protobuf.descriptor
import grpc
import six
from deprecated import deprecated

import bosdyn.client.server_util
from bosdyn.client.auth import InvalidLoginError, InvalidTokenError
from bosdyn.client.channel import generate_channel_options
from bosdyn.client.exceptions import Error

_LOGGER = logging.getLogger(__name__)


def cli_login_prompt(username=None, password=None):
    """Interactive CLI for scripting conveniences."""
    if username is None:
        print('Username: ', end='', file=sys.stderr)
        username = six.moves.input('')
    elif password is None:
        print('Username for robot [{}]: '.format(username), end='', file=sys.stderr)
        name = six.moves.input('')
        if name:
            username = name

    password = getpass.getpass(prompt='[{}] Password: '.format(username), stream=sys.stderr)
    return (username, password)


def cli_auth(robot, username=None, password=None):
    """Interactive CLI for authenticating with the robot."""
    successful = False
    while not successful:
        username, password = cli_login_prompt(username, password)
        try:
            robot.authenticate(username, password)
            successful = True
        except (InvalidLoginError, Error) as e:
            _LOGGER.exception(e)


def authenticate(robot, askpass=None):
    """Generic function for authenticating with the robot.

    Tries to authenticate using the following methods, in order:
        - An existing auth token
        - Username/Password supplied in the environment
        - With a specified callback function, returning a username and password.
        - A command line prompt, if possible (stdin is a tty).

    Args:
        askpass: A function that retrieves authentication credentials if none are specified via
                 environment variables.
    """
    # Try to re-authenticate with token. Continue if token expired or invalid.
    if robot.user_token:
        try:
            robot.authenticate_with_token(robot.user_token)
            return
        except InvalidTokenError as e:
            pass

    # Try to authenticate with credentials specified in environment.
    username = os.environ.get('BOSDYN_CLIENT_USERNAME')
    password = os.environ.get('BOSDYN_CLIENT_PASSWORD')
    if username and password:
        robot.authenticate(username, password)
        return

    # Fail if no way to ask for credentials.
    if not sys.stdin.isatty() and askpass is None:
        raise RuntimeError('Stdin is not a tty and no askpass specified.')

    # Get credentials and try to authenticate.
    if askpass is None:
        username, password = cli_login_prompt()
    else:
        username, password = askpass()

    robot.authenticate(username, password)


class DedupLoggingMessages(logging.Filter):
    """Logger filter to prevent duplicated messages from being logged.

    Args:
        always_print_logger_levels (set[logging.Level]): A set of logging levels which
                                                    any logged message at that level will
                                                    always be logged.
    """

    def __init__(self, always_print_logger_levels={logging.CRITICAL, logging.ERROR}):
        # Warning level mapped to last message logged.
        self.last_error_message = None
        self.always_print_logger_levels = always_print_logger_levels

    def filter(self, record):
        warning_level = record.levelno
        # Always allow messages above a certain warning level to be logged.
        if warning_level in self.always_print_logger_levels:
            return True

        error_message = record.getMessage()
        # Deduplicate logged messages by preventing a message that was just logged to be sent again.
        if self.last_error_message != error_message and error_message is not None:
            self.last_error_message = error_message
            return True

        return False


def setup_logging(verbose=False, include_dedup_filter=False,
                  always_print_logger_levels={logging.CRITICAL, logging.ERROR}):
    """Set up a basic streaming console handler at the root logger.

    Args:
        verbose (boolean): if False (default) show messages at INFO level and above,
                           if True show messages at DEBUG level and above.
        include_dedup_filter (boolean): If true, the logger includes a filter which
                                        will prevent repeated duplicated messages
                                        from being logged.
        always_print_logger_levels (set[logging.Level]): A set of logging levels which
                                                        any logged message at that level will
                                                        always be logged.
    """
    logger = get_logger()

    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    if not logger.handlers:
        streamlog = logging.StreamHandler()
        streamlog.setLevel(level)
        streamlog.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        if include_dedup_filter:
            # Propagate the filter through the handler. logging.Filter does not propagate to other
            # child loggers on its own, and must be attached to the handler.
            streamlog.addFilter(DedupLoggingMessages(always_print_logger_levels))
        logger.addHandler(streamlog)

    if logger.handlers and include_dedup_filter:
        # If a logger has existing handlers, check if the filter is there already. Also check if it is part of the
        # main log already. If not, add it to a new handler.
        filter_exists = None
        for handler in logger.handlers:
            filter_exists = filter_exists or does_dedup_filter_exist(handler,
                                                                     always_print_logger_levels)
        if not filter_exists:
            dedupFilterLog = logging.StreamHandler()
            # Propagate the filter through the handler. logging.Filter does not propagate to other
            # child loggers on its own, and must be attached to the handler.
            dedupFilterLog.addFilter(DedupLoggingMessages(always_print_logger_levels))
            logger.addHandler(dedupFilterLog)

    # Add the level and filter onto just the regular logger as well.
    logger.setLevel(level)
    if include_dedup_filter:
        if not does_dedup_filter_exist(logger, always_print_logger_levels):
            logger.addFilter(DedupLoggingMessages(always_print_logger_levels))


def does_dedup_filter_exist(logger, always_print_logger_levels):
    """Check if the DedupLoggingMessages filter exists for a logger.

    Returns:
        Boolean indicating if the DedupLoggingMessages filter already exists and matches the new parameters.
    """
    for filt in logger.filters:
        if type(
                filt
        ) == DedupLoggingMessages and filt.always_print_logger_levels == always_print_logger_levels:
            return True
    return False


def get_logger():
    return logging.getLogger()


def add_base_arguments(parser):
    """Add hostname argument to parser.

    Args:
        parser: Argument parser object.
    """
    parser.add_argument('hostname', help='Hostname or address of robot,'
                        ' e.g. "beta25-p" or "192.168.80.3"')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print debug-level messages')


def add_credentials_arguments(parser, credentials_no_warn=False):
    """Add username/password flags to parser.

    This function is marked deprecated and will be removed in a future release.

    Args:
        parser: Argument parser object.
    """

    def deprecated_username(arg):
        print(
            'Command line credentials deprecated! '
            'Please use BOSDYN_CLIENT_USERNAME and BOSDYN_CLIENT_PASSWORD env vars instead.',
            file=sys.stderr)
        return arg

    def deprecated_password(arg):
        print(
            'Command line credentials deprecated! '
            'Please use BOSDYN_CLIENT_USERNAME and BOSDYN_CLIENT_PASSWORD env vars instead.',
            file=sys.stderr)
        return arg

    if (not credentials_no_warn):
        _LOGGER.warning('Credentials in program options is deprecated. '
                        'Obtain credentials securely, such as with an environment variable, '
                        'interactive prompt, etc.')
    parser.add_argument('--username', type=deprecated_username,
                        help='[DEPRECATED] Username to use for authentication.')
    parser.add_argument('--password', type=deprecated_password,
                        help='[DEPRECATED] Password to use for authentication.')


def add_common_arguments(parser, credentials_no_warn=False):
    """Add arguments common to most applications used for authentication.

    This function is marked deprecated and will be removed in a future release.  Users should use
    add_base_arguments instead.

    Args:
        parser: Argument parser object.
    """
    add_credentials_arguments(parser, credentials_no_warn=credentials_no_warn)
    add_base_arguments(parser)


def read_payload_credentials(filename):
    """Read the guid and secret from a file.  The file should have the guid and secret
    as the first and second lines in the file.

    Args:
        filename: Name of the file to read.

    Returns:
        Tuple of (guid, secret)

    Raises:
         OSError if the credential file cannot be read.
         ValueError if the guid or secret are missing from the file.
    """
    with open(filename, 'r') as credentials_file:
        guid = credentials_file.readline().strip()
        secret = credentials_file.readline().strip()
    if not guid or not secret:
        raise ValueError('Failed to load GUID ({}) and/or secret ({}).'.format(guid, secret))
    return guid, secret


def get_guid_and_secret(parsed_options):
    """Get the guid and secret for a payload, based on the options that were added
    via add_payload_credentials_arguments().

    Args:
        parsed_options: Namespace result of parser.parse_args()

    Returns:
        Tuple of (guid, secret)

    Raises:
         OSError if the credential file cannot be read.
         Exception if no applicable arguments are given.
    """
    if parsed_options.guid or parsed_options.secret:
        return parsed_options.guid, parsed_options.secret
    if parsed_options.payload_credentials_file:
        return read_payload_credentials(parsed_options.payload_credentials_file)
    raise Exception('No payload credentials provided. Use --guid and --secret'
                    ' or --payload-credentials-file.')


def add_payload_credentials_arguments(parser, required=True):
    """Add arguments common to most payload related applications.
    Use get_guid_and_secret() to get the guid and secret from the resulting parse.

    Args:
        parser: Argument parser object.
        required: Require either the guid/secret or file arguments to be provided.
    """
    group = parser.add_mutually_exclusive_group(required=required)
    group.add_argument('--guid', help='Unique GUID of the payload.')
    parser.add_argument('--secret', help='Secret of the payload.')
    group.add_argument('--payload-credentials-file',
                       help='File from which to read payload guid and secret')


def add_service_hosting_arguments(parser):
    """Add arguments common to most applications hosting a GRPC service.

    Args:
        parser: Argument parser object.
    """
    parser.add_argument(
        '--port', default=0, help=
        ('The port number the service can be reached at (Warning: This port cannot be firewalled).'
         ' Defaults to 0, which will assign an ephemeral port'), type=int)


def add_service_endpoint_arguments(parser):
    """Add arguments common to most applications defining a GRPC service endpoint.

    Args:
        parser: Argument parser object.
    """
    add_service_hosting_arguments(parser)
    parser.add_argument(
        '--host-ip', required=True, help='Hostname or address the service can be reached at.'
        ' e.g. "192.168.50.5"')


@deprecated(reason='App tokens are no longer in use. Authorization is now handled via licenses.',
            version='2.0.1', action="always")
def default_app_token_path():
    """Do nothing, this method is kept only to maintain backwards compatibility."""
    return


@deprecated(reason='The GrpcServiceRunner class helper has moved to server_util.py. Please use '
            'bosdyn.client.server_util.GrpcServiceRunner.', version='3.0.0', action="always")
class GrpcServiceRunner(object):
    """A runner to start a gRPC server on a background thread and allow easy cleanup.

    Args:
        service_servicer (custom servicer class derived from ServiceServicer): Servicer that
            defines server behavior.
        add_servicer_to_server_fn (function): Function generated by gRPC compilation that
            attaches the servicer to the gRPC server.
        port (int): The port number the service can be accessed through on the host system.
            Defaults to 0, which will assign an ephemeral port.
        max_send_message_length (int): Max message length (bytes) allowed for messages sent.
        max_receive_message_length (int): Max message length (bytes) allowed for messages received.
        timeout_secs (int): Number of seconds to wait for a clean server shutdown.
        force_sigint_capture (bool): Re-assign the SIGINT handler to default in order to prevent
            other scripts from blocking a clean exit. Defaults to True.
        logger (logging.Logger): Logger to log with.
    """

    def __init__(self, service_servicer, add_servicer_to_server_fn, port=0, max_workers=4,
                 max_send_message_length=None, max_receive_message_length=None, timeout_secs=3,
                 force_sigint_capture=True, logger=None):
        self.logger = logger or _LOGGER
        self.timeout_secs = timeout_secs
        self.force_sigint_capture = force_sigint_capture

        # Use the name of the service_servicer class for print messages.
        self.server_type_name = type(service_servicer).__name__

        self.server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=max_workers),
            options=generate_channel_options(max_send_message_length, max_receive_message_length))
        add_servicer_to_server_fn(service_servicer, self.server)
        self.port = self.server.add_insecure_port('[::]:{}'.format(port))
        self.server.start()
        self.logger.info('Started the {} server.'.format(self.server_type_name))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def stop(self):
        self.logger.info("Shutting down the {} server.".format(self.server_type_name))
        shutdown_complete = self.server.stop(None)
        shutdown_complete.wait(self.timeout_secs)

    def run_until_interrupt(self):
        """Spin the thread until a SIGINT is received and then shut down cleanly."""
        if self.force_sigint_capture:
            # Ensure that KeyboardInterrupt is raised on a SIGINT.
            signal.signal(signal.SIGINT, signal.default_int_handler)

        # Monitor for SIGINT and shut down cleanly.
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        self.stop()



populate_response_header = deprecated(
    reason='The populate_response_header helper has moved to '
    'server_util.py. Please use bosdyn.client.server_util.populate_response_header.',
    version='3.0.0', action="always")(bosdyn.client.server_util.populate_response_header)

strip_large_bytes_fields = deprecated(
    reason='The strip_large_bytes_fields helper has moved to '
    'server_util.py. Please use bosdyn.client.server_util.strip_large_bytes_fields.',
    version='3.0.0', action="always")(bosdyn.client.server_util.strip_large_bytes_fields)

get_bytes_field_whitelist = deprecated(
    reason='The get_bytes_field_whitelist helper has moved to '
    'server_util.py. Please use bosdyn.client.server_util.get_bytes_field_allowlist.',
    version='3.0.0', action="always")(bosdyn.client.server_util.get_bytes_field_allowlist)

strip_image_response = deprecated(
    reason='The strip_image_response helper has moved to '
    'server_util.py. Please use bosdyn.client.server_util.strip_image_response.', version='3.0.0',
    action="always")(bosdyn.client.server_util.strip_image_response)

strip_get_image_response = deprecated(
    reason='The strip_get_image_response helper has moved to '
    'server_util.py. Please use bosdyn.client.server_util.strip_get_image_response.',
    version='3.0.0', action="always")(bosdyn.client.server_util.strip_get_image_response)

strip_local_grid_responses = deprecated(
    reason='The strip_local_grid_responses helper has moved to '
    'server_util.py. Please use bosdyn.client.server_util.strip_local_grid_responses.',
    version='3.0.0', action="always")(bosdyn.client.server_util.strip_local_grid_responses)

strip_store_image_request = deprecated(
    reason='The strip_store_image_request helper has moved to '
    'server_util.py. Please use bosdyn.client.server_util.strip_store_image_request.',
    version='3.0.0', action="always")(bosdyn.client.server_util.strip_store_image_request)

strip_store_data_request = deprecated(
    reason='The strip_store_data_request helper has moved to '
    'server_util.py. Please use bosdyn.client.server_util.strip_store_data_request.',
    version='3.0.0', action="always")(bosdyn.client.server_util.strip_store_data_request)

strip_record_signal_tick = deprecated(
    reason='The strip_record_signal_tick helper has moved to '
    'server_util.py. Please use bosdyn.client.server_util.strip_record_signal_tick.',
    version='3.0.0', action="always")(bosdyn.client.server_util.strip_record_signal_tick)

strip_record_data_blob = deprecated(
    reason='The strip_record_data_blob helper has moved to '
    'server_util.py. Please use bosdyn.client.server_util.strip_record_data_blob.', version='3.0.0',
    action="always")(bosdyn.client.server_util.strip_record_data_blob)

strip_log_annotation = deprecated(
    reason='The strip_log_annotation helper has moved to '
    'server_util.py. Please use bosdyn.client.server_util.strip_log_annotation.', version='3.0.0',
    action="always")(bosdyn.client.server_util.strip_log_annotation)
