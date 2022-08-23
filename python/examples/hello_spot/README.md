<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Hello Spot

This example program is the introductory programming example for Spot. It demonstrates how to initialize the SDK to talk to robot and how to command Spot to stand up, strike a pose, stand tall, sit down, and capture an image from a camera.

## Understanding Spot Programming

For your best learning experience, please use the [Quickstart Guide](../../../docs/python/quickstart.md) found in the SDK's docs/python directory. That will help you get your Python programming environment set up properly. Then, specifically for Hello Spot, you should look at the [Understanding Spot Programming](../../../docs/python/understanding_spot_programming.md) file in the same directory. This document walks you through all the commands found in this example!

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Common Problems

1. Remember, you will need to launch a software e-stop separately. The E-Stop programming example is [here](../estop/README.md).
2. Make sure the Motor Enable button on the Spot rear panel is depressed.
3. If you have a problem with Pillow/PIL, did you run the pip install with the requirements.txt as described above?
4. Make sure Spot is sitting upright, with the battery compartment on the side closest the floor.

## Run the Example

To run the example:

```
python3 hello_spot.py ROBOT_IP
```
