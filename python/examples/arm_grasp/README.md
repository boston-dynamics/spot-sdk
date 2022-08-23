<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Grasping

This example program shows using the ManipulationApiClient to request an automated grasp. It demonstrates how to
initialize the SDK to talk to robot, take and present a picture from a user specified image source, allows the
user to click the image to designate the item to pick, and request the robot to pick up the selected item. There
are command line arguments available for controlling the grasp.

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip
using the command:

```
python3 -m pip install -r requirements.txt
```

## Understanding Spot Programming

For your best learning experience, please use the [Quickstart Guide](../../../docs/python/quickstart.md)
found in the SDK's docs/python directory. That will help you get your Python programming environment set up properly.

## Common Problems

1. Remember, you will need to launch a software e-stop separately. The E-Stop programming example is [here](../estop/README.md).
2. Make sure the Motor Enable button on the Spot rear panel is depressed.
3. Make sure Spot is sitting upright, with the battery compartment on the side closest the floor.

## Run the Example

Please be aware that this demo causes the robot to walk and move its arm. Ensure there is enough
clearance around the robot to run this example. There should be at least 2 meters of space around
the item to grasp.

To run the example:

```
python3 arm_grasp.py ROBOT_IP
```
