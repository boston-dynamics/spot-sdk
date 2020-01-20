"""Settings common to a user's access to one robot."""
import copy
import logging
import time

import bosdyn.client.channel

from .auth import AuthClient
from .directory import DirectoryClient
from .exceptions import NonexistentAuthorityError
from .lease import LeaseWallet
from .log_annotation import LogAnnotationClient
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

class Robot(object):
    """Settings common to one user's access to one robot.

    See also Sdk and BaseClient
    """

    def __init__(self, name=None):
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

        # Things usually updated from an Sdk object.
        self.service_client_factories_by_type = {}
        self.service_type_by_name = {}
        self.request_processors = []
        self.response_processors = []
        self.app_token = None
        self.cert = None
        self.lease_wallet = LeaseWallet()
        self._time_sync_thread = None

    def __del__(self):
        if self._time_sync_thread:
            self._time_sync_thread.stop()

        if self._token_manager:
            self._token_manager.stop()

    def _get_token_id(self, username):
        return '{}.{}'.format(self.serial_number, username)

    def _update_token_cache(self, username=None):
        """Updates the cache with the existing user token.

           This method also instantiates a token manager to refresh the
           user token.  Furthermore, it should only be called after the
           token has been retrieved."""
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
        self.app_token = copy.deepcopy(other.app_token)
        self.cert = copy.deepcopy(other.cert)
        self.logger = other.logger.getChild(self._name or 'Robot')

    def ensure_client(self, service_name, channel=None):
        """Ensure a Client for a given service.

        Args:
            service_name -- The name of the service.
        Keyword args:
            channel -- gRPC channel object to use. Default None, in which case the Sdk data is used
                to generate a channel
        Throws NonexistentServiceError if the service is not found.
        """
        if service_name in self.service_clients_by_name:
            return self.service_clients_by_name[service_name]

        service_type = self.service_type_by_name[service_name]
        creation_function = self.service_client_factories_by_type[service_type]
        client = creation_function()
        self.logger.debug('Created client for %s with %s', service_name, creation_function)
        if channel is None:
            try:
                authority = self.authorities_by_name.get(service_name, client.default_authority)
            except AttributeError:
                raise NonexistentAuthorityError(
                    'Cannot determine authority from service name "{}" or client "{}"'.format(
                        service_type, client))
            channel = self.ensure_channel(authority)
        client.channel = channel
        client.update_from(self)
        self.service_clients_by_name[service_name] = client
        return client

    def ensure_channel(self, authority):
        """Get the channel to access the given authority, creating it if it doesn't exist."""
        if authority in self.channels_by_authority:
            return self.channels_by_authority[authority]

        # Channel doesn't exist, so create it.
        port = _DEFAULT_SECURE_CHANNEL_PORT
        creds = bosdyn.client.channel.create_secure_channel_creds(self.cert,
                                                                  lambda: (self.app_token, self.user_token))
        channel = bosdyn.client.channel.create_secure_channel(self.address, port, creds, authority)
        self.logger.debug('Created channel to %s at port %i', self.address, port)
        self.channels_by_authority[authority] = channel
        return channel

    def authenticate(self, username, password, timeout=None):
        """Authenticate to this Robot with the username/password at the given service.

           This method may throw TokenCache.WriteFailedError."""
        # We cannot use the directory for the auth service until we are authenticated, so hard-code
        # the authority name.
        auth_client = self.ensure_client(AuthClient.default_service_name)
        self.user_token = auth_client.auth(username, password, timeout=timeout)

        self._update_token_cache(username)

    def authenticate_with_token(self, token, timeout=None):
        """Authenticate to this Robot with the token at the given service.

           This method may throw TokenCache.WriteFailedError."""
        # We cannot use the directory for the auth service until we are authenticated, so hard-code
        # the authority name.
        auth_client = self.ensure_client(AuthClient.default_service_name)
        self.user_token = auth_client.auth_with_token(token, timeout=timeout)

        self._update_token_cache()

    def authenticate_from_cache(self, username, timeout=None):
        """Authenticate to this Robot with a cached token at the given service.

           This method may throw TokenCache.NotInCacheError or TokenCache.WriteFailedError."""
        token = self.token_cache.read(self._get_token_id(username))

        # We cannot use the directory for the auth service until we are authenticated, so hard-code
        # the authority name.
        auth_client = self.ensure_client(AuthClient.default_service_name)
        self.user_token = auth_client.auth_with_token(token, timeout=timeout)

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

    def list_services(self, directory_service_name=DirectoryClient.default_service_name):
        """Get all the available services on the robot."""
        dir_client = self.ensure_client(directory_service_name)
        return dir_client.list()

    def sync_with_directory(self):
        remote_services = self.list_services()
        for service in remote_services:
            self.authorities_by_name[service.name] = service.authority
            self.service_type_by_name[service.name] = service.type

    def start_time_sync(self):
        """Start time sync thread if needed."""
        if not self._time_sync_thread:
            self._time_sync_thread = TimeSyncThread(
                self.ensure_client(TimeSyncClient.default_service_name))
        if self._time_sync_thread.stopped:
            self._time_sync_thread.start()

    @property
    def time_sync(self):
        """Accessor for the time-sync thread.  Creates and starts thread if not already started."""
        self.start_time_sync()
        return self._time_sync_thread

    def operator_comment(self, comment, timestamp_secs=None, timeout=None):
        """Send an operator comment to the robot for the robot's log files.

        Args:
           comment (string):      Operator comment text to be added to the log.
           timestamp_secs:        Comment time in seconds since the unix epoch (client clock).
                                  If set, this is converted to robot time when sent to the robot.
                                  If None and time sync is available, the current time is converted
                                   to robot time and sent as the comment timestamp.
                                  If None and time sync is unavailable, the logged timestamp will
                                   be the time the robot receives this message.
           timeout:               Number of seconds to wait for RPC response.

        Raises:
          NotReadyError   |timestamp_secs| given, but time-sync thread is not ready.
          Timeout         |timestamp_secs| given, but time-sync has not been achieved.
        """
        client = self.ensure_client(LogAnnotationClient.default_service_name)
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
            Error: On any failure --> Lots to list here.
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
            Error: On any failure --> Lots to list here.
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
            pkg_safe_power_off(command_client, state_client, timeout_sec, update_frequency, timeout=timeout)

    def is_powered_on(self, timeout=None):
        """Check the power state of the robot.

        Args:
            timeout: Number of seconds to wait for RPC response.

        Returns:
            bool: Returns True if robot is powered on, False otherwise.

        Raises:
            Error: On any failure --> Lots to list here.
        """
        state_client = self.ensure_client(RobotStateClient.default_service_name)
        return pkg_is_powered_on(state_client, timeout=timeout)
