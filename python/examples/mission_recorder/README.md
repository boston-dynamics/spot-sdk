<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Mission Recorder

This example creates an interface for operating Spot with your keyboard, recording a mission, and saving it.

## Setup Dependencies

See requirements.txt for the dependencies required for this example. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Overview

The mission_recorder allows you to record Autowalk missions for Spot without the need for a tablet. You must have a fiducial marker printed out and posted in a place that is visible to Spot for this to work.

## How to Record a Mission

NOTE: All keyboard commands are case-sensitive.

1. Place at least one fiducial marker in a position that is visible to Spot’s cameras. More than one fiducial can be used (but each must be unique).
2. OPTIONAL: The robot's camera view can be monitored using the OBSERVE mode on the tablet.
3. Make sure that Spot’s hardware power switch is on and Spot’s hardware E-Stop is disabled.
4. Run the mission_recorder script:

```
python3 mission_recorder.py ROBOT_IP DIRECTORY_TO_SAVE_MISSION
```

5. Press the spacebar to release the software E-Stop.
6. Press ‘P’ to power on the robot.
7. Press ‘f’ to command the robot to stand up.
8. Move the robot using the [wasd keys](../wasd/README.md) to the desired starting point of the mission, which must have line-of-sight to the fiducial.
9. The text interface should indicate that the number of fiducials visible is at least 1.
10. If this number is 0, move the robot using the wasd keys until it can see the fiducial.
11. Press ‘m’ to start recording a mission.
12. Drive the robot along the desired path, using ‘w’ and ‘s’ to drive forward and back, ‘a’ and ‘d’ to strafe left and right, and ‘q’ and ‘e’ to turn left and right.
13. When you have finished training the path, press ‘g’ to save the mission and exit the mission_recorder.

## How to Record a Mission with Additional Fiducials for Localization

NOTE: All keyboard commands are case-sensitive.

1. Place at least one fiducial marker in a position that is visible to Spot’s cameras. More than one fiducial can be used (but each must be unique).
2. OPTIONAL: The robot's camera view can be monitored using the OBSERVE mode on the tablet.
3. Place additional fiducials along the Spot's intended path in locations that will be visible to Spot's cameras when Spot is nearby.
4. Make sure that Spot’s hardware power switch is on and Spot’s hardware E-Stop is disabled.
5. Run the mission_recorder script:

```
python3 mission_recorder.py ROBOT_IP DIRECTORY_TO_SAVE_MISSION
```

6. Press the spacebar to release the software E-Stop.
7. Press ‘P’ to power on the robot.
8. Press ‘f’ to command the robot to stand up.
9. Move the robot using the [wasd keys](../wasd/README.md) to the desired starting point of the mission, which must have line-of-sight to the fiducial.
10. The text interface should indicate that the number of fiducials visible is at least 1.
11. If this number is 0, move the robot using the wasd keys until it can see the fiducial.
12. Press ‘m’ to start recording a mission.
13. Drive the robot along the desired path, using ‘w’ and ‘s’ to drive forward and back, ‘a’ and ‘d’ to strafe left and right, and ‘q’ and ‘e’ to turn left and right.
14. When Spot is near one of the additional fiducials, verify that the fiducial can be seen in the camera view, then press 'l' (lower-case L) to insert a localization node.
15. Any number of fiducials and localization nodes may be added, but each fiducial must be unique.
16. Continue driving the robot along the desired path.
17. When you have finished training the path, press ‘g’ to save the mission and exit the mission_recorder.

## Keyboard Commands

When run, this example will create an interface in your terminal listing the controls which are as follows:

| Button | Functionality                       |
| ------ | ----------------------------------- |
| wasd   | Directional Strafing                |
| qe     | Turning                             |
| f      | Stand                               |
| v      | Sit                                 |
| m      | Start recording mission             |
| g      | Stop recording and generate mission |
| T      | Time-sync                           |
| r      | Self-right                          |
| l      | Return/Acquire Lease                |
| SPACE  | E-Stop                              |
| P      | Motor power & Control               |
| Tab    | Exit                                |

## How to Replay a Mission

See the instructions in the [Replay Mission](../replay_mission/README.md) example.
