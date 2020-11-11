# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Sdk is  a repository for settings typically common to a single developer and/or robot fleet."""
from __future__ import absolute_import
import glob
import logging
import os
import platform
import warnings

import datetime
from enum import Enum
import jwt
import pkg_resources

from .auth import AuthClient
from .channel import DEFAULT_MAX_MESSAGE_LENGTH
from .data_acquisition import DataAcquisitionClient
from .data_acquisition_store import DataAcquisitionStoreClient
from .data_buffer import DataBufferClient
from .data_service import DataServiceClient
from .directory import DirectoryClient
from .directory_registration import DirectoryRegistrationClient
from .docking import DockingClient
from .estop import EstopClient
from .fault import FaultClient
from .exceptions import Error
from .graph_nav import GraphNavClient
from .image import ImageClient
from .lease import LeaseClient
from .license import LicenseClient
from .log_annotation import LogAnnotationClient
from .local_grid import LocalGridClient
from .payload import PayloadClient
from .payload_registration import PayloadRegistrationClient
from .point_cloud import PointCloudClient
from .power import PowerClient
from .processors import AddRequestHeader
from .recording import GraphNavRecordingServiceClient
from .robot import Robot
from .robot_command import RobotCommandClient
from .robot_id import RobotIdClient
from .robot_state import RobotStateClient
from .spot_check import SpotCheckClient
from .time_sync import TimeSyncClient
from .world_object import WorldObjectClient


class SdkError(Error):
    """General class of errors to handle non-response non-rpc errors."""


class UnsetAppTokenError(SdkError):
    """Path to app token not set."""


class UnableToLoadAppTokenError(SdkError):
    """Cannot load the provided app token path."""


_LOGGER = logging.getLogger(__name__)

BOSDYN_RESOURCE_ROOT = os.environ.get('BOSDYN_RESOURCE_ROOT',
                                      os.path.join(os.path.expanduser('~'), '.bosdyn'))


def generate_client_name(prefix=''):
    """Returns a descriptive client name for API clients with an optional prefix."""
    import __main__
    try:
        process_info = '{}-{}'.format(os.path.basename(__main__.__file__), os.getpid())
    except AttributeError:
        process_info = '{}'.format(os.getpid())
    machine_name = platform.node()
    if not machine_name:
        import getpass
        try:
            user_name = getpass.getuser()
        # pylint: disable=broad-except
        except Exception:
            _LOGGER.warning('Could not get username')
            user_name = '<unknown host>'
    # Use the name of the host if available, username otherwise.
    return '{}{}:{}'.format(prefix, machine_name or user_name, process_info)


_DEFAULT_SERVICE_CLIENTS = [
    AuthClient,
    DataAcquisitionClient,
    DataAcquisitionStoreClient,
    DataBufferClient,
    DataServiceClient,
    DirectoryClient,
    DirectoryRegistrationClient,
    DockingClient,
    EstopClient,
    FaultClient,
    GraphNavClient,
    GraphNavRecordingServiceClient,
    ImageClient,
    LeaseClient,
    LicenseClient,
    LogAnnotationClient,
    LocalGridClient,
    PayloadClient,
    PayloadRegistrationClient,
    PointCloudClient,
    PowerClient,
    RobotCommandClient,
    RobotIdClient,
    RobotStateClient,
    SpotCheckClient,
    TimeSyncClient,
    WorldObjectClient,
]


def create_standard_sdk(client_name_prefix, service_clients=None, cert_resource_glob=None):
    """Return an Sdk with the most common configuration.

    Args:
        client_name_prefix: prefix to pass to generate_client_name()
        service_clients: List of service client classes to register in addition to the defaults.
        cert_resource_glob: Glob expression matching robot certificate(s).
                              Default None to use distributed certificate.

    Raises:
        IOError: Robot cert could not be loaded.
    """
    _LOGGER.debug('Creating standard Sdk, cert glob: "%s"', cert_resource_glob)
    sdk = Sdk(name=client_name_prefix)
    client_name = generate_client_name(client_name_prefix)
    sdk.load_robot_cert(cert_resource_glob)
    sdk.request_processors.append(AddRequestHeader(lambda: client_name))

    all_service_clients = _DEFAULT_SERVICE_CLIENTS
    if service_clients:
        all_service_clients += service_clients
    for client in all_service_clients:
        sdk.register_service_client(client)
    return sdk




