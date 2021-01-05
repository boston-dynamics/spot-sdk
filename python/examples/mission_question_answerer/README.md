<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Answering a Mission Question

This example program demonstrates how to periodically check the robot's Mission state for a question, then answer that question.

## Setup Dependencies
See the requirements.txt file for a list of python dependencies which can be installed with pip using
```
python3 -m pip install -r requirements.txt
```

## Start the mission_question_answerer Example
To run the example, run the command:
```
python3 -m mission_question_answerer --username USER --password PASSWORD ROBOT_IP
```

You may want to pass `--verbose` to the example, to see state from the robot even while the robot is not playing back a mission.

Run this example while the robot is playing back a mission that involves a "Prompt" element.

To play an arbitrary mission, see the [replay_mission](../replay_mission/README.md) example.

## Example Prompt Node Mission

### Building an Example Prompt Node Mission
To create a mission that uses a Prompt node, run the following:
```
python3 -m build_mission mission-with-prompt.bin
```

### Start the mission_question_answerer Example
```
python3 -m mission_question_answerer --username USER --password PASSWORD ROBOT_IP
```

### Replay the Mission
Use the `replay_mission` example to replay your saved mission from above by navigating to the `replay_mission` folder and running:
```
python3 -m replay_mission --mission <path_to_mission_file> --username USER --password PASSWORD ROBOT_IP
```
