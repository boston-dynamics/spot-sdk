"""Command-line utility code for interacting with robot services."""

from __future__ import print_function, division
import abc
import argparse
import signal
import threading
import time

import six

import bosdyn.client
from bosdyn.util import (duration_str, timestamp_to_datetime)

from .auth import InvalidLoginError
from .exceptions import Error, InvalidAppTokenError, ProxyConnectionError
from .directory import DirectoryClient, NonexistentServiceError
from .estop import EstopClient, EstopEndpoint, EstopKeepAlive
from .image import (ImageClient, UnknownImageSourceError, ImageResponseError, build_image_request)
from .lease import LeaseClient
from .log_annotation import (LogAnnotationClient, LogAnnotationTextMessage)
from .robot_id import RobotIdClient
from .robot_state import RobotStateClient
from .sdk import SdkError
from .time_sync import (TimeSyncClient, TimeSyncEndpoint, TimeSyncError)
from .util import (add_common_arguments, setup_logging)


# pylint: disable=too-few-public-methods
class Command(object, six.with_metaclass(abc.ABCMeta)):
    """Command-line command"""

    # The name of the command the user should enter on the command line to select this command.
    NAME = None

    # Whether authentication is needed before the command is run.
    # Most commands need authentication.
    NEED_AUTHENTICATION = True

    def __init__(self, subparsers, command_dict):
        command_dict[self.NAME] = self
        self._parser = subparsers.add_parser(self.NAME, help=self.__doc__)

    def run(self, robot, options):
        """Invoke the command."""
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
        """Implementation of the command."""


class Subcommands(Command):
    """Run subcommands."""

    def __init__(self, subparsers, command_dict, subcommands):
        super(Subcommands, self).__init__(subparsers, command_dict)
        command_dest = '{}_command'.format(self.NAME)
        cmd_subparsers = self._parser.add_subparsers(title=self.__doc__, dest=command_dest)
        self._subcommands = {}
        for subcommand in subcommands:
            subcommand(cmd_subparsers, self._subcommands)

    def _run(self, robot, options):
        command_dest = '{}_command'.format(self.NAME)
        subcommand = vars(options)[command_dest]
        return self._subcommands[subcommand].run(robot, options)


class DirectoryCommands(Subcommands):
    """Commands related to the directory service"""

    NAME = 'dir'

    def __init__(self, subparsers, command_dict):
        super(DirectoryCommands, self).__init__(subparsers, command_dict,
                                                [DirectoryListCommand, DirectoryGetCommand])


def _format_dir_entry(service_name, service_type, authority, tokens):
    print("{:23} {:31} {:27} {}".format(service_name, service_type, authority, tokens))


def _token_req_str(entry):
    """Returns a string representing tokens required for using the service."""
    required = []
    if entry.application_token_required:
        required.append('app')
    if entry.user_token_required:
        required.append('user')
    if not required:
        return ''
    return ', '.join(required)


def _show_directory_list(robot, as_proto=False):
    """Print service directory list for robot."""
    entries = robot.ensure_client(DirectoryClient.default_service_name).list()
    if not entries:
        print("No services found")
        return True
    if not as_proto:
        _format_dir_entry('name', 'type', 'authority', 'tokens')
        print("-" * 90)
    for entry in entries:
        if as_proto:
            print(entry)
        else:
            _format_dir_entry(entry.name, entry.type, entry.authority, _token_req_str(entry))
    return True


