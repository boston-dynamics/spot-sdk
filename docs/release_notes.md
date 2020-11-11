<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

<p class="github-only">
<b>The Spot SDK documentation is best viewed via our developer site at <a href="https://dev.bostondynamics.com">dev.bostondynamics.com</a>. </b>
</p>

# Spot Release Notes

## 2.1.0

### New Features

#### Spot I/O: [Data Acquisition](concepts/data_acquisition_overview.md)
This release features a new system for acquiring, storing, and retrieving sensor data. It comprises several new services and their associated clients.

**Data Acquisition Service**: The coordinating service that will capture images, robot metadata, and delegate to plugins to capture custom sensor data.

**[Data Acquisition Plugins](concepts/writing_services_for_data_acquisition.md)**: User-implemented services that can capture data from sensors and save it into the store.

**Data Acquisition Store**: Interface for saving data and metadata to disk for later retrieval.

**[Image services](concepts/writing_services_for_data_acquisition.md)**: Existing interface used in a new way. User-implemented image services will now be displayed in the tablet for driving, and be automatically capturable by the Data Acquisition Service.

#### New Mobility Commands
**Stance**: Allows precise placement of the feet of the robot, beyond just positioning the body.

**Battery change pose**: Rolls Spot over so that the battery is accessible removal and replacement.

#### Arm Control Preparation
Several changes have been made in preparation for the release of Spot’s arm. These represent new ways to accomplish the same control as before, but in a way that will be compatible with also controlling the robot’s arm in a future release.

**Synchronized commands and feedback**: A new synchronized_command for combining mobility control with arm and gripper control. This deprecates the mobility_command in the `RobotCommand` message. Additionally, the top-level command status has been moved into the individual full-body and mobility command feedback messages so that mobility and arm commands can individually report their state.

**Stop**: The existing full-body `Stop` command still exists, but there is an additional mobility-only `Stop` command that can be used to only stop the mobility without affecting any separate arm control.

#### [Service Faults](concepts/faults.md)
To simplify the development of reliable services and report when problems arise, a new set of reportable faults has been added, usable by all services.

**Fault Service**: Used to report or clear faults pertaining to a service or payload. The Python SDK includes a client library for triggering and clearing faults through this service.

**ServiceFaultState in RobotState**: All reported service faults will be included in the `RobotState` message. Clearing active faults will move them into historical faults. All service faults will automatically be displayed in the tablet interface to inform users.

**Directory and Payload Liveness faults**: New options for directory and payload registration enable liveness monitoring. When this feature is implemented, alongside directory or payload keep alives, service faults will be automatically raised when a service crashes or a payload disconnects.

**Integrations**: Boston Dynamics supported payloads incorporate service faults and liveness monitoring out of the box.
Spot CORE will report service faults if it experiences issues during startup, fails to communicate with the robot, detects an invalid payload configuration, or fails to communicate to an expected LiDAR.
Spot CAM will report service faults if it is disconnected from Spot or if any of its internal services crash.
The `bosdyn.client` command line interface can show and monitor reported faults.

#### Data Logging
The robot now dedicates some internal storage space to user data and logging. In addition to the data acquisition system, the user can store messages, events, time-series data, or arbitrary binary blobs.

**Data Buffer**: New service interface for storing various kinds of data onto the robot.

**Data Service**: Retrieval service that can be return the data stored to the data buffer

**BDDF**: File format for large downloads of stored data, and tools for reading the file.

**Download endpoints**: HTTPS download of a zip file of data acquisition mission datasets or bddf-encoded data.

#### Point Clouds
Point cloud service definitions are provided for retrieving point cloud data from LiDAR sensors, such as from the EAP payload.

#### Spot Cam
Congestion control now available for WebRTC streaming.
External microphones supported, with control for selecting microphones and setting gain levels individually.

#### Graph Nav
The localization data now includes a transform to a "seed" frame, providing a consistent global frame for use across multiple runs on the same map.

Localization data can be requested relative to a particular waypoint, rather than only the waypoint that the robot is currently localized to.

Additional control for whether the robot will navigate through areas with poor quality features.

#### Missions
Added nodes to support new functionality
* Point the SpotCAM PTZ to a specified orientation.
* Dock the robot at a charging station.
* Capture data through the data acquisition functionality.
* Manipulate strings in the blackboard.

