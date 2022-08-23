<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Gripper Camera Parameter Examples

These example programs show how to get and set gripper camera parameters. Parameters do not persist across reboots.

## Understanding Spot Programming

For your best learning experience, please use the [Quickstart Guide](../../../docs/python/quickstart.md)
found in the SDK's docs/python directory. That will help you get your Python programming environment set up properly.

## Setup Dependencies

This example requires the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Run the Examples

To run the example for getting current camera parameters:

```
python3 get_gripper_camera_params.py ROBOT_IP
```

To run the example for setting camera parameters:

```
python3 set_gripper_camera_params.py ROBOT_IP --PARAMETER_FLAG PARAMETER_VALUE
```

To run the example for setting the focus region of the camera:

```
python3 set_focus_region.py ROBOT_IP
```
