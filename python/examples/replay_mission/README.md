<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Replaying a Mission

This example shows how to replay a mission via the API. The user may pass a map directory and/or a mission file for Spot to play back.

This example assumes that Spot can see the fiducial from "Start" of your mission. To ensure the fiducial is in view, move Spot to a location where the initial fiducial is seen and verify that the fiducial has a purple overlay in the tablet camera view. You may then disconnect the tablet, engage the E-Stop on your current device, and replay the mission.

## Setup Dependencies

This example needs to be run with python3, and have the Spot SDK installed. See the requirements.txt file for a list of dependencies which can be installed with pip using the command:
```
python3 -m pip install -r requirements.txt
```

## Run the Example

To run the example:
```
python3 -m replay_mission --mission <path_to_mission> --username USER --password PASSWORD ROBOT_IP
```
