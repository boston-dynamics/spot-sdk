<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Joint Control

This example utilizes the Joint Control API that is available starting in v4.0 in order to wiggle Spot's arm. More generally, the Joint Control API allows for low-level control of the robot's joints.

## Setup Dependencies

### Software

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

### Hardware

Your Spot needs to have an arm.

### Licensing

Your robot needs to have a Joint Control license in order to run this example.

## Run the Example

You will need to launch a software e-stop separately. The E-Stop programming example is [here](../estop/README.md).

**Safety**: this example will result in Spot moving, so please ensure the area around Spot is kept clear.

To run the example:

```
python3 wiggle_arm.py ROBOT_IP
```
