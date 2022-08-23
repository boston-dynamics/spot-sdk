<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Adjusting Robot Stance In Place

This example will exercise the stance function to reposition the robot's feet.

## Setup Dependencies

These examples need to be run with python3, and have the Spot SDK installed. See the requirements.txt file for a list of dependencies which can be installed with pip.

```
python3 -m pip install -r requirements.txt
```

## Setup Robot

To properly setup for this example:

1. Have the robot in an area with ~1m space all around
2. Have the robot powered off
3. Use an external E-Stop endpoint from an api client or tablet

## Running the Example

When run, this script will

- Leave the tablet with cut motor power authority.
- Power on and stand up the robot.

Once standing, you will see the robot reposition its feet at the current body location to the foot offsets specified in the script.

```
python3 stance_in_place.py ROBOT_IP
```

Use Ctrl-C to exit the script and sit the robot.

## Change Offset

Pass values to arguments --x-offset and --y-offset to adjust the change in stance.
