<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# SpotCheck Mission Service

SpotCheck is a routine by Spot to calibrate its joints and check the functionality of the robot cameras (see [here](https://support.bostondynamics.com/s/article/SpotCheck-Joint-and-Camera-Calibration-49935) for more information).

This example creates a mission service that registers SpotCheck as an action on Spot. It can then be run as an action in a mission.

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Start the Example - Locally

To run the example from your computer for local development and testing, run the following command:

```
python3 spot_check_mission_service.py --host-ip {YOUR_IP} {ROBOT_IP}
```

## Add the Action

You can now add SpotCheck as an action. Go to `Hamburger Menu` --> `Settings` --> `Actions` --> `Create New Action` --> `Empty Inspection` --> `Create`. Configure the action likeso, then press `Save`:

- Name: `SpotCheck`
- Robot Body Control: `Body Pose`
- `Remote GRPC`
  - `Spot Check Callback`

The action should now be in the red + menu when recording or piloting the robot.

## Running the example as a CORE I/O extension

### Build the extension

From this directory, run:

```
python3 ../../extensions/build_extension.py --dockerfile-paths Dockerfile --build-image-tags spot_check_rms:latest --image-archive spot_check_rms.tar.gz --icon ./extension/icon.png --package-dir ./extension/ --spx ./spot_check_rms.spx
```

### Load the extension

Go to the CORE I/O's home page at https://{ROBOT_IP}:21443. Login credentials are the same as your robot. Load the .spx file created in the build step to extension page in the console.

## Run the action

When connected to Spot via tablet or Orbit, you can now run the Spot Check Action through the red + menu under actions.
