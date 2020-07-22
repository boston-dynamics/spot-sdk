# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Command-line utility code for interacting with robot services."""

from __future__ import print_function, division
import abc
import argparse
import numpy as np
import signal
import threading
import time
import os
from .exceptions import InvalidRequestError

import six

from bosdyn.api import image_pb2
from bosdyn.api.log_annotation_pb2 import LogAnnotationTextMessage
import bosdyn.client
from bosdyn.util import (duration_str, timestamp_to_datetime)

from .auth import InvalidLoginError
from .exceptions import Error, InvalidAppTokenError, ProxyConnectionError
from .directory import DirectoryClient, NonexistentServiceError
from .directory_registration import DirectoryRegistrationClient, DirectoryRegistrationResponseError
from .estop import EstopClient, EstopEndpoint, EstopKeepAlive
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
            return self._run(robot, options)
        except ProxyConnectionError:
            print('Could not contact robot with hostname "{}".'.format(options.hostname))
        except InvalidAppTokenError:
            print('The provided app token "{}" is invalid.'.format(options.app_token))
        except InvalidLoginError:
            print('Username "{}" and/or password are invalid.'.format(options.username))
        except Error as e:
            print('{}: {}'.format(type(e).__name__, e))

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
    """Commands related to the directory service.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'dir'

    def __init__(self, subparsers, command_dict):
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

    print(
        ('{:' + str(name_width) + '} {:' + str(type_width) + '} {:' + str(authority_width) + '} {}')
        .format(name, service_type, authority, tokens))


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
    """List all services in the directory.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'list'

    def __init__(self, subparsers, command_dict):
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
    """Get entry for a given service in the directory.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'get'

    def __init__(self, subparsers, command_dict):
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
    """Register entry for a service in the directory.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'register'

    def __init__(self, subparsers, command_dict):
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
    """Unregister entry for a service in the directory.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'unregister'

    def __init__(self, subparsers, command_dict):
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


class RobotIdCommand(Command):
    """Show robot-id.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'id'
    NEED_AUTHENTICATION = False

    def __init__(self, subparsers, command_dict):
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
    """Commands related to the log-annotation service.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'log'

    def __init__(self, subparsers, command_dict):
        super(LogAnnotationCommands, self).__init__(subparsers, command_dict,
                                                    [LogTextMsgCommand, LogOperatorCommentCommand])


class LogTextMsgCommand(Command):
    """Send a text-message to the robot to be logged.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'textmsg'

    def __init__(self, subparsers, command_dict):
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
    """Send an operator comment to the robot to be logged.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'comment'

    def __init__(self, subparsers, command_dict):
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


class RobotStateCommands(Subcommands):
    """Commands for querying robot state.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'state'

    def __init__(self, subparsers, command_dict):
        super(RobotStateCommands, self).__init__(subparsers, command_dict,
                                                 [FullStateCommand, MetricsCommand, RobotModel])


class FullStateCommand(Command):
    """Show robot state.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'full'

    def _run(self, robot, options):
        """Implementation of the command; prints RobotState proto.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.
        """
        proto = robot.ensure_client(RobotStateClient.default_service_name).get_robot_state()
        print(proto)


class RobotModel(Command):
    """Write robot URDF and mesh to local files.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'model'
    NEED_AUTHENTICATION = False

    def __init__(self, subparsers, command_dict):
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
        except (OSError):
            pass

        # Write each link model to its own file
        for l in hardware.skeleton.links:
            # Request a Skeleton.Link.ObjModel from the robot for link.name and write it to a file
            try:
                obj_model_proto = robot_state_client.get_robot_link_model(l.name)
            except InvalidRequestError as e:
                print(e, end='')
                print(" Name of link: " + l.name)
                continue

            # If file_name is empty, ignore
            if not obj_model_proto.file_name:
                continue

            # Write to a file, ignoring the robot path
            sub_path = ''.join(obj_model_proto.file_name.split('/')[:-1])  # robot defined path
            path = os.path.join(model_directory, sub_path)  # local path + robot path
            try:
                os.makedirs(path)
            except (OSError):
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
    """Show metrics (runtime, etc...).

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'metrics'

    def __init__(self, subparsers, command_dict):
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
    """Find clock difference between this and the robot clock.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'time-sync'

    def __init__(self, subparsers, command_dict):
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
        license = license_client.get_license_info()
        if options.proto:
            print(license)
        else:
            print(str(license))

        return True


