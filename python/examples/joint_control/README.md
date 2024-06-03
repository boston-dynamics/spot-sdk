<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Joint Control

These examples utilize the Joint Control API that is available starting in v4.0.2 in order to move the robot. More generally, the Joint Control API allows for low-level control of the robot's joints.

## Setup Dependencies

### Software

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

### Licensing

Your robot needs to have a Joint Control license in order to run this example.

## Examples

- [Robot Squat](#armless-robot-squat)
- [Arm Wiggle](#arm-wiggle)

### Armless Robot Squat

#### Hardware

Your Spot should be a base robot with out an arm attached.

#### Run the Example

You will need to launch a software e-stop separately. The E-Stop programming example is [here](../estop/README.md).

**Safety**: this example will result in Spot moving, so please ensure the area around Spot is kept clear. The robot should not be run from a dock and should start without motors on and in a nominal sitting position on the floor.

To run the example, set BOSDYN_CLIENT_USERNAME and BOSDYN_CLIENT_PASSWORD environment variables with the robot credentials and then run:

```
python3 noarm_squat.py ROBOT_IP
```

### Arm Wiggle

#### Hardware

Your Spot needs to have an arm.

#### Run the Example

You will need to launch a software e-stop separately. The E-Stop programming example is [here](../estop/README.md).

**Safety**: this example will result in Spot moving, so please ensure the area around Spot is kept clear.

To run the example, set BOSDYN_CLIENT_USERNAME and BOSDYN_CLIENT_PASSWORD environment variables with the robot credentials and then run:

```
python3 wiggle_arm.py ROBOT_IP
```
