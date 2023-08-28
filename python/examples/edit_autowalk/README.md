<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Edit Autowalk

This example shows how to edit and replay an autowalk via the API. The edit_autowalk.py script allows the user to remove, duplicate, and reorder autowalk actions as desired. In addition, the script also loads and plays the autowalk.

This example assumes that Spot can see the fiducial from "Start" of your mission. To ensure the fiducial is in view, move Spot to a location where the initial fiducial is seen and verify that the fiducial has a purple overlay in the tablet camera view. You may then disconnect the tablet, engage the E-Stop on your current device, and replay the mission.

## Setup Dependencies

This example needs to be run with python3, and have the Spot SDK installed. See the requirements.txt file for a list of dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

Before running the example, make sure to set the e-stop either using the tablet interface or computer. Look at the e-stop Python example for more information on how to set e-stop through the command line.

## Run the Example

You can use edit_autowalk.py to edit an Autowalk mission recorded using the tablet. Attach a USB cable to the tablet and copy the Autowalk mission directory to your PC. These missions are stored under Documents/bosdyn/autowalk on the tablet.

To edit and run an Autowalk mission from the tablet:

```
python3 -m edit_autowalk ROBOT_IP --walk_directory WALK_DIRECTORY --walk_filename WALK_FILENAME
```

The editing interface will open, allowing you to drag and drop actions as desired to create a modified autowalk. Additionally, you can choose to run the Autowalk mission once, periodically, or continuously.
