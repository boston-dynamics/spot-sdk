<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Animation files for Choreographer

Choreographer supports animations that are parsed from a specific file format into an `Animation` protobuf message and uploaded to the robot using the `UploadAnimation` RPC.

Animation files are human readable/editable text files with a `*.cha` extension. The animation file consists of three sections separated by a single empty line:

* Options
* Parameters
* Body

There are three methods for parsing an animation cha file into an `Animation` protobuf message:

1. Create an animations directory in the same directory as the Choreographer executable. All *.cha animation files within this directory will be automatically parsed and uploaded to robot when Choreographer is opened.

The directory structure looks like this:

```
dance_directory/
	choreographer.exe
	animations/
		bourree_arm.cha
		my_animation.cha
```

2. In Choreographer, select **Load Animated Move** from the File menu to upload a single animation file after the application is already opened.

3. The python script `animation_file_to_proto.py` in the bosdyn-choreography-client package parses the text file and can be used to output a protobuf message, which can be uploaded to the robot using the UploadAnimation RPC without using Choreographer.


## File specification

### File name and extension

The animation text file uses the `*.cha` extension. The filename becomes the move's name, which can be referenced in choreography sequences. Choreographer displays the animated move name with underscores converted to spaces and each word capitalized.

### Structure

The animation cha file consists of three sections. Each section must be present and separated by a blank line. In all three sections, values within the same line can be separated by any combination of spaces and tabs.

The file sections are:
- **Options**: Pre-defined information used by both Choreographer and the robot to interpret the animation correctly.
- **Parameters**: Adjustable values to customize the animated move further. Once enabled, these values can be viewed and further modified through widgets that will appear in the Parameters section of Choreographer.
- **Body**: One line defining the columns, followed by the complete set of key frames. The move duration/keyframe timestamps are indicated by either a timestamp in this section or computed from the frequency defined in the options section. The keyframes consist of either joint angles or poses for the body parts being controlled.

### Units

All units are in:
- Distance: meters
- Angles: radians
- Time: seconds. Sometimes time is measured in slices (¼ beat). The duration is dependent on the sequence's BPM (beats per minute).

### Commenting

Comments are supported within the animation files using either `#` or `//` and can take up an entire line in the file or be at the end of an existing line. Comments must be within one of the three main sections of the file and cannot create a new section.

## Options file section

The Options section defines how the animated move is controlled and interpreted by both Choreographer and the robot. The section consists of lines with a keyword at the beginning of the line and a fixed number of values separated by spaces following the keyword.

The number of values is specific to the keyword used as defined below. Some keywords, such as “neutral_start” have no values following the keyword.

The Options section must contain a definition for which tracks the animation controls. This is specified by the `controls` keyword and a line structured as follows:

```
controls TRACK1... TRACK_N
```
Following the keyword `controls`, the fields `TRACK1 … TRACK_N` are one or more of [legs, body, arm, gripper]. Example: `controls legs body` controls the legs and body but not the arm or gripper.

### Supported keywords for the Options section

The `controls` tracks keyword is mandatory; all other keywords in the Options section are optional. Descriptions of the available keywords and associated values follows:

`bpm VALUE`: Where `VALUE` is the nominal beats per minute of the animation.  If the script is at a different BPM, the animation will be time-scaled so it takes the same number of beats.  If not specified, the animation will play at the nominal speed regardless of script BPM, taking a variable number of beats.

`extendable`: Indicates the move can be stretched in Choreographer.  Doing so will cause the animation to loop.

`truncatable`: Indicates that the move can be shortened in Choreographer.  Doing so will cause the animation to end early.

`display_rgb RED GREEN BLUE`: Where `RED`, `GREEN`, `BLUE` are integer numbers between 0 and 255.  This defines the color the move block will display as within Choreographer.  If not present, a default color will be generated based on the hash of the file name.

`frequency HZ`: Where `HZ` is the number of frames per second in the animation body.  If unspecified, the time column must be present in the body.

`retime_to_integer_slices`: Rescales time slightly so that the move takes an integer number of slices.  If absent, the animation will be padded or truncated slightly to take an integer number of slices.

`description TEXT`: Where `TEXT` to be displayed within Choreographer as a description of the animation.