def _show_directory_entry(robot, service, as_proto=False):
    """Print a service directory entry."""
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
        super(DirectoryListCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')

    def _run(self, robot, options):
        _show_directory_list(robot, as_proto=options.proto)
        return True


class DirectoryGetCommand(Command):
    """Get entry for a given service in the directory."""

    NAME = 'get'

    def __init__(self, subparsers, command_dict):
        super(DirectoryGetCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')
        self._parser.add_argument('service', help='service name to get entry for')

    def _run(self, robot, options):
        try:
            _show_directory_entry(robot, options.service, as_proto=options.proto)
        except NonexistentServiceError:
            print('The requested service name "{}" does not exist.  Available services:'.format(options.service))
            _show_directory_list(robot, as_proto=options.proto)
            return False
        return True


class RobotIdCommand(Command):
    """Show robot-id."""

    NAME = 'id'
    NEED_AUTHENTICATION = False

    def __init__(self, subparsers, command_dict):
        super(RobotIdCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')

    def _run(self, robot, options):
        proto = robot.ensure_client(RobotIdClient.default_service_name).get_id()
        if options.proto:
            print(proto)
            return True
        nickname = ''
        if proto.nickname and proto.nickname != proto.serial_number:
            nickname = proto.nickname
        release = proto.software_release
        version = release.version
        print("{:20} {:15} {:10} {} ({})".format(proto.serial_number, proto.computer_serial_number,
                                           nickname, proto.species, proto.version))
        print(" Software: {}.{}.{} ({} {})".format(version.major_version, version.minor_version,
                                                   version.patch_level, release.changeset,
                                                   timestamp_to_datetime(release.changeset_date)))
        print("  Installed: {}".format(timestamp_to_datetime(release.install_date)))
        return True


class LogAnnotationCommands(Subcommands):
    """Commands related to the log-annotation service"""

    NAME = 'log'

    def __init__(self, subparsers, command_dict):
        super(LogAnnotationCommands, self).__init__(subparsers, command_dict,
                                                    [LogTextMsgCommand, LogOperatorCommentCommand])


class LogTextMsgCommand(Command):
    """Send a text-message to the robot to be logged."""

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
        super(LogOperatorCommentCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--timestamp', action='store_true',
                                  help='achieve time-sync and send timestamp')
        self._parser.add_argument('message', help='operator comment text')

    def _run(self, robot, options):
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
    """Commands for querying robot state"""

    NAME = 'state'

    def __init__(self, subparsers, command_dict):
        super(RobotStateCommands, self).__init__(subparsers, command_dict,
                                                 [FullStateCommand, MetricsCommand])


class FullStateCommand(Command):
    """Show robot state."""

    NAME = 'full'

    def _run(self, robot, options):
        proto = robot.ensure_client(RobotStateClient.default_service_name).get_robot_state()
        print(proto)


class MetricsCommand(Command):
    """Show metrics (runtime, etc...)."""

    NAME = 'metrics'

    def __init__(self, subparsers, command_dict):
        super(MetricsCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print metrics in proto format')

    def _run(self, robot, options):
        proto = robot.ensure_client(RobotStateClient.default_service_name).get_robot_metrics()
        if options.proto:
            print(proto)
            return True
        for metric in proto.metrics:
            print(self._format_metric(metric))
        return True

    @staticmethod
    def _secs_to_hms(seconds):
        isecs = int(seconds)
        seconds = isecs % 60
        minutes = (isecs // 60) % 60
        hours = isecs // 3600
        return '{:d}:{:02d}:{:02d}'.format(hours, minutes, seconds)

    @staticmethod
    def _distance_str(meters):
        if meters < 1000:
            return '{:.2f} m'.format(meters)
        return '{:.2f} km'.format(float(meters) / 1000)

    @staticmethod
    def _format_metric(metric):  # pylint: disable=too-many-return-statements
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
        super(TimeSyncCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')

    def _run(self, robot, options):
        endpoint = TimeSyncEndpoint(robot.ensure_client(TimeSyncClient.default_service_name))
        if not endpoint.establish_timesync(break_on_success=True):
            print("Failed to acheive time sync")
            return False

        if options.proto:
            print(endpoint.response)
            return True

        print("GRPC round-trip time: {}".format(duration_str(endpoint.round_trip_time)))
        print("Local time to robot time: {}".format(duration_str(endpoint.clock_skew)))

        return True


class LeaseCommands(Subcommands):
    """Commands related to the lease service"""

    NAME = 'lease'

    def __init__(self, subparsers, command_dict):
        super(LeaseCommands, self).__init__(subparsers, command_dict, [LeaseListCommand])


class LeaseListCommand(Command):
    """List all leases"""

    NAME = 'list'

    def __init__(self, subparsers, command_dict):
        super(LeaseListCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')

    def _run(self, robot, options):
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
    """Grab and hold estop until Ctl-C"""

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
    """Commands for querying images"""

    NAME = 'image'

    def __init__(self, subparsers, command_dict):
        super(ImageCommands, self).__init__(subparsers, command_dict,
                                            [ListImageSourcesCommand, GetImageCommand])

def _show_image_sources_list(robot, as_proto=False):
    """Print available image sources."""
    proto = robot.ensure_client(ImageClient.default_service_name).list_image_sources()
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
        super(ListImageSourcesCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--proto', action='store_true',
                                  help='print listing in proto format')

    def _run(self, robot, options):
        _show_image_sources_list(robot, as_proto=options.proto)


class GetImageCommand(Command):
    """Get an image from the robot."""

    NAME = 'get-image'

    def __init__(self, subparsers, command_dict):
        super(GetImageCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--outfile', default=None,
                                  help='filename into which to save the image')
        self._parser.add_argument('--quality-percent', type=int, default=75,
                                  help='Percent image quaility (0-100)')
        self._parser.add_argument('source_name', help='image source name')

    def _run(self, robot, options):
        image_request = build_image_request(options.source_name, options.quality_percent)
        try:
            response = robot.ensure_client(ImageClient.default_service_name).get_image([image_request])
        except UnknownImageSourceError:
            print('Requested image source "{}" does not exist.  Available image sources:'.format(options.source_name))
            _show_image_sources_list(robot)
            return False
        except ImageResponseError:
            print('Robot cannot generate the "{}" at this time.  Retry the command.'.format(options.source_name))
            return False

        for image_response in response:
            image_source_filename = 'image-{}.jpg'.format(image_response.source.name)
            filename = options.outfile or image_source_filename
            try:
                with open(filename, 'wb') as outfile:
                    outfile.write(image_response.shot.image.data)
                print('Saved "{}" to "{}".'.format(image_response.source.name, filename))
            except IOError:
                print('Failed to save "{}".'.format(image_response.source.name))
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
    RobotStateCommands(subparsers, command_dict)
    LogAnnotationCommands(subparsers, command_dict)
    TimeSyncCommand(subparsers, command_dict)
    LeaseCommands(subparsers, command_dict)
    BecomeEstopCommand(subparsers, command_dict)
    ImageCommands(subparsers, command_dict)

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
