<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Animation Recorder

This program can be run alongside tablet control of the robot to record, save and playback the motion the robot executes under tablet control. Animation Recorder records the robot using the Choreography Client logging service, which captures all the position and rotation information of the joints and body of the robot along with the time when they occurred. This information is then parsed into a _.cha animation file format. As a _.cha file, it contains all the information contained in the log, but can also be uploaded to the robot as an animated move which can then be turned into a choreography sequence. This choreography sequence containing the recorded move can then be played back on the robot.

## Understanding Spot Programming

For your best learning experience, please use the [Quickstart Guide](../../../docs/python/quickstart.md) found in the SDK's docs/python directory. That will help you get your Python programming environment set up properly. For understanding the Choreography Client look to the [Python Reference Guide](../../../python/bosdyn-choreography-client/src/bosdyn/choreography/client/choreography.md). For understanding Animation file formatting look to [Animation File Specification](../../../docs/concepts/choreography/animation_file_specification).

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Common Problems

1. Remember, you will need to be controlling the robot with the tablet before launching this program.
2. Make sure the Motor Enable button on the Spot rear panel is depressed.
3. The robot may power off during the upload progress for longer recorded animations. If this happens, you can power the robot back on using the tablet.
4. Start recording the robot only when it is in the basic upright standing position with all four feet on the ground, and avoid recording the robot sitting down, self-righting, or climbing stairs. Recording motions with any of these characteristics may cause the robot to fall during playback, or cause Animation Recorder to crash.

## Run the Example

To run the example:

```
python3 animation_recorder.py --download-filepath FOLDERNAME  ROBOT_IP
```