class Sdk(object):
    """Repository for settings typically common to a single developer and/or robot fleet.
    See also Robot for robot-specific settings.

    Args:
        name: Name to identify the client when communicating with the robot.
    """

    def __init__(self, name=None):
        self.cert = None
        self.logger = logging.getLogger(name or 'bosdyn.Sdk')
        self.request_processors = []
        self.response_processors = []
        self.service_client_factories_by_type = {}
        self.service_type_by_name = {}
        # Robots created by this Sdk, keyed by address.
        self.robots = {}

        # Set default max message length for sending and receiving. These values are used when
        # creating channels in the bosdyn.client.Robot class.
        self.max_send_message_length = DEFAULT_MAX_MESSAGE_LENGTH
        self.max_receive_message_length = DEFAULT_MAX_MESSAGE_LENGTH



    def create_robot(
            self,
            address,
            name=None
    ):
        """Get a Robot initialized with this Sdk, creating it if it does not yet exist.

        Args:
            address: Network-resolvable address of the robot, e.g. '192.168.80.3'
            name: A unique identifier for the robot, e.g. 'My First Robot'. Default None to
                        use the address as the name.
        Returns:
            A Robot initialized with the current Sdk settings.
        """


        if address in self.robots:
            return self.robots[address]
        robot = Robot(
            name=name or address
        )
        robot.address = address

        robot.update_from(self)
        self.robots[address] = robot

        return robot

    def set_max_message_length(self, max_message_length):
        """Updates the send and receive max message length values in all the clients/channels
        created from this point on.

        Args:
            max_message_length(int) : Max message length value to use for sending and receiving
                messages.

        Returns:
            None.
        """
        self.max_send_message_length = max_message_length
        self.max_receive_message_length = max_message_length

    def register_service_client(self, creation_func, service_type=None, service_name=None):
        """Tell the Sdk how to create a specific type of service client.

        Args:
            creation_func: Callable that returns a client. Typically just the class.
            service_type: Type of the service. If None (default), will try to get the name from
                creation_func.
            service_name: Name of the service. If None (default), will try to get the name from
                creation_func.
        """

        service_name = service_name or creation_func.default_service_name
        service_type = service_type or creation_func.service_type

        # Some services won't have a default service name at all.
        # They will have to get information from the directory.
        if service_name is not None:
            self.service_type_by_name[service_name] = service_type
        self.service_client_factories_by_type[service_type] = creation_func

    def load_robot_cert(self, resource_path_glob=None):
        """Load the SSL certificate for the robot.

        Args:
            resource_path_glob: Optional path to certificate resource(s).
                If None, will load the certificate in the 'resources' package.
                Otherwise, should be a glob expression to match certificates.
                Defaults to None.
        Raises:
            IOError: Robot cert could not be loaded.
        """
        self.cert = None
        if resource_path_glob is None:
            self.cert = pkg_resources.resource_stream('bosdyn.client.resources', 'robot.pem').read()
        else:
            cert_paths = [c for c in glob.glob(resource_path_glob) if os.path.isfile(c)]
            if not cert_paths:
                raise IOError('No files matched "{}"'.format(resource_path_glob))
            self.cert = bytes()
            for cert_path in cert_paths:
                with open(cert_path, 'rb') as cert_file:
                    self.cert += cert_file.read()

    @staticmethod
    def load_app_token(*_):
        """DEPRECATED (v2.0.1) - Kept for compatibility
        Load an app token from a file, and set it on the SDK.

        Arguments:
            resource_path: Path to app token file on file system.
        """
        warnings.warn(
            "App tokens are deprecated as of 2.0.1.  load_app_token is no longer necessary",
            DeprecationWarning)


def decode_token(token):
    """Decodes a JWT token without verification.

    Args:
        token: A string representing a token.

    Returns:
       Dictionary containing information about the token.
       Empty dictionary if failed to load token.

    Raises:
        UnableToLoadAppTokenError: If the token cannot be read.
    """
    try:
        values = jwt.decode(token, verify=False)
        return values
    except jwt.exceptions.DecodeError as err:
        raise UnableToLoadAppTokenError('Incorrectly formatted token {} --- {}'.format(token, err))
    except Exception as err:
        raise UnableToLoadAppTokenError('Problem decoding token {} --- {}'.format(token, err))


def log_token_time_remaining(token):
    """Log the time remaining until app token expires.

    Arguments:
        token: A jwt token

    Raises:
        UnableToLoadAppTokenError: If the token expiration information cannot be retrieved.
    """
    token_values = decode_token(token)
    if 'exp' not in token_values:
        raise UnableToLoadAppTokenError("Unknown token expiration")

    # Log time to expiration, with varying levels based on nearness.
    expire_time = datetime.datetime.fromtimestamp(token_values['exp'])
    time_to_expiration = expire_time - datetime.datetime.utcnow()
    if time_to_expiration < datetime.timedelta(seconds=0):
        _LOGGER.error('Your application token has expired. Please contact '
                      'support@bostondynamics.com to request a robot license as application '
                      'tokens have been deprecated.')
    elif time_to_expiration <= datetime.timedelta(days=30):
        _LOGGER.warning(
            'Application token expires in %s days on %s. Please contact '
            'support@bostondynamics.com to request a lease as application tokens '
            'have been deprecated.', time_to_expiration.days,
            datetime.datetime.strftime(expire_time, '%Y/%m/%d'))
    else:
        _LOGGER.debug('Application token expires on %s',
                      datetime.datetime.strftime(expire_time, '%Y/%m/%d'))