#### Choreography (License-dependent)
Play advanced choreographed routines for Spot. The choreography service requires a special license to use.

#### Docking (Beta, License-dependent)
The new Docking Service provides a way to autonomously dock at a charging station. It is currently in beta, and requires a special license to use.


### Bug Fixes and Improvements
**Graph Nav**
* Added fiducial-related status errors in `SetLocalizationResponse`, such as a fiducial being too far away or having poor data.
* Edges now record mobility params that were set during record time, and use them when navigating those edges.
* “Stuck” detection has changed, and the robot will report much sooner when it has no way to make progress.
* Improved `StartRecordingResponse` and `CreateWaypointResponse` to report errors about bad fiducials or point cloud data.

**Fiducial Detection**
* Fiducials now report a filtered pose in addition to the raw detected pose, to avoid jitter in individual detections.
* Fiducial detections include extra information, such as the detection covariance, camera frame, and status regarding ambiguity or error.

**Mission Nodes**
* The `BosdynGraphNavState` node can specify the id of the waypoint to use for the reported localization.

**Spot Check**
* Added status field in `SpotCheckCommandResponse`
* Improved the list of errors in `SpotCheckFeedbackResponse` message
* Spot Check now checks and reports results on hip range of motion

**Python client**
* Blocking “power on” and “power off” helpers report errors correctly, rather than always raising `CommandTimedOutError` if the robot could not power on or off.
* Added helper classes for registering and launching services.
* Added the ability to authenticate the robot instance from payload credentials.
* Printing the Spot sdk exceptions now provides more information.
* Increased default message size limit for receiving and sending messages to 100 MB
* Command line interface supports the new 2.1 functionality
    - Payload commands.
    - Payload registration commands.
    - Fault commands.
    - Data buffer commands.
    - Data service commands.
    - Data acquisition commands.

**Image capture parameters**
* Added exposure and gain parameters associated with an image capture.

**License interface**
* Added `GetFeatureEnabled()` to the `LicenseService` to query for particular license features.

### Breaking changes
**Robot Control**
A behavior fault (`CAUSE_LEASE_TIMEOUT`) is raised when the usage of a lease times out, and must be cleared before the robot can be commanded again.  This should have minimal effect on current clients, as this happens near the same time that the robot powers off from comms loss (which clears behavior faults).

**Graph Nav**
When GraphNav reports `STATUS_STUCK` while navigating, the robot will stop walking. It will need to be re-commanded to navigate in order to continue. Previous behavior was that the robot would continue walking when stuck until commanded to stop by a client.

**Missions**
Autowalk mission callback nodes only wait 10 seconds for a response.  When a mission calls `Tick()` on a mission callback service, it expects a quick response. In 2.0 it would wait up to 60 seconds for a response before retrying. This has been reduced to 10 seconds in version 2.1. Callbacks that do any significant work should be written to return with `STATUS_RUNNING` quickly, and then continue to do their work on another thread rather than trying to fit in all of their work before returning a response. The service can then base their response to subsequent `Tick()` requests on the status of that thread.


### Known Issues

**When a network transport failure occurs,** depending on the particular operating system and version of gRPC installed, the error from the python SDK may not always be the most specific error possible, such as `UnknownDnsNameError`.  It may instead be raised as either a generic `RpcError`, or another generic failure type such as `UnableToConnectToRobotError`.

**SpotCAM LED illumination levels** are not currently recorded or played back in Autowalk missions.

**When capturing both a PTZ and Panoramic image** in the same action, there may occasionally be two PTZ images captures along with the Panoramic image, rather than just one.

**If you write a custom data acquisition plugin or image service,** do not change its `DataAcquisitionCapability` or `ImageSource` set once it is running and registered. New capabilities may not be detected, and old capababilities may still be listed as available in the Data Acquisition service.  To change the capabilities of a service: unregister it from the directory, wait until its capabilities are no longer listed in the Data Acquisition service, and then re-register it. This waiting also applies to restarting a service if its capabilities will be different upon restart.

**If you write a custom data acquisition plugin without using our helper class,** its `GetStatus()` rpc is expected to complete immediately. If it takes too long to complete it can cause timeouts when requesting `GetStatus()` of the data acquisition service.

