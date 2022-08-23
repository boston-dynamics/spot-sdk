<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Frame Trajectory Commands

Spot's knowledge of different frames can be used to make issuing robot commands much simpler. This example shows how to query the robot for its current position in the visual and odom frames. It then shows how to issue a trajectory command in the visual or odom frames that describes the relative motion of the body.
Command line arguments are used to specify an offset to the current body's position, which is then commanded in odom or vision frame.

Note that trajectory commands cannot be issued in the body frame since this creates a goal point that is continually moving, so the trajectory can never reach the goal.

See [the geometry and frames documentation](../../../docs/concepts/geometry_and_frames.md) for more of an overview of Spot's frames and transformation geometry.

## E-Stop

You will have to launch a software E-Stop separately in order to run this example. See [the E-Stop examples.](../estop/README.md)

## Run the Example

To run the example (moving forward 1 meter):

```
python3 frame_trajectory_command.py ROBOT_IP --dx 1
```
