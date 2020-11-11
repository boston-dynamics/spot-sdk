# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Settings common to a user's access to one robot."""
import copy
import logging
import time

import bosdyn.client.channel

from .auth import AuthClient
from .channel import DEFAULT_MAX_MESSAGE_LENGTH
from .data_buffer import DataBufferClient
from .data_service import DataServiceClient
from .directory import DirectoryClient
from .directory_registration import DirectoryRegistrationClient
from .exceptions import Error
from .lease import LeaseWallet
from .payload_registration import PayloadRegistrationClient, PayloadAlreadyExistsError, PayloadNotAuthorizedError
from .power import PowerClient
from .power import power_on as pkg_power_on
from .power import power_off as pkg_power_off
from .power import safe_power_off as pkg_safe_power_off
from .power import is_powered_on as pkg_is_powered_on
from .robot_command import RobotCommandClient
from .robot_id import RobotIdClient
from .robot_state import RobotStateClient
from .time_sync import TimeSyncThread, TimeSyncClient, TimeSyncError
from .token_manager import TokenManager
from .token_cache import TokenCache

_LOGGER = logging.getLogger(__name__)
_DEFAULT_SECURE_CHANNEL_PORT = 443


class RobotError(Error):
    """General class of errors to handle non-response non-grpc errors."""




class UnregisteredServiceError(RobotError):
    """Full service definition has not been registered in the robot instance."""


class UnregisteredServiceNameError(UnregisteredServiceError):
    """Service name has not been registered in the robot instance."""

    def __init__(self, service_name):
        self.service_name = service_name

    def __str__(self):
        return 'Service name "{}" has not been registered'.format(self.service_name)


class UnregisteredServiceTypeError(UnregisteredServiceError):
    """Service type has not been registered in the robot instance."""

    def __init__(self, service_type):
        self.service_type = service_type

    def __str__(self):
        return 'Service type "{}" has not been registered'.format(self.service_type)


