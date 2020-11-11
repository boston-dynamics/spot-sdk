# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Command-line utility code for interacting with robot services."""

from __future__ import print_function, division
import abc
import argparse
import signal
import threading
import time
import os

import numpy as np
import six

from bosdyn.api import image_pb2
from bosdyn.api.data_buffer_pb2 import TextMessage
from bosdyn.api.data_index_pb2 import EventsCommentsSpec
from bosdyn.api.log_annotation_pb2 import LogAnnotationTextMessage
from bosdyn.api import data_acquisition_pb2
import bosdyn.client
from bosdyn.util import (duration_str, timestamp_to_datetime)

from .auth import InvalidLoginError
from .exceptions import Error, InvalidAppTokenError, InvalidRequestError, ProxyConnectionError, ResponseError
from .data_acquisition import DataAcquisitionClient
from .data_buffer import DataBufferClient
from .data_service import DataServiceClient
from .directory import DirectoryClient, NonexistentServiceError
from .directory_registration import DirectoryRegistrationClient, DirectoryRegistrationResponseError
from .estop import EstopClient, EstopEndpoint, EstopKeepAlive
from .payload import PayloadClient
from .payload_registration import PayloadRegistrationClient, PayloadAlreadyExistsError
from .image import (ImageClient, UnknownImageSourceError, ImageResponseError, build_image_request)
from .lease import LeaseClient
from .license import LicenseClient
from .log_annotation import LogAnnotationClient
from .local_grid import LocalGridClient
from .robot_id import RobotIdClient
from .robot_state import RobotStateClient
from .sdk import SdkError
from .time_sync import (TimeSyncClient, TimeSyncEndpoint, TimeSyncError)
from .util import (add_common_arguments, setup_logging)

# pylint: disable=too-few-public-methods
class Command(object, six.with_metaclass(abc.ABCMeta)):
    """Command-line command.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    # The name of the command the user should enter on the command line to select this command.
    NAME = None

    # Whether authentication is needed before the command is run.
    # Most commands need authentication.
    NEED_AUTHENTICATION = True

    def __init__(self, subparsers, command_dict):
        command_dict[self.NAME] = self
        self._parser = subparsers.add_parser(self.NAME, help=self.__doc__)

    def run(self, robot, options):
        """Invoke the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.
        """

        try:
            if self.NEED_AUTHENTICATION:
                robot.authenticate(options.username, options.password)
                robot.sync_with_directory() # Make sure that we can use all registered services.
            return self._run(robot, options)
        except ProxyConnectionError:
            print('Could not contact robot with hostname "{}".'.format(options.hostname))
        except InvalidAppTokenError:
            print('The provided app token "{}" is invalid.'.format(options.app_token))
        except InvalidLoginError:
            print('Username "{}" and/or password are invalid.'.format(options.username))
        except Error as err:
            print('{}: {}'.format(type(err).__name__, err))

    @abc.abstractmethod
    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.
        """


class Subcommands(Command):
    """Run subcommands.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
        subcommands: List of subcommands to run.
    """

    def __init__(self, subparsers, command_dict, subcommands):
        super(Subcommands, self).__init__(subparsers, command_dict)
        command_dest = '{}_command'.format(self.NAME)
        cmd_subparsers = self._parser.add_subparsers(title=self.__doc__, dest=command_dest)
        cmd_subparsers.required = True
        self._subcommands = {}
        for subcommand in subcommands:
            subcommand(cmd_subparsers, self._subcommands)

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            Execution of the specific subcommand from the options.
        """

        command_dest = '{}_command'.format(self.NAME)
        subcommand = vars(options)[command_dest]
        return self._subcommands[subcommand].run(robot, options)


class DirectoryCommands(Subcommands):
    """Commands related to the directory service."""

    NAME = 'dir'

    def __init__(self, subparsers, command_dict):
        """Commands related to the directory service.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(DirectoryCommands, self).__init__(subparsers, command_dict, [
            DirectoryListCommand, DirectoryGetCommand, DirectoryRegisterCommand,
            DirectoryUnregisterCommand
        ])


def _format_dir_entry(name, service_type, authority, tokens, name_width=23, type_width=31,
                      authority_width=27):
    """Prints the passed values as "name service_type authority tokens", with the first three using
    the specified width.

    Args:
        name: Name of the service.
        service_type: Type of the service.
        authority: Authority of the service.
        tokens: Tokens required for using the service.
        name_width: Width for printing the name value.
        type_width: Width for printing the service_type value.
        authority_width: Width for printing the authority value.
    """

    print(('{:' + str(name_width) + '} {:' + str(type_width) + '} {:' + str(authority_width) +
           '} {}').format(name, service_type, authority, tokens))


def _token_req_str(entry):
    """Returns a string representing tokens required for using the service.

    Args:
        entry: Service entry being checked.

    Returns:
        String with a comma-separated list of required tokens.
    """

    required = []
    if entry.user_token_required:
        required.append('user')
    if not required:
        return ''
    return ', '.join(required)


def _show_directory_list(robot, as_proto=False):
    """Print service directory list for robot.

    Args:
        robot: Robot object used to get the list of services.
        as_proto: Boolean to determine whether the directory entries should be printed as full
            proto definitions or formatted strings.

    Returns:
        True
    """

    entries = robot.ensure_client(DirectoryClient.default_service_name).list()
    if not entries:
        print("No services found")
        return True

    if as_proto:
        for entry in entries:
            print(entry)
        return True

    max_name_length = max(len(entry.name) for entry in entries)
    max_type_length = max(len(entry.type) for entry in entries)
    max_authority_length = max(len(entry.authority) for entry in entries)

    _format_dir_entry('name', 'type', 'authority', 'tokens', max_name_length + 4,
                      max_type_length + 4, max_authority_length + 4)
    print("-" * (20 + max_name_length + max_type_length + max_authority_length))
    for entry in entries:
        _format_dir_entry(entry.name, entry.type, entry.authority, _token_req_str(entry),
                          max_name_length + 4, max_type_length + 4, max_authority_length + 4)

    return True


