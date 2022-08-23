<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Responding to User Interaction via Light

This example will allow Spot to respond to a light shining in its front
left camera. The following describes what to expect:

- with the robot sitting, shine a light into the front left camera, Spot should stand up
- shine a light into the front left camera again, Spot should start tilting to follow the light
- remove the light, Spot should sit down

NOTE: Both the light detection and controller are very crude. One needs to have a very steady
hand to prevent the robot from "seeing" other bright lights in the front left camera.

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip
using the command:

```
python3 -m pip install -r requirements.txt
```

## Run the Example

To run the example:

```
python3 spot_light.py ROBOT_IP
```

### E-Stop Endpoint Dependency

The example depends on an external E-Stop endpoint application to configure E-Stop and cut off power to all motors in the robot, if necessary. In parallel with this example, please run the E-Stop SDK example as the E-Stop controller.
