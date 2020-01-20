<!--
Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

API Example - Answer a Mission question.

This example program demonstrates how to periodically check the robot's Mission state for a question, execute some code, then answer that question.
This is how we support triggering off-robot code as part of Autowalk.

## Setup Dependencies
See the requirements.txt file for a list of python dependencies which can be installed with pip.

## Running the Example
To run the example:
`python -m mission_question_answerer --username=user --password=password --app-token ~/.bosdyn/dev.app_token ROBOT_IP`

You may want to pass `--verbose` to the example, to see state from the robot even while the robot is not playing back a mission.

To see the effects of the `do_something` function, run the example while the robot is playing back a mission that involves a "Callback" element.