class Robot(object):
    """Settings common to one user's access to one robot.

    This is the main point of access to all client functionality.  The ensure_client member is used
    to get any client to a service exposed on the robot.  Additionally, many helpers are exposed to
    provide commonly used functionality without explicitly accessing a particular client object.

    Note that any rpc call made to the robot can raise an RpcError subclass if there are errors
    communicating with the robot.  Additionally, ResponseErrors will be raised if there was an error
    acting on the request itself.  An InvalidRequestError indicates a programming error, where the
    request was malformed in some way.  InvalidRequestErrors will never be thrown except in the
    case of client bugs.

    See also Sdk and BaseClient
    """

    _bootstrap_service_authorities = {
        AuthClient.default_service_name: 'auth.spot.robot',
        DataBufferClient.default_service_name: 'buffer.spot.robot',
        DataServiceClient.default_service_name: 'data.spot.robot',
        DirectoryClient.default_service_name: 'api.spot.robot',
        DirectoryRegistrationClient.default_service_name: 'api.spot.robot',
        PayloadRegistrationClient.default_service_name: 'payload-registration.spot.robot',
        RobotIdClient.default_service_name: 'id.spot.robot',
    }


    def __init__(
            self,
            name=None
    ):
        self._name = name
        self.address = None
        self.serial_number = None
        self.logger = logging.getLogger(self._name or 'bosdyn.Robot')
        self.user_token = None
        self.token_cache = TokenCache()
        self._token_manager = None
        self._current_user = None
        self.service_clients_by_name = {}
        self.channels_by_authority = {}
        self.authorities_by_name = {}
        self._robot_id = None


        # Things usually updated from an Sdk object.
        self.service_client_factories_by_type = {}
        self.service_type_by_name = {}
        self.request_processors = []
        self.response_processors = []
        self.app_token = None
        self.cert = None
        self.lease_wallet = LeaseWallet()
        self._time_sync_thread = None

        # Set default max message length for sending and receiving. These values are used when
        # creating channels.
        self.max_send_message_length = DEFAULT_MAX_MESSAGE_LENGTH
        self.max_receive_message_length = DEFAULT_MAX_MESSAGE_LENGTH

    def __del__(self):
        if self._time_sync_thread:
            self._time_sync_thread.stop()
        if self._token_manager:
            self._token_manager.stop()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def __enter__(self):
        return self

    def _get_token_id(self, username):
        return '{}.{}'.format(self.serial_number, username)

    def _update_token_cache(self, username=None):
        """Updates the cache with the existing user token.

           This method also instantiates a token manager to refresh the
           user token.  Furthermore, it should only be called after the
           token has been retrieved.

        Raises:
            token_cache.WriteFailedError: Error saving to the cache.
        """
        self._token_manager = self._token_manager or TokenManager(self)

        self._current_user = username or self._current_user

        if self._current_user:
            key = self._get_token_id(self._current_user)
            self.token_cache.write(key, self.user_token)

    def setup_token_cache(self, token_cache=None, unique_id=None):
        """Instantiates a token cache to persist the user token.

           If the user provides a cache, it will be saved in the robot object for convenience."""
        self.serial_number = unique_id or self.serial_number or self.get_id().serial_number
        self.token_cache = token_cache or self.token_cache

    def update_from(self, other):
        """Adds to this object's processors, etc based on other"""
        self.request_processors = other.request_processors + self.request_processors
        self.response_processors = other.response_processors + self.response_processors
        self.service_client_factories_by_type.update(other.service_client_factories_by_type)
        self.service_type_by_name.update(other.service_type_by_name)
        # Don't know the types here, so use explicit deepcopy.
        self.cert = copy.deepcopy(other.cert)
        self.logger = other.logger.getChild(self._name or 'Robot')
        self.max_send_message_length = other.max_send_message_length
        self.max_receive_message_length = other.max_receive_message_length


    def ensure_client(self, service_name, channel=None, options=[]):
        """Ensure a Client for a given service.
        Note: If a new service has been registered with the directory service, this may raise
        UnregisteredServiceNameError when trying to connect to it until sync_with_directory() is
        called.

        Args:
            service_name: The name of the service.
            channel: gRPC channel object to use. Default None, in which case the Sdk data
                       is used to generate a channel. The channel will become associated with
                       the client.

        Raises:
            UnregisteredServiceNameError: The service is not known.
            UnregisteredServiceTypeError: The client type for this service was never registered.
            RpcError:                There was an error communicating with the robot.
        """
        # Check if a client with this name is already running
        if service_name in self.service_clients_by_name:
            return self.service_clients_by_name[service_name]

        # Create an instance of the class
        try:
            service_type = self.service_type_by_name[service_name]
        except KeyError:
            raise UnregisteredServiceNameError(service_name)
        try:
            creation_function = self.service_client_factories_by_type[service_type]
        except KeyError:
            raise UnregisteredServiceTypeError(service_type)

        client = creation_function()
        self.logger.debug('Created client for %s', service_name)

        if channel is None:
            channel = self.ensure_channel(service_name, options=options)

        client.channel = channel
        client.update_from(self)
        # Track service clients that have been created to avoid duplicate clients
        self.service_clients_by_name[service_name] = client
        return client

    def get_cached_robot_id(self):
        """Return the RobotId proto for this robot, querying it from the robot if not yet cached.

        Raises:
            RpcError: There as a problem communicating with the robot.
        """
        if not self._robot_id:
            robot_id_client = self.ensure_client('robot-id')
            self._robot_id = robot_id_client.get_id()
        return self._robot_id

    def _should_send_app_token_on_each_request(self):
        robot_id = self.get_cached_robot_id()
        robot_software_version = robot_id.software_release.version
        # Send app tokens on 1.1.x and below versions of robot software to be backwards
        # compatible
        if robot_software_version.major_version <= 1 and robot_software_version.minor_version <= 1:
            return True
        # Otherwise, the robot software is recent enough to not require app tokens on every
        # request. Don't add them to help save data usage.
        return False


    def ensure_channel(self, service_name, options=[]):
        """Verify the right information exists before calling the ensure_secure_channel
        method.

        Args:
            service_name: Name of the service in the directory.
        Returns:
            Existing channel if found, or newly created channel if not found.
        Raises:
            RpcError: There was a problem communicating with the robot.
            UnregisteredServiceNameError: service_name is unknown.
        """

        # Update max send/receive message lengths.
        if 'grpc.max_receive_message_length' not in [option[0] for option in options]:
            options.append(('grpc.max_receive_message_length', self.max_receive_message_length))
        if 'grpc.max_send_message_length' not in [option[0] for option in options]:
            options.append(('grpc.max_send_message_length', self.max_send_message_length))


        # If a specific channel was not set, look up the authority so we can get a channel.
        # Get the authority from either
        #   1. The bootstrap authority for this client_class, if available
        #   2. The authority of a registered service with matching service_name in DirectoryService
        authority = Robot._bootstrap_service_authorities.get(service_name)

        # Attempt to get authority from the robot Directory Service by name
        if not authority:
            authority = self.authorities_by_name.get(service_name)
            if not authority:
                self.sync_with_directory()
                authority = self.authorities_by_name.get(service_name)

        # If authority still not known, then the service name has not been registered.
        if not authority:
            raise UnregisteredServiceNameError(service_name)

        skip_app_token_check = service_name == 'robot-id'
        return self.ensure_secure_channel(authority, skip_app_token_check, options=options)

    def ensure_secure_channel(self, authority, skip_app_token_check=False, options=[]):
        """Get the channel to access the given authority, creating it if it doesn't exist."""
        if authority in self.channels_by_authority:
            return self.channels_by_authority[authority]

        if skip_app_token_check:
            should_send_app_token = False
        else:
            should_send_app_token = self._should_send_app_token_on_each_request()

        # Channel doesn't exist, so create it.
        port = _DEFAULT_SECURE_CHANNEL_PORT
        creds = bosdyn.client.channel.create_secure_channel_creds(
            self.cert, lambda: (self.app_token, self.user_token), should_send_app_token)
        channel = bosdyn.client.channel.create_secure_channel(self.address, port, creds, authority,
                                                              options=options)
        self.logger.debug('Created channel to %s at port %i with authority %s', self.address, port,
                          authority)
        self.channels_by_authority[authority] = channel
        return channel


    def authenticate(
            self,
            username,
            password,
            timeout=None
    ):
        """Authenticate to this Robot with the username/password at the given service.

        Raises:
            InvalidLoginError: The username and/or password are not valid.
            token_cache.WriteFailedError: Authentication succeeded, but failed to update the
                local token_cache.
            RpcError: There was a problem communicating with the robot.
        """
        # We cannot use the directory for the auth service until we are authenticated, so hard-code
        # the authority name.
        auth_channel = self.ensure_secure_channel(
            Robot._bootstrap_service_authorities[AuthClient.default_service_name])
        auth_client = self.ensure_client(AuthClient.default_service_name, auth_channel)
        user_token = auth_client.auth(username, password, self.app_token, timeout=timeout)

        self.update_user_token(user_token, username)

    def authenticate_with_token(self, token, timeout=None):
        """Authenticate to this Robot with the token at the given service.

        Raises:
            InvalidTokenError: The token was incorrectly formed, for the wrong robot, or expired.
            token_cache.WriteFailedError: Authentication succeeded, but failed to update the
                local token_cache.
            RpcError: There was a problem communicating with the robot.
        """
        # We cannot use the directory for the auth service until we are authenticated, so hard-code
        # the authority name.
        auth_client = self.ensure_client(AuthClient.default_service_name)
        user_token = auth_client.auth_with_token(token, self.app_token, timeout=timeout)

        self.update_user_token(user_token)

    def authenticate_from_cache(self, username, timeout=None):
        """Authenticate to this Robot with a cached token at the given service.

        Raises:
            token_cache.NotInCacheError: No token found for this robot/username.
            token_cache.WriteFailedError: Authentication succeeded, but failed to update the
                local token_cache.
        """
        token = self.token_cache.read(self._get_token_id(username))

        # We cannot use the directory for the auth service until we are authenticated, so hard-code
        # the authority name.
        auth_client = self.ensure_client(AuthClient.default_service_name)
        user_token = auth_client.auth_with_token(token, self.app_token, timeout=timeout)

        self.update_user_token(user_token, username)

    def authenticate_from_payload_credentials(self, guid, secret, payload_registration_client=None,
                                              timeout=None):
        """Authenticate to this Robot with the guid/secret of the hosting payload.

        This call is used to authenticate to a robot using payload credentials. If a payload is
        not yet authorized, it will block until the payload is authorized by an operator in the
        robot web page.
        
        Raises:
            InvalidPayloadCredentialsError: The guid and/or secret are not valid.
            token_cache.WriteFailedError: Authentication succeeded, but failed to update the
                local token_cache.
            RpcError: There was a problem communicating with the robot.
        """
        printed_warning = False
        if payload_registration_client is None:
            payload_registration_client = self.ensure_client(
                PayloadRegistrationClient.default_service_name)
        user_token = None
        while user_token is None:
            try:
                user_token = payload_registration_client.get_payload_auth_token(
                    guid, secret, timeout=timeout)
            except PayloadNotAuthorizedError:
                if not printed_warning:
                    printed_warning = True
                    print('Payload is not authorized. Authentication will block until an'
                          ' operator authorizes the payload in the Admin Console.')
                pass
            time.sleep(0.1)
        self.update_user_token(user_token)

    def update_user_token(self, user_token, username=None):
        """Update this Robot with a user token.

        Raises:
            token_cache.WriteFailedError: Error saving to the cache.
        """
        self.user_token = user_token
        self._update_token_cache(username)

    def get_cached_usernames(self):
        """Return an ordered list of usernames queryable from the cache."""
        matches = self.token_cache.match(self.serial_number)
        usernames = []
        for match in matches:
            _, username = match.split('.')
            usernames.extend([username])

        return sorted(usernames)

    def get_id(self, id_service_name=RobotIdClient.default_service_name):
        """Get all the information that identifies the robot."""
        id_client = self.ensure_client(id_service_name)
        return id_client.get_id()

    def list_services(self, directory_service_name=DirectoryClient.default_service_name,
                      directory_service_authority=_bootstrap_service_authorities[
                          DirectoryClient.default_service_name]):
        """Get all the available services on the robot."""
        directory_channel = self.ensure_secure_channel(directory_service_authority)
        dir_client = self.ensure_client(directory_service_name, directory_channel)
        return dir_client.list()

    def sync_with_directory(self, directory_service_name=DirectoryClient.default_service_name,
                            directory_service_authority=_bootstrap_service_authorities[
                                DirectoryClient.default_service_name]):
        """Update local state with all available services on the robot.

        Returns:
            Dict[string, string]: Mapping of service name to service type
        """
        remote_services = self.list_services(
            directory_service_name=directory_service_name,
            directory_service_authority=directory_service_authority)
        for service in remote_services:
            self.authorities_by_name[service.name] = service.authority
            self.service_type_by_name[service.name] = service.type
        return self.service_type_by_name


    def register_payload_and_authenticate(self, payload, secret, timeout=None):
        """Register a payload with the robot and request a user_token.

        This method will block until the payload is authorized by an operator in the robot webpage.
        Raises:
            InvalidPayloadCredentialsError: The guid and/or secret are not valid.
            InvalidPayloadCredentialsError: The payload was rejected on the robot web page.
            token_cache.WriteFailedError: Authentication succeeded, but failed to update the
                local token_cache.
            RpcError: There was a problem communicating with the robot.
        """
        payload_registration_client = self.ensure_client(
            PayloadRegistrationClient.default_service_name)
        try:
            payload_registration_client.register_payload(payload, secret, timeout=timeout)
        except PayloadAlreadyExistsError:
            pass
        self.authenticate_from_payload_credentials(
            payload.GUID, secret, payload_registration_client=payload_registration_client,
            timeout=timeout)

    def start_time_sync(self, time_sync_interval_sec=None):
        """Start time sync thread if needed.

        Args:
            val (float): The interval (in seconds) that the time-sync estimate should be updated.
        """
        if not self._time_sync_thread:
            self._time_sync_thread = TimeSyncThread(
                self.ensure_client(TimeSyncClient.default_service_name))
        if time_sync_interval_sec:
            self._time_sync_thread.time_sync_interval_sec = time_sync_interval_sec
        if self._time_sync_thread.stopped:
            self._time_sync_thread.start()

    def stop_time_sync(self):
        """Stop the time sync thread if needed."""
        if not self._time_sync_thread.stopped:
            self._time_sync_thread.stop()

    @property
    def time_sync(self):
        """Accessor for the time-sync thread.  Creates and starts thread if not already started."""
        self.start_time_sync()
        return self._time_sync_thread

    def operator_comment(self, comment, timestamp_secs=None, timeout=None):
        """Send an operator comment to the robot for the robot's log files.

        Args:
           comment (string):        Operator comment text to be added to the log.
           timestamp_secs (float):  Comment time in seconds since the unix epoch (client clock).
                                    If set, this is converted to robot time when sent to the robot.
                                    If None and time sync is available, the current time is converted
                                    to robot time and sent as the comment timestamp.
                                    If None and time sync is unavailable, the logged timestamp will
                                    be the time the robot receives this message.
           timeout (float):         Number of seconds to wait for RPC response.

        Raises:
          NotEstablishedError: timestamp_secs given, but time-sync has not been achieved.
          RpcError:            A problem occurred sending the comment to the robot.
        """
        client = self.ensure_client(DataBufferClient.default_service_name)
        if timestamp_secs is None:
            try:
                robot_timestamp = self.time_sync.robot_timestamp_from_local_secs(time.time())
            except TimeSyncError:
                robot_timestamp = None  # Timestamp will be set when robot receives the reques msg.
        else:
            # This will raise an exception if time-sync is unavailable.
            robot_timestamp = self.time_sync.robot_timestamp_from_local_secs(timestamp_secs)
        client.add_operator_comment(comment, robot_timestamp=robot_timestamp, timeout=timeout)

    def power_on(self, timeout_sec=20, update_frequency=1.0, timeout=None):
        """Power on robot. This function blocks until robot powers on.

        Args:
            timeout_sec (float): Max time this function will block for.
            update_frequency (float): Frequency at which power status is checked.
            timeout: Number of seconds to wait for RPC response.

        Raises:
            PowerResponseError: Problem with the power on sequence.
            RpcError:           Problem communicating with the robot.
            power_client.CommandTimedOutError: The robot did not power on within timeout_sec
        """
        service_name = PowerClient.default_service_name
        client = self.ensure_client(service_name)
        pkg_power_on(client, timeout_sec, update_frequency, timeout=timeout)

    def power_off(self, cut_immediately=False, timeout_sec=20, update_frequency=1.0, timeout=None):
        """Power off robot. This function blocks until robot powers off. By default, this will
        attempt to put the robot in a safe state before cutting power.

        Args:
            cut_immediately (bool): True to cut power to the robot immediately. False to issue a
                safe power off command to the robot.
            timeout_sec (float): Max time this function will block for.
            update_frequency (float): Frequency at which power status is checked.
            timeout: Number of seconds to wait for RPC response.

        Raises:
            RpcError:                          Problem communicating with the robot.
            power_client.CommandTimedOutError: The robot did not power off within timeout_sec
            PowerResponseError:        If cut_immediately, raised on problems with the power on
                sequence.
            RobotCommandResponseError: If not cut_immediately, raised on problems with the safe
                power off.
        """
        if cut_immediately:
            power_client = self.ensure_client(PowerClient.default_service_name)
            pkg_power_off(power_client, timeout_sec, update_frequency, timeout=timeout)
        else:
            # Ideally we wouldn't need a state client, and all feedback could come from command
            # service. For V1, we should either implement this, or remove feedback from the proto
            # we are releasing. See bugzilla bug 4111 for more details.
            command_client = self.ensure_client(RobotCommandClient.default_service_name)
            state_client = self.ensure_client(RobotStateClient.default_service_name)
            pkg_safe_power_off(command_client, state_client, timeout_sec, update_frequency,
                               timeout=timeout)

    def is_powered_on(self, timeout=None):
        """Check the power state of the robot.

        Args:
            timeout: Number of seconds to wait for RPC response.

        Returns:
            bool: Returns True if robot is powered on, False otherwise.

        Raises:
            RpcError: A problem occurred trying to communicate with the robot.
        """
        state_client = self.ensure_client(RobotStateClient.default_service_name)
        return pkg_is_powered_on(state_client, timeout=timeout)

    def get_frame_tree_snapshot(self, timeout=None):
        """Get the current frame tree snapshot from the robot state client.

        Args:
            timeout: Number of seconds to wait for RPC response.

        Returns:
            An instance of the bosdyn.api.FrameTreeSnapshot that contains data
            from the latest robot state.

        Raises:
          RpcError: A problem occurred sending the comment to the robot.
        """
        client = self.ensure_client(RobotStateClient.default_service_name)
        current_state = client.get_robot_state(timeout=timeout)
        return current_state.kinematic_state.transforms_snapshot


