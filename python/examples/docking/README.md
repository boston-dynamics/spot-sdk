<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Robot Docking

## Setup Dependencies

These examples need to be run with python3, and have the Spot SDK installed. See the requirements.txt file for a list of dependencies which can be installed with pip.

```
python3 -m pip install -r requirements.txt
```

## Dock My Robot Example

### Setup Robot

To properly setup for this example:

1. Have the robot powered off.
2. Use an external E-Stop endpoint from an api client or tablet.

In addition, to dock:

1. Have the robot close to the dock so it can see the fiducial, with a clear path between the robot and dock.

Or, to undock:

1. Have the robot on a dock.

### Running the Example

When run with `--dock-id`, this script will

- Power on and stand up the robot.
- Move the robot onto the dock and engage the dock.
- Will retry if the first attempt fails.
- Power Off once engaged with the dock

When run with `--undock`, this script will

- Power on the robot.
- Disengage the robot from the dock.
- Walk forward off the dock.

```
python3 dock_my_robot.py (--dock-id DOCK_ID | --undock) ROBOT_IP
```

Try not to interrupt the robot while it's over the dock, loss of comms will make the robot sit on the dock in an incorrect way, possibly causing it to roll over or make it hard to recover autonomously.
