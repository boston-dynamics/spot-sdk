# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A tool to convert animation files into protobuf messages which can be uploaded to the robot
and used within choreography sequences."""

import argparse
import hashlib
import logging
import ntpath
import os
import sys

from google.protobuf import text_format, wrappers_pb2

import bosdyn.client
import bosdyn.client.util
from bosdyn.api.spot import choreography_sequence_pb2
from bosdyn.choreography.client.animation_file_conversion_helpers import *

LOGGER = logging.getLogger(__name__)

# The options keywords represent the first section of the file, and will be parsed into
# specific fields within the Animation proto.
OPTIONS_KEYWORDS_TO_FUNCTION = {
    "controls": controls_option,
    "bpm": bpm_option,
    "extendable": extendable_option,
    "truncatable": truncatable_option,
    "neutral_start": neutral_start_option,
    "precise_steps": precise_steps_option,
    "precise_timing": precise_timing_option,  # Deprecated.
    "timing_adjustability": timing_adjustability_option,
    "no_looping": no_looping_option,
    "arm_required": arm_required_option,
    "arm_prohibited": arm_prohibited_option,
    "starts_sitting": starts_sitting_option,
    "track_swing_trajectories": track_swing_trajectories_option,
    "assume_zero_roll_and_pitch": assume_zero_roll_and_pitch_option,
    "arm_playback": arm_playback_option,
    "display_rgb": display_rgb_option,
    "frequency": frequency_option,
    "retime_to_integer_slices": retime_to_integer_slices_option,
    "description": description_option,
    "custom_gait_cycle": custom_gait_cycle_option,
}

# The grouped headers represent animation keyframe values which can be used and specify multiple protobuf
# values for a single header keyword. For example, body_pos has x/y/z position values.
GROUPED_HEADERS = {
    "body_pos": (3, body_pos_handler),
    "com_pos": (3, com_pos_handler),
    "body_euler_rpy": (3, body_euler_rpy_angles_handler),
    "body_quat_xyzw": (4, body_quaternion_xyzw_handler),
    "body_quat_wxyz": (4, body_quaternion_wxyz_handler),
    "leg_joints": (12, leg_angles_handler),
    "foot_pos": (12, foot_pos_handler),
    "hand_pos": (3, hand_pos_handler),
    "hand_euler_rpy": (3, hand_euler_rpy_angles_handler),
    "hand_quat_xyzw": (4, hand_quaternion_xyzw_handler),
    "hand_quat_wxyz": (4, hand_quaternion_wxyz_handler),
    "contact": (4, contact_handler),
    "arm_joints": (6, arm_joints_handler),
    "fl_angles": (3, fl_angles_handler),
    "fr_angles": (3, fr_angles_handler),
    "hl_angles": (3, hl_angles_handler),
    "hr_angles": (3, hr_angles_handler),
    "fl_pos": (3, fl_pos_handler),
    "fr_pos": (3, fr_pos_handler),
    "hl_pos": (3, hl_pos_handler),
    "hr_pos": (3, hr_pos_handler),
}

# The single grouped headers represent animation keyframe values which can be used and specify a single
# protobuf value for the header keyword.
SINGLE_HEADERS = {
    "body_x": body_x_handler,
    "body_y": body_y_handler,
    "body_z": body_z_handler,
    "com_x": com_x_handler,
    "com_y": com_y_handler,
    "com_z": com_z_handler,
    "body_quat_w": body_quat_w_handler,
    "body_quat_x": body_quat_x_handler,
    "body_quat_y": body_quat_y_handler,
    "body_quat_z": body_quat_z_handler,
    "body_roll": body_roll_handler,
    "body_pitch": body_pitch_handler,
    "body_yaw": body_yaw_handler,
    "fl_hx": fl_hx_handler,
    "fl_hy": fl_hy_handler,
    "fl_kn": fl_kn_handler,
    "fr_hx": fr_hx_handler,
    "fr_hy": fr_hy_handler,
    "fr_kn": fr_kn_handler,
    "hl_hx": hl_hx_handler,
    "hl_hy": hl_hy_handler,
    "hl_kn": hl_kn_handler,
    "hr_hx": hr_hx_handler,
    "hr_hy": hr_hy_handler,
    "hr_kn": hr_kn_handler,
    "fl_x": fl_x_handler,
    "fl_y": fl_y_handler,
    "fl_z": fl_z_handler,
    "fr_x": fr_x_handler,
    "fr_y": fr_y_handler,
    "fr_z": fr_z_handler,
    "hr_x": hr_x_handler,
    "hr_y": hr_y_handler,
    "hr_z": hr_z_handler,
    "hl_x": hl_x_handler,
    "hl_y": hl_y_handler,
    "hl_z": hl_z_handler,
    "fl_contact": fl_contact_handler,
    "fr_contact": fr_contact_handler,
    "hl_contact": hl_contact_handler,
    "hr_contact": hr_contact_handler,
    "shoulder0": sh0_handler,
    "shoulder1": sh1_handler,
    "elbow0": el0_handler,
    "elbow1": el1_handler,
    "wrist0": wr0_handler,
    "wrist1": wr1_handler,
    "hand_x": hand_x_handler,
    "hand_y": hand_y_handler,
    "hand_z": hand_z_handler,
    "hand_quat_w": hand_quat_w_handler,
    "hand_quat_x": hand_quat_x_handler,
    "hand_quat_y": hand_quat_y_handler,
    "hand_quat_z": hand_quat_z_handler,
    "hand_roll": hand_roll_handler,
    "hand_pitch": hand_pitch_handler,
    "hand_yaw": hand_yaw_handler,
    "gripper": gripper_handler,
    "time": start_time_handler,
}

COMMENT_DELIMITERS = ["//", "#"]


class AnimationFileFormatError(Exception):
    """Specific Exception raised when we identify an issue with an animation (*.cha) file."""
    pass


class Animation():
    """Helper class to track values read from the animation file that are important to choreographer
    and necessary when uploading animated moves."""

    def __init__(self):
        # The name of the animated move.
        self.name = None

        # [Optional] The BPM which the move will be performed at.
        self.bpm = None

        # [Optional] The frequency at which the keyframes occur. If not provided in the CHA file, then
        # explicit timestamps must be provided for each keyframe.
        self.frequency = None

        # Default description for the animated move.
        self.description = "Animated dance move."

        # The protobuf message representing the animation.
        self.proto = choreography_sequence_pb2.Animation()

        # The color of the animated move's block when loaded in Choreographer.
        self.rgb = [100, 100, 100]

        # Each individual parameter line as read from a *.cha file.
        self.parameter_lines = []

    def create_move_info_proto(self):
        """Creates the MoveInfo protobuf message from the parsed animation file.

        Returns:
            The choreography_sequence.MoveInfo protobuf message for the animation as generated
            by the different animation fields in the Animation proto.
        """
        move_info = choreography_sequence_pb2.MoveInfo()
        move_info.name = self.name
        move_info.is_extendable = self.proto.extendable or self.proto.truncatable  # "is adjustable"

        # Should always have move.time, so the duration is the final time of the last frame.
        move_duration_sec = self.proto.animation_keyframes[-1].time
        if self.bpm is not None:
            # Compute the move length slices using the bpm.
            slices_per_minute = 4 * self.bpm
            move_duration_minutes = move_duration_sec / 60.0
            move_info.move_length_slices = int(move_duration_minutes * slices_per_minute)
        else:
            # Just use the time to size the move.
            move_info.move_length_time = move_duration_sec

        # Set the max/min info based on truncatable/extendable flags.
        if self.proto.truncatable and not self.proto.extendable:
            move_info.max_time = move_info.move_length_time
            move_info.max_move_length_slices = move_info.move_length_slices
        elif self.proto.extendable and not self.proto.truncatable:
            move_info.min_time = move_info.move_length_time
            move_info.min_move_length_slices = move_info.move_length_slices

        # Set the different track information
        move_info.controls_arm = self.proto.controls_arm
        move_info.controls_gripper = self.proto.controls_gripper
        move_info.controls_legs = self.proto.controls_legs
        move_info.controls_body = self.proto.controls_body

        # Set the choreographer-specific display information
        move_info.display.category = choreography_sequence_pb2.ChoreographerDisplayInfo.CATEGORY_ANIMATION
        move_info.display.color.r = self.rgb[0]
        move_info.display.color.g = self.rgb[1]
        move_info.display.color.b = self.rgb[2]
        move_info.display.color.a = 1.0
        move_info.display.description = self.description

        # Animations are required to start and end in a standing position (by default).
        if self.proto.starts_sitting:
            move_info.entrance_states.append(
                choreography_sequence_pb2.MoveInfo.TRANSITION_STATE_SIT)
        else:
            move_info.entrance_states.append(
                choreography_sequence_pb2.MoveInfo.TRANSITION_STATE_STAND)
        move_info.exit_state = choreography_sequence_pb2.MoveInfo.TRANSITION_STATE_STAND

        return move_info


def set_proto(proto_object, attribute_name, attribute_value):
    """Helper function to set a field to a specific value in the protobuf message.

    Args:
        proto_object (Protobuf message): Any generic protobuf message.
        attribute_name (String): The field name within the protobuf message.
        attribute_value: A value with type matching the field type defined in the protobuf
            message definition. This will be saved in the attribute_name field.

    Returns:
        Nothing. Mutates the input proto_object to update the specified field name to the
        provided value.
    """
    field_attr = getattr(proto_object, attribute_name)
    field_type = type(field_attr.value)
    field_attr.value = field_type(attribute_value)


def handle_nested_double_value_params(proto_object, name, attribute_value):
    """Helper function to set a field to a DoubleValue protobuf in a protobuf message.

    Args:
        proto_object (Protobuf message): Any generic protobuf message.
        name (String): The field name within the protobuf message. This name should
            be both the field name and sub-field name separated by a period. For example,
            for the Vec3 velocity field, the name would be 'velocity.x'.
        attribute_value: A value with type matching the field type defined in the protobuf
            message definition. This will be saved in the attribute_name field.

    Returns:
        Nothing. Mutates the input proto_object to update the specified field name to the
        provided value.
    """
    subfields = name.split(".")
    current_attr = proto_object
    for field in subfields:
        current_attr = getattr(current_attr, field)
    current_attr.CopyFrom(wrappers_pb2.DoubleValue(value=attribute_value))


def read_animation_params(animation):
    """Parses the set of lines that are the parameters section of the file.

    Reads the parameter lines into the min/max/default values in the Animation proto.

    Args:
        animation (Animation): The animation class structure containing the parameter lines.

    Returns:
        The mutated animation class, which now contains populated params fields in the
        animation's protobuf.
    """
    current_params_default = animation.proto.default_parameters
    current_params_min = animation.proto.minimum_parameters
    current_params_max = animation.proto.maximum_parameters
    group_field_splitter = "."
    for param in animation.parameter_lines:
        split_line = param.split()
        param_name = str(split_line[0])
        min_max_default_vals = [
            float(split_line[i]) if float(split_line[i]) != 0 else 1e-6 for i in range(1, 4)
        ]

        # Now create the parameter protobuf message.
        if group_field_splitter in param_name:
            # Non-individual fields, so handle slightly differently.
            try:
                handle_nested_double_value_params(current_params_min, param_name,
                                                  min_max_default_vals[0])
                handle_nested_double_value_params(current_params_default, param_name,
                                                  min_max_default_vals[1])
                handle_nested_double_value_params(current_params_max, param_name,
                                                  min_max_default_vals[2])
            except AttributeError:
                err = "Cannot parse file %s: unknown parameter field name %s." % (animation.name,
                                                                                  param_name)
                raise AnimationFileFormatError(err)
        else:
            # Individual field using a DoubleValue proto.
            try:
                set_proto(current_params_min, param_name, min_max_default_vals[0])
                set_proto(current_params_default, param_name, min_max_default_vals[1])
                set_proto(current_params_max, param_name, min_max_default_vals[2])
            except AttributeError:
                err = "Cannot parse file %s: unknown parameter field name %s." % (animation.name,
                                                                                  param_name)
                raise AnimationFileFormatError(err)
    return animation


def read_and_find_animation_params(animate_move_params_file, filepath_input=True):
    """Create a mapping of the parameter name to the default parameter values.

    Args:
        animate_move_params_file (string): filepath to the default parameters file, or a string representing the contents
            of the parameters file.
        filepath_input (boolean): With filepath_input set to True, the animate_move_params_file argument will be interpreted as
            a file path to the default parameters file. When set to False, the animate_move_params_file argument will be read as
            the information in the default parameters file passed as a string.

    Returns:
        A dictionary containing the parameter name as the key, and the full parameter line from
        the file as the value.
    """
    if (filepath_input):
        #if animate_move_params_file is a filepath open the file
        params_file = open(animate_move_params_file, "r")
    else:
        #if animate_move_params_file is a string of parameter information split the string by newline characters
        params_file = animate_move_params_file.splitlines()

    reading_animate_params = False
    animate_params_vals = {}
    for line in params_file:
        line = line.strip()
        if "animate_params" in line:
            # Starting the animate params section.
            reading_animate_params = True
            continue

        if reading_animate_params and line == "":
            # Finished reading the animate_params section.
            reading_animate_params = False
            return animate_params_vals

        if reading_animate_params:
            # Set the parameter name as the key, and the full parameter line (as a string) as the value in
            # the animate_params_vals dictionary.
            split_line = line.split()
            param_name = split_line[0]
            animate_params_vals[param_name] = line
            continue
    return animate_params_vals


def convert_animation_file_to_proto(animated_file, animate_move_params_file=""):
    """Parses a file into the animation proto that will be uploaded to the robot.

    Args:
        animated_file (string): The filepath to the animation text file.
        animate_move_params_file (string): [Optional] The filepath to a default set of move parameters.

    Returns:
        The Animation class, which contains the animation proto to be uploaded to the robot, as well
        as additional information to be used by Choreographer.
    """

    # Create a mapping of the default values for each parameter from the MoveParamsConfig.txt file.
    # These will be used if a user doesn't provide min/max/default, but does include the parameter
    # name in the file.
    maybe_use_default_params = animate_move_params_file != ""
    default_animate_params_values = {}
    if maybe_use_default_params:
        if os.path.exists(animate_move_params_file):
            # if there is a file at the location animate_move_params_file try to read the file
            default_animate_params_values = read_and_find_animation_params(animate_move_params_file)
        else:
            # if animate_move_params_file isn't a locatable file try to read the string as parameter field data
            default_animate_params_values = read_and_find_animation_params(
                animate_move_params_file, False)

    animation = Animation()
    animation.name = ntpath.basename(animated_file).split(".cha")[0]

    animation_specs = open(animated_file, "r")

    # Expecting three chunks, separated by a blank line.
    section_counter = 0

    # The set of keywords that describe each column in the movement section.
    movement_columns = []

    # If the keyframe needs the timestamps set based off the frequency, track that information here.
    # Value 1: indicates if it needs the timestamps set, value 2: indicates the current cumulative time
    # summed while iterating over each keyframe in the file.
    set_keyframe_times = [False, 0]

    # Make up a unique color that is persistent based on the animation name.
    name_hash = hashlib.md5(animation.name.encode())
    animation.rgb[0] = int(name_hash.hexdigest()[0:2], 16)
    animation.rgb[1] = int(name_hash.hexdigest()[2:4], 16)
    animation.rgb[2] = int(name_hash.hexdigest()[4:6], 16)

    for line in animation_specs:
        line = line.strip()

        if line == "":
            # The sections are separated by an empty line
            section_counter += 1
            continue

        # Check if there are any comments. Comments can be both at the end of an existing line, or
        # on a line of their own. They are marked with # or //. We want to just ignore them and continue
        # parsing the file as normal.
        for delim in COMMENT_DELIMITERS:
            line = line.split(delim)[0]  # Take any content before the comment starts.

        if line == "":
            # If after stripping all the comment content there is no line left, then continue.
            # We do NOT increment the section counter for comment lines!
            continue

        if section_counter == 0:
            # the first section is the "options section".
            # Take first word of line and use that as the options keyword. Apply whatever function
            # is specified for that keyword to the remaining line values.
            file_line_split = line.split()
            keyword = file_line_split[0]
            if keyword in OPTIONS_KEYWORDS_TO_FUNCTION:
                # Apply the keywords functionality to the animation class.
                OPTIONS_KEYWORDS_TO_FUNCTION[keyword](file_line_split, animation)

        elif section_counter == 1:
            # Second section represents the parameters for choreographer. Simply store the lines
            # for use by choreographer's config reader.
            line = line.strip().lower()
            if "no parameters" in line:
                # This is the keyword for no parameters, so just skip the section and move on.
                continue
            split_line = line.split()
            if len(split_line) == 1 and maybe_use_default_params:
                # If the parameter name was provided with no user-specified min/max/default values,
                # then attempt to use the default values from MoveParamsConfig.txt.
                if split_line[0] in default_animate_params_values:
                    animation.parameter_lines.append(default_animate_params_values[split_line[0]])
                else:
                    err = "Cannot parse file %s: parameter field name %s was provided but is not a default parameter." % (
                        animation.name, split_line[0])
                    raise AnimationFileFormatError(err)
            else:
                animation.parameter_lines.append(line)

        elif section_counter == 2:
            # The final section is the animated moves section.
            if len(movement_columns) == 0:
                # The first line will contain all the different column headers.
                movement_columns = line.split()

                # If "time" is not in the column, then we should set that for every keyframe based on frequency
                if "time" not in movement_columns:
                    set_keyframe_times[0] = True
                    if animation.frequency is None:
                        prefix = "Cannot parse file %s: " % animation.name
                        err = prefix + "Either frequency or keyframe timestamps must be provided. Neither were found."
                        raise AnimationFileFormatError(err)
                continue

            vals = line.split()
            animation_keyframe = choreography_sequence_pb2.AnimationKeyframe()
            current_index = 0
            for header in movement_columns:
                if header in GROUPED_HEADERS:
                    # For grouped headers, get the next N line values, where N is specified by the grouped
                    # headers dict, and set those in the animation keyframe protobuf message.
                    header_activities = GROUPED_HEADERS[header]
                    header_values = vals[current_index:current_index +
                                         header_activities[0]]  # not inclusive
                    header_values = [float(val) if val != '0' else 1e-6 for val in header_values]
                    header_activities[1](header_values, animation_keyframe)
                    current_index = current_index + header_activities[0]
                elif header in SINGLE_HEADERS:
                    # Add the single value into the animation keyframe protobuf message.
                    header_value = float(vals[current_index])
                    if header_value == 0:
                        header_value = 1e-6
                    SINGLE_HEADERS[header](header_value, animation_keyframe)
                    current_index += 1
                else:
                    # Don't fail silently and mismatch indices of other groups if one group header is not found.
                    err = "Cannot parse file %s: Unknown body movement keyword %s" % (
                        animation.name, header)
                    raise AnimationFileFormatError(err)

            if set_keyframe_times[0]:
                # Update the timestamp in the keyframe, then increment it based on the frequency
                animation_keyframe.time = set_keyframe_times[1]
                set_keyframe_times[1] += (1.0 / animation.frequency)

            # Add the animation frame into the animation proto.
            animation.proto.animation_keyframes.extend([animation_keyframe])

        else:
            # An animation file should only have 3 sections: the options, the parameters, and the body movement keyframes.
            err = (
                "Cannot parse file %s: Animation file contains more than 3 sections delineated by whitespace."
                " Make sure all comments are included in a existing section." % (animation.name))
            raise AnimationFileFormatError(err)

    animation.proto.name = animation.name
    if animation.bpm is not None:
        animation.proto.bpm = animation.bpm

    # Read out the parameters into protobuf messages.
    read_animation_params(animation)

    return animation


def write_animation_to_dest(animation, destination):
    """Write the new animation proto to a .cap file.

    Args:
        animation(Animation class): The animation class object generated by the
            `cha` file conversion helpers to save the protobuf from.
        destination (string): The full filepath to the location to save the animation
            protobuf message.
    """
    if (animation.name is None):
        LOGGER.error("Invalid file name, cannot save choreography sequence.")
        raise IOError("Invalid file name, cannot save choreography sequence.")

    if not os.path.exists(destination):
        LOGGER.error("Path(%s) to save file does not exist. Creating it." % destination)
        os.makedirs(destination, exist_ok=True)

    animation_proto_bytes = text_format.MessageToString(animation.proto)
    with open(str(os.path.join(destination, animation.name + ".cap")), 'w') as f:
        f.write(animation_proto_bytes)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cha-filepath', help='The filename of the animation file.')
    parser.add_argument('--cha-directory', help="The filepath to a directory with animation files.")
    parser.add_argument(
        '--config-filepath', help=
        'The filepath for a move params config file. This can be found using the ListAllMoves RPC.',
        default="")
    parser.add_argument('--destination-filepath',
                        help='The file location to save the animation proto.', default=".")
    options = parser.parse_args()

    if options.cha_filepath:
        animation = convert_animation_file_to_proto(options.cha_filepath, options.config_filepath)
        write_animation_to_dest(animation, options.destination_filepath)

    elif options.cha_directory:
        files_in_dir = os.listdir(options.cha_directory)
        for filename in files_in_dir:
            if filename.endswith(".cha"):
                animation = convert_animation_file_to_proto(
                    os.path.join(options.cha_directory, filename), options.config_filepath)
                write_animation_to_dest(animation, options.destination_filepath)

    else:
        print(
            "Please provide either the --cha-filepath argument for a single animation file, or the --cha-directory argument"
            " for a full directory of animation files.")

    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
