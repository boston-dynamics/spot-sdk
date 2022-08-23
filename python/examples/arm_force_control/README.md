<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Force Command

There are two force examples in this directory.

1. An example force trajectory by ramping up and down a vertical force over 10 seconds.
2. A more complex example demonstrating hybrid position-force mode and trajectories.

Both examples initialize the SDK to talk to robot and how to command Spot to stand before
executing the arm force control trajectories.

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

## Run the Examples

To run the force example:

```
python3 force_trajectory.py ROBOT_IP
```

To run the hybrid trajectory example:

```
python3 force_wrench_control.py ROBOT_IP
```
