# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import curses
import hashlib
import io
import logging
import math
import os
import re
import signal
import sys
import time
from datetime import datetime

from google.protobuf import text_format

import bosdyn.client.util
from bosdyn.api.spot import choreography_sequence_pb2
from bosdyn.choreography.client.animation_file_conversion_helpers import *
from bosdyn.choreography.client.animation_file_to_proto import (COMMENT_DELIMITERS, GROUPED_HEADERS,
                                                                OPTIONS_KEYWORDS_TO_FUNCTION,
                                                                SINGLE_HEADERS,
                                                                convert_animation_file_to_proto)
from bosdyn.choreography.client.choreography import (AnimationUploadHelper,
                                                     AnimationValidationFailedError,
                                                     ChoreographyClient)
from bosdyn.client import create_standard_sdk
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.license import LicenseClient

COMMAND_INPUT_RATE = 0.1
LOGGER = logging.getLogger(__name__)


class RecorderInterface(object):
    """Creates and plays animations on the robot by recording a robot being controlled by the tablet.

    Args:
        robot(robot): The incoming robot object to be recorded and controlled.
        download_filepath(string): Location where animation_recorder.py is located, used when saving and reading files.
    """

    def __init__(self, robot, download_filepath):
        self._robot = robot

        # Helper class for uploading animation files to the robot
        self._choreography_animation_helper = AnimationUploadHelper(self._robot)

        # ensure that the robot will be able to use the ChoreographyClient
        self._choreo_client = robot.ensure_client(ChoreographyClient.default_service_name)

        # Create clients -- do not use the for communication yet.
        self._lease_client = robot.ensure_client(LeaseClient.default_service_name)

        # filepath to animation_recorder.py
        self._download_filepath = download_filepath

        # name of the sub directory where animation files are saved and read
        self._animation_directory = ""

        # variables for tracking when an animated sequence finishes so the lease can be returned when it finishes,
        # with _start_time being when the animation started and _length_of_current_choreo being the duration of the
        # selected animation being played back
        self._length_of_current_choreo = 0
        self._start_time = 0

        # variable to keep track of the subset of the animation files list to display as options on
        # the playback screen
        self._page = 0

        # list to hold the names of the animation files
        self._proto_names = []

        # list containing the choreographies generated from the animation files in _proto_names
        self._choreos = []

        # variable for keeping track of the current lease when Animation Recorder is controlling the robot
        self._lease = None

        # variable for keeping track of the leaseKeepAlive instance when the lease is being controlled by Animation Recorder
        self._lease_alive = None

        # variable for determining if the program should quit
        self._exit_check = None

        # determine the screen to display:
        # 0 : main
        # 1 : save or discard the recorded animation
        # 2 : playback an option from the list of previously recorded animations
        self._screen = 0  # on start display the main screen

        # keep track of whether the program is recording or not recording
        self._recording = False

        # Check that an estop is connected with the robot so that the robot commands can be executed.
        # The E-Stop while using Animation Recorder should be the tablet.
        assert not robot.is_estopped(), "Robot is estopped. Please connect the robot to the tablet or use " \
                                        "the estop SDK example, to configure E-Stop."

        self._command_dictionary = {
            # list of viable key commands for the main screen
            ord('\t'): self._quit_program,
            ord('f'): self._start_recording,
            ord('g'): self._stop_recording,
            ord('o'): self._load_screen
        }

        self._question_command_dictionary = {
            # list of viable key commands for the save screen
            ord('y'): self._yes,
            ord('n'): self._no
        }

        self._load_command_dictionary = {
            # list of viable key commands for the playback screen
            ord('\t'): (self._done, 0),
            ord('1'): (self._choose_file, 0),
            ord('2'): (self._choose_file, 1),
            ord('3'): (self._choose_file, 2),
            ord('4'): (self._choose_file, 3),
            ord('5'): (self._choose_file, 4),
            ord('.'): (self._next, 0),
            ord(','): (self._back, 0)
        }

    def _quit_program(self):
        """Stop running the animation recorder api."""
        if self._exit_check is not None:
            self._exit_check.request_exit()

    def _start_recording(self):
        """Start recording the robot."""
        recording_length = 300  # Here recording length is set to 300 seconds (5 minutes), the maximum recording length.
        self._recording = True
        self._choreo_client.start_recording_state(recording_length)

    def _is_recording(self):
        """Returns the recording state as a string to be displayed on the main screen telling
        the user whether the program is currently recording animation.
        """
        if (self._recording):
            return "Recording"
        return "Not Recording"

    def _stop_recording(self):
        """Stop recording the robot."""
        self._choreo_client.stop_recording_state()
        if not self._recording:
            return True
        self._recording = False
        self._screen = 1

    def _yes(self):
        """Save the recording as an animation file and upload the related choreography to the robot."""
        self._screen = 0

        # create a unique name for the new animated recording
        now = datetime.now()
        dtime = now.strftime("%H%M%S")
        dday = now.strftime("%d%m%Y")
        name = dday + dtime

        # create the animation *.cha file from the choreography log and save it to the animation directory
        cha_path = os.path.join(self._download_filepath, self._animation_directory)
        cha_filename = self._choreo_client.choreography_log_to_animation_file(
            name, cha_path, self._robot.has_arm(), "truncatable")

        # upload the animation to the robot as a choreography sequence from the *.cha file and list
        # the animation for playback
        animation, choreography_seq = self.proto_to_choreo(cha_filename)
        self._proto_names.append(animation.name)
        self._choreos.append(choreography_seq)

    def _no(self):
        """Switches from the save screen to the main screen."""
        self._screen = 0

    def _load_screen(self):
        """Switches from the main screen to the playback screen."""
        self._screen = 2

    def _done(self, i):
        """Switches from the playback screen to the main screen."""
        self._screen = 0

    def _choose_file(self, i):
        """Ensure that chosen file has a valid animation at that index, then play the selected animation file."""
        if (len(self._proto_names) > i + (self._page * 5)):
            self._play_pre_recorded(i)

    def _next(self, i):
        """Display the next 5 animation files in the animation file list."""
        if self._page < len(self._proto_names) / 5:
            self._page += 1

    def _back(self, i):
        """Display the previous 5 animation files in the animation file list."""
        if self._page > 0:
            self._page -= 1

    def _upload_animation_proto(self, animation):
        """Helper function for uploading an animation protobuf to the robot while providing debug messages."""
        upload_response = None
        try:
            upload_response = self._choreography_animation_helper.upload_animated_move(
                animation.proto)
            # The python choreography client will throw an exception if the upload animated move rpc returns
            # a status code that isn't STATUS_OK.
            if upload_response is None:
                # The upload animation RPC may not be issued at all if the animation hasn't changed
                # and doesn't need to be sent to the robot. In that case, the response is None but we
                # still return true to indicate the move is successfully placed on robot.
                LOGGER.info(
                    "Success: %s (Animation is already uploaded to the robot)." % animation.name)
                return True
            LOGGER.info("Success: %s (Uploaded new/changed animation)." % animation.name)
        except AnimationValidationFailedError as validation_failed:
            upload_response = validation_failed.response
        except Exception as err:
            error_msg = "Failed to upload animation %s: [%s] %s" % (animation.name, str(
                type(err)), str(err))
            LOGGER.warning(error_msg)
            return False

        if upload_response is not None:
            if len(upload_response.warnings) > 0:
                error_msg = "Animation '" + str(
                    animation.name) + "' upload failed. The following warnings were produced: \n"
                for warn in upload_response.warnings:
                    error_msg += "\t"
                    error_msg += warn
                    LOGGER.warning(error_msg)

        LOGGER.info(upload_response.status)
        return upload_response.status == choreography_sequence_pb2.UploadAnimatedMoveResponse.STATUS_OK

    def proto_to_choreo(self, cha_filename):
        """Function for uploading the animation file as a protobuf to the robot and then turning the animation
        into a choreography sequence which can then be played on the robot.

        Args:
            cha_filename (string): Name of the *.cha animation file to be uploaded to the robot.

        Returns:
            The animation protobuf name.
            The choreography sequence containing the animation move described by the *.cha animation file.
        """

        # path to the *.cha animation file to be uploaded
        fpath = os.path.join(self._download_filepath, self._animation_directory)
        animated_file = os.path.join(fpath, cha_filename)

        # use the *.cha animation file to create an animation protobuf file. convert_animation_file_to_proto can take a second
        # optional argument for a filepath to a file containing the default values for animation parameter fields, but Animation
        # Recorder doesn't produce any animations that have parameter fields so only the *.cha animation file is needed.
        animation = convert_animation_file_to_proto(animated_file)

        #upload the created animation protobuf to the robot
        self._upload_animation_proto(animation)

        # turn animation into a choreography sequence:
        # initialize a ChoreographySequence object
        choreography_seq = choreography_sequence_pb2.ChoreographySequence()
        # assign the ChoreographySequence name to be the animation protobuf name
        choreography_seq.name = animation.name
        # assign the playback speed of the choreography sequence
        choreography_seq.slices_per_minute = 200 * 4

        # the MoveParamsList will contain the list of moves making up the choreography sequence. For Animation Recorder
        # the choreography sequences are one move long, where the move is the motion captured by the recording.
        MoveParamsList = []

        move_param = choreography_sequence_pb2.MoveParams()
        move_param.type = "animation"

        # start the move immediately with no delay
        move_param.start_slice = 0

        # calculate the expected duration of the move in slices by multiplying the duration of the animation in minutes by the
        # number of slices per minute of the created choreography sequence.
        move_param.requested_slices = math.ceil(
            ((animation.proto.animation_keyframes[-1].time -
              animation.proto.animation_keyframes[0].time) / 60) *
            choreography_seq.slices_per_minute)

        # assign the move the name of the animation protobuf
        move_param.animate_params.animation_name = animation.name

        # add the move to the list of moves
        MoveParamsList.append(move_param)

        # add the list of moves to the choreography sequence
        choreography_seq.moves.extend(MoveParamsList)

        # upload the choreography sequence to the robot
        upload_response = self._choreo_client.upload_choreography(choreography_seq,
                                                                  non_strict_parsing=True)

        # return the animation protobuf and choreography sequence
        return animation, choreography_seq

    def _play_pre_recorded(self, i):
        """Play the animation file at index i in the animation files list."""
        start_time = None

        # lease needs to be forcibly taken because the tablet is actively controlling the robot
        self._take_lease()
        self._length_of_current_choreo = self._choreos[
            self._page * 5 + i].moves[0].requested_slices / self._choreos[self._page * 5 +
                                                                          i].slices_per_minute
        self._start_time = self._time_in_secs()

        upload_response = self._choreo_client.upload_choreography(self._choreos[self._page * 5 + i],
                                                                  non_strict_parsing=True)
        self._choreo_client.execute_choreography(self._proto_names[self._page * 5 + i], start_time,
                                                 0)

    def _take_lease(self):
        """Begin communication with the robot."""
        # take the lease from the tablet
        self._lease = self._lease_client.take()

        # Construct our lease keep-alive object, which begins RetainLease calls in a thread.
        self._lease_alive = LeaseKeepAlive(self._lease_client, warnings=False, return_at_exit=True)

    def _time_in_secs(self):
        """Helper function for getting real time in seconds. Used to measure when a choreography has ended."""
        now = datetime.now()
        dtime_s, dtime_m, dtime_h = int(now.strftime("%S")), int(now.strftime("%M")), int(
            now.strftime("%H"))
        t = dtime_s + 60 * dtime_m + 60 * 60 * dtime_h
        return t

    def _return_lease(self):
        """Function to return a lease being used by Animation Recorder."""
        if self._lease_alive:
            self._lease_alive.shutdown()
            self._lease_alive = None

    def drive(self, stdscr):
        """Determine when to give back the lease and draw the curses screen while the program is active."""

        f_time = self._time_in_secs()

        # if the current time exceeds the time when an animation running on the robot was expected to finish,
        # give back the lease
        if (self._length_of_current_choreo != 0 and
                f_time > self._length_of_current_choreo + self._start_time):
            self._length_of_current_choreo = 0
            self._return_lease()

        with ExitCheck() as self._exit_check:

            stdscr.nodelay(True)  # Don't block for user input.
            stdscr.resize(26, 96)
            stdscr.refresh()

            # allow user input to appear on the curses interface
            curses.echo()

            try:
                while not self._exit_check.kill_now:
                    # draw the interface
                    self._drive_draw(stdscr)
                    try:
                        # take in user commands from keypress input
                        cmd = stdscr.getch()
                        # Do not queue up commands on client
                        self._drive_cmd(cmd)
                        time.sleep(COMMAND_INPUT_RATE)
                    except Exception:
                        time.sleep(2.0)
                        raise
            finally:
                stdscr.clear()
                self._return_lease()

    def _drive_draw(self, stdscr):

        if (self._screen == 0):
            self._main(stdscr)

        elif (self._screen == 1):
            self._question(stdscr)

        elif (self._screen == 2):
            self._load(stdscr)

    def _drive_cmd(self, key):
        """Run user commands at each update."""
        try:
            if (self._screen != 2):

                if (self._screen == 0):
                    cmd_function = self._command_dictionary[key]
                elif (self._screen == 1):
                    cmd_function = self._question_command_dictionary[key]
                cmd_function()

            else:
                (cmd_function, i) = self._load_command_dictionary[key]
                cmd_function(i)

        except KeyError:
            if key and key != -1 and key < 256:
                # self.add_message("Unrecognized keyboard command: '{}'".format(chr(key)))
                print("Unrecognized keyboard command.")
                time.sleep(2.0)

    def _main(self, stdscr):
        """Helper function for the _drive_draw function. Draw the main interface screen at each update."""
        stdscr.clear()  # clear screen
        stdscr.resize(26, 50)

        recording_state = self._is_recording()
        stdscr.addstr(11, 15, recording_state)

        stdscr.addstr(3, 5, "Commands: [TAB]: Quit")
        stdscr.addstr(4, 5, "          [f]: Record Choreography")
        stdscr.addstr(5, 5, "          [g]: Stop Recording Choreography")
        stdscr.addstr(6, 5, "          [o]: Playback")

        stdscr.refresh()

    def _question(self, stdscr):
        """Helper function for the _drive_draw function. Draw the save or discard interface screen at each update."""
        stdscr.clear()  # clear screen
        stdscr.resize(26, 50)

        stdscr.addstr(4, 5, "save choreography?")
        stdscr.addstr(5, 5, "          [y]: Save Choreography")
        stdscr.addstr(6, 5, "          [n]: Discard Recording")

        stdscr.refresh()

    def _load(self, stdscr):
        """Helper function for the _drive_draw function. Draw the playback options interface screen at each update."""
        stdscr.clear()  # clear screen
        stdscr.resize(26, 50)

        stdscr.addstr(20, 5, "                                       " + str(self._page))
        stdscr.addstr(4, 5, "Choose a file:")

        # write the animation options for the current page from the animation files list
        for i in range(0, 5):
            if len(self._proto_names) > (i + (self._page * 5)):
                stdscr.addstr(
                    5 + i, 5,
                    "          [" + str(i + 1) + "]: " + self._proto_names[i + (self._page * 5)])
            else:
                stdscr.addstr(5 + i, 5, "          [" + str(i + 1) + "]: ")

        stdscr.addstr(10, 5, "          [>]: Increment Page +")
        stdscr.addstr(11, 5, "          [<]: Increment Page -")
        stdscr.addstr(12, 5, "          [TAB]: Return to Main")

        stdscr.refresh()


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


