<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Follow a Fiducial

This example program demonstrates how to make Spot interactively walk to fiducial markers (april tags) it sees with its built-in cameras. The robot will iteratively:

- Detects fiducials in any of Spot's cameras, choosing the first fiducial detection it receives if there are multiple detections.
- Determines the go-to position based on the fiducial's location in the world.
- Commands the robot to walk towards the fiducial and repeat.

There are two modes in which this example can operate:

1. Using the world object service to detect fiducials, which are provided as a transformation in the world frame, using Spot's perception system. This mode has been added in the 1.2 software release of the spot-sdk.
2. To detect april tags in an image source using an external AprilTag library, compute the bounding box, and then transform the pixel coordinates into world coordinates.

The command line argument `--use-world-objects` will toggle between these modes. By default, this argument is set to true, so the program will use the world object service (mode 1).

## Setup Dependencies

These examples require the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

Additionally, the example requires a fiducial in Spot's range of view. This fiducial (also referenced as an april tag) must be the right size as specified in Spot's User Guide and documentation.

### External AprilTag library

If the user intends to only use fiducial detections from the world object service, then these installation instructions can be skipped.

This example uses an AprilTag library from an external repo (https://github.com/AprilRobotics/apriltag.git), please follow the instructions on the AprilTag github readme to fully set up the library (the instructions on the external github are targeted to a Linux OS).

On Linux, follow the instructions below to build the apriltag repository correctly:

- The `make install` command of the external apriltag repo instructions will install the shared library and requires `LD_LIBRARY_PATH=/usr/local/lib` to be set.
- For running the example in a virtualenv named `venv`, copy `apriltag.cpython-36m-x86_64-linux-gnu.so` from `~/.local/lib/python3.7/site-packages/` to `venv/lib/python3.7/site-packages/`. Note that "python3.7" is a placeholder for your system's python version.

This example is not supported on Windows OS if you want to use the external apriltag library. However, the example can be run using the world object service.

## Running the Example

### E-Stop Endpoint Dependency

The example depends on an external E-Stop endpoint application to configure E-Stop and cut off power to all motors in the robot, if necessary. In parallel with this example, please run the E-Stop SDK example as the E-Stop controller.

### Run Follow Fiducial Example

**Warning:** by default, obstacle avoidance is disabled so that the robot can walk to exactly to the location of the tag if necessary. This means the robot will get very close to walls or any people holding April Tags if the tag remains stationary while the program continues to iterate. Obstacle avoidance can be re-enabled, however this can prevent Spot from fully achieving the goal point (of the April Tag location).

Note: this example can only be run on Windows and Linux; Mac OS is not supported explicitly.

To run the example:

```
python3 -m fiducial_follow ROBOT_IP
```

To stop the robot from moving, either remove the fiducial it is following from all camera's field of view or stop the code in the command line.

### Robot Movement

If the boolean `_standup` is true, then the robot will power on and stand up, but will not walk to the fiducial. If the boolean `_movement_on` is also true, then the robot will walk towards the fiducial. The maximum speed can be adjusted by changing the values of `_max_x_speed` and `_max_y_speed`. By default, the robot has a speed limit of 1m/s for planar movement. To disable the speed limit, then set the command line argument `--limit-speed` to False. To enable obstacle avoidance, set the command line argument `--avoid-obstacles` to True.

### Stopping Distance

There is a buffer to have the robot stop a fixed distance from the tag. This can be set with the command line argument `--distance-margin`, which will offset the position by this distance (in meters) from the fiducial along the vector between the fiducial and the robot. When this argument is set to 0, the robot will stop exactly at its perceived location of the fiducial until another one is detected.
