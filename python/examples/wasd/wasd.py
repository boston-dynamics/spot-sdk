# Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""WASD driving of robot."""

from __future__ import print_function
from collections import OrderedDict
import curses
import logging
import signal
import sys
import threading
import time
import math
import io

from PIL import Image, ImageEnhance

from bosdyn.api import geometry_pb2
import bosdyn.api.power_pb2 as PowerServiceProto
# import bosdyn.api.robot_command_pb2 as robot_command_pb2
import bosdyn.api.robot_state_pb2 as robot_state_proto
import bosdyn.api.spot.robot_command_pb2 as spot_command_pb2
from bosdyn.client import create_standard_sdk, ResponseError, RpcError
from bosdyn.client.async_tasks import AsyncGRPCTask, AsyncPeriodicQuery, AsyncTasks
from bosdyn.client.estop import EstopClient, EstopEndpoint, EstopKeepAlive
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.power import PowerClient
from bosdyn.client.robot_command import RobotCommandClient, RobotCommandBuilder
from bosdyn.client.image import ImageClient
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.time_sync import TimeSyncError
import bosdyn.client.util
from bosdyn.util import duration_str, format_metric, secs_to_hms

LOGGER = logging.getLogger()

VELOCITY_BASE_SPEED = 0.5  # m/s
VELOCITY_BASE_ANGULAR = 0.8  # rad/sec
VELOCITY_CMD_DURATION = 0.6  # seconds
COMMAND_INPUT_RATE = 0.1

#   - program breaks if robot fails to stand (instead of using self-right)


def _grpc_or_log(desc, thunk):
    try:
        return thunk()
    except (ResponseError, RpcError) as err:
        LOGGER.error("Failed %s: %s", desc, err)


