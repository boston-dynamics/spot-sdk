# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Command-line utility code for interacting with robot services."""

from __future__ import division

import abc
import argparse
import datetime
import os
import signal
import sys
import threading
import time

from google.protobuf import json_format

import bosdyn.client
from bosdyn.api import data_acquisition_pb2, image_pb2
from bosdyn.api.data_buffer_pb2 import Event, TextMessage
from bosdyn.api.data_index_pb2 import EventsCommentsSpec
from bosdyn.api.robot_state_pb2 import BehaviorFault
from bosdyn.util import duration_str, timestamp_to_datetime

from .auth import InvalidLoginError, InvalidTokenError
from .data_acquisition import DataAcquisitionClient
from .data_acquisition_helpers import acquire_and_process_request
from .data_acquisition_plugin import DataAcquisitionPluginClient
from .data_buffer import DataBufferClient
from .data_service import DataServiceClient
from .directory import DirectoryClient, NonexistentServiceError
from .directory_registration import DirectoryRegistrationClient, DirectoryRegistrationResponseError
from .estop import EstopClient, EstopEndpoint, EstopKeepAlive
from .exceptions import Error, InvalidRequestError, ProxyConnectionError
from .image import (ImageClient, ImageResponseError, UnknownImageSourceError, build_image_request,
                    save_images_as_files)
from .lease import LeaseClient
from .license import LicenseClient
from .local_grid import LocalGridClient
from .log_status import InactiveLogError, LogStatusClient
from .payload import PayloadClient
from .payload_registration import PayloadAlreadyExistsError, PayloadRegistrationClient
from .power import (PowerClient, power_cycle_robot, power_off_payload_ports, power_off_robot,
                    power_off_wifi_radio, power_on_payload_ports, power_on_wifi_radio)
from .robot_id import RobotIdClient
from .robot_state import RobotStateClient
from .time_sync import TimeSyncClient, TimeSyncEndpoint, TimeSyncError, timespec_to_robot_timespan
from .util import add_common_arguments, authenticate, setup_logging



# pylint: disable=too-few-public-methods
class Command(object, metaclass=abc.ABCMeta):
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
                if hasattr(options, 'username') and hasattr(
                        options, 'password') and (options.username or options.password):
                    robot.authenticate(options.username, options.password)
                else:
                    authenticate(robot)
                robot.sync_with_directory()  # Make sure that we can use all registered services.
            return self._run(robot, options)
        except ProxyConnectionError:
            print('Could not contact robot with hostname "{}".'.format(options.hostname),
                  file=sys.stderr)
        except InvalidTokenError:
            print('The provided user token is invalid.', file=sys.stderr)
        except InvalidLoginError:
            print('Username and/or password are invalid.', file=sys.stderr)
        except Error as err:
            print('{}: {}'.format(type(err).__name__, err), file=sys.stderr)

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