**If you configure the estop service with custom timeouts** and set an invalid timeout, you will not receive an error, but the robot will set the timeout to something else. The maximum estop timeout is 60 seconds, and the maximum estop cut_power_timeout is 65 seconds.

**If you register a new service with the robot**, calling `robot.ensure_client()` to create a client for that service may result in a `UnregisteredServiceNameError`.

  * Workaround: call `robot.sync_with_directory()` before `robot.ensure_client()`

**SE2VelocityLimits require care**.  Correct usage of the `SE2VelocityLimit` message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

### Deprecations
The following services, fields, and functions will continue to work, but will be removed in a future version.

#### Services
The `LogAnnotationService` is replaced with the `DataBufferService`, which allows user access to the logged data.

#### Protobuf changes
Mobility commands have been moved from `RobotCommand`, and into `SynchronizedCommand` within `RobotCommand`. When changing clients to use `SynchronizedCommand`, be aware that the feedback will be in the new `SynchronizedCommand` feedback. The top-level command status is also deprecated in favor of a status within individual feedback messages. Changing clients to use the new `SynchronizedCommand` will make them compatible with arm commands in a future release.

The representation of `SE3Covariance` has changed to a matrix. The individual element representation is deprecated.

In the map edge annotations, the `ground_mu_hint` and `grated_floor` fields have moved into the `mobility_params` message.

#### Client changes
The helper functions in RobotCommandBuilder have new versions that use the new SynchronizedCommand.

`sit_command()` → `synchro_sit_command()`

`stand_command()` → `synchro_stand_command()`

`velocity_command()` → `synchro_velocity_command()`

`trajectory_command()` → `synchro_se2_trajectory_point_command()`

The non-synchro versions are deprecated, and will be removed at the time that the mobility commands are removed from RobotCommand.

### Sample Code

#### New
[**Data acquisition (new)**](../python/examples/data_acquisition_service/README.md)
* Example data acquisition plugin implementations.
* Examples for capturing and downloading data.
* Test program to validate a data acquisition plugin.

[**Comms Test (new)**](../python/examples/comms_test/README.md)
Demonstrates how to use the SDK to perform comms testing.

[**Data Service (new)**](../python/examples/data_service/README.md)
Get comments and data index information from the robot.

[**Ricoh theta image service (new)**](../python/examples/ricoh_theta/README.md)
Create a standard Boston Dynamics API image service that communicates with the Ricoh Theta camera.

[**Service faults (new)**](../python/examples/service_faults/README.md)
Demonstrates raising service faults, clearing service faults, and implementation of directory liveness checks.

[**Spot detect and follow (new)**](../python/examples/spot_detect_and_follow/README.md)
Collects images from the two front Spot cameras and performs object detection on a specified class

[**Stance (new)**](../python/examples/stance/README.md)
Exercises the stance function to reposition the robots feet.

[**Upload choreographed sequence (new)**](../python/examples/upload_choreographed_sequence/README.md)
Shows how to use the Choreography service to upload an existing choreographed sequence to the robot, and have the robot execute that uploaded routine.

[**Velodyne client (new)**](../python/examples/velodyne_client/README.md)
Demonstrates how to use the Velodyne service to query for point clouds.

[**Web cam image service (new)**](../python/examples/web_cam_image_service/README.md)
Implements the standard Boston Dynamics API image service and communicates to common web cameras using OpenCV.

[**World object with image coords (new)**](../python/examples/world_object_with_image_coordinates/README.md)
Demonstrates adding a world object that exists only in image coordinates, rather than having a full transform.

#### Updated
[**Fiducial follow (updated)**](../python/examples/fiducial_follow/README.md)
* Uses synchro commands

[**Frame trajectory command (updated)**](../python/examples/frame_trajectory_command/README.md)
* Uses synchro commands

[**Get image (updated)**](../python/examples/get_image/README.md)
* Added an option to auto-rotate images to be rightside-up.
* Added an option to retrieve images from user image services.
* Added support for more pixel formats.

[**GraphNav command-line (updated)**](../python/examples/graph_nav_command_line/README.md)
* Waypoints can be specified by either short codes or waypoint names.
* Waypoints sorted by creation time.

