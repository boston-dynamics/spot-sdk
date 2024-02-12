<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Arm Freeze Hand in Body / World

This example commands Spot's end-effector to hold a pose expressed in the ODOM and BODY frames,
demonstrating the differences of holding a pose relative to and expressed in fixed versus moving frame.
Commanding the hand frame to hold position in ODOM means that even as Spot's base moves, the end-effector
will remain fixed in space. In contrast, the same pose requested in the BODY frame will cause the hand
to move in space as the body moves around since the BODY frame is moving in the world.

Requesting Spot to hold a fixed Cartesian pose expressed in BODY is equivalent to freezing the arm's
joints. This example also shows how to make a joint request freezer and demonstrates how that request is
equivalent to the Cartesian BODY referenced command.

See [the geometry and frames documentation](../../../docs/concepts/geometry_and_frames.md) for more of an overview of Spot's frames and transformation geometry.

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

## Running the example

To run the example:

```
python3 arm_freeze_hand.py ROBOT_IP
```
