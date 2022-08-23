# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Interactive command-line mission recorder
"""

from __future__ import print_function

import curses
import logging
import os
import signal
import threading
import time
import traceback

from google.protobuf import wrappers_pb2 as wrappers

import bosdyn.api.robot_state_pb2 as robot_state_proto
import bosdyn.api.spot.robot_command_pb2 as spot_command_pb2
import bosdyn.client
import bosdyn.client.channel
import bosdyn.client.util
from bosdyn.api import geometry_pb2, world_object_pb2
from bosdyn.api.graph_nav import graph_nav_pb2, map_pb2, map_processing_pb2, recording_pb2
from bosdyn.api.mission import nodes_pb2
from bosdyn.client import ResponseError, RpcError, create_standard_sdk
from bosdyn.client.async_tasks import AsyncPeriodicQuery, AsyncTasks
from bosdyn.client.estop import EstopClient, EstopEndpoint, EstopKeepAlive
from bosdyn.client.frame_helpers import ODOM_FRAME_NAME
from bosdyn.client.graph_nav import GraphNavClient
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.map_processing import MapProcessingServiceClient
from bosdyn.client.power import PowerClient
from bosdyn.client.recording import (GraphNavRecordingServiceClient, NotLocalizedToEndError,
                                     NotReadyYetError)
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.time_sync import TimeSyncError
from bosdyn.client.world_object import WorldObjectClient
from bosdyn.util import duration_str, format_metric, secs_to_hms

LOGGER = logging.getLogger()

VELOCITY_BASE_SPEED = 0.5  # m/s
VELOCITY_BASE_ANGULAR = 0.8  # rad/sec
VELOCITY_CMD_DURATION = 0.6  # seconds
COMMAND_INPUT_RATE = 0.1

# Velocity limits for navigation (optional)
NAV_VELOCITY_MAX_YAW = 1.2  # rad/s
NAV_VELOCITY_MAX_X = 1.0  # m/s
NAV_VELOCITY_MAX_Y = 0.5  # m/s
NAV_VELOCITY_LIMITS = geometry_pb2.SE2VelocityLimit(
    max_vel=geometry_pb2.SE2Velocity(
        linear=geometry_pb2.Vec2(x=NAV_VELOCITY_MAX_X, y=NAV_VELOCITY_MAX_Y),
        angular=NAV_VELOCITY_MAX_YAW), min_vel=geometry_pb2.SE2Velocity(
            linear=geometry_pb2.Vec2(x=-NAV_VELOCITY_MAX_X, y=-NAV_VELOCITY_MAX_Y),
            angular=-NAV_VELOCITY_MAX_YAW))


def _grpc_or_log(desc, thunk):
    try:
        return thunk()
    except (ResponseError, RpcError) as err:
        LOGGER.error("Failed %s: %s" % (desc, err))


class ExitCheck(object):
    """A class to help exiting a loop, also capturing SIGTERM to exit the loop."""

    def __init__(self):
        self._kill_now = False
        signal.signal(signal.SIGTERM, self._sigterm_handler)
        signal.signal(signal.SIGINT, self._sigterm_handler)

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        return False

    def _sigterm_handler(self, _signum, _frame):
        self._kill_now = True

    def request_exit(self):
        """Manually trigger an exit (rather than sigterm/sigint)."""
        self._kill_now = True

    @property
    def kill_now(self):
        """Return the status of the exit checker indicating if it should exit."""
        return self._kill_now


class CursesHandler(logging.Handler):
    """logging handler which puts messages into the curses interface"""

    def __init__(self, wasd_interface):
        super(CursesHandler, self).__init__()
        self._wasd_interface = wasd_interface

    def emit(self, record):
        msg = record.getMessage()
        msg = msg.replace('\n', ' ').replace('\r', '')
        self._wasd_interface.add_message('{:s} {:s}'.format(record.levelname, msg))


class AsyncRobotState(AsyncPeriodicQuery):
    """Grab robot state."""

    def __init__(self, robot_state_client):
        super(AsyncRobotState, self).__init__("robot_state", robot_state_client, LOGGER,
                                              period_sec=0.2)

    def _start_query(self):
        return self._client.get_robot_state_async()


class RecorderInterface(object):
    """A curses interface for recording robot missions."""

    def __init__(self, robot, download_filepath):
        self._robot = robot

        # Flag indicating whether mission is currently being recorded
        self._recording = False

        # Flag indicating whether robot is in feature desert mode
        self._desert_mode = False

        # Filepath for the location to put the downloaded graph and snapshots.
        self._download_filepath = download_filepath

        # List of waypoint commands
        self._waypoint_commands = []

        # Dictionary indicating which waypoints are deserts
        self._desert_flag = {}

        # Current waypoint id
        self._waypoint_id = 'NONE'

        # Create clients -- do not use the for communication yet.
        self._lease_client = robot.ensure_client(LeaseClient.default_service_name)
        try:
            self._estop_client = self._robot.ensure_client(EstopClient.default_service_name)
            self._estop_endpoint = EstopEndpoint(self._estop_client, 'GNClient', 9.0)
        except:
            # Not the estop.
            self._estop_client = None
            self._estop_endpoint = None

        self._map_processing_client = robot.ensure_client(
            MapProcessingServiceClient.default_service_name)
        self._power_client = robot.ensure_client(PowerClient.default_service_name)
        self._robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
        self._robot_command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        self._world_object_client = robot.ensure_client(WorldObjectClient.default_service_name)

        # Set up the recording service client.
        self._recording_client = self._robot.ensure_client(
            GraphNavRecordingServiceClient.default_service_name)

        # Set up the graph nav service client.
        self._graph_nav_client = robot.ensure_client(GraphNavClient.default_service_name)

        # Local copy of the graph.
        self._graph = None
        self._all_graph_wps_in_order = []

        self._robot_state_task = AsyncRobotState(self._robot_state_client)
        self._async_tasks = AsyncTasks([self._robot_state_task])
        self._lock = threading.Lock()
        self._command_dictionary = {
            27: self._stop,  # ESC key
            ord('\t'): self._quit_program,
            ord('T'): self._toggle_time_sync,
            ord(' '): self._toggle_estop,
            ord('r'): self._self_right,
            ord('P'): self._toggle_power,
            ord('v'): self._sit,
            ord('f'): self._stand,
            ord('w'): self._move_forward,
            ord('s'): self._move_backward,
            ord('a'): self._strafe_left,
            ord('c'): self._auto_close_loops,
            ord('d'): self._strafe_right,
            ord('q'): self._turn_left,
            ord('e'): self._turn_right,
            ord('m'): self._start_recording,
            ord('l'): self._relocalize,
            ord('z'): self._enter_desert,
            ord('x'): self._exit_desert,
            ord('g'): self._generate_mission
        }
        self._locked_messages = ['', '', '']  # string: displayed message for user
        self._estop_keepalive = None
        self._exit_check = None

        # Stuff that is set in start()
        self._robot_id = None
        self._lease_keep_alive = None

    def start(self, lease_keep_alive):
        """Begin communication with the robot."""
        self._lease_keep_alive = lease_keep_alive
        self._robot_id = self._robot.get_id()
        if self._estop_endpoint is not None:
            self._estop_endpoint.force_simple_setup(
            )  # Set this endpoint as the robot's sole estop.

        # Clear existing graph nav map
        self._graph_nav_client.clear_graph()

    def shutdown(self):
        """Release control of robot as gracefully as possible."""
        LOGGER.info("Shutting down WasdInterface.")
        if self._estop_keepalive:
            # This stops the check-in thread but does not stop the robot.
            self._estop_keepalive.shutdown()

    def __del__(self):
        self.shutdown()

    def flush_and_estop_buffer(self, stdscr):
        """Manually flush the curses input buffer but trigger any estop requests (space)"""
        key = ''
        while key != -1:
            key = stdscr.getch()
            if key == ord(' '):
                self._toggle_estop()

    def add_message(self, msg_text):
        """Display the given message string to the user in the curses interface."""
        with self._lock:
            self._locked_messages = [msg_text] + self._locked_messages[:-1]

    def message(self, idx):
        """Grab one of the 3 last messages added."""
        with self._lock:
            return self._locked_messages[idx]

    @property
    def robot_state(self):
        """Get latest robot state proto."""
        return self._robot_state_task.proto

    def drive(self, stdscr):
        """User interface to control the robot via the passed-in curses screen interface object."""
        with ExitCheck() as self._exit_check:
            curses_handler = CursesHandler(self)
            curses_handler.setLevel(logging.INFO)
            LOGGER.addHandler(curses_handler)

            stdscr.nodelay(True)  # Don't block for user input.
            stdscr.resize(26, 96)
            stdscr.refresh()

            # for debug
            curses.echo()

            try:
                while not self._exit_check.kill_now:
                    self._async_tasks.update()
                    self._drive_draw(stdscr, self._lease_keep_alive)

                    try:
                        cmd = stdscr.getch()
                        # Do not queue up commands on client
                        self.flush_and_estop_buffer(stdscr)
                        self._drive_cmd(cmd)
                        time.sleep(COMMAND_INPUT_RATE)
                    except Exception:
                        # On robot command fault, sit down safely before killing the program.
                        self._safe_power_off()
                        time.sleep(2.0)
                        self.shutdown()
                        raise

            finally:
                LOGGER.removeHandler(curses_handler)

    def _count_visible_fiducials(self):
        """Return number of fiducials visible to robot."""
        request_fiducials = [world_object_pb2.WORLD_OBJECT_APRILTAG]
        fiducial_objects = self._world_object_client.list_world_objects(
            object_type=request_fiducials).world_objects
        return len(fiducial_objects)

    def _drive_draw(self, stdscr, lease_keep_alive):
        """Draw the interface screen at each update."""
        stdscr.clear()  # clear screen
        stdscr.resize(26, 96)
        stdscr.addstr(0, 0, '{:20s} {}'.format(self._robot_id.nickname,
                                               self._robot_id.serial_number))
        stdscr.addstr(1, 0, self._lease_str(lease_keep_alive))
        stdscr.addstr(2, 0, self._battery_str())
        stdscr.addstr(3, 0, self._estop_str())
        stdscr.addstr(4, 0, self._power_state_str())
        stdscr.addstr(5, 0, self._time_sync_str())
        stdscr.addstr(6, 0, self._waypoint_str())
        stdscr.addstr(7, 0, self._fiducial_str())
        stdscr.addstr(8, 0, self._desert_str())
        for i in range(3):
            stdscr.addstr(10 + i, 2, self.message(i))
        stdscr.addstr(14, 0, "Commands: [TAB]: quit                               ")
        stdscr.addstr(15, 0, "          [T]: Time-sync, [SPACE]: Estop, [P]: Power")
        stdscr.addstr(16, 0, "          [v]: Sit, [f]: Stand, [r]: Self-right     ")
        stdscr.addstr(17, 0, "          [wasd]: Directional strafing              ")
        stdscr.addstr(18, 0, "          [qe]: Turning, [ESC]: Stop                ")
        stdscr.addstr(19, 0, "          [m]: Start recording mission              ")
        stdscr.addstr(20, 0, "          [l]: Add fiducial localization to mission ")
        stdscr.addstr(21, 0, "          [z]: Enter desert mode                    ")
        stdscr.addstr(22, 0, "          [x]: Exit desert mode                     ")
        stdscr.addstr(23, 0, "          [g]: Stop recording and generate mission  ")

        stdscr.refresh()

    def _drive_cmd(self, key):
        """Run user commands at each update."""
        try:
            cmd_function = self._command_dictionary[key]
            cmd_function()

        except KeyError:
            if key and key != -1 and key < 256:
                self.add_message("Unrecognized keyboard command: '{}'".format(chr(key)))

    def _try_grpc(self, desc, thunk):
        try:
            return thunk()
        except (ResponseError, RpcError) as err:
            self.add_message("Failed {}: {}".format(desc, err))
            return None

    def _quit_program(self):
        if self._recording:
            self._stop_recording()
        self._robot.power_off()
        self.shutdown()
        if self._exit_check is not None:
            self._exit_check.request_exit()

    def _toggle_time_sync(self):
        if self._robot.time_sync.stopped:
            self._robot.time_sync.start()
        else:
            self._robot.time_sync.stop()

    def _toggle_estop(self):
        """toggle estop on/off. Initial state is ON"""
        if self._estop_client is not None and self._estop_endpoint is not None:
            if not self._estop_keepalive:
                self._estop_keepalive = EstopKeepAlive(self._estop_endpoint)
            else:
                self._try_grpc("stopping estop", self._estop_keepalive.stop)
                self._estop_keepalive.shutdown()
                self._estop_keepalive = None

    def _start_robot_command(self, desc, command_proto, end_time_secs=None):

        def _start_command():
            self._robot_command_client.robot_command(lease=None, command=command_proto,
                                                     end_time_secs=end_time_secs)

        self._try_grpc(desc, _start_command)

    def _self_right(self):
        self._start_robot_command('self_right', RobotCommandBuilder.selfright_command())

    def _sit(self):
        self._start_robot_command('sit', RobotCommandBuilder.synchro_sit_command())

    def _stand(self):
        self._start_robot_command('stand', RobotCommandBuilder.synchro_stand_command())

    def _move_forward(self):
        self._velocity_cmd_helper('move_forward', v_x=VELOCITY_BASE_SPEED)

    def _move_backward(self):
        self._velocity_cmd_helper('move_backward', v_x=-VELOCITY_BASE_SPEED)

    def _strafe_left(self):
        self._velocity_cmd_helper('strafe_left', v_y=VELOCITY_BASE_SPEED)

    def _strafe_right(self):
        self._velocity_cmd_helper('strafe_right', v_y=-VELOCITY_BASE_SPEED)

    def _turn_left(self):
        self._velocity_cmd_helper('turn_left', v_rot=VELOCITY_BASE_ANGULAR)

    def _turn_right(self):
        self._velocity_cmd_helper('turn_right', v_rot=-VELOCITY_BASE_ANGULAR)

    def _stop(self):
        self._start_robot_command('stop', RobotCommandBuilder.stop_command())

    def _velocity_cmd_helper(self, desc='', v_x=0.0, v_y=0.0, v_rot=0.0):
        self._start_robot_command(
            desc, RobotCommandBuilder.synchro_velocity_command(v_x=v_x, v_y=v_y, v_rot=v_rot),
            end_time_secs=time.time() + VELOCITY_CMD_DURATION)

    def _return_to_origin(self):
        self._start_robot_command(
            'fwd_and_rotate',
            RobotCommandBuilder.synchro_se2_trajectory_point_command(
                goal_x=0.0, goal_y=0.0, goal_heading=0.0, frame_name=ODOM_FRAME_NAME, params=None,
                body_height=0.0, locomotion_hint=spot_command_pb2.HINT_SPEED_SELECT_TROT),
            end_time_secs=time.time() + 20)

    def _toggle_power(self):
        power_state = self._power_state()
        if power_state is None:
            self.add_message('Could not toggle power because power state is unknown')
            return

        if power_state == robot_state_proto.PowerState.STATE_OFF:
            self._try_grpc("powering-on", self._request_power_on)
        else:
            self._try_grpc("powering-off", self._safe_power_off)

    def _request_power_on(self):
        bosdyn.client.power.power_on(self._power_client)

    def _safe_power_off(self):
        self._start_robot_command('safe_power_off', RobotCommandBuilder.safe_power_off_command())

    def _power_state(self):
        state = self.robot_state
        if not state:
            return None
        return state.power_state.motor_power_state

    def _lease_str(self, lease_keep_alive):
        alive = 'RUNNING' if lease_keep_alive.is_alive() else 'STOPPED'
        lease_proto = lease_keep_alive.lease_wallet.get_lease_state().lease_original.lease_proto
        lease = '{}:{}'.format(lease_proto.resource, lease_proto.sequence)
        return 'Lease {} THREAD:{}'.format(lease, alive)

    def _power_state_str(self):
        power_state = self._power_state()
        if power_state is None:
            return ''
        state_str = robot_state_proto.PowerState.MotorPowerState.Name(power_state)
        return 'Power: {}'.format(state_str[6:])  # get rid of STATE_ prefix

    def _estop_str(self):
        if not self._estop_client:
            thread_status = 'NOT ESTOP'
        else:
            thread_status = 'RUNNING' if self._estop_keepalive else 'STOPPED'
        estop_status = '??'
        state = self.robot_state
        if state:
            for estop_state in state.estop_states:
                if estop_state.type == estop_state.TYPE_SOFTWARE:
                    estop_status = estop_state.State.Name(estop_state.state)[6:]  # s/STATE_//
                    break
        return 'Estop {} (thread: {})'.format(estop_status, thread_status)

    def _time_sync_str(self):
        if not self._robot.time_sync:
            return 'Time sync: (none)'
        if self._robot.time_sync.stopped:
            status = 'STOPPED'
            exception = self._robot.time_sync.thread_exception
            if exception:
                status = '{} Exception: {}'.format(status, exception)
        else:
            status = 'RUNNING'
        try:
            skew = self._robot.time_sync.get_robot_clock_skew()
            if skew:
                skew_str = 'offset={}'.format(duration_str(skew))
            else:
                skew_str = "(Skew undetermined)"
        except (TimeSyncError, RpcError) as err:
            skew_str = '({})'.format(err)
        return 'Time sync: {} {}'.format(status, skew_str)

    def _waypoint_str(self):
        state = self._graph_nav_client.get_localization_state()
        try:
            self._waypoint_id = state.localization.waypoint_id
            if self._waypoint_id == '':
                self._waypoint_id = 'NONE'

        except:
            self._waypoint_id = 'ERROR'

        if self._recording and self._waypoint_id != 'NONE' and self._waypoint_id != 'ERROR':
            if self._waypoint_id not in self._desert_flag:
                self._desert_flag[self._waypoint_id] = self._desert_mode
            return 'Current waypoint: {} [ RECORDING ]'.format(self._waypoint_id)

        return 'Current waypoint: {}'.format(self._waypoint_id)

    def _fiducial_str(self):
        return 'Visible fiducials: {}'.format(str(self._count_visible_fiducials()))

    def _desert_str(self):
        if self._desert_mode:
            return '[ FEATURE DESERT MODE ]'
        else:
            return ''

    def _battery_str(self):
        if not self.robot_state:
            return ''
        battery_state = self.robot_state.battery_states[0]
        status = battery_state.Status.Name(battery_state.status)
        status = status[7:]  # get rid of STATUS_ prefix
        if battery_state.charge_percentage.value:
            bar_len = int(battery_state.charge_percentage.value) // 10
            bat_bar = '|{}{}|'.format('=' * bar_len, ' ' * (10 - bar_len))
        else:
            bat_bar = ''
        time_left = ''
        if battery_state.estimated_runtime:
            time_left = ' ({})'.format(secs_to_hms(battery_state.estimated_runtime.seconds))
        return 'Battery: {}{}{}'.format(status, bat_bar, time_left)

    def _fiducial_visible(self):
        """Return True if robot can see fiducial."""
        request_fiducials = [world_object_pb2.WORLD_OBJECT_APRILTAG]
        fiducial_objects = self._world_object_client.list_world_objects(
            object_type=request_fiducials).world_objects
        self.add_message("Fiducial objects: " + str(fiducial_objects))

        if len(fiducial_objects) > 0:
            return True

        return False

    def _start_recording(self):
        """Start recording a map."""
        if self._count_visible_fiducials() == 0:
            self.add_message("ERROR: Can't start recording -- No fiducials in view.")
            return

        if self._waypoint_id is None:
            self.add_message("ERROR: Not localized to waypoint.")
            return
        session_name = os.path.basename(self._download_filepath)
        # Create metadata for the recording session.
        client_metadata = GraphNavRecordingServiceClient.make_client_metadata(
            session_name=session_name, client_username=self._robot._current_user,
            client_id='Mission Recorder Example', client_type='Python SDK')
        environment = GraphNavRecordingServiceClient.make_recording_environment(
            waypoint_env=GraphNavRecordingServiceClient.make_waypoint_environment(
                client_metadata=client_metadata))
        # Tell graph nav to start recording map
        status = self._recording_client.start_recording(recording_environment=environment)
        if status != recording_pb2.StartRecordingResponse.STATUS_OK:
            self.add_message("Start recording failed.")
            return

        self.add_message("Started recording map.")
        self._graph = None
        self._all_graph_wps_in_order = []
        state = self._graph_nav_client.get_localization_state()
        if '' == state.localization.waypoint_id:
            self.add_message("No localization after start recording.")
            self._recording_client.stop_recording()
            return
        self._waypoint_commands = []
        # Treat this sort of like RPN / postfix, where operators follow their operands.
        # waypoint_id LOCALIZE means "localize to waypoint_id".
        # INITIALIZE takes no argument.
        # Implicitly, we make routes between pairs of waypoint ids as they occur.
        # `w0 w1 LOCALIZE w2` will give a route w0->w1, whereupon we localize,
        # and then a route w1->w2.
        self._waypoint_commands.append('INITIALIZE')
        # Start with the first waypoint.
        self._waypoint_commands.append(state.localization.waypoint_id)
        self._recording = True

    def _stop_recording(self):
        """Stop or pause recording a map."""
        if not self._recording:
            return True
        self._recording = False

        if self._waypoint_id != self._waypoint_commands[-1]:
            self._waypoint_commands += [self._waypoint_id]

        try:
            finished_recording = False
            status = recording_pb2.StopRecordingResponse.STATUS_UNKNOWN
            while True:
                try:
                    status = self._recording_client.stop_recording()
                except NotReadyYetError:
                    # The recording service always takes some time to complete. stop_recording
                    # must be called multiple times to ensure recording has finished.
                    self.add_message("Stopping...")
                    time.sleep(1.0)
                    continue
                break

            self.add_message("Successfully stopped recording a map.")
            return True

        except NotLocalizedToEndError:
            # This should never happen unless there's an internal error on the robot.
            self.add_message(
                "There was a problem while trying to stop recording. Please try again.")
            return False

    def _relocalize(self):
        """Insert localization node into mission."""
        if not self._recording:
            print('Not recording mission.')
            return False

        self.add_message("Adding fiducial localization to mission.")
        self._waypoint_commands += [self._waypoint_id]
        self._waypoint_commands += ['LOCALIZE']

        # Return to waypoint (in case localization shifted to another waypoint)
        self._waypoint_commands += [self._waypoint_id]
        return True

    def _enter_desert(self):
        self._desert_mode = True
        if self._recording:
            if self._waypoint_commands == [] or self._waypoint_commands[-1] != self._waypoint_id:
                self._waypoint_commands += [self._waypoint_id]

    def _exit_desert(self):
        self._desert_mode = False
        if self._recording:
            if self._waypoint_commands == [] or self._waypoint_commands[-1] != self._waypoint_id:
                self._waypoint_commands += [self._waypoint_id]

    def _generate_mission(self):
        """Save graph map and mission file."""

        # Check whether mission has been recorded
        if not self._recording:
            self.add_message("ERROR: No mission recorded.")
            return

        # Check for empty mission
        if len(self._waypoint_commands) == 0:
            self.add_message("ERROR: No waypoints in mission.")
            return

        # Stop recording mission
        if not self._stop_recording():
            self.add_message("ERROR: Error while stopping recording.")
            return

        # Save graph map
        os.mkdir(self._download_filepath)
        if not self._download_full_graph():
            self.add_message("ERROR: Error downloading graph.")
            return

        # Generate mission
        mission = self._make_mission()

        # Save mission file
        os.mkdir(os.path.join(self._download_filepath, "missions"))
        mission_filepath = os.path.join(self._download_filepath, "missions", "autogenerated")
        write_mission(mission, mission_filepath)

        # Quit program
        self._quit_program()

    def _make_desert(self, waypoint):
        waypoint.annotations.scan_match_region.empty.CopyFrom(
            map_pb2.Waypoint.Annotations.LocalizeRegion.Empty())

    def _download_full_graph(self, overwrite_desert_flag=None):
        """Download the graph and snapshots from the robot."""
        graph = self._graph_nav_client.download_graph()
        if graph is None:
            self.add_message("Failed to download the graph.")
            return False

        if overwrite_desert_flag is not None:
            for wp in graph.waypoints:
                if wp.id in overwrite_desert_flag:
                    # Overwrite anything that we passed in.
                    self._desert_flag[wp.id] = overwrite_desert_flag[wp.id]
                elif wp.id not in self._desert_flag:
                    self._desert_flag[wp.id] = False

        # Mark desert waypoints
        for waypoint in graph.waypoints:
            if self._desert_flag[waypoint.id]:
                self._make_desert(waypoint)

        # Write graph map
        self._write_full_graph(graph)
        self.add_message("Graph downloaded with {} waypoints and {} edges".format(
            len(graph.waypoints), len(graph.edges)))

        # Download the waypoint and edge snapshots.
        self._download_and_write_waypoint_snapshots(graph.waypoints)
        self._download_and_write_edge_snapshots(graph.edges)

        # Cache a list of all graph waypoints, ordered by creation time.
        # Because we only record one (non-branching) chain, all possible routes are contained
        # in ranges in this list.
        self._graph = graph
        wp_to_time = []
        for wp in graph.waypoints:
            time = wp.annotations.creation_time.seconds + wp.annotations.creation_time.nanos / 1e9
            wp_to_time.append((wp.id, time))
        # Switch inner and outer grouping and grab only the waypoint names after sorting by time.
        self._all_graph_wps_in_order = list(zip(*sorted(wp_to_time, key=lambda x: x[1])))[0]

        return True

    def _write_full_graph(self, graph):
        """Download the graph from robot to the specified, local filepath location."""
        graph_bytes = graph.SerializeToString()
        write_bytes(self._download_filepath, 'graph', graph_bytes)

    def _download_and_write_waypoint_snapshots(self, waypoints):
        """Download the waypoint snapshots from robot to the specified, local filepath location."""
        num_waypoint_snapshots_downloaded = 0
        for waypoint in waypoints:
            try:
                waypoint_snapshot = self._graph_nav_client.download_waypoint_snapshot(
                    waypoint.snapshot_id)
            except Exception:
                # Failure in downloading waypoint snapshot. Continue to next snapshot.
                self.add_message("Failed to download waypoint snapshot: " + waypoint.snapshot_id)
                continue
            write_bytes(os.path.join(self._download_filepath, 'waypoint_snapshots'),
                        waypoint.snapshot_id, waypoint_snapshot.SerializeToString())
            num_waypoint_snapshots_downloaded += 1
            self.add_message("Downloaded {} of the total {} waypoint snapshots.".format(
                num_waypoint_snapshots_downloaded, len(waypoints)))

    def _download_and_write_edge_snapshots(self, edges):
        """Download the edge snapshots from robot to the specified, local filepath location."""
        num_edge_snapshots_downloaded = 0
        num_to_download = 0
        for edge in edges:
            if len(edge.snapshot_id) == 0:
                continue
            num_to_download += 1
            try:
                edge_snapshot = self._graph_nav_client.download_edge_snapshot(edge.snapshot_id)
            except Exception:
                # Failure in downloading edge snapshot. Continue to next snapshot.
                self.add_message("Failed to download edge snapshot: " + edge.snapshot_id)
                continue
            write_bytes(os.path.join(self._download_filepath, 'edge_snapshots'), edge.snapshot_id,
                        edge_snapshot.SerializeToString())
            num_edge_snapshots_downloaded += 1
            self.add_message("Downloaded {} of the total {} edge snapshots.".format(
                num_edge_snapshots_downloaded, num_to_download))

    def _auto_close_loops(self):
        """Automatically find and close all loops in the graph."""
        close_fiducial_loops = True
        close_odometry_loops = True
        response = self._map_processing_client.process_topology(
            params=map_processing_pb2.ProcessTopologyRequest.Params(
                do_fiducial_loop_closure=wrappers.BoolValue(value=close_fiducial_loops),
                do_odometry_loop_closure=wrappers.BoolValue(value=close_odometry_loops)),
            modify_map_on_server=True)
        self.add_message("Created {} new edge(s).".format(len(response.new_subgraph.edges)))

    def _make_mission(self):
        """ Create a mission that visits each waypoint on stored path."""

        self.add_message("Mission: " + str(self._waypoint_commands))

        # Create a Sequence that visits all the waypoints.
        sequence = nodes_pb2.Sequence()

        prev_waypoint_command = None
        first_waypoint = True
        for waypoint_command in self._waypoint_commands:
            if waypoint_command == 'LOCALIZE':
                if prev_waypoint_command is None:
                    raise RuntimeError(f'No prev waypoint; LOCALIZE')
                sequence.children.add().CopyFrom(self._make_localize_node(prev_waypoint_command))
            elif waypoint_command == 'INITIALIZE':
                # Initialize to any fiducial.
                sequence.children.add().CopyFrom(self._make_initialize_node())
            else:
                if first_waypoint:
                    # Go to the beginning of the mission using any path. May be a no-op.
                    sequence.children.add().CopyFrom(self._make_goto_node(waypoint_command))
                else:
                    if prev_waypoint_command is None:
                        raise RuntimeError(f'No prev waypoint; route to {waypoint_command}')
                    sequence.children.add().CopyFrom(
                        self._make_go_route_node(prev_waypoint_command, waypoint_command))
                prev_waypoint_command = waypoint_command
                first_waypoint = False

        # Return a Node with the Sequence.
        ret = nodes_pb2.Node()
        ret.name = "Visit %d goals" % len(self._waypoint_commands)
        ret.impl.Pack(sequence)
        return ret

    def _make_goto_node(self, waypoint_id):
        """ Create a leaf node that will go to the waypoint. """
        ret = nodes_pb2.Node()
        ret.name = "goto %s" % waypoint_id
        vel_limit = NAV_VELOCITY_LIMITS

        # We don't actually know which path we will plan. It could have many feature deserts.
        # So, let's just allow feature deserts.
        tolerance = graph_nav_pb2.TravelParams.TOLERANCE_IGNORE_POOR_FEATURE_QUALITY
        travel_params = graph_nav_pb2.TravelParams(velocity_limit=vel_limit,
                                                   feature_quality_tolerance=tolerance)

        impl = nodes_pb2.BosdynNavigateTo(travel_params=travel_params)
        impl.destination_waypoint_id = waypoint_id
        ret.impl.Pack(impl)
        return ret

    def _make_go_route_node(self, prev_waypoint_id, waypoint_id):
        """ Create a leaf node that will go to the waypoint along a route. """
        ret = nodes_pb2.Node()
        ret.name = "go route %s -> %s" % (prev_waypoint_id, waypoint_id)
        vel_limit = NAV_VELOCITY_LIMITS

        if prev_waypoint_id not in self._all_graph_wps_in_order:
            raise RuntimeError(f'{prev_waypoint_id} (FROM) not in {self._all_graph_wps_in_order}')
        if waypoint_id not in self._all_graph_wps_in_order:
            raise RuntimeError(f'{waypoint_id} (TO) not in {self._all_graph_wps_in_order}')
        prev_wp_idx = self._all_graph_wps_in_order.index(prev_waypoint_id)
        wp_idx = self._all_graph_wps_in_order.index(waypoint_id)

        impl = nodes_pb2.BosdynNavigateRoute()
        backwards = False
        if wp_idx >= prev_wp_idx:
            impl.route.waypoint_id[:] = self._all_graph_wps_in_order[prev_wp_idx:wp_idx + 1]
        else:
            backwards = True
            # Switch the indices and reverse the output order.
            impl.route.waypoint_id[:] = reversed(
                self._all_graph_wps_in_order[wp_idx:prev_wp_idx + 1])
        edge_ids = [e.id for e in self._graph.edges]
        for i in range(len(impl.route.waypoint_id) - 1):
            eid = map_pb2.Edge.Id()
            # Because we only record one (non-branching) chain, and we only create routes from
            # older to newer waypoints, we can just follow the time-sorted list of all waypoints.
            if backwards:
                from_i = i + 1
                to_i = i
            else:
                from_i = i
                to_i = i + 1
            eid.from_waypoint = impl.route.waypoint_id[from_i]
            eid.to_waypoint = impl.route.waypoint_id[to_i]
            impl.route.edge_id.extend([eid])
            if eid not in edge_ids:
                raise RuntimeError(f'Was map recorded in linear chain? {eid} not in graph')

        if any(self._desert_flag[wp_id] for wp_id in impl.route.waypoint_id):
            tolerance = graph_nav_pb2.TravelParams.TOLERANCE_IGNORE_POOR_FEATURE_QUALITY
        else:
            tolerance = graph_nav_pb2.TravelParams.TOLERANCE_DEFAULT

        travel_params = graph_nav_pb2.TravelParams(velocity_limit=vel_limit,
                                                   feature_quality_tolerance=tolerance)
        impl.travel_params.CopyFrom(travel_params)
        ret.impl.Pack(impl)
        return ret

    def _make_localize_node(self, waypoint_id):
        """Make localization node."""
        loc = nodes_pb2.Node()
        loc.name = "localize robot"

        impl = nodes_pb2.BosdynGraphNavLocalize()
        impl.localization_request.fiducial_init = graph_nav_pb2.SetLocalizationRequest.FIDUCIAL_INIT_NEAREST_AT_TARGET
        impl.localization_request.initial_guess.waypoint_id = waypoint_id

        loc.impl.Pack(impl)
        return loc

    def _make_initialize_node(self):
        """Make initialization node."""
        loc = nodes_pb2.Node()
        loc.name = "initialize robot"

        impl = nodes_pb2.BosdynGraphNavLocalize()
        impl.localization_request.fiducial_init = graph_nav_pb2.SetLocalizationRequest.FIDUCIAL_INIT_NEAREST

        loc.impl.Pack(impl)
        return loc


def write_bytes(filepath, filename, data):
    """Write data to a file."""
    os.makedirs(filepath, exist_ok=True)
    with open(os.path.join(filepath, filename), 'wb+') as f:
        f.write(data)
        f.close()


def write_mission(mission, filename):
    """ Write a mission to disk. """
    open(filename, 'wb').write(mission.SerializeToString())


def setup_logging(verbose):
    """Log to file at debug level, and log to console at INFO or DEBUG (if verbose).

    Returns the stream/console logger so that it can be removed when in curses mode.
    """
    LOGGER.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Save log messages to file wasd.log for later debugging.
    file_handler = logging.FileHandler('wasd.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_formatter)
    LOGGER.addHandler(file_handler)

    # The stream handler is useful before and after the application is in curses-mode.
    if verbose:
        stream_level = logging.DEBUG
    else:
        stream_level = logging.INFO

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(stream_level)
    stream_handler.setFormatter(log_formatter)
    LOGGER.addHandler(stream_handler)
    return stream_handler


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('directory', help='Output directory for graph map and mission file.')
    parser.add_argument('--time-sync-interval-sec',
                        help='The interval (seconds) that time-sync estimate should be updated.',
                        type=float)
    parser.add_argument('--waypoint-commands-only', nargs='+',
                        help='Build a mission from the graph on-robot, specifying these commands')

    options = parser.parse_args()

    if os.path.exists(options.directory):
        LOGGER.error("ERROR: Directory %s already exists." % options.directory)
        return False

    stream_handler = setup_logging(options.verbose)

    # Create robot object.
    sdk = create_standard_sdk('MissionRecorderClient')
    robot = sdk.create_robot(options.hostname)
    try:
        bosdyn.client.util.authenticate(robot)
        robot.start_time_sync(options.time_sync_interval_sec)
    except RpcError as err:
        LOGGER.error("Failed to communicate with robot: %s" % err)
        return False

    recorder_interface = RecorderInterface(robot, options.directory)

    if options.waypoint_commands_only is not None:
        recorder_interface._waypoint_commands = options.waypoint_commands_only
        # Save graph map
        os.mkdir(recorder_interface._download_filepath)
        if not recorder_interface._download_full_graph(overwrite_desert_flag=[]):
            recorder_interface.add_message("ERROR: Error downloading graph.")
            return

        LOGGER.info(recorder_interface._all_graph_wps_in_order)
        # Generate mission
        mission = recorder_interface._make_mission()

        # Save mission file
        os.mkdir(recorder_interface._download_filepath + "/missions")
        mission_filepath = recorder_interface._download_filepath + "/missions/autogenerated"
        write_mission(mission, mission_filepath)
        return True

    with LeaseKeepAlive(recorder_interface._lease_client, must_acquire=True,
                        return_at_exit=True) as lease_keep_alive:
        try:
            recorder_interface.start(lease_keep_alive)
        except (ResponseError, RpcError) as err:
            LOGGER.error("Failed to initialize robot communication: %s" % err)
            return False

        try:
            # Prevent curses from introducing a 1 second delay for ESC key
            os.environ.setdefault('ESCDELAY', '0')
            # Run recorder interface in curses mode, then restore terminal config.
            curses.wrapper(recorder_interface.drive)
        except Exception as e:
            LOGGER.error("Mission recorder has thrown an error: %s" % repr(e))
            LOGGER.error(traceback.format_exc())
        finally:
            # Restore stream handler after curses mode.
            LOGGER.addHandler(stream_handler)

    return True


if __name__ == "__main__":
    if not main():
        os._exit(1)
    os._exit(0)