[**Hello spot (updated)**](../python/examples/hello_spot/README.md)
* Uses synchro commands

[**Logging (updated)**](../python/examples/logging/README.md)
* Switched to use Data Buffer for logging instead of the deprecated
`LogAnnotationService`.

[**Mission question answerer (updated)**](../python/examples/mission_question_answerer/README.md)
* Updated to prompt the user on the command line for an answer.

[**Mission recorder (updated)**](../python/examples/mission_recorder/README.md)
* Added support for navigating through feature-poor areas.

[**Payload (updated)**](../python/examples/payloads/README.md)
* Uses the new payload keep-alive.

[**Remote mission service (updated)**](../python/examples/remote_mission_service/README.md)
* Separated example_servicers.py into separate hello_world_mission_service.py and power_off_mission_service.py

[**Replay mission (updated)**](../python/examples/replay_mission/README.md)
* Added an option to skip the initial localization.

[**Self Registration (updated)**](../python/examples/self_registration/README.md)
* Uses new helpers for registration.

[**Spot CAM (updated)**](../python/examples/spot_cam/README.md)
* New option to delete all images from the USB drive.
* Support for the IR camera.

[**Spot light (updated)**](../python/examples/spot_light/README.md)
* Uses synchro commands

[**Wasd (updated)**](../python/examples/wasd/README.md)
* Uses synchro commands
* Supports battery change pose

[**Xbox controller (updated)**](../python/examples/xbox_controller/README.md)
* Uses synchro commands
* Supports battery change pose

#### Removed

**Ricoh Theta remote mission service (removed)**
* This has been removed and replaced with the Ricoh Theta image service, which provides better integration for displaying and capturing data.

**get_depth_plus_visual_image (removed)**
* Example removed because all robot cameras include `depth_in_visual_frame` sources by default.

**Spot check (removed)**
* Users can run Spot Check from the tablet.


## 2.0.2

### New Features

### Bug Fixes and Improvements

#### Power Command Exceptions
  * Power Client detects errors during a power command right away and propagates them up to the application before the command timeout is reached.

### Known Issues
Release 2.0.2 contains the same issues as release 2.0.1, listed below.

**If you delete an object from the world object service**, there is a chance that a ListWorldObjects call immediately afterwards may still include that object.

  * Workaround: wait a short time before expecting the object to be gone.

**If you register a new service with the robot**, calling robot.ensure_client to create a client for that service may result in a UnregisteredServiceNameError.

  * Workaround: call robot.sync_with_directory() before robot.ensure_client()

**SE2VelocityLimits require care**.  The proto comment states that "if set, limits the min/max velocity," implying that one should not set values for any directions one does not want limited. However, if any of the numeric fields are not set in the message, they will be interpreted as 0. For example, if angular is not set but linear is, then the message will be incorrectly interpreted as having an angular limit of 0 and the robot will fail to rotate (obviously not the intent). Similarly, if the user only sets say the 'x' field of linear, then 'y' will be incorrectly limited to 0 as well.

  * Workaround: Correct usage of the SE2VelocityLimit message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

**LogAnnotationClient does not include async versions** of its rpcs.

  * Workaround: If you need to call these in an async manner, call them on a separate thread.

## 2.0.1

### New Features

#### License Changes

App tokens are no longer required to authorize applications. Instead, each robot itself will be licensed itself. From a programming perspective, this means that it is no longer necessary to load app tokens into the sdk object, or to fill them out in GetAuthTokenRequest.

If a client attempts to call a function for which the robot is not licensed, the robot will respond with an error related to the license issue.  The PowerService and GraphNavService responses now include new error codes for license errors on certain actions.

There is a new LicenseClient which can be used to query the license information for a robot. License information can also be queried from the bosdyn.client command line utility.

### Bug Fixes and Improvements

#### Behavior Faults
  * The robot previously accepted new commands when there were behavior faults, but did not execute them and would not provide feedback on them. The robot will now reject them with the new status `STATUS_BEHAVIOR_FAULT`.
  * The python SDK will throw the exception `BehaviorFaultError`. 2.0.0 clients will throw a `ResponseError` in these cases.