def _show_directory_entry(robot, service, as_proto=False):
    """Print a service directory entry.

    Args:
        robot: Robot object used to get the list of services.
        service: Name of the service to print.
        as_proto: Boolean to determine whether the directory entries should be printed as full
            proto definitions or formatted strings.

    Returns:
        True
    """

    entry = robot.ensure_client(DirectoryClient.default_service_name).get_entry(service)
    if as_proto:
        print(entry)
    else:
        _format_dir_entry('name', 'type', 'authority', 'tokens')
        print("-" * 90)
        _format_dir_entry(entry.name, entry.type, entry.authority, _token_req_str(entry))
    return True


class DirectoryListCommand(Command):
    """List all services in the directory."""

    NAME = 'list'

    def __init__(self, subparsers, command_dict):
        """List all services in the directory.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(DirectoryListCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """
        _show_directory_list(robot, as_proto=options.proto)
        return True


class DirectoryGetCommand(Command):
    """Get entry for a given service in the directory."""

    NAME = 'get'

    def __init__(self, subparsers, command_dict):
        """Get entry for a given service in the directory.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(DirectoryGetCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')
        self._parser.add_argument('service', help='service name to get entry for')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            False if NonexistentServiceError is caught, True otherwise.
        """
        try:
            _show_directory_entry(robot, options.service, as_proto=options.proto)
        except NonexistentServiceError:
            print('The requested service name "{}" does not exist.  Available services:'.format(
                options.service))
            _show_directory_list(robot, as_proto=options.proto)
            return False
        return True


class DirectoryRegisterCommand(Command):
    """Register entry for a service in the directory."""

    NAME = 'register'

    def __init__(self, subparsers, command_dict):
        """Register entry for a service in the directory.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(DirectoryRegisterCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--service-name', required=True,
                                  help='unique name of the service')
        self._parser.add_argument('--service-type', required=True,
                                  help='Type of the service, e.g. bosdyn.api.RobotStateService')
        self._parser.add_argument('--service-authority', required=True,
                                  help='authority of the service')
        self._parser.add_argument('--service-hostname', required=True,
                                  help='hostname of the service computer')
        self._parser.add_argument('--service-port', required=True, type=int,
                                  help='port the service is running on')
        self._parser.add_argument('--no-user-token', action='store_true', required=False,
                                  help='disable requirement for user token')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            False if DirectoryRegistrationResponseError is caught, True otherwise.
        """
        directory_registration_client = robot.ensure_client(
            DirectoryRegistrationClient.default_service_name)

        try:
            directory_registration_client.register(options.service_name, options.service_type,
                                                   options.service_authority,
                                                   options.service_hostname, options.service_port,
                                                   user_token_required=not options.no_user_token)
        except DirectoryRegistrationResponseError as exc:
            print("Failed to register service {}.\nResponse Status: {}".format(
                options.service_name,
                bosdyn.api.directory_registration_pb2.RegisterServiceResponse.Status.Name(
                    exc.response.status)))
            return False
        else:
            print("Succesfully registered service {}".format(options.service_name))
            return True


class DirectoryUnregisterCommand(Command):
    """Unregister entry for a service in the directory."""

    NAME = 'unregister'

    def __init__(self, subparsers, command_dict):
        """Unregister entry for a service in the directory.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(DirectoryUnregisterCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--service-name', required=True,
                                  help='unique name of the service')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            False if DirectoryRegistrationResponseError is caught, True otherwise.
        """
        directory_registration_client = robot.ensure_client(
            DirectoryRegistrationClient.default_service_name)
        try:
            directory_registration_client.unregister(options.service_name)
        except DirectoryRegistrationResponseError as exc:
            print("Failed to unregister service {}.\nResponse Status: {}".format(
                options.service_name,
                bosdyn.api.directory_registration_pb2.UnregisterServiceResponse.Status.Name(
                    exc.response.status)))
            return False
        else:
            print("Succesfully unregistered service {}".format(options.service_name))
            return True


