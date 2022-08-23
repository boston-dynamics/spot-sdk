<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Constrained Manipulation

The examples here demonstrate how to use constrained manipulation
through the API. This feature is used to manipulate objects that
are constrained by the environment, and move in a low-dimensional space.
Examples include ball valves, switches, cabinets and drawers.

## Setup Dependencies

These examples need to be run with python3, and have the Spot SDK installed.

## Constrained Manipulation Example

Before running this example, we need to set up the
grasp of the object. Once the object is successfully grasped,
we can run the constrained manipulation example.

### Setup Robot and grasp and object

To properly setup for this example:

1. Use an external E-Stop endpoint from an api client or tablet
2. Power the robot on
3. Use the API or the tablet to drive the robot close to the object
   of interest, for e.g. a ball valve, cabinet, etc.
4. Grasp the object using the API scripts or the tablet
5. Run the run_constrained_manipulation.py script to manipulate
   constrained object.

### Running the Example

When run, this script will take over the lease
and perform manipulation for the task specified
in the script for a fixed duration of time.

You can construct your task type of interest by calling one of the
functions in constrained_manipulation_helper.py for e.g.
construct_crank_task(velocity_normalized)
in the run_constrained_manipulation.py script.

You can specify the task type, the velocity along the task
and the force or torque limits as arguments. Note that for
all tasks besides the knob task type, the velocity is a
normalized velocity in the range [-1, 1].
Please look in the file constrained_manipulation_helper.py
for more details on how the velocity is scaled with the force limit.

```
python3 run_constrained_manipulation.py ROBOT_IP --task-type crank  --task-velocity 0.5 --force-limit 40

```
