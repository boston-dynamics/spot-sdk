<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Frame Trajectory Commands

Spot's knowledge of different frames can be used to make issuing robot commands much simpler. This example shows how to query the robot for its current position in the visual and odom frames. It then shows how to issue a trajectory command in the visual or odom frames that describes the relative motion of the body. For example, it first issues a command telling Spot to walk forward one meter, but issues the trajectory described relative to the visual frame.

Note that trajectory commands cannot be issued in the body frame since this creates a goal point that is continually moving, so the trajectory can never reach the goal.


See [the geometry and frames documentation](../../../docs/concepts/geometry_and_frames.md) for more of an overview of Spot's frames and transformation geometry.


## E-Stop
You will have to launch a software E-Stop separately in order to run this example. See [the E-Stop examples.](../estop/README.md)

## Run the Example
To run the example:
```
python3 frame_trajectory_command.py --username USER --password PASSWORD ROBOT_IP
```
