<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# API Example - Answer a Mission question.

This example program demonstrates how to periodically check the robot's Mission state for a question, execute some code, then answer that question.

This is how we supported triggering off-robot code as part of Autowalk in version 1.1. For the latest example of performing callbacks in Autowalk, see the `remote_mission_service` example. For the usage of Prompt nodes, please see [Example Prompt Node Mission](#example-prompt-node-mission).

## Setup Dependencies
See the requirements.txt file for a list of python dependencies which can be installed with pip using
```
python -m pip install -r requirements.txt
```

## Start the mission_question_answerer Example
To run the example, run the command:
```
python -m mission_question_answerer --username USER --password PASSWORD ROBOT_IP
```

You may want to pass `--verbose` to the example, to see state from the robot even while the robot is not playing back a mission.

To see the effects of the `do_something` function, run this example while the robot is playing back a mission that involves a "Prompt" element.

To play an arbitrary mission, see the [replay_mission](../replay_mission/README.md) example.

## Example Prompt Node Mission

### Building an Example Prompt Node Mission
To create a mission that uses a Prompt node, run the following:
```
python -m build_mission PATH_TO_DESTINATION.txt
```

### Start the mission_question_answerer Example
```
python -m mission_question_answerer --username USER --password PASSWORD ROBOT_IP
```

### Replay the Mission
Use the `replay_mission` example to replay your saved mission from above by navigating to the `replay_mission` folder and running:
```
python -m replay_mission --mission <path_to_mission.txt> --username USER --password PASSWORD ROBOT_IP
```