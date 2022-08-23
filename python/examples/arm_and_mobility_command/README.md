<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Arm and Mobility

This example program shows sending a mobility and arm command at the same time. It demonstrates how to
initialize the SDK to talk to robot and how to command Spot to walk in a trajectory while simultaneously
moving the arm in a trajectory.

## Understanding Spot Programming

For your best learning experience, please use the [Quickstart Guide](../../../docs/python/quickstart.md)
found in the SDK's docs/python directory. That will help you get your Python programming environment set up properly.

## Common Problems

1. Remember, you will need to launch a software e-stop separately. The E-Stop programming example is [here](../estop/README.md).
2. Make sure the Motor Enable button on the Spot rear panel is depressed.
3. Make sure Spot is sitting upright, with the battery compartment on the side closest the floor.

## Setup Dependencies

This example requires the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Run the Example

Please be aware that this demo causes the robot to walk and move its arm. You have some
control over how much the robot moves (see \_L_ROBOT_SQUARE and \_L_ARM_CIRCLE) but regardless, the
robot should have at least (\_L_ROBOT_SQUARE + 3) m of space in each direction when this demo is used.
By default, \_L_ROBOT_SQUARE is 0.5, so an unmodified example should have ~3.5m space all around.

To run the example:

```
python3 arm_and_mobility_command.py ROBOT_IP
```