class LeaseCommands(Subcommands):
    """Commands related to the lease service.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'lease'

    def __init__(self, subparsers, command_dict):
        super(LeaseCommands, self).__init__(subparsers, command_dict, [LeaseListCommand])


class LeaseListCommand(Command):
    """List all leases.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'list'

    def __init__(self, subparsers, command_dict):
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
    """Grab and hold estop until Ctl-C.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'become-estop'

    _RPC_PRINT_CHOICES = ['timestamp', 'full']

    def __init__(self, subparsers, command_dict):
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
    """Commands for querying images.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'image'

    def __init__(self, subparsers, command_dict):
        super(ImageCommands, self).__init__(subparsers, command_dict,
                                            [ListImageSourcesCommand, GetImageCommand])


def _show_image_sources_list(robot, as_proto=False):
    """Print available image sources.

    Args:
        robot: Robot object on which to run the command.
        as_proto: Boolean to determine whether to print the full proto message, or a human-readable
            string in the format: source_name (rows x cols)

    Returns:
        True.
    """
    proto = robot.ensure_client(ImageClient.default_service_name).list_image_sources()
    if as_proto:
        print(proto)
    else:
        for image_source in proto:
            print("{:30s} ({:d}x{:d})".format(image_source.name, image_source.rows,
                                              image_source.cols))
    return True


class ListImageSourcesCommand(Command):
    """List image sources.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'list-sources'

    def __init__(self, subparsers, command_dict):
        super(ListImageSourcesCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')

    def _run(self, robot, options):
        """Implementation of the command.

        Args:
            robot: Robot object on which to run the command.
            options: Parsed command-line arguments.

        Returns:
            Output of _show_image_sources_list method.
        """
        _show_image_sources_list(robot, as_proto=options.proto)

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
        fd_out=open(filename, 'w')
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
    """Get an image from the robot and write it to an image file.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'get-image'

    def __init__(self, subparsers, command_dict):
        super(GetImageCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--outfile', default=None,
                                  help='filename into which to save the image')
        self._parser.add_argument('--quality-percent', type=int, default=75,
                                  help='Percent image quality (0-100)')
        self._parser.add_argument('source_name', metavar='SRC', nargs='+', help='image source name')

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
            response = robot.ensure_client(
                ImageClient.default_service_name).get_image(image_requests)
        except UnknownImageSourceError:
            print('Requested image source "{}" does not exist.  Available image sources:'.format(
                options.source_name))
            _show_image_sources_list(robot)
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
    """Commands for querying local grid maps.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'local_grid'

    def __init__(self, subparsers, command_dict):
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
    """List local grid sources.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'types'

    def __init__(self, subparsers, command_dict):
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


class GetLocalGridsCommand(Command):
    """Get local grids from the robot.

    Args:
        subparsers: List of argument parsers.
        command_dict: Dictionary of command names which take parsed options.
    """

    NAME = 'get'

    def __init__(self, subparsers, command_dict):
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
        response = robot.ensure_client(LocalGridClient.default_service_name).get_local_grids(options.types)

        for local_grid_response in response:
            print(local_grid_response)
        return True


def main(args=None):
    """Command-line interface for interacting with robot services."""
    parser = argparse.ArgumentParser(prog='bosdyn.client', description=main.__doc__)
    add_common_arguments(parser)

    command_dict = {}  # command name to fn which takes parsed options
    subparsers = parser.add_subparsers(title='commands', dest='command')

    # Register commands that can be run.
    DirectoryCommands(subparsers, command_dict)
    RobotIdCommand(subparsers, command_dict)
    LicenseCommand(subparsers, command_dict)
    RobotStateCommands(subparsers, command_dict)
    LogAnnotationCommands(subparsers, command_dict)
    TimeSyncCommand(subparsers, command_dict)
    LeaseCommands(subparsers, command_dict)
    BecomeEstopCommand(subparsers, command_dict)
    ImageCommands(subparsers, command_dict)
    LocalGridCommands(subparsers, command_dict)

    options = parser.parse_args(args=args)

    setup_logging(verbose=options.verbose)

    # Create robot object and authenticate.
    sdk = bosdyn.client.create_standard_sdk('BosdynClient')
    try:
        sdk.load_app_token(options.app_token)
    except SdkError:
        print('Cannot retrieve app token from "{}".'.format(options.app_token))
        return

    robot = sdk.create_robot(options.hostname)

    if not command_dict[options.command].run(robot, options):
        return