#### Map Recording
  * If the fiducials are not visible, the action will fail with `STATUS_MISSING_FIDUCIALS`. When starting recording or creating a manual waypoint in the GraphNavRecordingService, the client can require certain fiducials to be visible.  If the fiducials are not visible, the action will fail with `STATUS_MISSING_FIDUCIALS`.
  * When recording a map, grated floor mode and ground friction hints that are set in the recording environment are now correctly recorded into the map and used during playback.

#### SpotCam
  * Added an option to the SpotCam MediaLogService to retrieve the raw (unstitched) images for a log point.

#### Payload Integration
  * When a payload is authorized, it is given full access to the services on the robot, rather than a limited set. For example, a payload could now operate Spot.

#### Additional Fixes
  * Removed some obsolete or internal protobuf messages and service RPCs which were not in use in the SDK.
  * Fixed an issue where the SDK would continuously try to request new tokens if it lost connection to the robot at the time when it tried to renew its current user token.

### Known Issues
Release 2.0.1 contains the same issues as release 2.0.0, listed below.

**If you delete an object from the world object service**, there is a chance that a ListWorldObjects call immediately afterwards may still include that object.

  * Workaround: wait a short time before expecting the object to be gone.

**If you register a new service with the robot**, calling robot.ensure_client to create a client for that service may result in a UnregisteredServiceNameError.

  * Workaround: call robot.sync_with_directory() before robot.ensure_client()

**SE2VelocityLimits require care**.  The proto comment states that "if set, limits the min/max velocity," implying that one should not set values for any directions one does not want limited. However, if any of the numeric fields are not set in the message, they will be interpreted as 0. For example, if angular is not set but linear is, then the message will be incorrectly interpreted as having an angular limit of 0 and the robot will fail to rotate (obviously not the intent). Similarly, if the user only sets say the 'x' field of linear, then 'y' will be incorrectly limited to 0 as well.

  * Workaround: Correct usage of the SE2VelocityLimit message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

**LogAnnotationClient does not include async versions** of its rpcs.

  * Workaround: If you need to call these in an async manner, call them on a separate thread.

### Sample Code

[**Ricoh Theta (new)**](../python/examples/ricoh_theta/README.md)
  * Example that utilizes the 360-degree Ricoh Theta camera during an Autowalk mission.

[**Cloud Upload (new)**](../python/examples/cloud_upload/README.md)
  * Example that shows how to upload a file to a Google Cloud Platform (GCP) bucket or an Amazon Web Services (AWS) S3 bucket.

[**WASD**](../python/examples/wasd/README.md)
  * Updated to account for the additional state metrics that are reported.  Older versions of this example may fail when connecting to updated robots.

[**Spot Cam**](../python/examples/spot_cam/README.md)
  * Added support for viewing the WebRTC stream.

[**Replay Mission**](../python/examples/replay_mission/README.md)
  * The example script does not localize itself to any map, but assumes the robot is already localized or that the mission has a localization node in it.
  * It verifies that an estop is properly connected before trying to run the mission.
  * It contains an additional --timeout parameter that can be used to set an overall time limit on mission execution.

[**Mission Recorder**](../python/examples/mission_recorder/README.md)
  * Can add relocalization nodes to a mission.

[**Fiducial Follow**](../python/examples/fiducial_follow/README.md)
  * Fixed a UI crash on MacOS X.


## 2.0.0

### New Features

#### Autonomous Navigation APIs

The APIs used by Autowalk are now accessible to developers.

  * [Overall conceptual documents](concepts/README.md)
  * **GraphNavService**: Upload and download maps of the environment, update localizations to that map, and command the robot to autonomously navigate to a location in the map.  Example usage can be found in `graph_nav_command_line.py`.  Examples of interpreting the map data can be found in `graph_nav_view_map.py`
  * **GraphNavRecordingService**: Record maps while the robot walks around. Example usage found in `recording_command_line.py`
  * **MissionService**: Load and play autonomous missions.  Example mission creation is shown in `mission_recorder.py` with upload and playback usage shown in `replay_mission.py`
  * **RemoteMissionService**: A new method for handling mission callbacks, where the mission can trigger user code via an rpc.  For building your own callbacks, see the examples in remote_mission_service.

#### Spot CAM API

