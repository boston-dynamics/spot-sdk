# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Simple example of adding and running a behavior in the AudioVisual Service."""
import argparse
import sys
import time

from google.protobuf.duration_pb2 import Duration
from google.protobuf.wrappers_pb2 import BoolValue, Int32Value

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import audio_visual_pb2
from bosdyn.api.spot import choreography_params_pb2
from bosdyn.client.audio_visual import (AudioVisualClient, BehaviorExpiredError, DoesNotExistError,
                                        InvalidBehaviorError, PermanentBehaviorError)


def run_behavior(av_client, name, run_time):
    print(f"Trying to run behavior \"{name}\"...")
    try:
        print(f"Running behavior for {run_time} seconds...")
        # NOTE: this may look like a bug because it's local time, but the time is adjusted in the method.
        end_time_secs = time.time() + run_time
        response = av_client.run_behavior(name, end_time_secs, restart=False)
        if (response.run_result == audio_visual_pb2.RunBehaviorResponse.RESULT_BEHAVIOR_RUN):
            print("Successfully ran behavior!")
        elif (response.run_result == audio_visual_pb2.RunBehaviorResponse.RESULT_SYSTEM_DISABLED):
            print("Could not run behavior because the system is disabled.")
        elif (response.run_result == audio_visual_pb2.RunBehaviorResponse.RESULT_BEHAVIOR_DISABLED):
            print("The behavior did not run because it is disabled.")
        elif (response.run_result == audio_visual_pb2.RunBehaviorResponse.RESULT_LOW_PRIORITY):
            print("The behavior did not run because its priority is lower than running behavior.")

        time.sleep(run_time)
    except BehaviorExpiredError:
        print("Could not run behavior because the specified end_time is in the past.")
        return False
    except DoesNotExistError:
        print("Could not run behavior because behavior doesnt exist.")
        return False
    return True


def add_or_modify_behavior(av_client, name, behavior):
    print(f"Trying to add or modify behavior \"{name}\"...")
    try:
        av_client.add_or_modify_behavior(name, behavior)
        print("Successfully added behavior!")
        return True
    except InvalidBehaviorError:
        print("Specified behavior contained invalid field(s).")
        return False
    except PermanentBehaviorError:
        print("Behavior that exists in the system is permanent, so we cannot edit it.")
        return False


def delete_behaviors(av_client, names):
    formatted_names = ", ".join([f'"{name}"' for name in names])
    print(f"Trying to delete behaviors {formatted_names}")
    try:
        deleted_behaviors = av_client.delete_behaviors(behavior_names=names)
        formatted_deleted_names = ", ".join(
            [f'"{behavior.name}"' for behavior in deleted_behaviors])
        print(f"Successfully deleted behaviors: {formatted_deleted_names}!")
    except DoesNotExistError:
        print("A specified behavior name does not exist in the system.")
        return False
    except PermanentBehaviorError:
        print("Behavior that exists in the system is permanent, so we cannot edit it.")
        return False
    return True


