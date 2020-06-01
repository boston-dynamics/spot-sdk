<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# API Example - Creating a Custom User Interaction

This example will allow spot to response to a light shining in its front
left camera.  The following describes what to expect:

  - with the robot sitting, shine a light into the front left camera, spot should stand up
  - shine a light into the front left camera again, spot should start following the light
  - remove the light, spot should sit down

NOTE: Both the light detection and controller is very crude.  One needs to have a very steady
hands and prevent the robot from "seeing" other bright light in the front left camera.

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip
using the command:

```
python -m pip install -r requirements.txt
```

## Run the Example

To run the example:
```
python spot_light.py ROBOT_IP
```