Control and query all hardware features of the Spot CAM.  For examples of using each service, see the [Spot CAM command line example](../python/examples/spot_cam/README.md).

  * **CompositorService** and **StreamQualityService**: change the layout and quality of the webrtc stream.
  * **PtzService**: Direct PTZ cameras to desired poses.
  * **LightingService**: Control the individual brightness of the illuminator LEDs.
  * **MediaLogService**: Save and retrieve high-resolution images to and from the internal USB drive for later processing.
  * **AudioService**: Upload and play sounds over the SpotCAM speakers.
  * **NetworkService**: Adjust networking settings.
  * **HealthService**, **VersionService**, **PowerService**: Query the status of the hardware and software, and power components on and off.

#### Payload API integration

[Payloads with a compute component can self-register with Spot and API services](payload/configuring_payload_software.md)

  * **DirectoryRegistrationService**: Allows end users to register new gRPC services running on a payload into the robots service directory.  This allows for communicating through the robot’s proxy to the service from off-robot, and for registering mission callbacks for integrations with Autowalk missions.  See `directory_modification.py` for example usage.
  * **PayloadRegistrationService**: Payloads can now register themselves with the robot, providing their properties and awaiting authorization from a robot administrator.  See the self_registration and payloads examples for how to register your own payload.


#### Environmental APIs

Learn more about how Spot is perceiving the world around it.
  * **WorldObjectService**: Request details of any objects that has been detected in the world, and add your own detections.  Example usage can be found in `mutate_world_objects.py`, `fiducial_follow.py`, and `add_image_coordinates.py`.
  * **LocalGridService**: Request maps of the area around the robot, including terrain height and obstacle classification.  Example usage shown by the bosdyn.client command line utility and the `basic_streaming_visualizer.py` example.
  * **depth_in_visual_frame** image sources. These depth map images have the same dimension, extrinsics, and intrinsics as the grayscale image sources, which can help with pixel-depth correspondence issues.

### Bug Fixes and Improvements

#### Expanded and improved documentation

  * Python QuickStart has been revamped to streamline getting up and running on the SDK.
  * Conceptual documentation has been added to explain key ideas on how to develop for Spot.
  * Payload developers guide has been added.
  * Generated documents of the API protocol have also been added.

#### Improved performance over poor communication links

  * Reduced API request overhead by several hundred bytes/request.
  * TimeSync estimator more resilient to outlier latencies and temporary network outages.

#### Additional robot state is exposed

  * PowerState: Overall charge percentage and estimated runtime.
  * KinematicState: Body velocities are now available in KinematicState.
  * RobotState: Foot contact state (in contact vs. not in contact).

#### Clients can specify additional advanced locomotion options

  * Can now disable various low-level locomotion defaults for special situations and terrain (stair tracking, pitch limiting, cliff avoidance).
  * Body rotation can be specified as an offset to nominal or to horizontal.

#### Consistent Frame usage across API

  *  See more details in the Breaking Changes section.

#### bosdyn.client command line tool improvements

  * Downloading of depth images supported. Depth maps will be written to PGM files.
  * Directory listing has improved formatting.

### Breaking changes

Version 2.0 contains several breaking changes.  While some clients and programs written for the version 1.* SDK may still work, expect some updates to be necessary for most programs.

#### Frame handling

[Documentation of frames on Spot](concepts/geometry_and_frames.md):

* Documentation of frames on Spot ([link](concepts/geometry_and_frames.md)):
* The Frame message (`geometry.proto`) and FrameType have been deprecated, and the frame is now described as a string throughout the API.
* When receiving data from the robot (robot state, images, grid maps, world objects, etc.), the data will come with a string describing the frame it is represented in, but also a FrameTreeSnapshot message which describes how to transform the data into other frames.
* Use the helpers in `frame_helpers.py` (in particular `get_a_tform_b`) to compute appropriate transforms for your use case.  See `frame_trajectory_command.py` for an example of using transforms to command the robot.
* Code written for version 1 will need to update to the following new convention:


| Version 1 frame enum | Version 2 frame string | frame_helpers.py constant |
|----------------------|------------------------|---------------------------|
| FRAME_KO             | “odom”                 | ODOM_FRAME_NAME           |
| FRAME_VO             | “vision”               | VISION_FRAME_NAME         |
| FRAME_BODY           | “body”                 | BODY_FRAME_NAME           |


