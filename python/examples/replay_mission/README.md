<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Replaying a Mission

This example shows how to replay a mission via the API. The replay_mission.py script allows the user to replay Autowalk missions using graph_nav, as well as simple missions that do not use graph_nav for navigation.

This example assumes that Spot can see the fiducial from "Start" of your mission. To ensure the fiducial is in view, move Spot to a location where the initial fiducial is seen and verify that the fiducial has a purple overlay in the tablet camera view. You may then disconnect the tablet, engage the E-Stop on your current device, and replay the mission.

## Setup Dependencies

This example needs to be run with python3, and have the Spot SDK installed. See the requirements.txt file for a list of dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Run the Example

You can use replay_mission.py to replay an Autowalk mission recorded using the tablet. Attach a USB cable to the tablet and copy the Autowalk mission directory to your PC. These missions are stored under Documents/bosdyn/autowalk on the tablet.

To run an Autowalk mission:

```
python3 -m replay_mission ROBOT_IP autowalk --walk_directory WALK_DIRECTORY --walk_filename WALK_FILENAME
```

Your SDK applications can also create custom mission files as described [here](../../../docs/concepts/autonomy/missions_service.md)

See the [documentation](../mission_question_answerer/README.md) for the Mission Question Answerer for an example.

To run a simple non-Autowalk mission that does not use graph_nav for navigation:

```
python3 -m replay_mission ROBOT_IP simple CUSTOM_MISSION_FILE
```