def _format_dir_entry(  # pylint: disable=too-many-arguments
        name, service_type, authority, tokens, name_width=23, type_width=31, authority_width=27):
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
            # pylint: disable=no-member
            print("Failed to register service {}.\nResponse Status: {}".format(
                options.service_name,
                bosdyn.api.directory_registration_pb2.RegisterServiceResponse.Status.Name(
                    exc.response.status)))
            return False
        else:
            print("Successfully registered service {}".format(options.service_name))
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
            # pylint: disable=no-member
            print("Failed to unregister service {}.\nResponse Status: {}".format(
                options.service_name,
                bosdyn.api.directory_registration_pb2.UnregisterServiceResponse.Status.Name(
                    exc.response.status)))
            return False
        else:
            print("Successfully unregistered service {}".format(options.service_name))
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
        super(PayloadCommands, self).__init__(subparsers, command_dict,
                                              [PayloadListCommand, PayloadRegisterCommand])


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
        secret: The secret that the payload will be registered with.
    Returns:
        True
    """
    payload_registration_client = robot.ensure_client(
        PayloadRegistrationClient.default_service_name)
    payload = bosdyn.api.payload_pb2.Payload(GUID=guid, name=name)
    try:
        payload_registration_client.register_payload(payload, secret)
    except PayloadAlreadyExistsError:
        print('\nA payload with this GUID is already registered. Check the robot Admin Console.')
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


def _show_all_faults(robot):
    """Print faults for the robot.

    Args:
        robot: Robot object used to get the list of services.
    """
    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    robot_state = robot_state_client.get_robot_state()
    system_fault_state = robot_state.system_fault_state
    behavior_fault_state = robot_state.behavior_fault_state
    service_fault_state = robot_state.service_fault_state

    print('\n' + '-' * 80)
    if len(system_fault_state.faults) == 0:
        print("No active system faults.")
    else:
        for fault in system_fault_state.faults:
            print('''
{fault.name}
    Error Message: {fault.error_message}
    Onset Time: {timestamp}''' \
              .format(fault=fault, timestamp=timestamp_to_datetime(fault.onset_timestamp)))

    print()
    if len(behavior_fault_state.faults) == 0:
        print("No active behavior faults.")
    else:
        for fault in behavior_fault_state.faults:
            print('''
{cause}
    Onset Time: {timestamp}
    Clearable: {clearable}''' \
                  .format(cause=BehaviorFault.Cause.Name(fault.cause),
                          timestamp=timestamp_to_datetime(fault.onset_timestamp),
                          clearable=BehaviorFault.Status.Name(fault.status)))

    print()
    if len(service_fault_state.faults) == 0:
        print("No active service faults.")
    else:
        for fault in service_fault_state.faults:
            print('''
{fault.fault_id.fault_name}
    Service Name: {fault.fault_id.service_name}
    Payload GUID: {fault.fault_id.payload_guid}
    Error Message: {fault.error_message}
    Onset Time: {timestamp}'''\
    .format(fault=fault, timestamp=timestamp_to_datetime(fault.onset_timestamp)))


class FaultShowCommand(Command):
    """Show all faults currently active in robot state."""

    NAME = 'show'

    def __init__(self, subparsers, command_dict):
        """Show all faults currently active in robot state.

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
        _show_all_faults(robot)
        return True


class FaultWatchCommand(Command):
    """Watch all faults in robot state and print them out."""

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
        try:
            while True:
                _show_all_faults(robot)
                time.sleep(1)
        except KeyboardInterrupt:
            pass

        return True