class PayloadCommands(Subcommands):
    """Commands related to the payload and payload registration services."""

    NAME = 'payload'

    def __init__(self, subparsers, command_dict):
        """Commands related to the payload and payload registration services.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(PayloadCommands, self).__init__(subparsers, command_dict, [PayloadListCommand, PayloadRegisterCommand])

def _show_payload_list(robot, as_proto=False):
    """Print payload list for robot.

    Args:
        robot: Robot object used to get the list of services.
        as_proto: Boolean to determine whether the payload entries should be printed as full
            proto definitions or formatted strings.

    Returns:
        True
    """

    payload_protos = robot.ensure_client(PayloadClient.default_service_name).list_payloads()
    if not payload_protos:
        print("No payloads found")
        return True

    if as_proto:
        for payload in payload_protos:
            print(payload)
        return True

    # Print out the payload name, description, and GUID in columns with set width.
    name_width = 30
    description_width = 60
    guid_width = 36
    print(('\n{:' + str(name_width) + '} {:' + str(description_width) + '} {:' + str(guid_width) +
           '}').format('Name', 'Description', 'GUID'))
    print("-" * (5 + name_width + description_width + guid_width))
    for payload in payload_protos:
        print(('{:' + str(name_width) + '} {:' + str(description_width) + '} {:' + str(guid_width) +
               '}').format(payload.name, payload.description, payload.GUID))
    return True


class PayloadListCommand(Command):
    """List all payloads registered with the robot."""

    NAME = 'list'

    def __init__(self, subparsers, command_dict):
        """List all payloads registered with the robot.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(PayloadListCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """
        _show_payload_list(robot, as_proto=options.proto)
        return True


def _register_payload(robot, name, guid, secret):
    """Register a payload with the robot.

    Args:
        robot: Robot object used to register the payload.
        name: The name that will be assigned to the registered payload.
        guid: The GUID that will be assigned to the registered payload.
        secret: The secret that the pyaload will be registed with.
    Returns:
        True
    """
    payload_registration_client = robot.ensure_client(
        PayloadRegistrationClient.default_service_name)
    payload = bosdyn.api.payload_pb2.Payload(GUID=guid, name=name)
    try:
        payload_registration_client.register_payload(payload, secret)
    except PayloadAlreadyExistsError:
        print('\nA payload with this GUID is already registed. Check the robot Admin Console.')
    else:
        print('\nPayload successfully registered with the robot.\n'
              'Before it can be used, the payload must be authorized in the Admin Console.')
    return True


class PayloadRegisterCommand(Command):
    """Register a payload with the robot."""

    NAME = 'register'

    def __init__(self, subparsers, command_dict):
        """Register a payload with the robot.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(PayloadRegisterCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--payload-name', required=True, help='name of the payload')
        self._parser.add_argument('--payload-guid', required=True, help='guid of the payload')
        self._parser.add_argument('--payload-secret', required=True, help='secret for the payload')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """
        _register_payload(robot, options.payload_name, options.payload_guid, options.payload_secret)


class FaultCommands(Subcommands):
    """Commands related to the fault service and robot state service (for fault reading)."""

    NAME = 'fault'

    def __init__(self, subparsers, command_dict):
        """Commands related to the fault service and robot state service (for fault reading).

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(FaultCommands, self).__init__(subparsers, command_dict,
                                            [FaultShowCommand, FaultWatchCommand])


def _show_service_faults(robot):
    """Print service faults for the robot.

    Args:
        robot: Robot object used to get the list of services.
    """

    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    service_fault_state = robot_state_client.get_robot_state().service_fault_state

    print("\n\n\n" + "-" * 80)
    if (len(service_fault_state.faults) == 0):
        print("No active service faults.")
        return

    for fault in service_fault_state.faults:
        print('''
{fault.fault_id.fault_name}
    Service Name: {fault.fault_id.service_name}
    Payload GUID: {fault.fault_id.payload_guid}
    Error Message: {fault.error_message}
    Onset Time: {timestamp}'''\
    .format(fault=fault, timestamp=timestamp_to_datetime(fault.onset_timestamp)))
    return


class FaultShowCommand(Command):
    """Show all service faults currently active in robot state."""

    NAME = 'show'

    def __init__(self, subparsers, command_dict):
        """Show all service faults currently active in robot state.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(FaultShowCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """
        _show_service_faults(robot)
        return True


class FaultWatchCommand(Command):
    """Watch all service faults in robot state and print them out."""

    NAME = 'watch'

    def __init__(self, subparsers, command_dict):
        """Watch all service faults in robot state and print them out.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(FaultWatchCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """
        print('Press Ctrl-C or send SIGINT to exit\n\n')
        while True:
            _show_service_faults(robot)
            time.sleep(1)

        return True


class RobotIdCommand(Command):
    """Show robot-id."""

    NAME = 'id'
    NEED_AUTHENTICATION = False

    def __init__(self, subparsers, command_dict):
        """Show robot-id.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(RobotIdCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True.
        """
        proto = robot.ensure_client(RobotIdClient.default_service_name).get_id()
        if options.proto:
            print(proto)
            return True
        nickname = ''
        if proto.nickname and proto.nickname != proto.serial_number:
            nickname = proto.nickname
        release = proto.software_release
        version = release.version
        print(u"{:20} {:15} {:10} {} ({})".format(proto.serial_number, proto.computer_serial_number,
                                                  nickname, proto.species, proto.version))
        print(" Software: {}.{}.{} ({} {})".format(version.major_version, version.minor_version,
                                                   version.patch_level, release.changeset,
                                                   timestamp_to_datetime(release.changeset_date)))
        print("  Installed: {}".format(timestamp_to_datetime(release.install_date)))
        return True


class LogAnnotationCommands(Subcommands):
    """Commands related to the log-annotation service."""

    NAME = 'log'

    def __init__(self, subparsers, command_dict):
        """Commands related to the log-annotation service.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(LogAnnotationCommands, self).__init__(
            subparsers, command_dict,
            [DataBufferTextMsgCommand, LogTextMsgCommand, LogOperatorCommentCommand])


class DataBufferTextMsgCommand(Command):
    """Send a text-message to the data buffer to be logged."""

    NAME = 'buffertext'

    def __init__(self, subparsers, command_dict):
        """Send a text-message to the data buffer to be logged.

        Args:
            subparsers: List of argument parsers.
            command_dict: DIctionary of command names which take parsed options.
        """
        super(DataBufferTextMsgCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--timestamp', action='store_true',
                                  help='achieve time-sync and send timestamp')
        self._parser.add_argument('--tag', help='Tag for message')
        parser_log_level = self._parser.add_mutually_exclusive_group()
        parser_log_level.add_argument('--debug', '-D', action='store_true',
                                      help='Log at debug-level')
        parser_log_level.add_argument('--info', '-I', action='store_true', help='Log at info-level')
        parser_log_level.add_argument('--warn', '-W', action='store_true', help='Log at warn-level')
        parser_log_level.add_argument('--error', '-E', action='store_true',
                                      help='Log at error-level')
        self._parser.add_argument('message', help='Message to log')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            False if TimeSyncError is caught, True otherwise.
        """
        robot_timestamp = None
        if options.timestamp:
            try:
                robot_timestamp = robot.time_sync.robot_timestamp_from_local_secs(
                    time.time(), timesync_timeout_sec=1.0)
            except TimeSyncError as err:
                print("Failed to send message with timestamp: {}.".format(err))
                return False
        msg_proto = TextMessage(message=options.message, timestamp=robot_timestamp)
        if options.debug:
            msg_proto.level = TextMessage.LEVEL_DEBUG
        elif options.warn:
            msg_proto.level = TextMessage.LEVEL_WARN
        elif options.error:
            msg_proto.level = TextMessage.LEVEL_ERROR
        else:
            msg_proto.level = TextMessage.LEVEL_INFO

        if options.tag:
            msg_proto.tag = options.tag

        data_buffer_client = robot.ensure_client(DataBufferClient.default_service_name)
        data_buffer_client.add_text_messages([msg_proto])

        return True


class LogTextMsgCommand(Command):
    """Send a text-message to the robot to be logged."""

    NAME = 'textmsg'

    def __init__(self, subparsers, command_dict):
        """Send a text-message to the robot to be logged.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(LogTextMsgCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--timestamp', action='store_true',
                                  help='achieve time-sync and send timestamp')
        self._parser.add_argument('--service', default='bosdyn.client',
                                  help='Name of service for message')
        self._parser.add_argument('--tag', help='Tag for message')
        parser_log_level = self._parser.add_mutually_exclusive_group()
        parser_log_level.add_argument('--debug', '-D', action='store_true',
                                      help='Log at debug-level')
        parser_log_level.add_argument('--info', '-I', action='store_true', help='Log at info-level')
        parser_log_level.add_argument('--warn', '-W', action='store_true', help='Log at warn-level')
        parser_log_level.add_argument('--error', '-E', action='store_true',
                                      help='Log at error-level')
        self._parser.add_argument('message', help='Message to log')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            False if TimeSyncError is caught, True otherwise.
        """
        robot_timestamp = None
        if options.timestamp:
            try:
                robot_timestamp = robot.time_sync.robot_timestamp_from_local_secs(
                    time.time(), timesync_timeout_sec=1.0)
            except TimeSyncError as err:
                print("Failed to send message with timestamp: {}.".format(err))
                return False
        msg_proto = LogAnnotationTextMessage(message=options.message, timestamp=robot_timestamp)
        if options.debug:
            msg_proto.level = LogAnnotationTextMessage.LEVEL_DEBUG
        elif options.warn:
            msg_proto.level = LogAnnotationTextMessage.LEVEL_WARN
        elif options.error:
            msg_proto.level = LogAnnotationTextMessage.LEVEL_ERROR
        else:
            msg_proto.level = LogAnnotationTextMessage.LEVEL_INFO

        if options.service:
            msg_proto.service = options.service
        if options.tag:
            msg_proto.tag = options.tag

        log_client = robot.ensure_client(LogAnnotationClient.default_service_name)
        log_client.add_text_messages([msg_proto])

        return True


class LogOperatorCommentCommand(Command):
    """Send an operator comment to the robot to be logged."""

    NAME = 'comment'

    def __init__(self, subparsers, command_dict):
        """Send an operator comment to the robot to be logged.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(LogOperatorCommentCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--timestamp', action='store_true',
                                  help='achieve time-sync and send timestamp')
        self._parser.add_argument('message', help='operator comment text')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            False if TimeSyncError is caught, True otherwise.
        """
        client_timestamp = None
        if options.timestamp:
            client_timestamp = time.time()
            try:
                robot.time_sync.wait_for_sync(timeout_sec=1.0)
            except TimeSyncError as err:
                print("Failed to get timesync for setting comment timestamp: {}.".format(err))
                return False
        robot.operator_comment(options.message, timestamp_secs=client_timestamp)
        return True


class DataServiceCommands(Subcommands):
    """Commands for querying the data-service."""

    NAME = 'data'

    def __init__(self, subparsers, command_dict):
        """Commands for querying the data-service

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(DataServiceCommands,
              self).__init__(subparsers, command_dict,
                             [GetDataBufferCommentsCommand, GetDataBufferEventsCommand,
                              GetDataBufferStatusCommand])


class GetDataBufferCommentsCommand(Command):
    """Get operator comments from the robot."""

    NAME = 'comments'

    def __init__(self, subparsers, command_dict):
        """Get operator comments from the robot.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(GetDataBufferCommentsCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """
        client = robot.ensure_client(DataServiceClient.default_service_name)
        print(client.get_events_comments(EventsCommentsSpec(
            comments=True)).events_comments.operator_comments)
        return True


class GetDataBufferEventsCommand(Command):
    """Get events from the robot."""

    NAME = 'events'

    def __init__(self, subparsers, command_dict):
        """Get events from the robot.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(GetDataBufferEventsCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """
        client = robot.ensure_client(DataServiceClient.default_service_name)
        spec = EventsCommentsSpec()
        spec.events.add()
        print(client.get_events_comments(spec).events_comments.events)
        return True


class GetDataBufferStatusCommand(Command):
    """Get status of data-buffer on robot."""

    NAME = 'status'

    def __init__(self, subparsers, command_dict):
        """Get status of data-buffer on robot

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(GetDataBufferStatusCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--get-blob-specs', '-B', action='store_true',
                                  help='get list of channel/msgtype/source combinations')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """
        client = robot.ensure_client(DataServiceClient.default_service_name)
        print(client.get_data_buffer_status(get_blob_specs=options.get_blob_specs))
        return True


class RobotStateCommands(Subcommands):
    """Commands for querying robot state."""

    NAME = 'state'

    def __init__(self, subparsers, command_dict):
        """Commands for querying robot state.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(RobotStateCommands, self).__init__(subparsers, command_dict,
                                                 [FullStateCommand, MetricsCommand, RobotModel])


class FullStateCommand(Command):
    """Show robot state."""

    NAME = 'full'

    def __init__(self, subparsers, command_dict):
        """Show robot state.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(FullStateCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        """Implementation of the command; prints RobotState proto.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.
        """
        proto = robot.ensure_client(RobotStateClient.default_service_name).get_robot_state()
        print(proto)
        return True


class RobotModel(Command):
    """Write robot URDF and mesh to local files."""

    NAME = 'model'
    NEED_AUTHENTICATION = False

    def __init__(self, subparsers, command_dict):
        """Write robot URDF and mesh to local files.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(RobotModel, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--outdir', default='Model_Files',
                                  help='directory into which to save the files')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True.
        """
        robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
        hardware = robot_state_client.get_robot_hardware_configuration()

        # Write files in user-specified directory, or use default name
        model_directory = options.outdir

        # Make the directory, if it does not already exist
        try:
            os.makedirs(model_directory)
        except OSError:
            pass

        # Write each link model to its own file
        for link in hardware.skeleton.links:
            # Request a Skeleton.Link.ObjModel from the robot for link.name and write it to a file
            try:
                obj_model_proto = robot_state_client.get_robot_link_model(link.name)
            except InvalidRequestError as err:
                print(err, end='')
                print(" Name of link: " + link.name)
                continue

            # If file_name is empty, ignore
            if not obj_model_proto.file_name:
                continue

            # Write to a file, ignoring the robot path
            sub_path = '/'.join(obj_model_proto.file_name.split('/')[:-1])  # robot defined path
            path = os.path.join(model_directory, sub_path)  # local path + robot path
            try:
                os.makedirs(path)
            except OSError:
                pass

            path_and_name = os.path.join(path, obj_model_proto.file_name.split('/')[-1])
            with open(path_and_name, "w") as obj_file:
                obj_file.write(obj_model_proto.file_contents)
            print('Link file written to ' + path_and_name)

        # Write the corresponding urdf file inside the link directory
        with open(os.path.join(model_directory, "model.urdf"), "w") as urdf_file:
            urdf_file.write(hardware.skeleton.urdf)
        print('URDF file written to ' + os.path.join(model_directory, "model.urdf"))

        return True


class MetricsCommand(Command):
    """Show metrics (runtime, etc...)."""

    NAME = 'metrics'

    def __init__(self, subparsers, command_dict):
        """Show metrics (runtime, etc...).

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(MetricsCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print metrics in proto format')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True.
        """
        proto = robot.ensure_client(RobotStateClient.default_service_name).get_robot_metrics()
        if options.proto:
            print(proto)
            return True
        for metric in proto.metrics:
            print(self._format_metric(metric))
        return True

    @staticmethod
    def _secs_to_hms(seconds):
        """Converts seconds to hours:minutes:seconds string.

        Args:
            seconds: Seconds to convert.

        Returns:
            String in the format hours:MM:SS.
        """
        isecs = int(seconds)
        seconds = isecs % 60
        minutes = (isecs // 60) % 60
        hours = isecs // 3600
        return '{:d}:{:02d}:{:02d}'.format(hours, minutes, seconds)

    @staticmethod
    def _distance_str(meters):
        """Converts distance to human-readable string.

        Args:
            meters: Distance in meters to convert.

        Returns:
            String with meters with two digit precision if distance is less than 1000 meters, or
            kilometers with two digit precision otherwise.
        """
        if meters < 1000:
            return '{:.2f} m'.format(meters)
        return '{:.2f} km'.format(float(meters) / 1000)

    @staticmethod
    def _format_metric(metric):  # pylint: disable=too-many-return-statements
        """Convert metric input to human-readable string.

        Args:
            metric: Input metric object to convert.

        Returns:
            String in the format: Label float_value units.
        """
        if metric.HasField('float_value'):
            if metric.units == 'm':
                return '{:20} {}'.format(metric.label,
                                         MetricsCommand._distance_str(metric.float_value))
            return '{:20} {:.2f} {}'.format(metric.label, metric.float_value, metric.units)
        elif metric.HasField('int_value'):
            return '{:20} {} {}'.format(metric.label, metric.int_value, metric.units)
        elif metric.HasField('bool_value'):
            return '{:20} {} {}'.format(metric.label, metric.bool_value, metric.units)
        elif metric.HasField('duration'):
            return '{:20} {}'.format(metric.label,
                                     MetricsCommand._secs_to_hms(metric.duration.seconds))
        elif metric.HasField('string'):
            return '{:20} {}'.format(metric.label, metric.string_value)
        # ??
        return '{:20} {} {}'.format(metric.label, metric.value, metric.units)


class TimeSyncCommand(Command):
    """Find clock difference between this and the robot clock."""

    NAME = 'time-sync'

    def __init__(self, subparsers, command_dict):
        """Find clock difference between this and the robot clock.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(TimeSyncCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            False if timesync cannot be established, True otherwise.
        """
        endpoint = TimeSyncEndpoint(robot.ensure_client(TimeSyncClient.default_service_name))
        if not endpoint.establish_timesync(break_on_success=True):
            print("Failed to achieve time sync")
            return False

        if options.proto:
            print(endpoint.response)
            return True

        print("GRPC round-trip time: {}".format(duration_str(endpoint.round_trip_time)))
        print("Local time to robot time: {}".format(duration_str(endpoint.clock_skew)))

        return True


class LicenseCommand(Command):
    """Show installed license."""

    NAME = "license"

    def __init__(self, subparsers, command_dict):
        super(LicenseCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True.
        """
        license_client = robot.ensure_client(LicenseClient.default_service_name)
        license_info = license_client.get_license_info()
        if options.proto:
            print(license_info)
        else:
            print(str(license_info))

        return True


class LeaseCommands(Subcommands):
    """Commands related to the lease service."""

    NAME = 'lease'

    def __init__(self, subparsers, command_dict):
        """Commands related to the lease service.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(LeaseCommands, self).__init__(subparsers, command_dict, [LeaseListCommand])


class LeaseListCommand(Command):
    """List all leases."""

    NAME = 'list'

    def __init__(self, subparsers, command_dict):
        """List all leases.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(LeaseListCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True.
        """
        lease_client = robot.ensure_client(LeaseClient.default_service_name)
        resources = lease_client.list_leases()
        if options.proto:
            print(resources)
            return True
        for resource in resources:
            print(self._format_lease_resource(resource))
        return True

    @staticmethod
    def _format_lease_resource(resource):
        return str(resource)


class BecomeEstopCommand(Command):
    """Grab and hold estop until Ctl-C."""

    NAME = 'become-estop'

    _RPC_PRINT_CHOICES = ['timestamp', 'full']

    def __init__(self, subparsers, command_dict):
        """Grab and hold estop until Ctl-C.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(BecomeEstopCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--timeout', type=float, help='EStop timeout (seconds)',
                                  default=10)
        self._parser.add_argument('--rpc-print', choices=self._RPC_PRINT_CHOICES,
                                  default='timestamp',
                                  help='How much of the request/response messages to print')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True.
        """
        # Get a client to the estop service.
        client = robot.ensure_client(EstopClient.default_service_name)

        # If we'd only like to print timestamps of messages, change the client's callbacks that
        # convert messages to string.

        def _timestamp_fmt_request(request):
            return '(request timestamp: {})'.format(request.header.request_timestamp.ToSeconds())

        def _timestamp_fmt_response(response):
            return '(response timestamp: {})'.format(response.header.response_timestamp.ToSeconds())

        if options.rpc_print == 'timestamp':
            client.request_trim_for_log = _timestamp_fmt_request
            client.response_trim_for_log = _timestamp_fmt_response

        # Create the endpoint to the robot estop system.
        # Timeout should be chosen to balance safety considerations with expected service latency.
        # See the estop documentation for details.
        endpoint = EstopEndpoint(client, 'command-line', options.timeout)
        # Have this endpoint to set up the robot's estop system such that it is the sole estop.
        # See the function's docstring and the estop documentation for details.
        endpoint.force_simple_setup()
        # Create the helper class that does periodic check-ins. This also starts the checking-in.
        exit_signal = threading.Event()

        # Define a function to call on SIGINT that asserts an estop and cleanly shuts down.
        def sigint_handler(sig, frame):
            """Cleanly shut down the application on interrupt."""
            #pylint: disable=unused-argument
            # Signal that we want to exit the program.
            exit_signal.set()

        print('Press Ctrl-C or send SIGINT to exit')
        # Install our signal handler function.
        signal.signal(signal.SIGINT, sigint_handler)

        with EstopKeepAlive(endpoint) as keep_alive:
            # Now we wait. The thread in EstopKeepAlive will continue sending messages to the estop
            # service on its own.
            while not exit_signal.wait(10):
                pass
            # EStop the robot.
            keep_alive.stop()
            # The keep_alive object's exit() function will shut down the thread.

        # This will let another endpoint fill our role, if they want to use the current
        # configuration. For details, see the estop documentation.
        endpoint.deregister()

        return True


class ImageCommands(Subcommands):
    """Commands for querying images."""

    NAME = 'image'

    def __init__(self, subparsers, command_dict):
        """Commands for querying images.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(ImageCommands, self).__init__(subparsers, command_dict,
                                            [ListImageSourcesCommand, GetImageCommand])


def _show_image_sources_list(robot, as_proto=False, service_name=None):
    """Print available image sources.

    Args:
        robot: Robot object on which to run the command.
        as_proto: Boolean to determine whether to print the full proto message, or a human-readable
            string in the format: source_name (rows x cols)

    Returns:
        True.
    """
    service_name = service_name or ImageClient.default_service_name
    proto = robot.ensure_client(service_name).list_image_sources()
    if as_proto:
        print(proto)
    else:
        for image_source in proto:
            print("{:30s} ({:d}x{:d})".format(image_source.name, image_source.rows,
                                              image_source.cols))
    return True


class ListImageSourcesCommand(Command):
    """List image sources."""

    NAME = 'list-sources'

    def __init__(self, subparsers, command_dict):
        """List image sources.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(ListImageSourcesCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')
        self._parser.add_argument('--service-name', default=ImageClient.default_service_name,
                                  help='Image service to query')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            Output of _show_image_sources_list method.
        """
        _show_image_sources_list(robot, as_proto=options.proto, service_name=options.service_name)
        return True


def write_pgm(image_response, outfile):
    """Write raw data from image_response to a PGM file.

    Args:
        image_response: ImageResponse object to parse.
        outfile: Name of the output file, if None is passed, then "image-{SOURCENAME}.pgm" is used.
    """

    if image_response.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_DEPTH_U16:
        dtype = np.uint16
    else:
        dtype = np.uint8

    img = np.frombuffer(image_response.shot.image.data, dtype=dtype)
    height = image_response.shot.image.rows
    width = image_response.shot.image.cols
    img = img.reshape(height, width)
    image_source_filename = 'image-{}.pgm'.format(image_response.source.name)
    filename = outfile or image_source_filename

    try:
        fd_out = open(filename, 'w')
    except IOError as err:
        print("Cannot open file " + filename + "Exception: ")
        print(err)
        return

    max_val = np.amax(img)
    pgm_header = 'P5' + ' ' + str(width) + ' ' + str(height) + ' ' + str(max_val) + '\n'
    fd_out.write(pgm_header)
    img.tofile(fd_out)
    print('Saved matrix with pixel values from camera "{}" to file "{}".'.format(
        image_response.source.name, filename))


class GetImageCommand(Command):
    """Get an image from the robot and write it to an image file."""

    NAME = 'get-image'

    def __init__(self, subparsers, command_dict):
        """Get an image from the robot and write it to an image file.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(GetImageCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--outfile', default=None,
                                  help='Filename into which to save the image')
        self._parser.add_argument('--quality-percent', type=int, default=75,
                                  help='Percent image quality (0-100)')
        self._parser.add_argument('source_name', metavar='SRC', nargs='+', help='Image source name')
        self._parser.add_argument('--service-name', help='Image service to query',
                                  default=ImageClient.default_service_name)

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True if successful, False if exceptions are caught.
        """
        image_requests = [
            build_image_request(source_name, options.quality_percent)
            for source_name in options.source_name
        ]
        try:
            response = robot.ensure_client(options.service_name).get_image(image_requests)
        except UnknownImageSourceError:
            print('Requested image source "{}" does not exist.  Available image sources:'.format(
                options.source_name))
            _show_image_sources_list(robot, service_name=options.service_name)
            return False
        except ImageResponseError:
            print('Robot cannot generate the "{}" at this time.  Retry the command.'.format(
                options.source_name))
            return False

        for image_response in response:
            # Save raw sources as text files with the full matrix saved as text values. Each row in
            # the file represents a raw in the matrix. All other formats are saved as JPEG files.
            if not image_response.shot.image.format == image_pb2.Image.FORMAT_JPEG:
                write_pgm(image_response, options.outfile)
            else:
                image_source_filename = 'image-{}.jpg'.format(image_response.source.name)
                filename = options.outfile or image_source_filename
                try:
                    with open(filename, 'wb') as outfile:
                        outfile.write(image_response.shot.image.data)
                    print('Saved "{}" to "{}".'.format(image_response.source.name, filename))
                except IOError as err:
                    print('Failed to save "{}".'.format(image_response.source.name))
                    print(err)
        return True


class LocalGridCommands(Subcommands):
    """Commands for querying local grid maps."""

    NAME = 'local_grid'

    def __init__(self, subparsers, command_dict):
        """Commands for querying local grid maps.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(LocalGridCommands, self).__init__(subparsers, command_dict,
                                                [ListLocalGridTypesCommand, GetLocalGridsCommand])


def _show_local_grid_sources_list(robot, as_proto=False):
    """Print available local grid sources.

    Args:
        robot: Robot object on which to run the command.
        as_proto: Boolean to determine whether to print the full proto message, or just the list of
            names.

    Returns:
        True.
    """
    proto = robot.ensure_client(LocalGridClient.default_service_name).get_local_grid_types()
    if as_proto:
        print(proto)
    else:
        for local_grid_type in proto:
            print(local_grid_type.name)
    return True


class ListLocalGridTypesCommand(Command):
    """List local grid sources."""

    NAME = 'types'

    def __init__(self, subparsers, command_dict):
        """List local grid sources.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(ListLocalGridTypesCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            Output of _show_local_grid_sources_list method.
        """
        _show_local_grid_sources_list(robot, as_proto=options.proto)
        return True


class GetLocalGridsCommand(Command):
    """Get local grids from the robot."""

    NAME = 'get'

    def __init__(self, subparsers, command_dict):
        """Get local grids from the robot.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(GetLocalGridsCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--outfile', default=None,
                                  help='filename into which to save the image')
        self._parser.add_argument('types', metavar='SRC', nargs='+', help='image types')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True.
        """
        response = robot.ensure_client(LocalGridClient.default_service_name).get_local_grids(
            options.types)

        for local_grid_response in response:
            print(local_grid_response)
        return True


class DataAcquisitionCommand(Subcommands):
    """Acquire data from the robot and add it in the data buffer with the metadata, or request
    status."""

    NAME = 'acquire'

    def __init__(self, subparsers, command_dict):
        """Acquire data from the robot and add it in the data buffer with the metadata, or request
        status.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(DataAcquisitionCommand,
              self).__init__(subparsers, command_dict,
                             [DataAcquisitionServiceCommand,
                             DataAcquisitionRequestCommand,
                             DataAcquisitionStatusCommand])


class DataAcquisitionRequestCommand(Command):
    """Capture and save images or metadata specified in the command line arguments."""

    NAME = 'request'

    def __init__(self, subparsers, command_dict):
        """Capture and save images or metadata specified in the command line arguments.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(DataAcquisitionRequestCommand, self).__init__(
            subparsers, command_dict)
        self._parser.add_argument('--image-source', metavar='IMG_SRC', default=[],
                                  help='Image source name', action='append')
        self._parser.add_argument('--image-service', metavar='SERVICE_NAME', default=[],
                                  help='Image service name for the image source.', action='append')
        self._parser.add_argument('--data-source', metavar='DATA_SRC', default=[],
                                  help='Data source name', action='append')
        self._parser.add_argument('--action-name', help='The action name to save the data with.',
                                  default="quick_captures")
        self._parser.add_argument('--group-name', help='The group name to save the data with.',
                                  default="command_line")
        self._parser.add_argument('--non-blocking-request',
                                  help='Return after making the acquisition request, without monitoring' +\
                                      ' the status for completion.',
                                  default=False, action='store_true')

    def _run(self, robot, options):
        """Implementation of the 'request' command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.
        """
        if not options.data_source and not (options.image_source and options.image_service):
            self._parser.error(
                'A request requires either a data source name or an image source+service name.')
        if len(options.image_source) != len(options.image_service):
            self._parser.error(
                'A request must have a 1:1 correspondence between image source and image service arguments.')

        captures = data_acquisition_pb2.AcquisitionRequestList()
        captures.data_captures.extend([data_acquisition_pb2.DataCapture(name=data_name) for data_name in options.data_source])
        img_captures = []
        for i, src_name in enumerate(options.image_source):
            img_service = options.image_service[i]
            img_captures.append(data_acquisition_pb2.ImageSourceCapture(
                image_service=img_service, image_source=src_name))
        captures.image_captures.extend(img_captures)

        robot.time_sync.wait_for_sync(timeout_sec=1.0)
        data_acquisition_client = robot.ensure_client(DataAcquisitionClient.default_service_name)
        acquisition_id = None
        try:
            acquisition_id = data_acquisition_client.acquire_data(captures, options.action_name, options.group_name)
            print("Request ID: "+str(acquisition_id))
        except ResponseError as err:
            print("RPC error occurred: " + str(err))
            return False
        if options.non_blocking_request:
            # Won't check the status and wait for a success/failure if the user specified
            # this should not be a blocking command.
            return True

        while True:
            print("Waiting for acquisition (id: " + str(acquisition_id) + ") to complete.")
            get_status_response = None
            try:
                get_status_response = data_acquisition_client.get_status(acquisition_id)
            except ResponseError as err:
                print("Exception: " + str(err))
                return False
            print("Current status is: " +
                data_acquisition_pb2.GetStatusResponse.Status.Name(get_status_response.status))
            if get_status_response.status == data_acquisition_pb2.GetStatusResponse.STATUS_COMPLETE:
                return True
            if get_status_response.status == data_acquisition_pb2.GetStatusResponse.STATUS_TIMEDOUT:
                print("Unrecoverable request timeout: {}".format(get_status_response))
                return False
            if get_status_response.status == data_acquisition_pb2.GetStatusResponse.STATUS_DATA_ERROR:
                print("Data error was recieved: {}".format(get_status_response))
                return False
            time.sleep(0.2)
        return True


class DataAcquisitionServiceCommand(Command):
    """Get list of different data acquisition capabilities."""

    NAME = 'info'


    def __init__(self, subparsers, command_dict):
        """Get list of different data acquisition capabilities.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(DataAcquisitionServiceCommand, self).__init__(subparsers, command_dict)

        # Constants to describe width of columns for printing the data names and types
        self._data_type_width = 15
        self._data_name_width = 35
        self._service_name_width = 30

    def _format_and_print_capability(self, data_type, data_name, service_name=""):
        """Print the data acquisition capability.

        Args:
            data_type (string): Either image or data capabilities.
            data_name (string): The name of the data acquisition capability
            service_name(string): For image capabilites, a service name is required.
        """
        print(('{:' + str(self._data_type_width) + '} {:' + str(self._data_name_width) + '} {:' + str(self._service_name_width) +
               '}').format(data_type, data_name, service_name))

    def _run(self, robot, options):
        """Implementation of the 'info' command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.
        """
        capabilities = robot.ensure_client(DataAcquisitionClient.default_service_name).get_service_info()
        print("Data Acquisition Service's Available Capabilities\n")
        self._format_and_print_capability("Data Type", "Data Name", "(optional) Service Name")
        print("-"*(self._data_type_width+self._data_name_width+self._service_name_width))
        for data_name in capabilities.data_sources:
            self._format_and_print_capability("data",data_name.name)
        for img_service in capabilities.image_sources:
            for img in img_service.image_source_names:
                self._format_and_print_capability("image", img, img_service.service_name)
        return True



class DataAcquisitionStatusCommand(Command):
    """Get status of an acquisition request based on the request id."""

    NAME = 'status'

    def __init__(self, subparsers, command_dict):
        """Get status of an acquisition request based on the request id.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(DataAcquisitionStatusCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('id', type=int, help='Response id to get the status for')

    def _run(self, robot, options):
        """Implementation of the 'status' command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            False if NonexistentServiceError is caught, True otherwise.
        """
        response = robot.ensure_client(DataAcquisitionClient.default_service_name).get_status(
            options.id)
        print(response)
        return True


def main(args=None):
    """Command-line interface for interacting with robot services."""
    parser = argparse.ArgumentParser(prog='bosdyn.client', description=main.__doc__)
    add_common_arguments(parser)

    command_dict = {}  # command name to fn which takes parsed options
    subparsers = parser.add_subparsers(title='commands', dest='command')

    # Register commands that can be run.
    DirectoryCommands(subparsers, command_dict)
    PayloadCommands(subparsers, command_dict)
    FaultCommands(subparsers, command_dict)
    RobotIdCommand(subparsers, command_dict)
    LicenseCommand(subparsers, command_dict)
    RobotStateCommands(subparsers, command_dict)
    LogAnnotationCommands(subparsers, command_dict)
    DataServiceCommands(subparsers, command_dict)
    TimeSyncCommand(subparsers, command_dict)
    LeaseCommands(subparsers, command_dict)
    BecomeEstopCommand(subparsers, command_dict)
    ImageCommands(subparsers, command_dict)
    LocalGridCommands(subparsers, command_dict)
    DataAcquisitionCommand(subparsers, command_dict)

    options = parser.parse_args(args=args)

    setup_logging(verbose=options.verbose)

    # Create robot object and authenticate.
    sdk = bosdyn.client.create_standard_sdk('BosdynClient')

    robot = sdk.create_robot(options.hostname)

    if not options.command:
        print("Need to specify a command")
        parser.print_help()
        return False

    if not command_dict[options.command].run(robot, options):
        return False

    return True
