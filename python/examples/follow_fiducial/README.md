<!--
Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# API Example - Follow a Fiducial 

This example program demonstrates how to make Spot interactively walk to fiducial markers it sees with its built-in cameras.  The robot will iteratively:
  * Detects fiducials in any of Spot's cameras, choosing the fiducial nearest the robot.
  * Converts the detected fiducial from camera coordinates to the kinematic odometry coordinates (world frame)
  * Commands the robot to walk towards the fiducial and stop at the position of the fiducial in the world
  * Stream videos displaying the views of all of Spot's five cameras with the bounding boxes around the detected fiducial. To disable the image displays, set `_display_images` to False. 

## Setup Dependencies
This example uses an AprilTag library from an external repo (https://github.com/AprilRobotics/apriltag.git), please follow the instructions on the AprilTag github readme to fully setup the library (the instructions on the external github are targeted to a Linux OS). 

On Linux, follow the instructions below to build the apriltag repository correctly:
- The `make install` command of the external apriltag repo instructions will install the shared library and requires `LD_LIBRARY_PATH=/usr/local/lib` to be set.
- For running the example in a virtualenv named `venv`, copy `apriltag.cpython-36m-x86_64-linux-gnu.so` from `~/.local/lib/python3.7/site-packages/` to `venv/lib/python3.7/site-packages/`. Note that "python3.7" is a placeholder for your system's python version.

On MacOS, follow the instructions below to build the apriltag repository correctly:
- Install cmake if it is not installed.
- Run `open /Library/Developer/CommandLineTools/Packages/macOS_SDK_headers_for_macOS_10.14.pkg` to install missing `stdio.h` file. The name of the `pkg` file might be different, depending on the MacOS version.
- Clone the apriltag git repository referenced above.
- Open the CMakeLists.txt and:
  - Remove `,-rpath=lib`
  - Replace libapriltag.so with libapriltag.dylib
- Run cmake and make commands as specified in the apriltag README file
- Copy the compiled apriltag library into your python site-packages folder. For example, if you configure a virtualenv named `venv`, execute this command `cp /Users/apitester/.local/lib/python3.7/site-packages/apriltag.cpython-37m-darwin.so venv/lib/python3.7/site-packages/`
- Update the file fiducial_follow.py to specify `self._display_images = False` instead of `True`. Images are not displayed on MacOS with OpenCV.

Note, in these instructions, the filepath `/Users/apitester/.local/lib/python3.7/site-packages/` represents the folder where the apriltag github library installs by default on MacOS, and it includes "apitester" as a placeholder for your system username, and "python3.7" as a placeholder for your system's python version.

This example is not supported on Windows OS.

The remaining dependencies are listed in the requirements.txt file, and can be installed with pip.

## Running the Example
The Python implementation works only in Python 3 due to the apriltag library dependency. The attributes `_fiducial_width_mm` and `_fiducial_height_mm` must be changed to match the real-life fiducial's dimensions (in millimeters).

**Warning:** by default, obstacle avoidance is disabled. This means the robot will get very close to walls or any people holding April Tags if the tag remains stationary while the program continues to iterate. Obstacle avoidance can be re-enabled, however this prevents Spot from fully achieving the goal point (of the April Tag location).

To run the example:
`python3 -m fiducial_follow --username=user --password=password --app-token ~/.bosdyn/dev.app_token 192.168.80.3 `

To stop the robot from moving, either remove the fiducial it is following from all camera's field of view or stop the code in the command line.

### Robot Movement
If the boolean `_standup` is true, then the robot will power on and stand up, but will not walk to the fiducial. If the boolean `_movement_on` is also true, then the robot will walk towards the fiducial. The maximum speed can be adjusted by changing the values of `_max_x_speed` and `_max_y_speed`. If no speed limit is wanted, set `_limit_speed` to False. Additionally, to disable obstacle avoidance so that the robot can walk to exactly to the location of the tag, set `_avoid_obstacles` to False.

### Stopping Distance
There is a buffer to have the robot stop a fixed distance from the tag, which can be adjusted by changing `_dist_x_desired` and `_dist_y_desired`. When both are set to 0, the robot will stop exactly at its perceived location of the fiducial until another one is detected.