class LogStatusCommands(Subcommands):
    """Start, update and terminate experiment logs, start and terminate retro logs and check status of
    active logs for robot."""

    NAME = 'log-status'
    NEED_AUTHENTICATION = True

    def __init__(self, subparsers, command_dict):
        """Interact with logs for robot

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(LogStatusCommands, self).__init__(subparsers, command_dict, [
            GetLogCommand,
            GetActiveLogStatusesCommand,
            ExperimentLogCommand,
            StartRetroLogCommand,
            TerminateLogCommand,
        ])


class GetLogCommand(Command):
    """Get log status but log id."""

    NAME = 'get'

    def __init__(self, subparsers, command_dict):
        """Get log status from robot

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(GetLogCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('id', help='id of log bundle to display')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """

        client = robot.ensure_client(LogStatusClient.default_service_name)
        response = client.get_log_status(options.id)
        print(response.log_status)
        return True


class GetActiveLogStatusesCommand(Command):
    """Get active log bundles for robot."""

    NAME = 'active'

    def __init__(self, subparsers, command_dict):
        """Retrieve active log statuses for robot.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(GetActiveLogStatusesCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """
        client = robot.ensure_client(LogStatusClient.default_service_name)
        response = client.get_active_log_statuses()
        print(response.log_statuses)
        return True


class ExperimentLogCommand(Subcommands):
    """Give experiment log commands to robot."""

    NAME = 'experiment'

    def __init__(self, subparsers, command_dict):
        """Start a timed or continuous experiment log.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(ExperimentLogCommand, self).__init__(subparsers, command_dict, [
            StartTimedExperimentLogCommand,
            StartContinuousExperimentLogCommand,
        ])


class StartTimedExperimentLogCommand(Command):
    """Start a timed experiment log."""

    NAME = 'timed'

    def __init__(self, subparsers, command_dict):
        """Start timed experiment log

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(StartTimedExperimentLogCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('seconds', type=float, help='how long should the experiment run?')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """

        client = robot.ensure_client(LogStatusClient.default_service_name)
        response = client.start_experiment_log(options.seconds)
        print(response.log_status)
        return True


class StartContinuousExperimentLogCommand(Command):
    """Start a continuous experiment log."""

    NAME = 'continuous'

    def __init__(self, subparsers, command_dict):
        """Start continuous experiment log, defaulted to update keep alive time by 10 seconds every 5 seconds.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(StartContinuousExperimentLogCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('-sleep', type=float, default=5,
                                  help='how long should thread sleep before extending')

    @staticmethod
    def handle_keyboard_interruption(client, log_id):
        try:
            print(" Received keyboard interruption\n\n")
            response = client.terminate_log(log_id)
            print(response.log_status)
        except KeyboardInterrupt:
            client.terminate_log_async(log_id)
            print("Log will terminate shortly")
            response = client.get_log_status(log_id)
            print(response.log_status)

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """

        client = robot.ensure_client(LogStatusClient.default_service_name)
        response = client.start_experiment_log(options.sleep * 2)
        log_id = response.log_status.id
        print("Experiment log id: ", log_id)
        print('Use terminate command, press Ctrl-C or send SIGINT to complete log\n\n')

        try:
            while True:
                time.sleep(options.sleep)
                client.update_experiment(log_id, options.sleep * 2)
        except InactiveLogError:
            response = client.get_log_status(log_id)
            print(response.log_status)
        except KeyboardInterrupt:
            self.handle_keyboard_interruption(client, log_id)
        return True


class StartRetroLogCommand(Command):
    """Start a retro log."""

    NAME = 'retro'

    def __init__(self, subparsers, command_dict):
        """Start a retro log

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(StartRetroLogCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('seconds', type=float, help='how long should the retro log run?')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """

        client = robot.ensure_client(LogStatusClient.default_service_name)
        response = client.start_retro_log(options.seconds)
        print(response.log_status)
        return True


class TerminateLogCommand(Command):
    """Terminate log gathering process."""

    NAME = 'terminate'

    def __init__(self, subparsers, command_dict):
        """Terminate log on robot

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(TerminateLogCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('id', help='id of log to terminate')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """

        client = robot.ensure_client(LogStatusClient.default_service_name)
        response = client.terminate_log(options.id)
        print(response.log_status)
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


class DataBufferCommands(Subcommands):
    """Commands related to the data-buffer service."""

    NAME = 'log'

    def __init__(self, subparsers, command_dict):
        """Commands related to the data-buffer service.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(DataBufferCommands, self).__init__(subparsers, command_dict,
                                                 [TextMsgCommand, OperatorCommentCommand])


class TextMsgCommand(Command):
    """Send a text-message to the data buffer to be logged."""

    NAME = 'textmsg'

    def __init__(self, subparsers, command_dict):
        """Send a text-message to the data buffer to be logged.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(TextMsgCommand, self).__init__(subparsers, command_dict)
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
        # pylint: disable=no-member
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


class OperatorCommentCommand(Command):
    """Send an operator comment to the robot to be logged."""

    NAME = 'comment'

    def __init__(self, subparsers, command_dict):
        """Send an operator comment to the robot to be logged.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(OperatorCommentCommand, self).__init__(subparsers, command_dict)
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
        super(DataServiceCommands, self).__init__(
            subparsers, command_dict,
            [GetDataBufferCommentsCommand, GetDataBufferEventsCommand, GetDataBufferStatusCommand])


class GetDataBufferEventsCommentsCommand(Command):
    """Parent class for commands grabbing operator comment and events."""

    def __init__(self, subparsers, command_dict):
        """Get operator comments from the robot.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(GetDataBufferEventsCommentsCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true', help='print in proto format')
        self._parser.add_argument(
            '-T', '--timespan',
            help='Time span (default all).  "1h" (last hour), "10m-5m" (from 10 to 5 minutes ago).')
        self._parser.add_argument('-R', '--robot-time', action='store_true',
                                  help='Specified timespan is in robot time')

    @abc.abstractmethod
    def _run(self, robot, options):
        pass

    @abc.abstractmethod
    def pretty_print(self, values):
        """Print output of request in a human-friendly way."""

    def _get_result(self, request_spec, robot, options, get_values_fn):
        client = robot.ensure_client(DataServiceClient.default_service_name)
        if options.timespan:
            if options.robot_time:
                time_sync_endpoint = None
            else:
                time_sync_client = robot.ensure_client(TimeSyncClient.default_service_name)
                time_sync_endpoint = TimeSyncEndpoint(time_sync_client)
                if not time_sync_endpoint.establish_timesync():
                    print("Failed to get timesync for requesting comments.")
                    return False
            time_range = timespec_to_robot_timespan(options.timespan, time_sync_endpoint)
            # pylint: disable=no-member
            request_spec.time_range.CopyFrom(time_range)
        values = get_values_fn(client.get_events_comments(request_spec))
        if options.proto:
            print(values)
        else:
            self.pretty_print(values)
        return True


class GetDataBufferCommentsCommand(GetDataBufferEventsCommentsCommand):
    """Get operator comments from the robot."""

    NAME = 'comments'

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """
        request_spec = EventsCommentsSpec(comments=True)

        def _get_comments(response):
            return response.events_comments.operator_comments

        return self._get_result(request_spec, robot, options, _get_comments)

    def pretty_print(self, values):  # pylint: disable=no-self-use
        last_date_shown = None
        for comment in values:
            dtm = datetime.datetime.fromtimestamp(comment.timestamp.seconds +
                                                  comment.timestamp.seconds * 1e-9)
            if dtm.date() != last_date_shown:
                print("\n[{}]".format(dtm.date()))
                last_date_shown = dtm.date()
            print(" {}  {}".format(dtm.time(), comment.message.strip()))


class GetDataBufferEventsCommand(GetDataBufferEventsCommentsCommand):
    """Get events from the robot."""

    NAME = 'events'

    def __init__(self, subparsers, command_dict):
        """Get operator comments from the robot.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(GetDataBufferEventsCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--type', help='query for only the given event-type')
        # pylint: disable=no-member
        self._parser.add_argument(
            '--level',
            choices=Event.Level.keys()[1:],  # slice skips UNSET
            help='limit level to this and above')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """

        request_spec = EventsCommentsSpec()
        event_spec = request_spec.events.add()  # pylint: disable=no-member
        if options.type:
            event_spec.type = options.type
        if options.level:
            event_spec.level.value = Event.Level.Value(options.level)  # pylint: disable=no-member

        def _get_events(response):
            return response.events_comments.events

        return self._get_result(request_spec, robot, options, _get_events)

    @staticmethod
    def _level_name(event):
        prefix = 'LEVEL_'
        # pylint: disable=no-member
        name = event.Level.Name(event.level)
        if name.startswith(prefix):
            return name[len(prefix):]
        return name

    def pretty_print(self, values):  # pylint: disable=no-self-use
        last_date_shown = None
        for event in values:
            start_secs = event.start_time.seconds + event.start_time.seconds * 1e-9
            start_dt = datetime.datetime.fromtimestamp(start_secs)
            if start_dt.date() != last_date_shown:
                print("\n[{}]".format(start_dt.date()))
                last_date_shown = start_dt.date()
            if event.end_time and event.end_time != event.start_time:
                end_secs = event.end_time.seconds + event.end_time.seconds * 1e-9
                end_dt = datetime.datetime.fromtimestamp(end_secs)
                print(" {}-{} (END) ({:16}) {:16}  {:16} <{}> ".format(
                    start_dt.time(), end_dt.time(), end_secs - start_secs, event.type,
                    self._level_name(event), event.source))
            else:
                timing = '' if event.end_time else '(START)'
                print(" {} {} {:16}  {:16}  <{}> ".format(start_dt.time(), timing, event.type,
                                                          self._level_name(event), event.source))
            if event.description:
                print("\t{}".format(event.description))


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
        super(RobotStateCommands, self).__init__(
            subparsers, command_dict,
            [FullStateCommand, HardwareConfigurationCommand, MetricsCommand, RobotModel])


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


class HardwareConfigurationCommand(Command):
    """Show robot hardware configuration."""

    NAME = 'hardware'

    def __init__(self, subparsers, command_dict):
        """Show robot hardware configuration.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(HardwareConfigurationCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        """Implementation of the command; prints HardwareConfiguration proto.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.
        """
        proto = robot.ensure_client(
            RobotStateClient.default_service_name).get_robot_hardware_configuration()
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
    def _timestamp_str(timestamp):
        """Converts a timestamp to a human-readable string.

        Args:
            timestamp: Protobuf timestamp to convert

        Returns:
             Timestamp string in ISO 8601 format

        """
        # The json format of a timestamp is a string that looks like '"2022-01-12T21:56:05Z"',
        # so we strip off the outer quotes and return that.
        return json_format.MessageToJson(timestamp).strip('"')

    @staticmethod
    def _format_metric(metric):  # pylint: disable=too-many-return-statements
        """Convert metric input to human-readable string.

        Args:
            metric: Input metric object to convert.

        Returns:
            String in the format: Label float_value units.
        """
        field = metric.WhichOneof('values')
        if field is None:
            return '{:20} missing value'.format(metric.label)
        value = getattr(metric, field)

        # Special case formatting
        if field == 'duration':
            return '{:20} {}'.format(metric.label, MetricsCommand._secs_to_hms(value.seconds))
        elif field == 'timestamp':
            return '{:20} {}'.format(metric.label, MetricsCommand._timestamp_str(value))
        elif field == 'float_value':
            if metric.units == 'm':
                return '{:20} {}'.format(metric.label, MetricsCommand._distance_str(value))
            return '{:20} {:.2f} {}'.format(metric.label, value, metric.units)
        else:
            # Default formatting
            return '{:20} {} {}'.format(metric.label, value, metric.units)


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
        self._parser.add_argument('-f', '--feature-codes', nargs='+',
                                  help='Optional feature list for GetFeatureEnabled API.')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True.
        """
        license_client = robot.ensure_client(LicenseClient.default_service_name)
        self._get_license_info(license_client, options)
        self._get_feature_enabled(license_client, options)
        return True

    def _get_license_info(self, license_client, options):
        license_info = license_client.get_license_info()
        if options.proto:
            print(license_info)
        else:
            print(str(license_info))

    def _get_feature_enabled(self, license_client, options):
        if not options.feature_codes or len(options.feature_codes) == 0:
            return

        feature_enabled = license_client.get_feature_enabled(options.feature_codes)
        for feature in feature_enabled:
            if feature_enabled[feature]:
                print(f"Feature {feature} is enabled.")
            else:
                print(f"Feature {feature} is not enabled.")


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
            image_formats = [image_pb2.Image.Format.Name(i)[7:] for i in image_source.image_formats]
            pixel_formats = [
                image_pb2.Image.PixelFormat.Name(i)[13:] for i in image_source.pixel_formats
            ]
            print("{:30s} ({:d}x{:d}) {:15s} {:15s}".format(image_source.name, image_source.rows,
                                                            image_source.cols,
                                                            ','.join(image_formats),
                                                            ','.join(pixel_formats)))
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
        # Save the image files in the correct format (jpeg, pgm for raw/rle).
        save_images_as_files(response)

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
        super(DataAcquisitionCommand, self).__init__(subparsers, command_dict, [
            DataAcquisitionServiceCommand, DataAcquisitionRequestCommand,
            DataAcquisitionStatusCommand, DataAcquisitionGetLiveDataCommand
        ])


class DataAcquisitionRequestCommand(Command):
    """Capture and save images or metadata specified in the command line arguments."""

    NAME = 'request'

    def __init__(self, subparsers, command_dict):
        """Capture and save images or metadata specified in the command line arguments.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(DataAcquisitionRequestCommand, self).__init__(subparsers, command_dict)
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
                'A request must have a 1:1 correspondence between image source and image service arguments.'
            )

        captures = data_acquisition_pb2.AcquisitionRequestList()
        captures.data_captures.extend(
            [data_acquisition_pb2.DataCapture(name=data_name) for data_name in options.data_source])
        img_captures = []
        for i, src_name in enumerate(options.image_source):
            img_service = options.image_service[i]
            img_captures.append(
                data_acquisition_pb2.ImageSourceCapture(image_service=img_service,
                                                        image_source=src_name))
        captures.image_captures.extend(img_captures)

        robot.time_sync.wait_for_sync(timeout_sec=1.0)
        data_acquisition_client = robot.ensure_client(DataAcquisitionClient.default_service_name)
        success = acquire_and_process_request(data_acquisition_client, captures, options.group_name,
                                              options.action_name,
                                              block_until_complete=not options.non_blocking_request)
        return success


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
        self._service_name_width = 35
        self._has_live_data_width = 30

    def _format_and_print_capability(self, data_type, data_name, service_name="", has_live_data=""):
        """Print the data acquisition capability.

        Args:
            data_type (string): Either image or data capabilities.
            data_name (string): The name of the data acquisition capability
            service_name(string): For image capabilities, a service name is required.
        """
        print(
            ('{:' + str(self._data_type_width) + '} {:' + str(self._data_name_width) + '} {:' +
             str(self._service_name_width) + '} {:' + str(self._has_live_data_width) + '}').format(
                 data_type, data_name, service_name, has_live_data))

    def _run(self, robot, options):
        """Implementation of the 'info' command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.
        """
        capabilities = robot.ensure_client(
            DataAcquisitionClient.default_service_name).get_service_info()
        print("Data Acquisition Service's Available Capabilities\n")
        self._format_and_print_capability("Data Type", "Data Name", "(optional) Service Name",
                                          "(optional) has_live_data")
        print("-" * (self._data_type_width + self._data_name_width + self._service_name_width +
                     self._has_live_data_width))
        for data_name in capabilities.data_sources:
            self._format_and_print_capability("data", data_name.name, data_name.service_name,
                                              str(data_name.has_live_data))
        for img_service in capabilities.image_sources:
            for img in img_service.image_source_names:
                self._format_and_print_capability("image", img, img_service.service_name)
        for ncb_worker in capabilities.network_compute_sources:
            for model in ncb_worker.models.data:
                self._format_and_print_capability("models", model.model_name,
                                                  ncb_worker.server_config.service_name)
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


class DataAcquisitionGetLiveDataCommand(Command):
    """Call GetLiveData based on service name."""

    NAME = 'live'

    def __init__(self, subparsers, command_dict):
        """Call GetLiveData based on service name.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(DataAcquisitionGetLiveDataCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--data-source', metavar='DATA_SRC', default=[],
                                  help='Data source name', action='append', required=True)

    def _run(self, robot, options):
        """Implementation of the 'live' command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True once complete.
        """
        daq_client = robot.ensure_client(DataAcquisitionClient.default_service_name)
        request = data_acquisition_pb2.LiveDataRequest()
        request.data_captures.extend(
            [data_acquisition_pb2.DataCapture(name=data_name) for data_name in options.data_source])
        response = daq_client.get_live_data(request)
        print(response)
        return True


class HostComputerIPCommand(Command):
    """Determine a computer's IP address."""

    NAME = 'self-ip'
    NEED_AUTHENTICATION = False

    def __init__(self, subparsers, command_dict):
        """Determine the IP address of the current computer used to talk to the robot.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(HostComputerIPCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            True
        """
        print("The IP address of the computer used to talk to the robot is: %s" %
              (bosdyn.client.common.get_self_ip(robot._name)))


class PowerCommand(Subcommands):
    """Send power commands to the robot."""

    NAME = 'power'

    def __init__(self, subparsers, command_dict):
        """Send power commands to the robot.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(PowerCommand, self).__init__(
            subparsers,
            command_dict,
            [
                PowerRobotCommand,
                PowerPayloadsCommand,
                PowerWifiRadioCommand,
            ])


class PowerRobotCommand(Command):
    """Control the power of the entire robot."""

    NAME = 'robot'

    def __init__(self, subparsers, command_dict):
        """Power cycle or power off robot computers.

        Note that this is only compatible with certain robots. Check HardwareConfiguration for details.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(PowerRobotCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('cmd', choices=['cycle', 'off'])

    def _run(self, robot, options):
        """

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.
        """
        robot.time_sync.wait_for_sync(timeout_sec=1.0)
        lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
        with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True,
                                                return_at_exit=True):
            power_client = robot.ensure_client(PowerClient.default_service_name)
            if options.cmd == 'cycle':
                power_cycle_robot(power_client)
            elif options.cmd == 'off':
                power_off_robot(power_client)


class PowerPayloadsCommand(Command):
    """Control the power of robot payloads."""

    NAME = 'payload'

    def __init__(self, subparsers, command_dict):
        """Power on or off robot payloads.

        Note that this is only compatible with certain robots. Check HardwareConfiguration for details.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(PowerPayloadsCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('on_off', choices=['on', 'off'])

    def _run(self, robot, options):
        """

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.
        """

        robot.time_sync.wait_for_sync(timeout_sec=1.0)
        lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
        with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True,
                                                return_at_exit=True):
            power_client = robot.ensure_client(PowerClient.default_service_name)
            if options.on_off == 'on':
                power_on_payload_ports(power_client)
            elif options.on_off == 'off':
                power_off_payload_ports(power_client)


class PowerWifiRadioCommand(Command):
    """Control the power of robot wifi radio."""

    NAME = 'wifi'

    def __init__(self, subparsers, command_dict):
        """Power on or off robot LTE radio.

        Note that this is only compatible with certain robots. Check HardwareConfiguration for details.

        Args:
            subparsers: List of argument parsers.
            command_dict: Dictionary of command names which take parsed options.
        """
        super(PowerWifiRadioCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('on_off', choices=['on', 'off'])

    def _run(self, robot, options):
        """

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.
        """

        robot.time_sync.wait_for_sync(timeout_sec=1.0)
        lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
        with bosdyn.client.lease.LeaseKeepAlive(lease_client, must_acquire=True,
                                                return_at_exit=True):
            power_client = robot.ensure_client(PowerClient.default_service_name)
            if options.on_off == 'on':
                power_on_wifi_radio(power_client)
            elif options.on_off == 'off':
                power_off_wifi_radio(power_client)




def main(args=None):
    """Command-line interface for interacting with robot services."""
    parser = argparse.ArgumentParser(prog='bosdyn.client', description=main.__doc__)
    add_common_arguments(parser, credentials_no_warn=True)

    command_dict = {}  # command name to fn which takes parsed options
    subparsers = parser.add_subparsers(title='commands', dest='command')

    # Register commands that can be run.
    DirectoryCommands(subparsers, command_dict)
    PayloadCommands(subparsers, command_dict)
    FaultCommands(subparsers, command_dict)
    RobotIdCommand(subparsers, command_dict)
    LicenseCommand(subparsers, command_dict)
    LogStatusCommands(subparsers, command_dict)
    RobotStateCommands(subparsers, command_dict)
    DataBufferCommands(subparsers, command_dict)
    DataServiceCommands(subparsers, command_dict)
    TimeSyncCommand(subparsers, command_dict)
    LeaseCommands(subparsers, command_dict)
    BecomeEstopCommand(subparsers, command_dict)
    ImageCommands(subparsers, command_dict)
    LocalGridCommands(subparsers, command_dict)
    DataAcquisitionCommand(subparsers, command_dict)
    HostComputerIPCommand(subparsers, command_dict)
    PowerCommand(subparsers, command_dict)

    options = parser.parse_args(args=args)

    setup_logging(verbose=options.verbose)

    # Create robot object and authenticate.
    sdk = bosdyn.client.create_standard_sdk('BosdynClient')
    sdk.register_service_client(DataAcquisitionPluginClient)

    robot = sdk.create_robot(options.hostname)

    if not options.command:
        print("Need to specify a command")
        parser.print_help()
        return False

    if not command_dict[options.command].run(robot, options):
        return False

    return True