def _image_to_ascii(image, new_width):
    """Convert an rgb image to a ASCII 'image' that can be displayed in a terminal."""

    ASCII_CHARS = '@#S%?*+;:,.'

    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(0.8)

    # Scaling image before rotation by 90 deg.
    scaled_rot_height = new_width
    original_rot_width, original_rot_height = image.size
    scaled_rot_width = (original_rot_width * scaled_rot_height) // original_rot_height
    # Scaling rotated width (height, after rotation) by half because ASCII chars
    #  in terminal seem about 2x as tall as wide.
    image = image.resize((scaled_rot_width // 2, scaled_rot_height))

    # Rotate image 90 degrees, then convert to grayscale.
    image = image.transpose(Image.ROTATE_270)
    image = image.convert('L')

    def _pixel_char(pixel_val):
        return ASCII_CHARS[pixel_val * len(ASCII_CHARS) // 256]

    img = []
    row = [' '] * new_width
    last_col = new_width - 1
    for idx, pixel_char in enumerate(_pixel_char(val) for val in image.getdata()):
        idx_row = idx % new_width
        row[idx_row] = pixel_char
        if idx_row == last_col:
            img.append(''.join(row))
    return img


class ExitCheck(object):
    """A class to help exiting a loop, also capturing SIGTERM to exit the loop."""

    def __init__(self, exit_delay_secs):
        self._exit_delay_secs = exit_delay_secs
        self._old_sigterm_handler = None
        self._time_exit_requested = None
        self._on_exit_callbacks = OrderedDict()  # name -> callback

    def run_callback_on_exit(self, name, callback):
        """Adds a callback to be invoked when 'with' scope ends.

        Args:
         name      string name of callback
         callback  zero-argument function (thunk) to be called.
        """
        self._on_exit_callbacks[name] = callback

    def __enter__(self):
        self._old_sigterm_handler = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, self.request_exit)
        print("Set new signal handler")
        return self

    def __exit__(self, _type, _value, _traceback):
        # Restore the original signal handler
        for name, callback in self._on_exit_callbacks.items():
            try:
                callback()
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Exception in callback '%s' on exit", name)
        if self._old_sigterm_handler:
            signal.signal(signal.SIGTERM, self._old_sigterm_handler)
            print("Original handler installed")

    @property
    def exit_requested(self):
        """Returns True if request_exit has been called."""
        return self._time_exit_requested is not None

    @property
    def keep_alive(self):
        """Returns False if the main loop should exit, True if it shold keep running."""
        return (self._time_exit_requested is None or
                (time.time() - self._time_exit_requested) < self._exit_delay_secs)

    def request_exit(self, _signum=None, _frame=None):
        """Causes future checks of keep_alive to return False after exit_delay."""
        if self._time_exit_requested is None:
            LOGGER.info("Exit requested")
            self._time_exit_requested = time.time()


class CursesHandler(logging.Handler):
    """logging handler which puts messages into the curses interface"""

    def __init__(self, wasd_interface):
        super(CursesHandler, self).__init__()
        self._wasd_interface = wasd_interface

    def emit(self, record):
        msg = record.getMessage()
        msg = msg.replace('\n', ' ').replace('\r', '')
        self._wasd_interface.add_message('{:s} {:s}'.format(record.levelname, msg))


class AsyncMetrics(AsyncPeriodicQuery):
    """Grab robot metrics every few seconds."""

    def __init__(self, robot_state_client):
        super(AsyncMetrics, self).__init__("robot_metrics", robot_state_client, LOGGER,
                                           period_sec=5.0)

    def _start_query(self):
        return self._client.get_robot_metrics_async()


class AsyncRobotState(AsyncPeriodicQuery):
    """Grab robot state."""

    def __init__(self, robot_state_client):
        super(AsyncRobotState, self).__init__("robot_state", robot_state_client, LOGGER,
                                              period_sec=0.2)

    def _start_query(self):
        return self._client.get_robot_state_async()


class AsyncImageCapture(AsyncGRPCTask):
    """Grab camera images from the robot."""

    def __init__(self, robot):
        super(AsyncImageCapture, self).__init__()
        self._image_client = robot.ensure_client(ImageClient.default_service_name)
        self._ascii_image = None
        self._video_mode = False
        self._should_take_image = False

    @property
    def ascii_image(self):
        """Return the latest captured image as ascii."""
        return self._ascii_image

    def toggle_video_mode(self):
        """Toggle whether doing continuous image capture."""
        self._video_mode = not self._video_mode

    def take_image(self):
        """Request a one-shot image."""
        self._should_take_image = True

    def _start_query(self):
        self._should_take_image = False
        source_name = "frontright_fisheye_image"
        return self._image_client.get_image_from_sources_async([source_name])

    def _should_query(self, now_sec):  # pylint: disable=unused-argument
        return self._video_mode or self._should_take_image

    def _handle_result(self, result):
        import io
        image = Image.open(io.BytesIO(result[0].shot.image.data))
        self._ascii_image = _image_to_ascii(image, new_width=70)

    def _handle_error(self, exception):
        LOGGER.exception("Failure getting image: %s", exception)


class WasdInterface(object):
    """A curses interface for driving the robot."""

    def __init__(self, robot):
        self._robot = robot
        # Create clients -- do not use the for communication yet.
        self._lease_client = robot.ensure_client(LeaseClient.default_service_name)
        self._estop_client = robot.ensure_client(EstopClient.default_service_name)
        self._estop_endpoint = EstopEndpoint(self._estop_client, 'wasd', 9.0)
        self._power_client = robot.ensure_client(PowerClient.default_service_name)
        self._robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
        self._robot_command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        self._robot_metrics_task = AsyncMetrics(self._robot_state_client)
        self._robot_state_task = AsyncRobotState(self._robot_state_client)
        self._image_task = AsyncImageCapture(robot)
        self._async_tasks = AsyncTasks(
            [self._robot_metrics_task, self._robot_state_task, self._image_task])
        self._lock = threading.Lock()
        self._command_dictionary = {
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
            ord('d'): self._strafe_right,
            ord('q'): self._turn_left,
            ord('e'): self._turn_right,
            ord('I'): self._image_task.take_image,
            ord('O'): self._image_task.toggle_video_mode,
        }
        self._locked_messages = ['', '', '']  # string: displayed message for user
        self._estop_keepalive = None
        self._exit_check = None

        # Stuff that is set in start()
        self._robot_id = None
        self._lease = None

    def start(self):
        """Begin communication with the robot."""
        self._robot_id = self._robot.get_id()
        self._lease = self._lease_client.acquire()
        self._estop_endpoint.force_simple_setup()  # Set this endpoint as the robot's sole estop.

    def shutdown(self):
        """Release control of robot as gracefully as posssible."""
        LOGGER.info("Shutting down WasdInterface.")
        if self._robot.time_sync:
            self._robot.time_sync.stop()
        if self._estop_keepalive:
            _grpc_or_log("stopping estop", self._estop_keepalive.stop)
            self._estop_keepalive = None
        if self._lease:
            _grpc_or_log("returning lease", lambda: self._lease_client.return_lease(self._lease))
            self._lease = None

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

    @property
    def robot_metrics(self):
        """Get latest robot metrics proto."""
        return self._robot_metrics_task.proto

    def drive(self, stdscr):
        """User interface to control the robot via the passed-in curses screen interface object."""
        with ExitCheck(exit_delay_secs=2.0) as self._exit_check, \
              LeaseKeepAlive(self._lease_client,
                             keep_running_cb=lambda: self._exit_check.keep_alive) \
                             as lease_keep_alive:
            curses_handler = CursesHandler(self)
            curses_handler.setLevel(logging.INFO)
            LOGGER.addHandler(curses_handler)

            stdscr.nodelay(True)  # Don't block for user input.

            # for debug
            curses.echo()

            try:
                while self._exit_check.keep_alive:
                    self._async_tasks.update()
                    self._drive_draw(stdscr, lease_keep_alive)

                    if not self._exit_check.exit_requested:
                        try:
                            cmd = stdscr.getch()
                            # Do not queue up commands on client
                            self.flush_and_estop_buffer(stdscr)
                            self._drive_cmd(cmd)

                        except Exception:
                            # On robot command fault, sit down safely before killing the program.
                            self._safe_power_off()
                            time.sleep(2.0)
                            raise

                    time.sleep(COMMAND_INPUT_RATE)
            finally:
                LOGGER.removeHandler(curses_handler)

    def _drive_draw(self, stdscr, lease_keep_alive):
        """Draw the interface screen at each update."""
        stdscr.clear()  # clear screen
        stdscr.addstr(0, 0, '{:20s} {}'.format(self._robot_id.nickname,
                                               self._robot_id.serial_number))
        stdscr.addstr(1, 0, self._lease_str(lease_keep_alive))
        stdscr.addstr(2, 0, self._battery_str())
        stdscr.addstr(3, 0, self._estop_str())
        stdscr.addstr(4, 0, self._power_state_str())
        stdscr.addstr(5, 0, self._time_sync_str())
        for i in range(3):
            stdscr.addstr(7 + i, 2, self.message(i))
        self._show_metrics(stdscr)
        stdscr.addstr(10, 0, "Commands: [TAB]: quit")
        stdscr.addstr(11, 0, "          [T]: Time-sync, [SPACE]: Estop, [P]: Power")
        stdscr.addstr(12, 0, "          [I]: Take image, [O]: Video mode")
        stdscr.addstr(13, 0, "          [v]: Sit, [f]: Stand, [r]: Self-right")
        stdscr.addstr(14, 0, "          [wasd]: Directional strafing")
        stdscr.addstr(15, 0, "          [qe]: Turning")

        # print as many lines of the image as will fit on the curses screen
        if self._image_task.ascii_image != None:
            max_y, _max_x = stdscr.getmaxyx()
            for y_i, img_line in enumerate(self._image_task.ascii_image):
                if y_i + 16 >= max_y:
                    break
                stdscr.addstr('\n' + img_line)

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
        self._sit()
        self._exit_check.request_exit()

    def _toggle_time_sync(self):
        if self._robot.time_sync.stopped:
            self._robot.time_sync.start()
        else:
            self._robot.time_sync.stop()

    def _toggle_estop(self):
        """toggle estop on/off. Initial state is ON"""
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
        self._start_robot_command('sit', RobotCommandBuilder.sit_command())

    def _stand(self):
        self._start_robot_command('stand', RobotCommandBuilder.stand_command())

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

    def _velocity_cmd_helper(self, desc='', v_x=0.0, v_y=0.0, v_rot=0.0):
        self._start_robot_command(desc,
                                  RobotCommandBuilder.velocity_command(
                                      v_x=v_x, v_y=v_y, v_rot=v_rot),
                                  end_time_secs=time.time() + VELOCITY_CMD_DURATION)

    #  This command makes the robot move very fast and the 'origin' is very unpredictable.
    def _return_to_origin(self):
        self._start_robot_command('fwd_and_rotate',
                                  RobotCommandBuilder.trajectory_command(
                                      goal_x=0.0, goal_y=0.0, goal_heading=0.0,
                                      frame=geometry_pb2.Frame(base_frame=geometry_pb2.FRAME_KO),
                                      params=None, body_height=0.0,
                                      locomotion_hint=spot_command_pb2.HINT_SPEED_SELECT_TROT),
                                  end_time_secs=time.time() + 20)

    def _take_ascii_image(self):
        source_name = "frontright_fisheye_image"
        image_response = self._image_client.get_image_from_sources([source_name])
        image = Image.open(io.BytesIO(image_response[0].shot.image.data))
        ascii_image = self._ascii_converter.convert_to_ascii(image, new_width=70)
        self._last_image_ascii = ascii_image

    def _toggle_ascii_video(self):
        if self._video_mode:
            self._video_mode = False
        else:
            self._video_mode = True

    # def _clear_behavior_faults(self):
    #     cmd = robot_state_proto.GetRobotState()
    #     self._start_robot_command(cmd)
    #     robot_command_pb2.clear_behavior_fault(behavior_fault_id = , lease = self._lease)

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

    def _show_metrics(self, stdscr):
        metrics = self.robot_metrics
        if not metrics:
            return
        for idx, metric in enumerate(metrics.metrics):
            stdscr.addstr(2 + idx, 50, format_metric(metric))

    def _power_state(self):
        state = self.robot_state
        if not state:
            return None
        return state.power_state.motor_power_state

    def _lease_str(self, lease_keep_alive):
        alive = 'RUNNING' if lease_keep_alive.is_alive() else 'STOPPED'
        lease = '{}:{}'.format(self._lease.lease_proto.resource, self._lease.lease_proto.sequence)
        return 'Lease {} THREAD:{}'.format(lease, alive)

    def _power_state_str(self):
        power_state = self._power_state()
        if power_state is None:
            return ''
        state_str = robot_state_proto.PowerState.MotorPowerState.Name(power_state)
        return 'Power: {}'.format(state_str[6:])  # get rid of STATE_ prefix

    def _estop_str(self):
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


def _setup_logging(verbose):
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
    bosdyn.client.util.add_common_arguments(parser)
    options = parser.parse_args()

    stream_handler = _setup_logging(options.verbose)

    # Create robot object.
    sdk = create_standard_sdk('WASDClient')
    sdk.load_app_token(options.app_token)
    robot = sdk.create_robot(options.hostname)
    try:
        robot.authenticate(options.username, options.password)
        robot.start_time_sync()
    except RpcError as err:
        LOGGER.error("Failed to communicate with robot: %s", err)
        return False

    wasd_interface = WasdInterface(robot)
    try:
        wasd_interface.start()
    except (ResponseError, RpcError) as err:
        LOGGER.error("Failed to initialize robot communication: %s", err)
        return False

    LOGGER.removeHandler(stream_handler)  # Don't use stream handler in curses mode.
    try:
        # Run wasd interface in curses mode, then restore terminal config.
        curses.wrapper(wasd_interface.drive)
    finally:
        # Restore stream handler after curses mode.
        LOGGER.addHandler(stream_handler)

    wasd_interface.shutdown()

    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
