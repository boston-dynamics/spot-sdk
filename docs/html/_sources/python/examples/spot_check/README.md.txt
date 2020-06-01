<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# API Example - Performing SpotCheck and Camera Calibration

This example program demonstrates how to run Spot camera calibration and SpotCheck in an API application.

Note that both routines need the estop to be released and that during the procedure the robot will stand and move autonomously. The robot can be stopped at any time with ctrl-c or the estop_gui button.

## Setup Dependencies
This example requires physical setup and space for the calibration procedures to complete successfully:
- SpotCheck: Position the robot in a sitting position on a wide open space on the ground. Note this routine will take a minute.

- CameraCalibration: Position the robot sitting on the ground, with the rear target facing the calibration target as described in the user manual. Note this routine will take ~15 minutes.

As well, these examples need to be run with python3, and have the SDK 2.0 installed. See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:
```
python -m pip install -r requirements.txt
```
The command line argument `--command` followed by one of {'spot_check', 'camera_cal'} is required to specify which calibration should be run by the example program.

## Run the Example
To run the example:
```
python spot_check.py --username USER --password PASSWORD --command {'spot_check', 'camera_cal'} ROBOT_IP
```