`neutral_start`: Applies only to moves that control the body but do not contain leg information.  Indicates the move can be assumed to start in a neutral stand.  If not specified, it is instead assumed that the center of footprint is at the origin of the animation frame.

`precise_steps`: Step exactly at the animated locations, even at the expense of balance.

`precise_timing`: Step exactly at the animated times, even at the expense of balance.

`track_swing_trajectories`: Track animated swing trajectories.  Otherwise, takes standard swings between animated liftoff and touchdown locations.

`arm_playback OPTION`: Where `OPTION` is one of the following. If `OPTION` is not included the default behavior is for arm animations specified as joint angles to playback as joint space and animations specified as hand poses to default to workspace.

- `jointspace`: Arm animation playback is with respect to the body.
- `workspace`: Arm animation playback is with respect to the current footprint.
- `workspace_dance_frame`: Arm animation playback is with respect to a dance frame in workspace. Parameter arm_dance_frame_id can be used to specify which dance frame if multiple exist.

`requires_arm`: If set true, can not be loaded on a robot without an arm.

`no_looping`: If the animation completes before the move's duration, freeze rather than looping.  Without this option, the animation might loop because either the move duration was extended or because the `speed` parameter was set to a value greater than 1.

## Parameters file section
The parameters section defines adjustable values for the animated move. Each parameter value specified will show in the parameters panel in Choreographer when the animation is selected to be edited/added. The parameter names coincide with the values present in the `AnimateParams` protobuf message (in choreography_params.proto). The animation parameters may only apply for moves which control specific tracks (arm, gripper, body,legs). Each parameter is described on a single line and can be specified two different ways:

1. The parameter name, followed by the minimum, default, and maximum value (in that order).
```
PARAMETER_NAME    MINIMUM_VALUE    DEFAULT_VALUE    MAXIMUM_VALUE
```

2. Only the parameter name, and the limits/default will be configured from predefined values within Choreographer.
```
PARAMETER_NAME
```
Note: If no parameters are needed, put the keywords “no parameters” as the parameter section such that the file will still be parsed correctly.

### Supported parameters pertaining to all tracks

`speed`: Play the animation at this time multiplier.

`offset_slices`: Start the move with the script at this slice.

### Supported parameters when controlling the body track

`body_entry_slices`: How many slices to spend transitioning smoothly from the previous pose to the animated pose trajectory for body motion.

`body_exit_slices`: How many slices to spend transitioning from the animated trajectory back to the nominal pose.  If set to 0, will not transition back.

`translation_multiplier.x`: Multiply the body motion in the x direction.

`translation_multiplier.y`: Multiply the body motion in the y direction.

`translation_multiplier.z`: Multiply the body motion in the z direction.

`rotation_multiplier.roll`: Multiply the body motion in the roll direction.

`rotation_multiplier.pitch`: Multiply the body motion in the pitch direction.

`rotation_multiplier.yaw`: Multiply the body motion in the yaw direction.

`body_tracking_stiffness`: How hard to try to track the animated body motion.  Only applicable to animations that control both the body and the legs.  On a scale of 1 to 10 (11 for a bit extra).  Higher will result in more closely tracking the animated body motion, but possibly at the expense of balance for more difficult animations.

### Supported parameters when controlling the arm track

`arm_entry_slices`: How many slices to spend transitioning smoothly from the previous pose to the animated pose trajectory for arm and gripper motion.

`shoulder_0_offset`: Offset to add to the SH0 angle in all animation keyframes.

`shoulder_1_offset`: Offset to add to the SH1 angle in all animation keyframes.

`elbow_0_offset`: Offset to add to the EL0 angle in all animation keyframes.

`elbow_1_offset`: Offset to add to the EL1 angle in all animation keyframes.

`wrist_0_offset`: Offset to add to the WR0 angle in all animation keyframes.

`wrist_1_offset`: Offset to add to the WR1 angle in all animation keyframes.

`arm_required`: Prevents a robot without an arm from loading the animation.

`arm_prohibited`: Prevents a robot with an arm from loading the animation.

### Supported parameters when controlling the gripper track

`gripper_offset`: Offset to add to the gripper angle in all animation keyframes.

