<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Arm JointMove Command

An example of commanding a JointMove with Spot's arm. The basic example initializes the SDK to talk to robot and
then requests Spot to stand before executing the JointMove trajectory. There is also a more advanced example that
shows how to send a continuous joint trajectory with many points using the API

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

## Running the basic example

To run the example:

```
python3 arm_joint_move.py ROBOT_IP
```

## Running the long trajectory example

To run the example:

```
python3 arm_joint_long_trajectory.py ROBOT_IP
```
