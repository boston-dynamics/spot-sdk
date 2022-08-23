<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

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

This example will constantly monitor the robot for any running missions and any questions asked by those missions.
To run the example, run the command:

```
python3 -m mission_question_answerer ROBOT_IP
```

You may want to pass `--verbose` to the example, to see state from the robot even while the robot is not playing back a mission.

This example will only monitor the mission and answer questions. To play back a mission that includes a "Prompt" element, see the [replay_mission](../replay_mission/README.md) example, described below.

## Example Prompt Node Mission

### Building an Example Prompt Node Mission

To create a mission that uses a Prompt node, run the following:

```
python3 -m build_mission mission-with-prompt.bin
```

### Start the mission_question_answerer Example

```
python3 -m mission_question_answerer ROBOT_IP
```

### Replay the Mission

Use the `replay_mission` example to replay your saved mission from above by navigating to the `replay_mission` folder and running:

```
python3 -m replay_mission ROBOT_IP simple <path_to_mission_file>
```