def main():

    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument(
        '-d', '--download-filepath', help=
        'Name for the new directory where recorded *.cha animation files will be read and saved',
        default=os.getcwd())
    options = parser.parse_args()

    default_filepath = os.path.dirname(os.path.realpath(__file__))

    # create an sdk
    sdk = bosdyn.client.create_standard_sdk('AnimationRecorder')

    # Create robot object with the ability to access the ChoreographyClient
    sdk.register_service_client(ChoreographyClient)
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    license_client = robot.ensure_client(LicenseClient.default_service_name)
    if not license_client.get_feature_enabled([ChoreographyClient.license_name
                                              ])[ChoreographyClient.license_name]:
        LOGGER.error("This robot is not licensed for choreography.")
        sys.exit(1)

    recorder_interface = RecorderInterface(robot, default_filepath)

    # create the subdirectory for recorded animation files, with a default directory name of 'recorded_animations [DATE: DAY-MONTH-YEAR]'
    if len(options.download_filepath) == 0:
        now = datetime.now()
        options.download_filepath = "recorded_animations_" + now.strftime("%d-%m-%Y")

    recorder_interface._animation_directory = options.download_filepath
    fpath = os.path.join(recorder_interface._download_filepath,
                         recorder_interface._animation_directory)

    if not os.path.isdir(fpath):
        # create the new subdirectory with the chosen name
        os.mkdir(fpath)
        print("recorded animations directory created : " + options.download_filepath)
    else:
        # if the folder already existed save files in the existing subdirectory
        print("recorded animations will be saved to directory : " + options.download_filepath)

    # Run the program with curses user interface
    try:
        # Prevent curses from introducing a 1 second delay for ESC key
        os.environ.setdefault('ESCDELAY', '0')
        # Run animation recorder interface in curses mode, then restore terminal config.
        curses.wrapper(recorder_interface.drive)

    except Exception as e:
        LOGGER.error("Animation Recorder has thrown an error: [%r] %s", e, e)

    finally:
        # Do any final cleanup steps.
        recorder_interface._quit_program()

    return True


if __name__ == "__main__":
    if not main():
        os._exit(1)
    os._exit(0)