#### New Exceptions

New RpcError exceptions can be raised during rpc calls. If you were already catching RpcErrors, you will catch these.  If you were catching individual subclasses, be aware of these new ones.

  * PermissionDeniedError
  * ResponseTooLargeError
  * NotFoundError
  * TransientFailureError

There are some new exceptions that can be thrown due to errors with the request before any rpc is made.  They generally indicate programmer error, so depending on your use case it may be acceptable to not catch them to find bugs in your program.  If it is important to catch all exceptions, be aware that these exist, and all inherit from bosdyn.client.Error

  * TimeSyncRequired
  * NoSuchLease
  * LeaseNotOwnedByWallet

When creating clients or channels from a Robot object, a new class of exceptions inheriting from RobotError may be raised.  NonexistentAuthorityError is no longer thrown, but other RpcErrors may be raised.

  * UnregisteredServiceError
  * UnregisteredServiceNameError
  * UnregisteredServiceTypeError

Robot command client will throw a new error if a frame is specified that the robot does not recognize.

  * UnknownFrameError

#### Moved or Renamed

* Trajectories must now specify the frame name in the parent message instead of the trajectory itself.
* Trajectory commands can no longer be specified in a body frame since the output behavior can be ambiguous.
* Robot command messages were split into different proto files (basic_command, full_body_command), which will change import/include paths.
* ‘vel’ field in SE3TrajectoryPoint renamed to **velocity** (`trajectory.proto`)
* Updates in `Payload.proto`
  * LabelPrefix field was changed from String to Repeated String
  * body_T_payload renamed to body_tform_payload
  * mount_T_payload renamed to mount_tform_payload

#### Removed

* All Frame messages have been replaced by frame strings where applicable.
* AddLogAnnotationResponse does not have a status field anymore, errors are encoded in the message header information
* ko_tform_body, vo_tform_body, and ground_plane_rt_ko in Kinematic state have been replaced with the transforms_snapshot.
* The SampleCommon message for image captures has been replaced by acquisition time and a FrameTreeSnapshot.

#### Miscellaneous

* bosdyn-client has added a dependency on numpy
* Autowalk missions and maps recorded with version 1.1 are not compatible with version 2.0

### Known issues

**If you delete an object from the world object service**, there is a chance that a ListWorldObjects call immediately afterwards may still include that object.

  * Workaround: wait a short time before expecting the object to be gone.

**If you register a new service with the robot**, calling robot.ensure_client to create a client for that service may result in a UnregisteredServiceNameError.

  * Workaround: call robot.sync_with_directory() before robot.ensure_client()

**SE2VelocityLimits require care**.  The proto comment states that "if set, limits the min/max velocity," implying that one should not set values for any directions one does not want limited. However, if any of the numeric fields are not set in the message, they will be interpreted as 0. For example, if angular is not set but linear is, then the message will be incorrectly interpreted as having an angular limit of 0 and the robot will fail to rotate (obviously not the intent). Similarly, if the user only sets say the 'x' field of linear, then 'y' will be incorrectly limited to 0 as well.

  * Workaround: Correct usage of the SE2VelocityLimit message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

**LogAnnotationClient does not include async versions** of its rpcs.

  * Workaround: If you need to call these in an async manner, call them on a separate thread.

### Sample Code

[**directory**](../python/examples/directory/README.md)

  * Register, update, and unregister a service.

[**payloads**](../python/examples/payloads/README.md)

  * Renamed from `get_payload`.
  * Expanded to show payload version handling.

[**self_registration**](../python/examples/self_registration/README.md)

  * Example showing how to set up a payload that registers itself with the robot, hosts a service, and registers its service with the robot.

**add_image_coordinates_to_scene** (Renamed to **world_object_with_image_coordinates** in 2.1.0)

  * Example using the API demonstrating adding image coordinates to the world object service.

[**estop \(updated\)**](../python/examples/estop/README.md)

  * New EstopNoGui as a command-line addition to the GUI version of the E-Stop example.

**get_depth_plus_visual_image** (Removed in 2.1.0)

  * Example demonstrates how to use the new depth_in_visual_frame image sources to visualize depth in a fisheye image.