def main():

    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('-mb', '--max-brightness', type=float, required=False, default=None,
                        help='Maximum brightness for the LEDs.')
    parser.add_argument('-mbv', '--max-buzzer-volume', type=float, required=False, default=None,
                        help='Maximum volume for the buzzer.')
    parser.add_argument('-msv', '--max-speaker-volume', type=float, required=False, default=None,
                        help='Maximum volume for the speaker.')
    parser.add_argument('-t', '--run-time', type=int, default=30,
                        help='How long to run the behavior for.')
    parser.add_argument(
        '-b', '--behavior-name', type=str, default="custom", help=
        'Add/modify and run a custom behavior (instead of a stock behavior) to the system before running it.'
    )

    # LED sequence type
    def parse_led_sequence_type(value):
        # Accept either a comma-separated string of 3 ints or a supported string
        allowed_strings = {"blink", "pulse", "solid"}
        if value in allowed_strings:
            return value
        else:
            raise argparse.ArgumentTypeError("LED sequence type must be blink, pulse, or solid.")

    parser.add_argument('-l', '--led-sequence-type', type=parse_led_sequence_type, default="normal",
                        help='LED sequence type as blink, pulse, or solid.')

    def parse_color(value):
        # Accept either a comma-separated string of 3 ints or a supported string
        allowed_strings = {"normal", "warning", "danger"}
        if value in allowed_strings:
            return value
        elif ',' in value:
            parts = value.split(',')
            if len(parts) != 3:
                raise argparse.ArgumentTypeError(
                    "Color must be normal, warning, danger, or a comma-separated values (r,g,b).")
            try:
                return tuple(int(p) for p in parts)
            except ValueError:
                raise argparse.ArgumentTypeError("Color values must be integers.")
        else:
            raise argparse.ArgumentTypeError(
                "Color must be normal, warning, danger, or a 3 comma-separated values (r,g,b).")

    parser.add_argument(
        '-c', '--color', type=parse_color, default="normal",
        help='Color as normal, warning, danger, or a 3 comma-separated integers (r,g,b).')
    parser.add_argument('-d', '--delete', action='store_true',
                        help='Delete custom behavior after running')
    options = parser.parse_args()

    # Audio-visual parameters
    params = {}
    if options.max_brightness is not None:
        params['max_brightness'] = options.max_brightness
    if options.max_buzzer_volume is not None:
        params['buzzer_max_volume'] = options.max_buzzer_volume
    if options.max_speaker_volume is not None:
        params['speaker_max_volume'] = options.max_speaker_volume

    # Behavior parameters
    should_cleanup = options.delete
    run_time = options.run_time
    behavior_name = options.behavior_name

    # Create robot object with an image client
    sdk = bosdyn.client.create_standard_sdk('AudioVisualBehaviorsClient')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    av_client = robot.ensure_client(AudioVisualClient.default_service_name)

    if params:
        # Set system params (enabled, max brightness, max volume)
        print("Setting A/V system parameters...")
        resp = av_client.set_system_params(enabled=True, **params)
        print("Result:", resp)

    print("Getting A/V system parameters...")
    resp = av_client.get_system_params()
    print("Result:", resp)

    # Print the list of behaviors present in the system
    existing_behaviors = av_client.list_behaviors()
    if not existing_behaviors:
        print("No behaviors found in the system. Exiting...")
        return False

    print("Existing behaviors:")
    # Default to lowest priority, then set the priority to the highest priority plus 1, thereby making this script
    # the highest priority.
    priority = 0
    for behavior in existing_behaviors:
        print(f"- name: {behavior.name} | priority: {behavior.behavior.priority}")
        if priority < behavior.behavior.priority:
            priority = behavior.behavior.priority + 1

    if behavior_name != "custom" and behavior_name in [
            behavior.name for behavior in existing_behaviors
    ]:
        print("Running an existing behavior...")
        if not run_behavior(av_client, behavior_name, run_time):
            print('Exiting...')
            return False
    # Define a new AudioVisual behavior
    elif behavior_name == "custom":
        print("Adding and running a custom behavior...")

        def get_led_blink_sequence(color, period, duty_cycle=0.5):
            return audio_visual_pb2.LedSequenceGroup.LedSequence(
                blink_sequence=audio_visual_pb2.LedSequenceGroup.LedSequence.BlinkSequence(
                    color=color, period=period, duty_cycle=duty_cycle))

        # This method is unused, but you can uncomment it below to experiment if you'd like.
        def get_led_pulse_sequence(color, period):
            return audio_visual_pb2.LedSequenceGroup.LedSequence(
                pulse_sequence=audio_visual_pb2.LedSequenceGroup.LedSequence.PulseSequence(
                    color=color, period=period))

        # This method is also unused, but you can uncomment it below to experiment if you'd like.
        def get_led_solid_color_sequence(color):
            return audio_visual_pb2.LedSequenceGroup.LedSequence(
                solid_color_sequence=audio_visual_pb2.LedSequenceGroup.LedSequence.
                SolidColorSequence(color=color))

        def get_color_from_user_color_input(color):
            if isinstance(color, str):
                if color == "normal":
                    return audio_visual_pb2.Color(preset=audio_visual_pb2.Color.PRESET_NORMAL)
                elif color == "warning":
                    return audio_visual_pb2.Color(preset=audio_visual_pb2.Color.PRESET_WARNING)
                elif color == "danger":
                    return audio_visual_pb2.Color(preset=audio_visual_pb2.Color.PRESET_DANGER)
                else:
                    raise Exception(f"Unknown color '{color}'.")
            elif isinstance(color, tuple) and len(color) == 3:
                return audio_visual_pb2.Color(
                    rgb=audio_visual_pb2.Color.RGB(r=color[0], g=color[1], b=color[2]))
            else:
                raise Exception(
                    f"Invalid color {color}. Use normal, warning, danger, or a tuple of (r, g, b).")

        ############
        # LEDs #####
        ############
        try:
            color = get_color_from_user_color_input(options.color)
        except Exception as e:
            print(f"Error: {e}")
            print("Exiting...")
            return False

        color_period = Duration(nanos=500000000)  # 500 ms
        # There are different types of LED sequences. Two additional ones are commented out below.
        # Note that this example does not include a helper function for creating an AnimationSequence.
        if options.led_sequence_type == "blink":
            led_sequence = get_led_blink_sequence(color, color_period)
        elif options.led_sequence_type == "pulse":
            led_sequence = get_led_pulse_sequence(color, color_period)
        elif options.led_sequence_type == "solid":
            led_sequence = get_led_solid_color_sequence(color)
        led_sequence_group = audio_visual_pb2.LedSequenceGroup(
            front_center=led_sequence, front_left=led_sequence, front_right=led_sequence,
            hind_left=led_sequence, hind_right=led_sequence)

        ############
        # Buzzer ###
        ############
        note_duration = Duration(nanos=200000000)  # 200 ms

        def make_note_with_duration(note, octave, flat=False, sharp=False,
                                    note_duration=note_duration):
            return audio_visual_pb2.AudioSequenceGroup.BuzzerSequence.NoteWithDuration(
                note=choreography_params_pb2.BuzzerNoteParams(
                    note=note, octave=Int32Value(value=octave), flat=BoolValue(value=flat),
                    sharp=BoolValue(value=sharp)), duration=note_duration)

        def make_rest_or_peak_spl_with_duration(note, note_duration=note_duration):
            return audio_visual_pb2.AudioSequenceGroup.BuzzerSequence.NoteWithDuration(
                note=choreography_params_pb2.BuzzerNoteParams(note=note), duration=note_duration)

        def get_test_buzzer_sequence():
            buzzer_sequence = audio_visual_pb2.AudioSequenceGroup.BuzzerSequence()

            # This function tests everything: peak SPL, rest, notes (sharp, flat, and neither sharp nor flat).
            MUSICAL_NOTES = [
                choreography_params_pb2.BuzzerNoteParams.Note.NOTE_C,
                choreography_params_pb2.BuzzerNoteParams.Note.NOTE_D,
                choreography_params_pb2.BuzzerNoteParams.Note.NOTE_E,
                choreography_params_pb2.BuzzerNoteParams.Note.NOTE_F,
                choreography_params_pb2.BuzzerNoteParams.Note.NOTE_G,
                choreography_params_pb2.BuzzerNoteParams.Note.NOTE_A,
                choreography_params_pb2.BuzzerNoteParams.Note.NOTE_B,
            ]
            NOTE_REST = choreography_params_pb2.BuzzerNoteParams.Note.NOTE_REST
            NOTE_PEAK_SPL = choreography_params_pb2.BuzzerNoteParams.Note.NOTE_PEAK_SPL
            octaves = [3, 4, 5, 6, 7]
            # Peak SPL
            buzzer_sequence.notes.append(make_rest_or_peak_spl_with_duration(NOTE_PEAK_SPL))
            # Rest
            buzzer_sequence.notes.append(make_rest_or_peak_spl_with_duration(NOTE_REST))
            # Up scale (neither sharp nor flat)
            for octave in octaves:
                for note_name in MUSICAL_NOTES:
                    buzzer_sequence.notes.append(make_note_with_duration(note_name, octave))
            # Rest
            buzzer_sequence.notes.append(make_rest_or_peak_spl_with_duration(NOTE_REST))
            # Down scale (sharp)
            for octave in reversed(octaves):
                for note_name in reversed(MUSICAL_NOTES):
                    buzzer_sequence.notes.append(
                        make_note_with_duration(note_name, octave, sharp=True))
            # Rest
            buzzer_sequence.notes.append(make_rest_or_peak_spl_with_duration(NOTE_REST))
            # Up scale (flat)
            for octave in octaves:
                for note_name in MUSICAL_NOTES:
                    buzzer_sequence.notes.append(
                        make_note_with_duration(note_name, octave, flat=True))
            # Rest
            buzzer_sequence.notes.append(make_rest_or_peak_spl_with_duration(NOTE_REST))
            # Peak SPL
            buzzer_sequence.notes.append(make_rest_or_peak_spl_with_duration(NOTE_PEAK_SPL))
            # Down scale (neither sharp nor flat))
            for octave in reversed(octaves):
                for note_name in reversed(MUSICAL_NOTES):
                    buzzer_sequence.notes.append(make_note_with_duration(note_name, octave))

            return buzzer_sequence

        audio_sequence_group = audio_visual_pb2.AudioSequenceGroup(
            buzzer=get_test_buzzer_sequence())
        behavior = audio_visual_pb2.AudioVisualBehavior(enabled=True, priority=priority,
                                                        led_sequence_group=led_sequence_group,
                                                        audio_sequence_group=audio_sequence_group)

        # Try to add our behavior
        if not add_or_modify_behavior(av_client, behavior_name, behavior):
            print("Exiting...")
            return False

        # Ask the user for permission before proceeding if the buzzer volume is above the obnoxiousness threshold
        if options.max_buzzer_volume > 0.1:
            input(
                f"WARNING: The buzzer volume, {options.max_buzzer_volume}, is set above 0.1 and is loud enough to be obnoxious. Press Enter to continue, or Ctrl+C to abort..."
            )

        # Run the behavior
        if not run_behavior(av_client, behavior_name, run_time):
            print("Exiting...")
            return False

        if should_cleanup:
            print("Cleaning up by removing behavior from system.")
            if not delete_behaviors(av_client, [behavior_name]):
                print("Exiting...")
                return False
    else:
        print(f'Behavior {behavior_name} not found in the system. Exiting...')
        return False

    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
