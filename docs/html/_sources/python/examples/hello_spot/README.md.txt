<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# API Example - Hello Spot

This example program is the introductory programming example for Spot.  It demonstrates how to initialize the SDK to talk to robot, commanding Spot to stand up, strike a pose, stand tall, sit down, and capture an image from a camera.

## Understanding Spot Programming
For your best learning experience, please use the [Quickstart Guide](../../../docs/python/quickstart.md) found in the SDK's docs/python directory.  That will help you get your Python programming environment setup properly.  Then specifically for Hello Spot, you should look at the [Understanding Spot Programming](../../../docs/python/understanding_spot_programming.md) file in the same directory, this document walks you through all the commands found in this example!

## Setup Dependencies
See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:
```
python -m pip install -r requirements.txt
```

## Common Problems
1. Remember, you will need to launch a software e-stop separately.  The E-Stop programming examples is [here](../estop/README.md).
2. Make sure the Motor Enable button on the Spot rear panel is depressed.
3. If you have a problem with Pillow/PIL, did you run the pip install with the requirements.txt as described above?

## Run the Example
To run the example:
```
python hello_spot.py --username USER --password PASSWORD --app-token=<path_to_app_token> ROBOT_IP
```
Note: The default path for app-token is ~/.bosdyn/dev.app_token. You should save your token there for ease of use.