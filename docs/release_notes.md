<!--
Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Boston Dynamics SDK Release Notes

## 1.1.0

The 1.1.0 SDK software is published under a new software license which can be found in the LICENSE file at the top of the SDK directory.

### New features
* **ImageService** exposes depth maps from on-board stereo cameras as additional image sources. Image Sources specify an ImageType to differentiate depth maps from grayscale images.

* **PayloadService** is a new service which lists all known payloads on the robot.

* **SpotCheckService** is a new service which runs actuator and camera calibration.

* **E-Stop soft timeouts.** In prior software release, E-Stop endpoints which stopped checking in would result in the power to the robot's motors being cut immediatly. Now the E-Stop endpoint can be configured so Spot will attempt to sit followed by cutting power. The timeout parameter for an E-Stop endpoint specifies when the sitting behavior starts, and the cut_power_timeout parameter specifies when the power will cut off.

* **TerrainParams** can be added to MobilityParams to provide hints about the terrain that Spot will walk on. The coefficient of friction of the ground can be specified. Whether the terrain is grated metal can also be specified.

* **Log Annotations** a new type of log: Blob for large binary data.

### Sample code

The sample code directory structure has changed to directory-per-example under python/examples. Each example includes a requirements.txt file for specifying dependencies.
* **estop** is a desktop GUI which creates an E-Stop endpoint for a robot. This example demonstrates how to use the E-Stop endpoint system, and is a useful utility on its own.
* **follow_fiducial** is an example where Spot will follow an AprilTag fiducial that it can see in its on-board cameras. This demonstrates how to use camera extrinsics and intrinsics to convert pixels to world coordinates, and how to use the trajectory commands.
* **get-image** is a simple example to retrieve images from Spot and save them to disk. It shows how to use the basics of the image service.
* **get-payload** is a simple example which lists all of the payloads on the robot. It shows how to use the payload service.
* **get_robot_state** is a simple example to retrieve robot state.
* **hello_spot** is carried over from prior SDK releases. It is an introductory tutorial showing basic use of the Spot SDK.
* **logging** demonstrates how to add custom annotations to Spot’s log files.
* **spot_check** demonstrates how to use SpotCheck - Spot’s in-the-field calibration behavior..
* **spot_light** is a demo where Spot rotates its body while standing to try to face a flashlight seen in its front cameras.
* **spot_tensorflow_detector** demonstrates how to integrate the Spot SDK with Tensorflow for object classification from images.
* **time_sync** is a simple example demonstrating how to use the TimeSync service.
* **wasd** is carried over from prior SDK releases. It is an interactive program which uses keyboard control for the robot, and demonstrates how to use a variety of commands.
* **xbox_controller** demonstrates how to specify more advanced options for mobility commands.

### Bug fixes and Improvements
* Too many invalid login attempts will lock a user out from being able to authenticate for a temporary period to prevent brute-force attacks. GetAuthTokenResponse indicates this state with a STATUS_TEMPORARILY_LOCKED_OUT.
* Elliptic Curve (ECDSA) cryptography used for user tokens - reducing the size of RPC requests by several hundred bytes.
* gRPC exceptions are correctly handled in Python 3.
* Command-line tool handles unicode robot nicknames correctly.
* Command-line tool supports retrieving robot model information (URDF and object files)
* Command-line tool supports retrieving multiple images at once.
* “Strict Version” support for software version.
* App Token paths which include “~” will automatically expand, rather than fail.
* Mobility Commands which have MobilityParams.vel_limit with only a min or max velocity are correctly handled. In prior releases, these commands would result in no movement at all.
* Mobility Commands which have BodyControlParams.base_offset_rt_footprint.reference_time in the past result in a STATUS_EXPIRED response rather than a STATUS_INVALID_REQUEST.
* SE2VelocityCommands with unset slew_rate_limit are correctly handled. In prior releases, an unset slew_rate_limit would result in the robot walking in place.

### Deprecations and breaking changes
* Removed support for Python 2.7. Only Python 3.6+ is supported due to upcoming Python 2 End-of-Life. Windows 10, macOS, and Ubuntu LTS are still supported.
* The HINT_PACE LocomotionHint is no longer supported due to physical stability issues. Any commands which specify a HINT_PACE LocomotionHint will be treated like a HINT_JOG LocomotionHint is specified.
* HINT_AUTO_TROT and HINT_AUTO_AMBLE are deprecated as names - use HINT_SPEED_SELECT_TROT and HINT_SPEED_SELECT_AMBLE respectively going forward.
* Protocol Buffer locations changed to split services from messages. Any direct imports of protocol buffers by client applications will need to change to support the 1.1.0 version changes.

## 1.0.1

* Improved documentation on SDK installation.
* Clearer Python dependency requirements.
* RobotId service exposes computer serial number in addition to robot serial number.
* wasd image capture works in Python 3.
* Fixed timing bugs in power service.

## 1.0.0

Initial release of the SDK.
