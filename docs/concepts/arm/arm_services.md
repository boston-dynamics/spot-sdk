<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Arm Services

## Manipulation Service
This API provides high-level control for walking to and picking up items in the world.  The service walks the robot up to the object, not on top of it.  The idea being that you want to interact or manipulate the object. For specifying grasps, there are parameters available for
* Specifying the depth of the grasp
  * Item pressed tightly against the palm of the gripper or squeezed with just the tip of the finger.
* Constraints about the orientation of the grasp
  * "Only grasp from this direction" or "only do top down grasp"
* How much the robot is allowed to move the grasp
* Which camera source produced the image (for correcting calibration errors)

See the following examples for using this service:

[**Walk to Object:**](../../../python/examples/arm_walk_to_object/README.md)
Commands the robot to walk towards an object in preparation to grasp it. The example opens an image view and lets a user select an object by clicking it in the image.

[**Grasp:**](../../../python/examples/arm_grasp/README.md)
Shows how to autonomously grasp an object based on the object's image coordinates in pixel space. It opens an image view and lets a user select an object by clicking on the image.

## ArmSurfaceContact Service
Control the end-effector while pushing on a surface. This mode is useful for drawing, wiping, and other similar behaviors where high accuracy position moves are required while pushing down with some force.  This service is similar to the `ArmCartesianCommand` message available in the `RobotCommand` service, but is specialized for this type of task and has higher position accuracy.

See the following examples for using this service:

[**Surface Contact:**](../../../python/examples/arm_surface_contact/README.md)
Requests an end effector trajectory move while applying some force to the ground.

[**GCode:**](../../../python/examples/arm_gcode/README.md)
A [GCODE](https://en.wikipedia.org/wiki/G-code) interpreter that can be used to draw with sidewalk chalk.

## Door Service
The door service is a framework for opening doors.  We support three command types:
* **AutoGrasp**: This message requires users to specify a location to search for a door handle along with and some door parameters. Spot autonomously grabs the handle, opens the door, and walks through.
* **Warmstart**: In Warmstart, the assumption is the robot is already grasping the door handle.  The robot will skip the grasp stage of auto, and immediately begin opening the door and then traverses through the doorway.
* **AutoPush**: Used for doors that can be opened via a push without requiring a grasp. This includes pushbars, crashbars, and doors without a latching mechanism. The robot will point the hand down and push the door open with its wrist based on a push point supplied over the API.

See the following example for using this service:

[**Door Opening:**](../../../python/examples/arm_door/README.md)
This examples uses both the `ManipulationAPIService` and the `DoorService` to have Spot semi-autonomously open a door. It opens an image display and requires the user to select the door handle and the door hinge. After receiving input, it uses the `ManipulationAPIService` to estimate the handles position in 3D space and aligns the robot with the door handle. Then it uses the `DoorService` to issue an automatic door open request.