`gripper_multiplier`: Multiply all gripper angles by this value.

`gripper_strength_fraction`: How hard the gripper can squeeze.  Fraction of full strength.

### Supported parameters when controlling arm and gripper tracks

`arm_dance_frame_id`: Dance frame to reference for workspace arm moves. Only valid in combination with the option `arm_playback workspace_dance_frame` (specified in the options section of the file).

## Body keyframe file section

The body keyframe section defines the actual animated move through keyframes describing either the pose or joint angles at each keyframe timestamp. Each keyframe is a single line consisting of a number of fields determined by the number of columns specified. The first line will specify what value is in each column and how many columns there will be; it is written as a series of key words (space separated) where each keyword has an fixed number of columns that the parser expects.

Columns defined by keywords can either be an individual definition, or a group definition describing a fixed number of values. For example, “body_pos” describes a group of three columns, and “body_x body_y body_z” describes those same three columns using the individual column keywords.

The same column value cannot be specified multiple times. Column values are only defined in the first line of the body keyframe section. Some columns are multiple ways of specifying the same body control (for example, “leg_joints” and “foot_pos”) and will be mutually exclusive when defining an animated move.

Column definitions are required for each track that is being controlled (as specified in the options section). If additional columns controlled unspecified tracks are included, they will be ignored when the animated move is executed.

### Supported columns not pertaining to a particular track

`time`: The timestamp of each frame. The start of the animation is 0.  This column and the “frequency” option are mutually exclusive, but one is required.

### Supported columns pertaining to gripper track

`gripper`: Gripper joint angle. Required.

The field gripper is required.

### Supported columns pertaining to arm track

`arm_joints`: Grouping of 6 columns [shoulder0 shoulder1 elbow0 elbow1 wrist0 wrist1]. Represents the arm joint angles.  Any columns not included will be held constant at the previous joint angle. Mutually exclusive with hand_pos and hand orientation specifications.

`hand_pos`: Grouping of [hand_x hand_y hand_z]. Hand position in the animation frame.

`hand_quat_wxyz`: Grouping of [hand_quat_w hand_quat_x hand_quat_y hand_quat_z].  Mutually exclusive with other orientation specifications.

`hand_quat_xyzw`: Grouping of hand_quat_x hand_quat_y hand_quat_z hand_quat_w].  Mutually exclusive with other orientation specifications.

`hand_euler_rpy`: Grouping of [hand_roll hand_pitch hand_yaw] Mutually exclusive with other orientation specifications.

### Supported columns pertaining to body track

`body_pos`: Grouping of [body_x body_y body_z]. Body position in the animation frame.  Mutually exclusive with com_pos.

`com_pos`: Grouping of [com_x com_y com_z].  Center of Mass position in the animation frame.  Mutually exclusive with body_pos.

`body_quat_wxyz`: Grouping of [body_quat_w body_quat_x body_quat_y body_quat_z].  Mutually exclusive with other orientation specifications.

`body_quat_xyzw`: Grouping of [body_quat_x body_quat_y body_quat_z body_quat_w].  Mutually exclusive with other orientation specifications.

`body_euler_rpy`: Grouping of [body_roll body_pitch body_yaw] Mutually exclusive with other orientation specifications.

At least one dimension of the body must be specified.

### Supported columns pertaining to legs track

`leg_joints`: Grouping of [fl_hx fl_hy fl_kn fr_hx fr_hy fr_kn hl_hx hl_hy hl_kn hr_hx hr_hy hr_kn].  Can also be grouped by leg as [fl_angles fr_angles hl_angles hr_angles]  Mutually exclusive (by leg) with foot_pos.

`foot_pos`: Grouping of [fl_x fl_y fl_z fr_x fr_y fr_z hl_x hl_y hl_z hr_x hr_y hr_z].  Can also be grouped by leg as [fl_pos fr_pos hl_pos hr_pos].  Mutually exclusive (by leg) with leg_joints.

`contact`: Grouping of [fl_contact fr_contact hl_contact hr_contact].  1 if in stance.  0 if in swing.  If absent, contact will be inferred from either leg_joints or foot_pos.

Either leg_joints or foot_pos are required for each leg.