[**get_mission_state**](../python/examples/get_mission_state/README.md)

  * Example program demonstrates how to retrieve information about the state of the currently-running mission.

[**frame_trajectory_command**](../python/examples/frame_trajectory_command/README.md)

  * Example program shows how to retrieve Spot's location in both the visual and odometry frames. Using these frames, the program shows how to build and execute a command to move Spot to that location plus 1.0 in the x axis.

[**get_robot_state_async**](../python/examples/get_robot_state_async/README.md)

  * Example demonstrates 3 different methods for working with Spot asynchronous functions.

[**get_world_objects**](../python/examples/get_world_objects/README.md)

  * Example demonstrate how to use the world object service to list the objects Spot can detect, and filter these lists for specific objects or objects after a certain time stamp.

[**graph_nav_command_line**](../python/examples/graph_nav_command_line/README.md)

  * Command line interface for graph nav with options to download/upload a map and to navigate a map.

[**graph_nav_view_map**](../python/examples/graph_nav_view_map/README.md)

  * Example shows how to load and view a graph nav map.

[**mission_recorder**](../python/examples/mission_recorder/README.md)

  * Example with an interface for operating Spot with your keyboard, recording a mission, and saving it.

[**remote_mission_service**](../python/examples/remote_mission_service/README.md)

  * Run a gRPC server that implements the RemoteMissionService service definition.
  * Connect a RemoteClient directly to that server.
  * Build a mission that talks to that server.

[**replay_mission**](../python/examples/replay_mission/README.md)

  * Example on how to replay a mission via the API.

[**spot_cam**](../python/examples/spot_cam/README.md)

  * Examples to demonstrate how to interact with the Spot CAM.

[**visualizer**](../python/examples/visualizer/README.md)

  * Example to visualize Spot's perception scene in a consistent coordinate frame.

[**world_object_mutations**](../python/examples/world_object_mutations/README.md)

  * Examples to demonstrate how to use the world object service to add, change, and delete world objects.

[**xbox_controller** \(updated\)](../python/examples/xbox_controller/README.md)

  * Added support for Windows driver.

## 1.1.2

### New features

* **Missions API Beta and Callbacks** When an Autowalk Mission is created with a "Callback" event, a client can detect that change using a beta version of the Mission API, then tell the robot to continue or abort the Mission. Example uses include a sensor payload that detects Callback events and captures sensor information before advancing the mission, and a desktop UI which waits for the user to push a button before advancing the mission.

* **External Forces Beta**. Mobility commands can specify how to handle external forces. Examples of external forces could include an object that Spot is towing, or an object Spot is pushing. The default behavior is to do nothing, but clients can specify whether Spot should estimate external forces and compensate for it, or explicitly specify what the external forces are.

### Bug fixes and improvements

* **Depth image** extrinsics are fixed. In earlier 1.1.x releases, the extrinsics were incorrectly the same as the fisheye cameras.

* **App Token expiration logging.**. The Python SDK object logs if the app token will expire in the next 30 days. New tokens can be requested at support@bostondynamics.com.

### Sample Code

* **mission_question_answerer** demonstrates how to build a client which responds to Mission Callbacks.


## 1.1.1
1.1.1 has no SDK-related changes.


## 1.1.0
The 1.1.0 SDK software is published under a new software license which can be found in the LICENSE file at the top of the SDK directory.

### New features

* **ImageService** exposes depth maps from on-board stereo cameras as additional image sources. Image Sources specify an ImageType to differentiate depth maps from grayscale images.

* **PayloadService** is a new service which lists all known payloads on the robot.

* **SpotCheckService** is a new service which runs actuator and camera calibration.

* **E-Stop soft timeouts.** In prior software release, E-Stop endpoints which stopped checking in would result in the power to the robot's motors being cut immediately. Now the E-Stop endpoint can be configured so Spot will attempt to sit followed by cutting power. The timeout parameter for an E-Stop endpoint specifies when the sitting behavior starts, and the cut_power_timeout parameter specifies when the power will cut off.

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

* Removed support for Python 2.7. Only Python 3.6+ is supported due to upcoming Python 2 End-of-Life. Windows 10, MacOS, and Ubuntu LTS are still supported.

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
