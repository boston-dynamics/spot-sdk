<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# API Example - Mission Recorder

This example creates an interface for operating Spot with your keyboard, recording a mission, and saving it.

## Setup Dependencies
See requirements.txt for the dependencies required for this example. Using pip, these dependencies can be installed using:
```
python -m pip install -r requirements.txt
```

## Overview
The mission_recorder allows you to record Autowalk missions for Spot without the need for a tablet.  You must have a fiducial marker printed out and posted in a place that is visible to Spot for this to work.

## How to Record a Mission
1. Place at least one fiducial marker in a position that is visible to Spot’s cameras.  More than one fiducial can be used (but each must be unique).
2. Make sure that Spot’s hardware power switch is on and Spot’s hardware E-Stop is disabled.
3. Run the mission_recorder script:

```
python mission_recorder.py --username USER --password PASSWORD ROBOT_IP DIRECTORY_TO_SAVE_MISSION
```

4. Press the spacebar to release the software E-Stop.
5. Press ‘P’ to power on the robot.  NOTE: All keyboard commands are case-sensitive.
6. Press ‘f’ to command the robot to stand up.
7. Move the robot using the [wasd keys](../wasd/README.md) to the desired starting point of the mission, which must have line-of-sight to the fiducial.
8. The text interface should indicate that the number of fiducials visible is at least 1.
9. If this number is 0, move the robot using the wasd keys until it can see the fiducial.
10. Press ‘m’ to start recording a mission.
11. Drive the robot along the desired path, using ‘w’ and ‘s’ to drive forward and back, ‘a’ and ‘d’ to strafe left and right, and ‘q’ and ‘e’ to turn left and right.
12. When you have finished training the path, press ‘g’ to save the mission and exit the mission_recorder.

## Keyboard Commands
When run, this example will create an interface in your terminal listing the controls which are as follows:

| Button             | Functionality                       |
|--------------------|-------------------------------------|
| wasd               | Directional Strafing                |
| qe                 | Turning                             |
| f                  | Stand                               |
| v                  | Sit                                 |
| m                  | Start recording mission             |
| g                  | Stop recording and generate mission |
| T                  | Time-sync                           |
| r                  | Self-right                          |
| l                  | Return/Acquire Lease                |
| SPACE              | E-Stop                              |
| P                  | Motor power & Control               |
| Tab                | Exit                                |

## How to Replay a Mission
See the instructions in the [Replay Mission](../replay_mission/README.md) example.
