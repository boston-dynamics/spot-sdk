<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Controlling the Arm with a Keyboard

This example creates an interface for controlling the arm with your keyboard. The example initializes the SDK to talk to robot and takes keyboard inputs to send cylindrical and angular hand velocity commands.

## Understanding Spot Programming

For your best learning experience, please use the [Quickstart Guide](../../../docs/python/quickstart.md)
found in the SDK's docs/python directory. That will help you get your Python programming environment set up properly.

## Common Problems

1. Use the keyboard interface to release the e-stop [SPACE] and power [P] the robot before sending hand commands. No need launch a separate software e-stop.
2. Make sure the Motor Enable button on the Spot rear panel is depressed.
3. Make sure Spot is sitting upright, with the battery compartment on the side closest the floor.

## Setup Dependencies

This example requires the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Running the Example

```
python3 arm_wasd.py ROBOT_IP
```

When run, this example will create an interface in your terminal listing the controls which are as follows:

| Button | Functionality            |
| ------ | ------------------------ |
| wasd   | Radial/Azimuthal Control |
| rf     | Up/Down Control          |
| uo     | X-axis Rotation Control  |
| ik     | Y-axis Rotation Control  |
| jl     | Z-axis Rotation Control  |
| nm     | Open/Close gripper       |
| y      | Unstow Arm               |
| h      | Stow Arm                 |
| q      | Stand                    |
| e      | Sit                      |
| x      | Return/Acquire Lease     |
| SPACE  | E-Stop                   |
| P      | Motor power & Control    |
| Tab    | Exit                     |
