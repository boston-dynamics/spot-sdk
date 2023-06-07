<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Setting Spot Arm grasp state and carry overrides

An example of setting the grasp state and carry state overrides for Spot's arm. It demonstrates how to set the gripper holding state without grasping an object, and how the arm can move depending on the grasp state and carry state.

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

Please be aware that this demo causes the robot to stand up and move its arm. Ensure there is enough clearance around the robot to run this example. There should be at least 2 meters of space around the robot.

To run the example:

```
python3 arm_grasp_carry_overrides.py ROBOT_IP
```
