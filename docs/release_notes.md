<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

<p class="github-only">
<b>The Spot SDK documentation is best viewed via our developer site at <a href="https://dev.bostondynamics.com">dev.bostondynamics.com</a>. </b>
</p>

# Spot Release Notes

## 4.0.3

### Breaking Changes

- No changes from 4.0.2

### Deprecations

- No changes from 4.0.2

### Known Issues

- No changes from 4.0.2

## 4.0.2

### Breaking Changes

- Same as 4.0.1

### New Features

#### Joint Control

The Joint Control API allows for low-level control of the robot's joints. Note that this API is experimental and license-limited; the robot must have a Joint Level Control license installed in order for this API to be used. Please see the [documentation](concepts/joint_control/README.md) for more information and [supplemental](concepts/joint_control/supplemental_data.md) robot information which may be useful for development or simulation of the robot.

### Bug Fixes and Improvements

#### Choreography

- A new field, `return_animation_names_only`, has been added to the [GetChoreographySequenceRequest](../protos/bosdyn/api/spot/choreography_sequence.proto#getchoreographysequencerequest) message. This field allows clients to save bandwidth by requesting only the animation names and not the entire animation for the specified choreography sequence. Correspondingly, a new message, `GetAnimation`, allows clients to request individual animations by name.

#### Robot State

- Two new fields, `kinematic_state` and `contact_states`, have been added to the [RobotStateStreamResponse](../protos/bosdyn/api/robot_state.proto#robotstatestreamresponse) message. The `kinematic_state` field contains information about the pose and velocity of the robot body frame in the odom and vision frames. The `contact_states` field contains information about the foot positions and contact state, on a per-foot basis, of the robot. The `GetRobotStateStream` RPC is a lightweight, streaming version of the `GetRobotState` RPC that clients who need the lowest latency possible can use (e.g., users of the Joint Control API).

#### Orbit

- The [Orbit Client](../python/bosdyn-orbit/src/bosdyn/orbit/client.py) now works on Python 3.6 and Python 3.7. Previously, it was broken on those Python versions due to an import failure. The **deprecated** [Scout Client](../python/bosdyn-orbit/src/bosdyn/orbit/client.py) had the same issue and has also been fixed.

### Deprecations

- Same as 4.0.1

### Known Issues

- Same as 4.0.1

### Spot Sample Code

#### New

- [Joint Control: Robot Squat](../python/examples/joint_control/README.md#armless-robot-squat): An example that utilizes the joint control API to move the robot for a robot without an arm attached.
- [Joint Control: Wiggle Arm](../python/examples/joint_control/README.md#arm-wiggle): An example that utilizes the joint control API to move the robot for a robot with an arm attached.

#### Updated

- [GPS Listener](../python/examples/gps_service/README.md): A bug that caused this example to crash when a GPS receiver published an NMEA message without a timestamp has been fixed. The [NMEAParser](../python/bosdyn-client/src/bosdyn/client/gps/NMEAParser.py) now ignores NMEA messages without timestamps. In addition to that, the baud rate of the GPS receiver used in conjunction with this example is now configurable via a command-line argument.

### Orbit Sample Code

#### Updated

- [Hello Webhook](../python/examples/orbit/webhook/README.md): A bug that caused this example to crash when the webhook event type was `TEST` has been fixed. The `TEST` event type is useful for debugging webhooks without having to perform an action using the robot.

## 4.0.1

### Breaking Changes

- A breaking change that was present in 4.0.0, but was unfortunately not reported, is that Network Compute Bridge workers are now required to set the status field. Previously, this was not required. One of the Network Compute Bridge examples has been updated accordingly (see [here](../python/examples/network_compute_bridge/README.md)).

### Bug Fixes and Improvements

- In Spot software versions prior to 4.0.1, the `bosdyn.client.power.power_off_robot` and `bosdyn.client.power.safe_power_off_robot` methods may not de-energize the robot. Note that the `safe_power_off_robot` method will still cause the robot’s motors to power off, but will not cause the entire robot to shut down. If your robot uses this or any integration that relies on the programmatic full shutdown, and your robot is affected by this issue, we recommend updating to 4.0.1 or later Spot software.

- [Orbit Client](../python/bosdyn-orbit/src/bosdyn/orbit/README.md) and [Scout Client](../python/bosdyn-scout/src/bosdyn/scout/README.md): For developers on Python <= 3.8, the Orbit and (deprecated) Scout clients failed to import due to the use of a feature that is only available starting in Python 3.9. This feature is no longer used.

- Examples that use the `GrpcServiceRunner` in `bosdyn.client.server_util` with the default argument `force_sigint_capture=True` no longer fail on Windows. A check for the Operating System (OS) has been added so that this does not happen.

- The diagnostics and exception handling in `bosdyn.client.area_callback_service_utils` have been improved.

- Fixed an issue where the robot would try to walk up the center of very wide staircases. Now, it stays closer to the recorded path up the staircase. The path on the stairs can be overridden by changing a new field, `traversal_y_offset`, which has been added to the [edge annotations](../protos/bosdyn/api/graph_nav/map.proto#edge) message.

### Deprecations

In addition to those listed for 4.0.0:

- GraphNav map edge annotations: `flat_ground`

### Known Issues

- Same as 4.0.0

### Sample Code

#### Updated

##### Spot

- [Tester Programs](../python/examples/tester_programs/README.md): The instructions for the tester programs that may be used to test image services and data acquisition plugins have been made more clear.

- [Fan Control](../python/examples/fan_command/README.md): Fixed flipped `response` and `request` arguments, which caused the `GetRemoteMissionServiceInfo` method to fail.

- [Network Request](../python/examples/network_request_callback/README.md): Fixed flipped `response` and `request` arguments, which caused the `GetRemoteMissionServiceInfo` method to fail.

- [Power Off Mission Service Callback](../python/examples/remote_mission_service/README.md): Fixed flipped `response` and `request` arguments, which caused the `GetRemoteMissionServiceInfo` method to fail.

- [Build Extension](../python/examples/extensions/README.md): The `build_extension.py` script now defaults to building Extensions for the ARM64 architecture now.

- [Comms Test](../python/examples/comms_test/README.md): The command to run the Docker image has been updated (previously, it was incorrect).

- [Edit Autowalk](../python/examples/edit_autowalk/README.md): The mission status is now printed regularly, as well as any mission questions as they occur.

- [Custom Parameter Image Server](../python/examples/service_customization/custom_parameter_image_server/README.md): This example now works on CORE I/O. A webcam that is compatible with CORE I/O is required (e.g., Logitech, Inc. HD Pro Webcam C920).

- [Post-Docking Callback](../python/examples/post_docking_callbacks/README.md): Fixed an issue where the example would break if a time period was supplied.

- [Spot Light](../python/examples/spot_light/README.md): A brightness threshold has been added, so that if the user does not have a light that is bright enough, they can adjust the threshold so that the robot will stand.

- [Network Compute Bridge Worker (Fire Extinguisher)](../python/examples/network_compute_bridge/fire_extinguisher_server/README.md): The instructions have been updated to demonstrate how to configure the Inspection in the tablet.

- [Network Compute Bridge Worker (TensorFlow)](../python/examples/network_compute_bridge/README.md): The `status` field in NetworkComputeResponse is now set.

##### Orbit

- <a href="orbit/docs.html">Orbit API</a>: The name of the `site_elements` endpoint has been corrected (previously `SiteElements`).

- [Orbit Send Robot Back to Dock](../python/examples/orbit/send_robot_back_to_dock/README.md): The example has been made more interactive.

## 4.0.0

### Breaking Changes

The following fields and services have been **removed**.

- `LogAnnotationService`
- Auth application token, `application_token`, and its corresponding statuses, `STATUS_INVALID_APPLICATION_TOKEN` and `STATUS_EXPIRED_APPLICATION_TOKEN`
- Robot commands: non-synchronized mobility commands. Top-level feedback messages.
- Graph Nav map edge annotations: `vel_limit`, `ground_mu_hint`, `grated_floor`
- SpotCheck feedback: `foot_height_results` and `leg_pair_results`

The mapping between voltage and GPIO pins on the CoreIO has changed as part of the Jetpack 5 update. {5: 133, 12: 19, 24: 148} is now {5: 440, 12: 320, 24: 453}. Please see the updated [CoreIO GPIO](../python/examples/core_io_gpio/README.md) example.

Network Compute Bridge workers are now required to set the status field. Previously, this was not required.

### New Features

#### Autowalk and Missions

- The focus state of the SpotCam PTZ is now configurable using `focus_state`. The tablet allows the user to configure the SpotCam PTZ focus during autowalk recording. Clients that previously were unable to use the `SpotCamAlignment` action wrapper because of issues with auto-focus may now use this action wrapper with the desired manual focus setting.

- The stow behavior of Spot's arm while Spot is navigating to its next `Target` is now configurable using `target_stow_behavior`.

- The gripper behavior of Spot's arm after Spot has executed an action is now configurable using `disable_post_action_close`.

- Support for Choreography has been added to autowalk. Please see the `MissionUploadChoreography` and `ExecuteChoreography` messages. The robot must have a choreography license in order to use this. Please see the [choreography documentation](concepts/choreography/choreographer.md) for more information.

- Support for visualization of route progress with the addition of `CompletedRoute` to the `NavigationFeedbackResponse` message.

- `Prompt` nodes now support custom paramater specification for answers, enabling prompts for any data supported by the Service Customization service. More detailed descriptions of how to specify these parameters can be found in the [service customization documentation](concepts/service_customization.md).

#### Orbit (formerly Scout)

- [**Webhooks**](./concepts/about_orbit.md#webhooks): Webhooks are a new mechanism for clients to subscribe to real-time Orbit events. In order to receive events, Webhook subscribers must register with Orbit via the settings UI or the new `/webhooks` endpoints documented as part of the <a href="orbit/docs.html">Orbit API</a>. Corresponding helper functions such as `post_webhook` are available in [bosdyn-orbit](https://pypi.org/project/bosdyn-orbit/)'s client.

- [**Scheduler**](./concepts/about_orbit.md#scheduling-missions): Alongside the new Orbit scheduler, one can also schedule missions via the new `/calendar` set of <a href="orbit/docs.html">Orbit API</a> endpoints. Corresponsing helper functions such as `post_calendar_event` and `get_calendar` are available in [bosdyn-orbit](https://pypi.org/project/bosdyn-orbit/)'s client.

#### GPS

Spot can now autonomously navigate and localize on Graph Nav maps that have been recorded while using a Global Positioning System (GPS) receiver. Note that the robot does not consume GPS data directly from GPS receivers. Instead, the GPS receiver must be connected to a payload computer (e.g., Core I/O) that is running software that receives the required information from the GPS receiver, then communicates it to the `Aggregator Service` using the `NewGpsDataRequest` RPC. Extensive documentation is available [here](concepts/autonomy/gps.md); an [example](../python/examples/gps_service/README.md) is also provided. One thing worth noting is that although the example makes use of NMEA messages, there is no reason the payload computer could not receive configure the receiver to output messages in a different format (e.g., GSOF, UBX, OEM7).

#### Robot Mobility

A new enum value, `SWING_HEIGHT_AUTO`, has been added to the `SwingHeight` enum. This setting results in the swing height being automatically adjusted based upon the current state of the robot and its surrounding environment.

A new enum, `DescentPreference`, has been added to the `StairData` message. The user may allow the robot to descend the stairs facing forwards by setting `DESCENT_PREFERENCE_PREFER_REVERSE` or `DESCENT_PREFERENCE_NONE`. This setting can be useful for allowing the robot to descend a staircase where there was not enough room to turn around after the initial descent (e.g., a catwalk).

#### Data Acquisition Live Data

This feature allows payloads to display live data on the tablet and Orbit during teleoperation. The `GetLiveData` RPC has been added to both the Data Acquisition and Data Acquisition Plugin services. Please see the [CoreIO Modem Plugin](../python/examples/data_acquisition_service/signals_coreio_modem_plugin/README.md) example. Helper functions have been added to [signal_helpers.py](../python/bosdyn-client/src/bosdyn/client/signals_helpers.py), [unit_helpers.py](../python/bosdyn-client/src/bosdyn/client/units_helpers.py), and `test_signals_helpers.py`. The [DataAcquisitionClient](../python/bosdyn-client/src/bosdyn/client/data_acquisition.py) and [DataAcquisitionPluginService](../python/bosdyn-client/src/bosdyn/client/data_acquisition_plugin_service.py) classes have been updated accordingly.

#### Data Acquisition Store

Two RPCs have been added, namely `QueryStoredCaptures` and `QueryMaxCaptureId`. `QueryStoredCaptures` is used to query the DAQ Store for stored data while `QueryMaxCaptureId` returns only the largest capture ID for the associated query. These RPCs are intended to be used instead of the `/v1/data-buffer/daq-data/` endpoint.

#### Spot Arm

- The field, `disable_velocity_limiting`, has been added to the `ArmCartesianCommand` message. Setting this field to `true` **disables** protections that prevent the arm from moving unexpectedly fast. Users must exercise extreme caution when setting this field to `true`.
- The field, `disable_safety_check`, has been added to the `ArmImpedanceCommand` message. Setting this field to `true` **disables** the cancellation of an arm trajectory for unsafe behaviors. Users must exercise extreme caution when setting this field to `true`.
- A new enum value, `STATUS_TRAJECTORY_CANCELLED`, has been added to the `Feedback` message of `ArmImpedanceCommand`. This feedback status indicates whether an arm instability was detected, and if it was detected, the command is cancelled. This new status may be useful for debugging purposes.

#### Network Compute Bridge

A new enum value, `NETWORK_COMPUTE_STATUS_ANALYSIS_FAILED`, has been added to the `NetworkComputeStatus` enum. If the Network Compute Bridge Worker fails to process the input image for some reason (e.g., it was blurry), the Worker may use this status to indicate that the action should be retried. If the action is part of an autowalk, the `retry_count` in the `FailureBehavior` message must be > 0.

#### [Service Customization](./concepts/service_customization.md)

Our [service customization helpers](../python/bosdyn-client/src/bosdyn/client/service_customization_helpers.py) now include more helper functions, including:

- Generation of specs from a set of Python-native objects as arguments. See `make_list_param_spec` for an example.
- Conversions to Python-native values for `DictParams`, `ListParams`, and `OneOfParams`. See `dict_params_to_dict` for an example.
- Generation of default parameter values from a parameter spec. See `double_spec_to_default` for an example.
- [Value coercion](./concepts/service_customization.md#parameter-coercion), which allows you to gracefully handle errors from parameter values being out of spec. See `int_param_coerce_to` for an example of this, although one is more likely to use `dict_param_coerce_to`.

#### Choreography

- Added `GetChoreographySequence` RPC to request the full sequence proto with a given name from Spot.
- Added `ChoreographyTimeAdjust` RPC to slightly modify the start time of the next `ExecuteChoreography` RPC request that will be received by the robot in the future.

#### Safety-Related Stopping Function

Added `ResetSafetyStop` RPC for Safety-Related Stopping Function (SRSF) compatible robots. Robots equipped with this feature will be listed as Safety-Related Stopping Function (SRSF) "Enabled" under the hardware information section found in the "About" page on the robot's admin console.

#### GraphNav

New [configuration options](concepts/autonomy/graphnav_area_callbacks.md#configuring-behavior-for-a-callback) have been added to Area Callbacks to specify GraphNav's behavior with respect to blockages, impairment, entities, and stopping poses for callback regions.  

### Bug Fixes and Improvements

Clients are now configured with a default 5s keep-alive time, which triggers a faster reconnect with the service, when the network connection goes down.

Lease update change: ignore failed old leases in the case the wallet contains the new lease.

A new `SystemState` message that includes the temperature data for the robot's motors has been added to the `RobotState` message. This new message is expected to expand in the future. The documentation for the `Kinematic State` message in [robot_state.proto](../protos/bosdyn/api/robot_state.proto) has been improved.

The SpotCam [CompositorClient](../python/bosdyn-client/src/bosdyn/client/spot_cam/compositor.py) now sets both the `coords` (deprecated in v3.3) and `meter` fields for backwards compability purposes in the `set_ir_meter_overlay` and `set_ir_meter_overlay_async` methods.

In the SpotCam [PtzClient](../python/bosdyn-client/src/bosdyn/client/spot_cam/ptz.py), `focus_mode` overrides `distance` in the `set_ptz_focus_state` and `set_ptz_focus_state_async` methods, so long as it is not set to `None`.

Two new helper functions have been added to the `Vec3` class in [math_helpers.py](../python/bosdyn-client/src/bosdyn/client/math_helpers.py), namely `to_numpy` and `from_numpy`. These functions may be used to convert back and forth between `Vec3` and numpy arrays.

The `get_info` method in the [Mission Client](../python/bosdyn-mission/src/bosdyn/mission/client.py) now supports very large missions which would have previously exceeded the maximum protobuf size. If the robot software version is such that the `GetInfoAsChunks` RPC is unimplemented, `get_info` falls back to the `GetInfo` RPC instead.

For non-Core I/O payloads, it is now recommended to [authenticate and register payloads](../python/examples/self_registration/README.md) by generating a payload credentials file with a unique GUID and secret. The `read_or_create_payload_credentials` and `add_payload_credentials_file_argument` [helper functions](../python/bosdyn-client/src/bosdyn/client/util.py) assist with doing this. Core I/O Extensions should continue reading the existing on-disk file, located at `/opt/payload_credentials/payload_guid_and_secret`.

GraphNav will no longer restart an Area Callback in the middle of a region if it re-routes.  It will instead call a [new Area Callback RPC](concepts/autonomy/graphnav_area_callbacks.md#handling-re-routing) to inform the callback of the change.

Published robot state messages previously contained kinematic information for a non-existant HR0 joint on Spot's arm, set to all zeros. This has been removed and the published kinematic information now only contains existing joints. The number of published joints will be one less than on releases < 4.0. Customers storing local copies of Spot URDF files may need to reacquire them from the robot after updating to 4.0.

### Deprecations

- The protos in the `bosdyn-choreography-protos` package have been moved into [bosdyn-api](https://pypi.org/project/bosdyn-api/); `bosdyn-choreography-protos` is now an empty package that just depends on `bosdyn-api`.

- The `number_of_steps` in the `Staircase` message is deprecated and replaced by the length of the `steps` field in the same message (`Staircase`).

- The `pixel_to_camera_space` method in the `ImageClient` class has been updated such that the `image_proto` argument should now be of type `image_pb2.ImageSource` (previously `image_pb2.Image`). If the method is called with an `image_proto` argument of type `image_pb2.ImageCaptureAndSource` or `image_pb2.ImageResponse`, a warning message is logged.

- **Network Compute Bridge**: The `object_in_image` in the `NetworkComputeResponse` message is deprecated and replaced by `object_in_image` in `OutputImage`

- **Autowalk**: The `root_id` in the `ElementIdentifiers` message is deprecated and replaced by `navigation_id` in the same message.

- **Mission Prompt**: The `options` list in `Prompt` message is deprecated and replaced by the wrapped `OptionsList options_list` field to support answer specification by both `OptionsList options` and `DictParam.Spec custom_params`.

- **Mission Service**: the `impl` field (type `google.protobuf.Any`) in `type` oneof

- `bosdyn.client.robot_id.create_strict_version()` uses deprecated `distutils` functionality. Use `bosdyn.client.robot_id.version_tuple()` instead.

- The kinematic_state's transforms_snapshot now uses "arm0.link_wr1" instead of "link_wr1" for the name of the frame attached to the SpotArm's wr1 link. This is (1) the name used in the URDF description of the robot and (2) the name used in the image service snapshots. We will continue to publish the kinematic_state's snapshot with the deprecated name in the 4.0 release, but it will be removed in a future release.

#### Orbit (formerly Scout)

- The package `bosdyn-scout` is deprecated and replaced with [bosdyn-orbit](https://pypi.org/project/bosdyn-orbit/), due to Scout being renamed to Orbit. As a result, the pre-existing examples in `../python/examples/scout/` are moved to `../python/examples/orbit/`. All examples use `bosdyn-orbit` instead of `bosdyn-scout`.

- The `/login` <a href="orbit/docs.html">Orbit API</a> endpoint is now deprecated. It has been functionally replaced by the `/api_token/authenticate` endpoint. This endpoint allows an admin user to generate an API Access Token with specific permissions for use against the Orbit API. A corresponding `authenticate_with_api_token` helper function in [bosdyn-orbit](https://pypi.org/project/bosdyn-orbit/)'s client has replaced 3.3's `authenticate_with_password` function.

- The `/missions` set of <a href="orbit/docs.html">Orbit API</a> endpoints are now deprecated in favor of the `/site_walks` endpoints. Corresponding helper functions such as `get_site_walks` in [bosdyn-orbit](https://pypi.org/project/bosdyn-orbit/)'s client support this.

### Known Issues

#### New in 4.0

- There are circular imports between bosdyn/api/gps/registration.proto and bosdyn/api/world_object.proto. This may break proto code generation for some languages (e.g., Go).

#### Preexisting, but undiscovered prior to 4.0

- The /v1/data-buffer/daq-data/ REST endpoint sometimes fails to return all of the requested data. Two workarounds are to (1) modify the query parameters such that a subset of data is returned or (2) use the new QueryStoredCaptures RPC.

#### Preexisting

- Same as 3.3.2.

### Sample Code

#### New

- [Arm Freeze ](../python/examples/arm_freeze/README.md): Command Spot's end-effector to hold a pose expressed in the ODOM and BODY frames,
  demonstrating the differences of holding a pose relative to and expressed in fixed versus moving frames.

- [Long Arm Cartesian Trajectory](../python/examples/arm_trajectory/README.md): Show how to follow a long cartesian trajectory with the arm.

- [Orbit Schedule Mission](../python/examples/orbit/schedule_mission/README.md): An example to show how to create, edit, and delete a mission calendar event using Orbit web API.

- [Orbit Runs Response](../python/examples/orbit/runs_response/README.md): Tutorial to show how to use the Orbit client to get runs response and process data through the Orbit web API.

- [Orbit Send Robot Back to Dock](../python/examples/orbit/send_robot_back_to_dock/README.md): An example to show how to send robot back to the dock using Orbit web API.

- [Orbit Disable/Enable Calendar Events Based on Weather](../python/examples/orbit/toggle_mission_based_on_weather/README.md): An example to show how to enable or disable calendar events based on weather using Orbit web API.

- [Orbit Webhooks](../python/examples/orbit/webhook/README.md): An example to show how to utilize webhooks using Orbit web API to obtain data.

- [SpotCam Video Recording](../python/examples/spot_cam/README.md): An example that shows how to record a video using SpotCam.

- [DAQ Plugin with Custom Parameters](../python/examples/service_customization/custom_parameters_data_acquisition/README.md): An example that shows how to use custom parameters with a DAQ plugin.

- [Reset Safety Stop](../python/examples/reset_safety_stop/README.md): An example that shows how to reset the primary and redundant safety stops on a Safety-Related Stopping Function (SRSF) configured robot. Robots equipped with this feature will be listed as SRSF "Enabled" under the hardware information section found in the "About" page on the robot's admin console.

- [Metrics Over CoreIO](../python/examples/metrics_over_coreio/README.md): An example that shows to upload metrics to Boston Dynamics via CoreIO LTE or WiFi (using a WiFi dongle).

- [View GraphNav Map in a Web Browser](../python/examples/graph_nav_view_gps/README.md): An example that shows how to view a GraphNav map on Open Street Maps in a Web Browser.

- [GPS Listener](../python/examples/gps_service/README.md): An example that shows how to consume data from a GPS receiver and send it to Spot. The example includes configurations for the Trimble SPS986 and Leica GA03 receivers, though any GPS receiver that publishes the required information could hypothetically be used (your mileage may vary based upon the receiver's performance).

- [Extract Images from Walk](../python/examples/extract_images_from_walk/README.md): An example that shows how to extract all of the record-time images embedded in a .walk and create a .pptx slideshow containing them.

- [Signals CoreIO Modem](../python/examples/data_acquisition_service/signals_coreio_modem_plugin/README.md): An example that gets modem data from the CoreIO and sends it to the robot in such a way (using the Signals API) that it is displayed on the tablet and Orbit in real-time.

- [Extensions](../python/examples/extensions/README.md): A couple of [helper scripts](./payload/docker_containers.md#helper-scripts) have been introduced to help create CORE I/O and Scout Extensions. These can even be used to package any other Dockerized example into an Extension.

#### Updated

- [Area Callbacks](../python/examples/area_callback/README.md): Updated to set the new callback configuration parameters.

- [Orbit Hello](../python/examples/orbit/hello_orbit/README.md): Updated to use `bosdyn-orbit` instead of `bosdyn-scout`.

- [Orbit Export Run Archives](../python/examples/orbit/export_run_archives/README.md): Updated to use `bosdyn-orbit` instead of `bosdyn-scout`.

- [Fan Control Mission Service](../python/examples/fan_command/README.md): FanOffServicer now implements GetRemoteMissionServiceInfo, which prevents a harmless message from being printed when the example is run.

- [GraphNav Command Line](../python/examples/graph_nav_command_line/README.md): Added support for navigating the robot to a given latitude/longitude/yaw. Some new helper functions include `_clear_graph_and_cache`, `_navigate_to_gps_coords`, `_parse_gps_goal_from_args`, and `_navigate_to_parsed_gps_coords`.

- [GraphNav View Map](../python/examples/graph_nav_command_line/README.md): Added two command-line arguments that control whether text for each waypoint and world object should be shown.

- [Arm Impedance Control](../python/examples/arm_impedance_control/README.md): Updated to use "arm0.link_wr1" instead of "link_wr1" for the name of the WR1 frame.

- [BDDF Download](../python/examples/bddf_download/README.md): Updated documentation to indicate that (at most) 1 hour of data may be requested. If the user requests more than 1 hour, an error is now bubbled up through the GUI.

- [Network Compute Bridge Worker (Fire Extinguisher)](../python/examples/network_compute_bridge/fire_extinguisher_server/README.md): The base image in Dockerfile.l4t has been updated to account for v4.0 CoreIO running on Jetpack 5.

- [Network Request Callback](../python/examples/network_request_callback/README.md): The base image in Dockerfile.coreio has been updated to account for a dependency that requires Python 3.10. NetworkRequestCallbackServicer now implements GetRemoteMissionServiceInfo, which prevents a harmless message from being printed when the example is run.

- [Post-Docking Callback (Cloud Upload)](../python/examples/post_docking_callbacks/README.md): FanOffServicer now implements GetRemoteMissionServiceInfo, which prevents a harmless message from being printed when the example is run.

- [Power Off Mission Service Callback](../python/examples/remote_mission_service/README.md): PowerOffServicer now implements GetRemoteMissionServiceInfo, which prevents a harmless message from being printed when the example is run.

- [Ricoh Theta](../python/examples/ricoh_theta/README.md): The base image in Dockerfile.l4t has been updated to account for v4.0 CoreIO running on Jetpack 5. When no password argument is supplied, the default password for the Ricoh Theta now includes only the numeric portion of the Ricoh Theta SSID (as described in the Ricoh Theta documentation).

- [Custom Parameter Image Server](../python/examples/service_customization/custom_parameter_image_server/README.md): The base image in Dockerfile.l4t has been updated to account for v4.0 CoreIO running on Jetpack 5.

- [Custom Parameter Network Compute Bridge Worker](../python/examples/service_customization/custom_parameter_ncb_worker/README.md): The base image in Dockerfile.l4t has been updated to account for v4.0 CoreIO running on Jetpack 5. Specific instructions for how to build the corresponding Spot Extension are now included.

- [Detect and Follow](../python/examples/spot_detect_and_follow/README.md): The base image in Dockerfile.l4t has been updated to account for v4.0 CoreIO running on Jetpack 5. Specific instructions for how to build the corresponding Spot Extension are now included.

- [DAQ Plugin Tester](../python/examples/tester_programs/README.md): The plugin now tests for whether the DAQ plugin is publishing live data.

- [Fetch Tutorial](python/fetch_tutorial/fetch1.md): The example has been updated such that it no longer uses the `trajectory_command` method, which has been removed. The base image in Dockerfile.l4t has been updated to account for v4.0 CoreIO running on Jetpack 5.

- [Self Registration](../python/examples/self_registration/README.md): Updated to generate and read a unique GUID and secret from a payload credentials file, as is now recommended for payload authentication.

- [Payloads](../python/examples/payloads/README.md): Updated to generate and read a unique GUID and secret from a payload credentials file, as is now recommended for payload authentication.

- [SpotCam - Opening .pgm/.raw Files](concepts/data_acquisition_thermal_raw.md): The example code for opening SpotCam .pgm and/or .raw files has been updated to also work for files downloaded from the tablet and/or Scout. Previously, it only worked for files downloaded from the SpotCam.

[**Mission question answerer (updated)**](../python/examples/mission_question_answerer/README.md)

## 3.3.1

### Upcoming Removals

Several protobuf fields or services are scheduled to be removed in the 4.0 release. Please ensure that they are no longer used within your code.

- `LogAnnotationService`
- Auth application token.
- Robot commands: non-synchronized mobility commands. Top-level feedback messages.
- Graph Nav map edge annotations: `vel_limit`, `ground_mu_hint`, `grated_floor`
- SpotCheck feedback: `foot_height_results` and `leg_pair_results`

### Bug Fixes and Improvements

In the upcoming release 4.0, we plan to change the encoding for real-valued fields in local grids to RAW instead of RLE (Run-Length Encoded) and provide client helpers for decoding. Make sure your code handles the `encoding` field in `LocalGridResponse` correctly.

Updated Data Acquisition system diagram and Network Compute Bridge documentation.

Added LogStatus documentation in the list of robot services.

`min_timeout` value in `AcquireDataRequest`:

- Added as an argument in Data Acquisition Service SDK client.
- Updated mission service to specify the field in requests to Data Acquisition Service.
- Propagated to RPCs sent to the Image and Network Compute Bridge services.

Added `path_following_mode` and `ground_clutter_mode` arguments in `most_restrictive_travel_params` method in `boston.mission` util.py (found [here](../python/bosdyn-mission/src/bosdyn/mission/README.md)).

Added `get_run_archives_by_id` method in [Scout client](../python/bosdyn-scout/src/bosdyn/scout/README.md).

The Inverse Kinematics Service is now available on robots without arms. Only body-mounted tools are supported on such robots.

### Known Issues

Same as 3.3.0

### Sample Code

#### New

[Log Status](../python/examples/log_status/README.md): Show how to query the log status service.

[Scout Export Run Archives](../python/examples/orbit/export_run_archives/README.md): Show how to export run archives from Scout for the recent completed missions.

[Simple Alert Server](../python/examples/network_compute_bridge/README.md): Additional Network Compute Bridge worker that generates responses with alerts.

#### Updated

[Edit Autowalk](../python/examples/edit_autowalk/README.md): Fixed documentation and improved arguments accepted by the example application so the walk filename is not assumed to be autogenerated.

[Fire Extinguisher Network Compute Bridge Worker](../python/examples/network_compute_bridge/fire_extinguisher_server/README.md): Added `min_confidence` parameter and fixed output images so they are displayed on the tablet.

[Network Compute Bridge](../python/examples/network_compute_bridge/README.md): Updated requirements files and docker instructions.

[Replay Mission](../python/examples/replay_mission/README.md): Fixed documentation and improved arguments accepted by the example application so the walk filename is not assumed to be autogenerated. Updated example to use Autowalk service to load Autowalk missions.

## 3.3.0

### Upcoming Removals

Several protobuf fields or services are scheduled to be removed in the 4.0 release. Please ensure that they are no longer used within your code.

- `LogAnnotationService`
- Auth application token.
- Robot commands: non-synchronized mobility commands. Top-level feedback messages.
- Graph Nav map edge annotations: `vel_limit`, `ground_mu_hint`, `grated_floor`
- SpotCheck feedback: `foot_height_results` and `leg_pair_results`

### New Features

#### New Service - Inverse Kinematics

Users can make reachability and stance-selection queries for reaching to locations with the arm or pointing a body-mounted sensor.
Requests can specify pose or gaze targets for a wrist-mounted or body-mounted tool, with a variety of options for body, arm, and stance configuration.
The service responds with a full robot configuration (and frame snapshot including body, feet, and tool) that satisfies the specifications of the request, or an indication that no solution was found.

This service is only available if an arm is attached to the robot.

#### New Service - LogStatus

Use the [LogStatus service](concepts/robot_services.md#log-status) to start and terminate experiment or retro logs. These logs can be used with Boston Dynamics support to diagnose problems with the robot or its systems.

#### Service Customization

When writing a service to extend the capabilities of the robot, there are now additional fields and messages to allow the service to specify which and what kind of parameters that the service can accept with its requests. These parameters can be modified by end users via tablet operation or Scout. The services that support this customization are

- Image services
- Data Acquisition plugins
- Network Compute Bridge workers
- Remote Mission callbacks
- Area Callbacks

More detailed descriptions of how to specify these parameters can be found in the [service customization documentation](concepts/service_customization.md).

#### Arm and Manipulation

- **Constrained Manipulation**: Users can put constrained manipulation in velocity control or position control of the task space. Previously, all constrained manipulation motions were velocity controlled, meaning that users would for example specify the velocity of turning a crank.
  In position control mode, the user can specify target positions, such as the angle or distance to move the object, as well as acceleration limits to obey.
  Previously, the internal estimator was always reset with a new request. Now users can disable that resetting, for cases where the task configuration has not changed from the previous request.
- **Door opening**: Added new `STATUS_STALLED` and `STATUS_NOT_DETECTED` [error statuses](../protos/bosdyn/api/spot/door.proto#doorcommand-feedback-status), and `DoorCommand.Feedback` reports progress through the door.
- **Gripper Camera**: New options added for controlling white balance, gamma, and sharpness.
- Added many pieces of information to `ArmImpedanceCommand.Feedback`.

#### Navigation

**No-Go Regions**: Added the ability to apply user-defined rectangular obstacles to the foot and body obstacle maps.  
A user can define rectangular regions in which the robot should not step, and/or rectangular regions the body should not enter, in addition to the standard obstacle mapping.
By default, a User No-Go Region will add both a body obstacle, and a slightly expanded footstep obstacle to the respective obstacle maps. If this default behavior is not desired there are optional flags to designate the User No-Go Region as just a body obstacle or just a foot obstacle instead of both, and to remove the extra padding on the foot obstacle.
These regions are added via the World Object Service, which now includes an `object_lifetime` field with the duration after which the obstacle expires.

**Area Callbacks** can raise a `PathBlocked` error to indicate that the region is blocked and graph nav should re-route.
Area callbacks that control the robot through the region can now update the localization to the end of the region when they have successfully moved the robot through the region so that Graph Nav does not try to re-navigate the region.

**Uploading Graphs** has more validation steps and will report `STATUS_INVALID_GRAPH` under more scenarios. There is a new `ValidationStatus` to show the results of this process. Recoverable graph problems will not cause the load to fail, but will instead be reported as "warnings" in the `ValidationStatus` message.

**Topology Processing** (auto loop closure) is now much less aggressive about creating loop closures and will make fewer and better loop closures than before, with the exception of waypoints near docks which are more forgiving (to allow the robot to get back to the dock from more locations).

If the robot gets stuck, it will report a "stuck reason" indicating which kind of failure resulted in getting stuck.

#### Choreography

Added a new `ChoreographyCommand` RPC to support [interactive choreography moves](concepts/choreography/custom_gait.md).

Added a new `ChoreographyStatus` RPC so that users can receive feedback on the dance state a robot is in and a robot’s progress in completing a dance or current move(s) in a dance.

- Added `exit_state` field in `SequenceInfo` message to specify the exit transition state of the sequence.
- Added `execution_id` field in `ExecuteChoreographyResponse` message with the unique ID for the execution.
- Added `id` field in `MoveParams` message, set by the client or auto-assigned by the service, to be reported in the `ChoreographyStatusResponse` `ActiveMoves` field.
- Added `custom_gait_params` and `leg_joint_params` fields in `MoveParams` object.
- Added `is_looping` field in `MoveInfo` message.
- Added `entrance_state` field in `ChoreographySequence` message to specify an explicit entrance state in the case where the first legs-track move accepts multiple entrance states.
- Animations now support more flexibility to adjusting timing, can specify whether the animation starts from a sit pose, or can specify that an Animation can be used for a custom gait.

#### Payloads

New fields in the Payload proto enable a liveness check, similar to a service liveness check. The robot will periodically try to ping (ICMP) the payload to see if it is still connected.

- `liveness_timeout_secs`: How long payload can be unpingable before a liveness fault is raised.
- `ipv4_address`: Address for the robot to ping the payload at.
- `link_speed`: Expected ethernet speed negotiated.

If present, the `ipv4_address` field will also be used to detect whether a payload is mounted to the front or rear payload port. If a payload preset has a label "mount_port:rear" and the payload is connected to the front port, it will not be displayed on the registration page. The same is true if there is a preset "mount_port:front" and the payload is connected to the rear port.

#### Images and Data

Added the SpotCamAlignment action wrapper for aligning Spot Cam image captures.

Images can be stored for Data Acquisition and RemoteGrpc elements in order to aid in editing walks.

Updated the `IrMeterOverlay` Spot Cam message and added a new RPC to get the current overlay.

Added new RPCs for setting and getting the focus state of the Spot Cam PTZ.

Added exposure settings to the `StreamParams` message.

New `AvailableModels` message to describe Network Compute Bridge models available for data acquisition capture.

New unique `id` returned in `Store*` responses from the `DataAcquisitionStore` service. This id can be used in a `DataIdentifier` to uniquely identify a particular piece of stored data.

#### Robot Control

- `ClearBehaviorFault` echos back the behavior fault if it was active at the time of request.
- `ClearBehaviorFault` specifies a list of blocking hardware faults for an unclearable behavior fault.
- An absolute desired position and orientation of the robot’s body origin can now be specified when standing.
- Users can override the configured Leases and Params when issuing an Autoreturn `StartRequest`.
- A new `ImpairedStatus` value indicates when the entity detector (required for certain new avoidance behaviors) is not working.

### Bug Fixes and Improvements

- Mission blackboard state is now reported in the `NodeState` message.
- `GraphNavClient.set_localization_full_response` added to return the full response.
- `RecordingClient.start_recording_full` added to return the full response.
- The Robot object has `get_cached_hardware_hardware_configuration()` for checking the hardware configuration efficiently.
- The Robot object has an explicit `shutdown()` to stop any background threads it may be running.
- World objects can be added or deleted in bulk using the `send_add_mutation_requests()` and `send_delete_mutation_requests()` helpers.
- Uploading Graphs has more validation steps and will report `STATUS_INVALID_GRAPH` under more scenarios. There is a new `ValidationStatus` to show the results of this process. Recoverable graph problems will not cause the load to fail, but will instead be reported as warnings in the `ValidationStatus` message.
- Some mission RPCs could fail due to response message size limits when missions become very large. Newly added RPCs (LoadMissionAsChunks2, GetInfoAsChunks, GetMissionAsChunks) use streaming responses that are assembled into the proper response.

### Dependencies

The Python SDK now requires protobuf >= 3.19.4

### Deprecations

The following will continue to work, but have been deprecated and may be removed in a future release.

#### NetworkComputeBridge

The NetworkComputeBridge Worker service has been re-worked to be more straightforward and provide additional options. The `NetworkCompute` RPC is deprecated from the NetworkComputeBridge Workers services; use the new `WorkerCompute` RPC instead.

When calling the NetworkComputeBridge service, the `input_data` is deprecated in the `NetworkComputeRequest` message; use `input_data_bridge` instead. When using the `input_data_bridge` input, the following changes will apply to the `NetworkComputeResponse` output:

- Deprecated `image_response` field; use `image_responses` instead.
- Deprecated `image_rotation_angle` field; The worker should handle rotation on its own.
- Deprecated the `alert_data` field; use `alert_data` in `OutputImage` instead.
- Deprecated `roi_output_data` field; support for non-image products will be added in a future release.

#### Deprecated fields and values

**GripperCameraParam**: Renamed `CameraMode` enum values.

**Graph Nav**: The `StraightStaircase` representation of staircases is deprecated and replaced with the new `StaircaseWithLandings`.

**Choreography**; The `precise_timing` in `Animation` message is deprecated and replaced by the more fine-grained control of `timing_adjustability` field.

**Leases**: Use `is_stale` instead of the stale time in the `LeaseResource` message to determine staleness.

#### Python functions

`BaseClient.chunk_message` has been moved to the `data_chunk` module, along with other serialization functions.

`BaseClient.request_trim_for_log` and `BaseClient.response_trim_for_log` are deprecated with no replacement. Logging should use regular %-based formatting, rather than prematurely forcing serialization.

### Breaking Changes

When the robot loses connection with an E-stop endpoint, an attempt to power on the robot will now return `STATUS_KEEP_ALIVE_MOTOR_OFF` instead of `STATUS_ESTOPPED`. In python code it will raise the `KeepaliveMotorsOffError` exception instead of `EstoppedError`.

Some malformed Graph Nav graphs were previously accepted, but would leave the service in a bad state. These graphs are now explicitly rejected during upload.

### Known Issues

**When a network transport failure occurs,** depending on the particular operating system and version of gRPC installed, the error from the python SDK may not always be the most specific error possible, such as `UnknownDnsNameError`. It may instead be raised as either a generic `RpcError`, or another generic failure type such as `UnableToConnectToRobotError`.

**If you write a custom data acquisition plugin or image service,** do not change its `DataAcquisitionCapability` or `ImageSource` set once it is running and registered. New capabilities may not be detected, and old capabilities may still be listed as available in the Data Acquisition service. To change the capabilities of a service: unregister it from the directory, wait until its capabilities are no longer listed in the Data Acquisition service, and then re-register it. This waiting also applies to restarting a service if its capabilities will be different upon restart.

**If you write a custom data acquisition plugin without using our helper class,** its `GetStatus()` RPC is expected to complete immediately. If it takes too long to complete it can cause timeouts when requesting `GetStatus()` of the data acquisition service.

**If you register a new service with the robot**, calling `robot.ensure_client()` to create a client for that service may result in a `UnregisteredServiceNameError`.

- Workaround: call `robot.sync_with_directory()` before `robot.ensure_client()`

**SE2VelocityLimits require care**. Correct usage of the `SE2VelocityLimit` message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

**Velodyne client API example has python/matplotlib issue** and it needs PyQt5

- Workaround: run `pip install pyqt5` in the venv to get it to work.

**Robot command feedback response incorrect with multiple clients running** in the configuration with a Mission client sending synchro arm commands with body lease and a Localnav client sending synchro mobility command with mobility lease. In this case, sending both robot command requests and robot command feedback requests, messes up the feedback request for the mission client. It was receiving feedback for the mobility request, and not the arm request.

**CustomParam validation** will fail if extra parameters are provided that are not in the spec.

### Sample Code

#### New

[Arm Grasp Carry Overrides](../python/examples/arm_grasp_carry_overrides/README.md): Show how to set grasp and carry overrides for Spot Arms.

[Arm Impedance Control](../python/examples/arm_impedance_control/README.md): Show how to send arm impedance commands to the robot.

[Arm WASD](../python/examples/arm_wasd/README.md): Create an interface for controlling the arm with your keyboard.

[Inverse Kinematics](../python/examples/inverse_kinematics/README.md): Show to interact with the [Inverse Kinematics Service](concepts/arm/arm_services.md#inverse-kinematics-service).

[Network Request Callback](../python/examples/network_request_callback/README.md): Provide a callback that queries a network endpoint and then checks if the response contains a particular string.

[Record Autowalk](../python/examples/record_autowalk/README.md): Create an interface for recording an Autowalk with your keyboard.

[Scout - Hello Scout](../python/examples/orbit/hello_orbit/README.md): Introductory programming example for the Scout client, which uses the Scout web API.

[Service Customization for Image Services](../python/examples/service_customization//custom_parameter_image_server/README.md): Show how to host an image service that contains an image source with custom parameters.

[Service Customization for Network Compute Worker Services](../python/examples/service_customization/custom_parameter_ncb_worker/README.md): Show how to host a Network Compute Bridge Worker service that contains custom parameters.

[User Nogo Region](../python/examples/user_nogo_regions/README.md): Show how to add and delete user no-go regions to create user-defined body and/or foot obstacles using the World Object service.

#### Updated

[Area_callback](../python/examples/area_callback/README.md): Added `lease_client.take()` call.

[Arm_constrained_manipulation](../python/examples/arm_constrained_manipulation/README.md): Improved documentation, introduced the position control loop for constrained manipulation and fixed bugs in setting position and velocity variables.

[Arm Impedence_Control](../python/examples/arm_impedance_control/README.md): Added impedance feedback.

[Estop](../python/examples/estop/README.md): Added feedback in GUI.

[Gripper Camera Params](../python/examples/gripper_camera_params/README.md): Made all gripper camera parameters configurable.

[Hello_spot](../python/examples/hello_spot/README.md): Updated body control command.

[Replay Mission](../python/examples/replay_mission/README.md): Split timeout parameter into upload timeout and mission timeout.

[Spot CAM](../python/examples/spot_cam/README.md)

- Added compositor get/set reticle calls.
- Removed network settings calls.
- Added get/set ptz focus calls.
- Added `exposure_mode` and `exposure_duration` in `StreamQualityCommand`.

[Spot Detect and Follow](../python/examples/spot_detect_and_follow/README.md)

- Added documentation for running it as a Spot Extension.
- Added authentication through payload credentials.

[Payloads](../python/examples/payloads/README.md): Updated example to work with robots that do not have an arm.

[Remote Mission Service](../python/examples/remote_mission_service/README.md): Updated example to use custom parameters.

## 3.2.3

No changes from 3.2.2.

## 3.2.2

### Bug Fixes and Improvements

Improved CORE I/O documentation on passwords, user specifications in Spot Extensions, and ports for incoming traffic.

Updated [Data Acquisition Tutorial](python/daq_tutorial/daq1.md) documentation on udev rules to refrect changes on the automatic execution of udev rules during a Spot Extension installation.

### Known Issues

Same as 3.2.0

### Sample Code

#### Updated

Updated Nvidia base docker image version in Dockerfile of the following:

- [Fetch tutorial](python/fetch_tutorial/fetch1.md),
- Crosswalk Lights and Look Both Ways [Area Callback examples](../python/examples/area_callback/README.md),
- Fire Extinguisher Detector Network Compute Bridge worker [example](../python/examples/network_compute_bridge/fire_extinguisher_server/README.md),
- [Ricoh Theta example](../python/examples/ricoh_theta/README.md)

Updated [Fire Extinguisher Detector example](../python/examples/network_compute_bridge/fire_extinguisher_server/README.md) to work with the updated tensorflow version installed in the updated nvidia base docker image.

## 3.2.1

### Bug Fixes and Improvements

Fixed issues relating to GraphNav Area Callbacks and loop closures where connections could be made in the middle of an Area Callback. These connections are now prohibited. Maps with incorrect connections must be re-recorded or reprocessed with the map processing service to re-create better loop closures.

Updated Fetch tutorial with information to run on CORE I/O payload.

Added [Getting Started](concepts/about_orbit.md) section in Scout documentation.

Removed unused imports in the protobuf files `protos/bosdyn/api/autowalk/walks.proto`, `protos/bosdyn/api/graph_nav/area_callback.proto`, `protos/bosdyn/api/graph_nav/graph_nav.proto`, `protos/bosdyn/api/mission/nodes.proto`.

Autowalk missions:

- Added flag for skipping actions.
- Added action duration field.

Fixed a bug in our `Vec3` cross product in `python/bosdyn-client/src/bosdyn/client/math_helpers.py`

### Known Issues

Same as 3.2.0

### Sample Code

#### Updated

[Replay Mission](../python/examples/replay_mission/README.md): Updated example to point to correct mission file.

[Velodyne Client](../python/examples/velodyne_client/README.md): Fixed velodyne client PyQt dependency issue.

## 3.2.0

### New Features

#### Autowalk Service

Enables API clients to specify high level autonomous behaviors for Spot using an easily editable format. The autowalk format is a list of actions and their associated locations. Using this service, users can program the robot to “go to location A, perform action A, go to location B, perform action B, etc.”. The autowalk service compiles the autowalk into a behavior tree that can then be uploaded to the robot and played using the mission service. Previously this feature was only available on the tablet, but now it is a service for all client applications.

#### Arm Impedance Control (Beta)

Enables users to specify virtual springs and forces about the end effector. Users can specify a trajectory that the hand (or something attached to the hand) should follow while being dragged along by those springs. They can also add an additional feed-forward wrench (force + torque) that the end effector can apply. This command can be useful for tasks such as inserting a peg into a hole, or sliding along a surface.

Notes:

- This is a beta release, so care should be taken when specifying parameters, as damage to the robot or the surrounding environment may occur.
- Currently the maximum stiffness achievable with an impedance command is less than an ArmCartesianCommand, so if high positioning accuracy is required, ArmCartesianCommand or ArmSurfaceContact should be used.

#### Graph Nav – Area Callbacks

Enables users to register a callback that is called in certain areas of the map during navigation. These “Area Callbacks” can instruct the robot to wait until the area is safe to cross (such as a crosswalk), take control of the robot and perform an action (such as opening a door), or perform a background action while in a certain area of the map (such as flashing lights or playing sounds).
This enables integration with the [Graph Nav](concepts/autonomy/graphnav_service.md) navigation system to extend its capabilities in terms of safety and new actions while navigating. See the [Area Callback](concepts/autonomy/graphnav_area_callbacks.md) documentation for more details.

#### Fan Power Control

Fan Commands request the robot to power the fans to a certain percent level (0 being off, 100 being full power) for a certain duration, for use cases such as temporarily turning the fans off during an audio recording. A fan command being accepted does not guarantee that it will work for its entire duration, for cases such as the robot ran too hot and therefore took back control of the fans, or another fan command was overrode the existing fan command.

#### Ground Clutter

When this feature is enabled, the robot will treat low objects (shorter than 30cm height) as obstacles during mission playback. The robot will only be willing to step up or down onto different surfaces if it had stepped on them during mission recording. This mode may cause the robot to take unexpected turns in some environments if the robot perceives small objects (real or imagined). Very small objects (e.g. extension cords) will likely still be ignored by the robot.

#### Added CORE I/O Documentation

CORE I/O payload replaces the Spot CORE payload. We added the documentation related to the new features in CORE I/O in [here](payload/coreio_documentation.md)

#### Added Spot Extensions Documentation

CORE I/O contains improved functionality to package and run applications as Spot Extensions. We added the Spot Extensions documentation [here](payload/docker_containers.md#manage-payload-software-in-core-i-o)

### Bug Fixes and Improvements

#### API

Choreography API:

- Deprecated `known_sequences` and added `SequenceInfo` with the list of choreography sequences the robot knows about.
- RPC additions:
  - `DeleteSequence`: Delete the retained file for a choreography sequence so the sequence will be forgotten on reboot.
  - `SaveSequence`: Write a choreography sequence as a file to robot memory so it will be retained through reboot.
  - `ModifyChoreographyInfo`: Edit the metadata of a choreography sequence and update any retained files for that sequence with the new metadata.
  - `ClearAllSequenceFiles`: Reset to a clean slate with no retained files by deleting all non-permanent choreography related files.

Added full `ImageRequest` in data_acquisition request and deprecated `image_source` and `image_format` fields.

Docking:

- Added UpdateDockingParams in DockingCommandFeedbackRequest to update paramaters relating to the specified command ID.
- Added `STATUS_ERROR_STUCK` in `DockingCommandFeedbackResponse` to flag the robot not making progress towards docking.

Added `Matrixf`, `MatrixInt64`, `MatrixInt32` and `Vector` in `geometry.proto`.

GraphNav:

- `graph_nav.proto`:
  - Added refinement field in GraphNav’s `SetLocalizationRequest` as a choice of refining fiducial results with ICP or with visual features.
  - Added `STATUS_VISUAL_ALIGNMENT_FAILED` in SetLocalizationResponse to flag the visual feature based alignment failing or the pose solution being considered unreliable.
  - Added `path_following_mode`, `blocked_path_wait_time` and `ground_clutter_mode` in GraphNav’s `TravelParams`.
  - Added definitions to support the new Area Callbacks feature.
  - Added `route_following_status` in `NavigationFeedbackResponse` with additional information about what kind of route the robot is following and why.
  - Added `blockage_status` in `NavigationFeedbackResponse` with additional information about whether or not the robot believes the current route to be blocked.
  - Added `ValidateGraph` RPC to run a check on the currently loaded map.
- `map.proto`:
  - Added optional `ClientMetadata` field with information to attach to waypoints that are being recorded.
  - Added `robot_id` field with information of the robot that created this waypoint and `recording_started_on` field with information about when the recording session started in robot time basis in `WaypointSnapshot`.
  - Added `path_following_mode`, `disable_directed_exploration`, `area_callbacks`, `ground_clutter_mode` to `Edge` definition.
- `recording.proto`:
  - Added `STATUS_ROBOT_IMPAIRED` in `StartRecordingResponse` to flag the robot being unable to start recording because it is impaired
  - Added `STATUS_ROBOT_IMPAIRED` in `StartRecordingResponse` with information on why the robot is impaired.
  - Added `status` and `impaired_state` fields in `GetRecordStatusResponse` with information on whether the robot is impaired.

Missions:

- `mission.proto`:
  - Added `severity` field in `Question` with the severity of the question.
  - Added `path_following_mode` and `ground_clutter_mode` in `PlaySettings` with information on whether to use default or strict path following mode and whether or not to enable ground clutter avoidance, and which type.
- `nodes.proto`:
  - Added `Switch` node definition in mission definition to run a specific child based on a specified pivot_value.
  - Added `respect_child_failure` flag in mission `Repeat` nodes to control whether a repeat node will keep running its child regardless of whether or not the child succeeds or fails.
  - `BosdynRecordEvent` message:
    - Added `succed_early` to control the wait for the `RecordEvents` RPC.
    - Added `additional_parameters` to support runtime parameters.
  - `RemoteGrpc` message:
    - Added `severity` field to determine what sort of alerting a prompt triggers.
    - Added `BosdynGripperCameraParamsState` message to get the state of the gripper camera params from the robot.
    - Added `SetGripperCameraParams` message to set gripper camera params.
    - Added optional variables `cleared_cause_fall_blackboard_name`, `cleared_cause_hardware_blackboard_name` and `cleared_cause_lease_timeout_blackboard_name` in `FormatBlackboard` message to store cleared behavior faults.

Network Compute Bridge:

- Updated `ImageSourceAndService` field in `NetworkComputeRequest` to be a choice between existing `image_source` field and a more complete `ImageRequest` field with all the image requests field.
- Added `output_images` field in `NetworkComputeResponse` to output images generated by a model.

Added `stair_mode` field in `MobilityParams` with selected option for stairs mode.

Spotcheck:

- Added `STATE_ARM_JOINT_CHECK` in `SpotCheckFeedbackResponse.State` message for arm joint endstops and cross error check being underway.
- Added `ERROR_ARM_CHECK_COLLISION` and `ERROR_ARM_CHECK_TIMEOUT` enum values in `SpotCheckFeedbackResponse.Error` to flag an arm motion causing collisions (e.g. w/ a payload) or timeout during arm joint check.
- Added `ERROR_ENCODER_SHIFTED` and `ERROR_COLLISION` enum values in `JointKinematicCheckResult.Error` to flag whether the measured endstops shifted from kin cal or the joint would have a collision.
- Added `STATUS_CALIBRATION_VERIFICATION_FAILED` enum in `CameraCalibrationFeedbackResponse.Status` to flag Spotcheck failed after the camera calibration.

#### Documentation

Improved Choreography documentation with 3.2 functionality and API changes.

Updated the lease usage in the Fetch tutorial.

Updated the Data Acquisition Tutorial documentation with information on how to convert the tutorial into a Spot Extension to run on the CORE I/O.

Added documentation on thermal SpotCAM images [here](concepts/data_acquisition_thermal_raw.md).

#### SDK

Added `AutowalkClient` to support the new Autowalk functionality

Added `LoggingHandler` class in `data_buffer.py` as a logging system Handler that will publish text to the data-buffer service

Added `InvalidGravityAlignmentError` error in `map_processing.py` to report if one or more anchoring hints disagrees with gravity.

Updated `PayloadRegistrationKeepAlive` to catch `TooManyRequestsError` exceptions and continue on in such cases.

Added fan power control/feedback methods in python PowerClient; also added `FanControlTemperatureError` to report current measured robot temperatures are too high to accept user fan commands.

Added `RobotImpairedError` in Python `GraphNavRecordingServiceClient` to report failures to start recording because the robot is impaired.

Added `sync_with_services_list` in `robot.py` as an alternate version of `sync_with_directory` that takes the list of services directly and does not perform any RPCs.

Added `update_secure_channel_port` in `robot.py` to update the port used for creating secure channels, instead of using the default 443

Added `payload_estimation_command` method in `robot_command.py` to get the robot estimate payload mass.

Added `exc_callback` function as an argument in `ResponseContext` in `server_util.py` to be called with exception type, value, and traceback info if an exception is raised in the body of the "with" statement.

Added `CameraSpotCheckTimedOutError`, `CameraSpotCheckFeedbackError` and `CameraCalibrationResponseError` in `spot_check.py` as errors for timing out waiting for SUCCESS response from camera spot check, general class of errors for camera spot check feedback and general class of errors for camera calibration routines, respectively.

Updated `RemoteClient` to use lease processors and lease wallet when not given explicit leases.

Added `_build_establish_session_request` and `_build_tick_request` helper functions in `remote_client.py`.

Added `lease_resource_hierarchy.py` with helper functionality for managing hierarchy of lease resources.

Added `lease_validator.py` with functionality to track lease usage in intermediate services.

Added `spot_cam/lights_helper.py` with helper functionality to control SpotCAM lights.

### Deprecations

Deprecated Choreography API `known_sequences`; use new `SequenceInfo` instead.

Deprecated `image_source` and `image_format` fields in DAQ requests and added full `ImageRequest` instead.

The boolean field `stair_hint` is deprecated from `MobilityParams` and it has been replaced by the field `stairs_mode`.

Deprecated `LogAnnotationHandler`; use `bosdyn.client.data_buffer.LoggingHandler` instead.

`safe_power_off` method is deprecated in `PowerClient` and replaced by the less ambiguous `safe_power_off_motors` function.

Removed `_should_send_app_token_on_each_request` method in `robot.py`.

Deprecated Spot CORE Documentation and moved to [Pre-3.2 Spot CORE Documentation](payload/spot_core_documentation.md).

### Breaking Changes

### Dependencies

### Known Issues

**When a network transport failure occurs,** depending on the particular operating system and version of gRPC installed, the error from the python SDK may not always be the most specific error possible, such as `UnknownDnsNameError`. It may instead be raised as either a generic `RpcError`, or another generic failure type such as `UnableToConnectToRobotError`.

**If you write a custom data acquisition plugin or image service,** do not change its `DataAcquisitionCapability` or `ImageSource` set once it is running and registered. New capabilities may not be detected, and old capabilities may still be listed as available in the Data Acquisition service. To change the capabilities of a service: unregister it from the directory, wait until its capabilities are no longer listed in the Data Acquisition service, and then re-register it. This waiting also applies to restarting a service if its capabilities will be different upon restart.

**If you write a custom data acquisition plugin without using our helper class,** its `GetStatus()` RPC is expected to complete immediately. If it takes too long to complete it can cause timeouts when requesting `GetStatus()` of the data acquisition service.

**If you register a new service with the robot**, calling `robot.ensure_client()` to create a client for that service may result in a `UnregisteredServiceNameError`.

- Workaround: call `robot.sync_with_directory()` before `robot.ensure_client()`

**SE2VelocityLimits require care**. Correct usage of the `SE2VelocityLimit` message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

**Python wheels 3.1.2.1 and 3.2.0 do not work on nvidia docker image** `nvcr.io/nvidia/l4t-tensorflow:r32.6.1-tf2.5-py3`.

- Workaround: Use `nvcr.io/nvidia/l4t-tensorflow:r32.7.1-tf2.5-py3` as the base image instead.

**Velodyne client API example has python/matplotlib issue** and it needs PyQt5

- Workaround: run `pip install pyqt5` in the venv to get it to work.

**Robot command feedback response incorrect with multiple clients running** in the configuration with a Mission client sending synchro arm commands with body lease and a Localnav client sending synchro mobility command with mobility lease. In this case, sending both robot command requests and robot command feedback requests, messes up the feedback request for the mission client. It was receiving feedback for the mobility request, and not the arm request.

**Binary files are not handled correctly in git when cloning SDK on Windows** The failure is due to a random string of bytes mapping to `\n` in the binary protobuf getting converted to `^M` (CRLF) in Windows.

### Sample Code

#### New

[Area Callback](../python/examples/area_callback/README.md): Example with a Crosswalk Area Callback action

[Arm Impedance Control](../python/examples/arm_impedance_control/README.md): Example for how to send arm impedance commands with the robot

[CORE I/O GPIO](../python/examples/core_io_gpio/README.md): Example to demonstrate how to use the CORE I/O GPIO pins to blink an LED

[Edit Autowalk](../python/examples/edit_autowalk/README.md): Example on how to edit and replay an Autowalk via the API

[Fan Commands](../python/examples/fan_command/README.md): Example to provide a basic Python script to call and receive feedback on a fan command and provide a usable template for writing a callback that issues and blocks during a fan command.

#### Updated

[Docking](../python/examples/docking/README.md): Added undock function.

[Fiducial Follow](../python/examples/fiducial_follow/README.md): Updated example for better lease usage.

[GraphNava Command-Line](../python/examples/graph_nav_command_line/README.md): Fixed lease usage.

[Mission Recorder](../python/examples/mission_recorder/README.md): Added metadata for the recording session.

[Network Compute Bridge](../python/examples/network_compute_bridge/README.md): Added configuration to create a Spot Extension with the example.

[Post Docking Callback](../python/examples/post_docking_callbacks/README.md): Added configuration to create a Spot Extension with the example.

[Remote Mission Callback](../python/examples/remote_mission_service/README.md): Updated example to use lease processors and lease wallet when not given explicit leases.

[Replay Mission](../python/examples/replay_mission/README.md): Added strict_mode option to use strict path following mode and cleaned up lease use.

[SpotCAM](../python/examples/spot_cam/README.md):

- Fixed SpotCAM `webrtc` client reliance on CLI credentials.
- Added spotcam ir meter example into command line.
- Hardcoded dependency versions that work with Python 3.6.

[Spot Detect and Follow](../python/examples/spot_detect_and_follow/README.md): Added configuration to create a Spot Extension with the example and various improvements.

[Stitch Front Images](../python/examples/stitch_front_images/README.md): Add live viewer to example.

## 3.1.2.1

### Dependencies

The `bosdyn-api` and `bosdyn-choreography-protos` packages have been rebuilt to support the latest `protobuf` package. They now require a minimum `protobuf` version of 3.6.1.

## 3.1.2

### Bug Fixes and Improvements

Added payloads and lidar transform in GraphNav's `WaypointSnapshot` to help with:

- Not getting lost when a big payload occluded the lidar.
- Determine which payloads were used to record a map.

### Known Issues

Same as 3.1.0

## 3.1.1

### Known Issues

Same as 3.1.0

### Sample Code

[**Network Compute Bridge (updated)**](../python/examples/network_compute_bridge/README.md)
Modified server to use user confidence value as a threshold for returning detections

## 3.1.0

### New Features

#### Safely powering off on staircases.

To improve safety when operating on stairs, the robot may now autonomously walk off staircases in scenarios where it may have previously entered a sit. In the event of communication loss, critically low battery state of charge, or a Safe Power Off Request, the robot will walk off the staircase before sitting and powering off. The direction of travel will generally be to descend the stairs unless the robot has already reached the top landing. This includes automatic sit-and-power-off cases such as from low battery or the E-stop `SETTLE_THEN_CUT` level, as well as any client SafePowerOff commands. It does _not_ affect immediate power cut cases such the PowerOff command or the E-stop CUT level.  
To override this behavior for SafePowerOff commands, there is a new unsafe_action field in `SafePowerOffCommand` which can be set to `UNSAFE_FORCE_COMMAND` to force the command to take place immediately. To override this behavior for E-stop or battery power off, set the `disable_stair_error_auto_descent` field in the mobility params for the robot commands.
As part of this change, a new `TerrainState` message in `RobotState` contains the `is_unsafe_to_sit` value to report when the robot considers the terrain unsafe to sit on.

#### Lease timeout changes.

The behavior of the robot and leases is changed when the lease owner fails to retain the lease. Prior to 3.1, the robot would sit down and power off, and the lease would be revoked. This behavior allowed a new owner to smoothly take control of the robot in the case that a previous owner left without first returning the lease, but has proved to be frustrating when short comms losses trigger this behavior.
Starting in 3.1, failing to retain the lease will cause the lease to become “stale”. If the lease is stale, another client can acquire the lease and begin using the robot. However, if the original owner returns and begins retaining the lease or sending commands before another client acquires ownership, the lease will become “fresh” again without the original owner needing to re-acquire the robot. This staleness is reported via the new `stale_time` field in the `LeaseResource` message.
This change means that **the robot will no longer sit down and power off if the lease owner disappears.** For clients that still want that behavior, it is recommended to use an E-stop endpoint with the owner (which is already the common case), so that a comms interruption will cause the robot to sit and power off via the E-stop system.

#### Data Acquisition

A [new tutorial](python/daq_tutorial/daq1.md) provides a walk-through of integrating new sensors with the data acquisition system. It explains how to write, deploy, and use image services and data acquisition plugins with Spot, and how to process the resulting data.

In addition to images and data capabilities, DataAcquisitionRequests can specify network compute actions to perform on captured images by adding a [NetworkComputeCapture](../protos/bosdyn/api/data_acquisition.proto) in the acquisition request list. This capture will save the image and any computed data from the network compute response. This currently only operates on images and will only save the data returned in the response. For use cases that require sending other input data or saving other kinds of output data, it is still recommended to implement a data acquisition plugin to do that work.

Robot image services now report which image formats and pixel formats they support via new fields in the `ImageSource` message. When requesting images, clients can specify a desired pixel format, and also a resize ratio. These options allow for reduced bandwidth in cases where the client only needs a smaller image or a grayscale image. New status errors `STATUS_UNSUPPORTED_PIXEL_FORMAT_REQUESTED` and `STATUS_UNSUPPORTED_RESIZE_RATIO_REQUESTED` can now be returned if the client makes a request that is unsupported. User image services should also report the options they support. The `VisualImageSource` constructor now includes an optional argument for a list of supported pixel formats.

#### Alerts

A new [AlertData](../protos/bosdyn/api/alerts.proto) message has been added for the purpose of triggering live alerts for various events that can happen during a mission. These alerts can be saved into the `DataAcquisitionStore` service using the new `StoreAlertData` RPC and queried using the `ListStoredAlertData` RPC. Additionally, the alert data can be added to the response from a network compute bridge worker, where it will be automatically saved into the data acquisition store when captured as part of a data acquisition request. If a client calls the network compute bridge service itself, the alert data will be returned to the client in the response but not automatically saved to the data acquisition store.

#### New Services

[**GripperCameraParamService**](../protos/bosdyn/api/gripper_camera_param.proto) – Set or query various modes and options on the camera in the robot’s gripper.

[**RayCastService**](../protos/bosdyn/api/ray_cast.proto) – Find intersections between a ray and the robot’s representation of the environment.

#### Control and Feedback

The Self-Right command now provides feedback in the `SelfRightCommand.Feedback` message as to whether it has successfully completed.

When Stand commands come to rest at their final pose, they will now enter a “frozen” state with locked joints. This keeps the robot more stationary for sensor data collection. Disturbances will still cause the robot to adjust and react to recover its position. The status of this “frozen” state is provided by the new `StandingState` enum in `StandCommand.Feedback`.

A new option, `enable_robot_locomotion` has been added to `ConstrainedManipulationCommand.Request`. When set to true, the robot will take steps to keep the hand in the workspace during a constrained manipulation command.

A new message, `BodyAssistForManipulation`, has been added to the BodyControlParams to allow clients to specify whether the body height or yaw should be used to assist the arm in manipulation. This new option cannot be used together with body offset trajectories specified in the `base_offset_rt_footprint` field.

#### Python Helpers

- `image.depth_image_to_pointcloud()` to convert depth images to numpy point clouds.
- `image_service_helpers.convert_RGB_to_grayscale()` to convert color images to grayscale.
- `math_helpers` now includes `Vec2` and `Vec3` objects.
- `robot_command.arm_joint_move_helper()` constructs RobotCommands for joint trajectories.

- `robot_command.blocking_sit()` and `robot_command.blocking_selfright()` command sit and self-right commands and block until they complete.

- `robot_command.block_for_trajectory_cmd()` will block until the feedback for a given body trajectory command indicates that it is complete.

- `util.add_payload_credentials_arguments()` adds a `–payloads-credentials-file` argument that can be used in place of the `–guid` and `–secret` arguments. This simplifies deployment to payload computers that contain a file with the correct credentials.

- `util.read_payload_credentials()` reads payload GUID and secret values from a file for use with payload registration and authentication.

- `util.get_guid_and_secret()` is a helper that will return the guid and secret, regardless of if the user used `–guid` and `--secret` or `--payload-credentials-file`.

- `world_object.draw_sphere()` and `world_object.draw_oriented_bounding_box()` can be used to set objects in the world object service for debugging purposes.

#### Choreography

A new `ListAllSequences` RPC allows clients to list all of the available sequences that are known to the robot and can be executed.

#### Missions

A new node type, `ClearBehaviorFaults` will allow a mission to autonomously clear behavior faults when desired.

### Bug Fixes and Improvements

In the python client library the [LeaseKeepAlive](../python/bosdyn-client/src/bosdyn/client/lease.py) context manager continually sends RetainLease commands to the robot to keep ownership of a lease. It has been upgraded to support more complete lease management by acquiring the lease if it is not owned when created and an option to return it when it exits. To preserve backwards compatibility, the initial acquisition is allowed to fail, and it does not return it by default. There are two options that control this behavior: `must_acquire=True` means that any exceptions that are raised during acquisition are not caught and are raised to the code creating the keep-alive, and `return_at_exit=True` means that the lease will be returned when exiting or shutting down the keep-alive. Both of these options default to `False` currently.

Arm joint trajectories now include self-collision avoidance to prevent hitting the body or payload with the arm.

The DockProperties of the docks from the World Object Service have an additional `from_prior` field that can indicate when that particular object comes from prior map knowledge and was not directly detected. Docking Feedback includes a new failure case `STATUS_ERROR_UNREFINED_PRIOR`, for situations in which the dock prior could not be confirmed as a real dock.

Certain commands may be unavailable when the robot is docked (such as rolling over to change the battery). In those cases, the command response will fail with the new `STATUS_DOCKED`.

Many gRPC services on the robot have now enabled support gRPC compression, which will be used if the client gRPC library supports it.

The `bosdyn.client` `metrics` command will print the metrics correctly again.

#### Graph Nav

When localizing to a graph nav map, the `SetLocalization`, `UploadGraph`, and `UploadWaypointSnapshot` RPCs can fail with the new `STATUS_INCOMPATIBLE_SENSORS` if the map was recorded using a different sensor setup than the robot currently has onboard. For example, if the map was recorded with a lidar scanner, and the robot does not currently have one equipped. For `UploadWaypointSnapshot`, the new status enum will not be known to clients using older versions of the SDK and thus they will not recognize it as an error.
The new `SensorCompatibilityStatus` in the responses will report whether the map and/or robot have lidar data for these error cases.

Clearing the map when in the middle of recording would break the recording process. Requesting to clear the map in this case will now return `STATUS_RECORDING`. Clients using older versions of the SDK will not know about this new status field and will not treat it as an error case.

#### Spot Check

Spot Check now has two extra states that it can report being in: `STATE_GRIPPER_CAL` and `STATE_SIT_DOWN_AFTER_RUN`. It also has two extra error types it can detect and report: `ERROR_GRIPPER_CAL_TIMEOUT` as a top-level error and `ERROR_INVALID_RANGE_OF_MOTION` for joints.

### Deprecations

Automatic data buffer logging of gRPC messages is deprecated. The gRPC messages will continue to be available for download via HTTP in 3.1, but support will be removed in a future release.

FollowArmCommand’s `disable_walking` is deprecated. To reproduce the robot's behavior of `disable_walking == true`, issue a StandCommand setting the `enable_body_yaw_assist_for_manipulation` and `enable_hip_height_assist_for_manipulation` MobilityParams to true. Any combination of the `enable_*_for_manipulation` are accepted in stand giving finer control of the robot's behavior.

When commanding door opening, the options `SWING_DIRECTION_INSWING` and `SWING_DIRECTION_OUTSWING` have been renamed to `SWING_DIRECTION_PULL` and `SWING_DIRECTION_PUSH`.

The signature of `CameraInterface.image_decode()` for user image services has changed from passing individual parameters such as `image_format` and `quality_percent` to directly passing in the image request proto. This change makes it easier to add new options to image requests without breaking existing image service implementations. Services can access the previous parameters via the image request proto, as well as accessing new parameters such as `pixel_format` and `resize_ratio`.

The `–username` and `–password` command line options are deprecated in the Python SDK. There are security concerns with using usernames and passwords on the command line. Instead of using `bosdyn.client.util.add_common_arguments(parser)` we recommend using `bosdyn.client.util.add_base_arguments(parser)` which will not include those options, and then authenticating via `bosdyn.client.util.authenticate(robot)`, which will read from the `BOSDYN_CLIENT_USERNAME` and `BOSDYN_CLIENT_PASSWORD` environment variables. The `bosdyn.client` and `bosdyn.client.bddf_download` programs will continue to support the old options for now but usage should be switched to the environment variable method instead.

We have changed the [LeaseKeepAlive](../python/bosdyn-client/src/bosdyn/client/lease.py#bosdyn.client.lease.LeaseKeepAlive) helper to handle more of the lease life-cycle management, where it can acquire and return the lease itself. However, we have kept its default behavior largely unchanged for now to not break existing code. In a future release we may change the defaults for `return_at_exit` and `must_acquire` to `True`. Applications that desire the previous behavior should explicitly set `must_acquire` and `return_at_exit` to `False` to preserve that behavior across a change in the defaults.

The `DARK` option for auto white balance for the Spot CAM stream has been deprecated.

#### Renamed functions and classes

The original names still exist, but are deprecated.

`bosdyn.client.graph_nav.UnrecongizedCommandError` has been renamed to `bosdyn.client.graph_nav.UnrecognizedCommandError`.

`bosdyn.bddf.message_reader.channel_name_to_series_decriptor()` has been renamed to `bosdyn.bddf.message_reader.channel_name_to_series_descriptor()`

The `from_obj()` methods on the math helper classes have been renamed to `from_proto()`.

### Breaking Changes

#### Behavior change on lease timeout

Because leases are no longer revoked when the owner fails to check in, there are two changes that must be accounted for:

1. The robot will not automatically sit down and power off if the owner times out. It will still sit down and power off if an E-stop endpoint times out. For use cases that want the owner’s absence to cause the robot to sit and power off, make sure that the owner is also maintaining an E-stop endpoint.
2. Any client calling `ListLeases` to try to determine if the robot is owned will need to check the `stale_time` of the `LeaseResource`. Instead of calling `ListLeases` before `AcquireLease`, we recommend just calling `AcquireLease` first, and reacting to any `STATUS_RESOURCE_ALREADY_CLAIMED` status in the response.

#### Behavior change of powering off on stairs

The new safety features to avoid powering off and sliding down stairs means that there is a behavioral change to SafePowerOff commands, powering off due to low battery, and powering off due to an E-stop `LEVEL_SETTLE_THEN_CUT`. While the new behavior should be safer, be aware that these commands will now cause locomotion before sitting and powering off.

#### Disallowed Commands

The robot may not be commanded to go to the battery change pose when docked.

The Graph Nav map may not be cleared in the middle of recording.

#### Data Acquisition

The DataAcquisitionStore service is queryable for the IDs of items that have been stored by it. It would previously track everything that had been stored since the last time that the robot had been restarted. As of 3.1, it will track only the last 10,000 items stored.

### Dependencies

The `bosdyn-client` package no longer depends on `requests`.

### Known Issues

**When a network transport failure occurs,** depending on the particular operating system and version of gRPC installed, the error from the python SDK may not always be the most specific error possible, such as `UnknownDnsNameError`. It may instead be raised as either a generic `RpcError`, or another generic failure type such as `UnableToConnectToRobotError`.

**Spot CAM LED illumination levels** are not currently recorded or played back in Autowalk missions.

**If you write a custom data acquisition plugin or image service,** do not change its `DataAcquisitionCapability` or `ImageSource` set once it is running and registered. New capabilities may not be detected, and old capabilities may still be listed as available in the Data Acquisition service. To change the capabilities of a service: unregister it from the directory, wait until its capabilities are no longer listed in the Data Acquisition service, and then re-register it. This waiting also applies to restarting a service if its capabilities will be different upon restart.

**If you write a custom data acquisition plugin without using our helper class,** its `GetStatus()` RPC is expected to complete immediately. If it takes too long to complete it can cause timeouts when requesting `GetStatus()` of the data acquisition service.

**If you register a new service with the robot**, calling `robot.ensure_client()` to create a client for that service may result in a `UnregisteredServiceNameError`.

- Workaround: call `robot.sync_with_directory()` before `robot.ensure_client()`

**SE2VelocityLimits require care**. Correct usage of the `SE2VelocityLimit` message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

### Sample Code

All examples have been changed to read the username and password from environment variables instead of taking `--username` and `--password` arguments.

Additionally, most examples now use the LeaseKeepAlive for complete lease management by setting the `must_acquire` and `return_at_exit` arguments to `True` at construction. This helps ensure that the lease is properly returned when the example is complete.

The arm and manipulation examples have been updated to use the new `block_until_arm_arrives()` helper instead of `sleep()` calls.

The included Dockerfiles now contain default command line arguments for their entrypoints where appropriate. This means that it is not necessary to specify any command line arguments when running them in their default configuration (on the Spot CORE). However when running in a non-default configuration, _all_ command line arguments will need to be specified.

[**Comms Mapping (new)**](../python/examples/comms_mapping/README.md)
Creates an image service that can be selected on the tablet controller that displays a map of wifi signal strength.

[**Gripper Camera Params (new)**](../python/examples/gripper_camera_params/README.md)
Demonstrates how to control the capture parameters for the gripper camera.

[**Ray Cast (new)**](../python/examples/ray_cast/README.md)
Demonstrates how to perform ray-casting queries using the new RayCastService.

[**Animation Recorder (updated)**](../python/examples/animation_recorder/README.md)
First checks if the robot has the correct license for choreography.

[**Arm Force Control (updated)**](../python/examples/arm_force_control/README.md)
Updated to use the new `BodyAssistForManipulation` parameters.

[**Arm Gcode (updated)**](../python/examples/arm_gcode/README.md)
Some updates to parsing gcode files. Added a new `--test-file-parsing` option to only try to read the file, without executing it.

[**Arm joint move (updated)**](../python/examples/arm_joint_move/README.md)
Added a more advanced example that shows how to send a continuous trajectory with many points.

[**BDDF download (updated)**](../python/examples/bddf_download/README.md)
Fixed the ping check on Windows.

[**Data Acquisition (updated)**](../python/examples/data_acquisition_service/README.md)
Includes a new example plugin that saves battery data. This is used as part of the [Data Collection Tutorial](python/daq_tutorial/daq1.md)

[**Get Image (updated)**](../python/examples/get_image/README.md)
Supports a new `--pixel-format` option to be able to specify the desired format.

[**Graph Nav Command Line (updated)**](../python/examples/graph_nav_command_line/README.md)
The recording example correctly handles the `NotReadyYetError` response when stopping recording.

[**Ricoh Theta (updated)**](../python/examples/ricoh_theta/README.md)
Includes support for pixel format and resize ratio.

[**Spot CAM (updated)**](../python/examples/spot_cam/README.md)
Fixed a memory leak related to audio streams.

[**Tester Programs (updated)**](../python/examples/tester_programs/README.md)
The image service tester only requests image and pixel formats that the service reports that it supports, and it will check that the returned type matches the requested type. It will also report a summary at the end of all errors and warnings it found.

[**Upload Choreographed Sequence (updated)**](../python/examples/upload_choreographed_sequence/README.md)
Checks that the robot is correctly licensed for choreography before running.
Includes a new `--upload-only` option that will upload the sequence without running it.

[**Basic Streaming Visualizer (updated)**](../python/examples/visualizer/README.md)
Added an example to draw gripper depth data as a point cloud.

[**Web Cam Image Service (updated)**](../python/examples/service_customization/custom_parameter_image_server/README.md)
Includes support for pixel format and resize ratio.

[**World Object Mutations (updated)**](../python/examples/world_object_mutations/README.md)
Demonstrate using the new drawing helper.

[**Xbox Controller (updated)**](../python/examples/xbox_controller/README.md)
Cleaner lease usage throughout.

## 3.0.3

### Bug fixes and improvements

Reduced RPC calls to the Fault service in `image_service_helpers.py`.

Example documentation cleanup and improvements.

### Known Issues

Same as 3.0.0

## 3.0.2

### New Features

Added `GetSystemLog` RPC in SpotCAM Health service to retrieve an encrypted log of system events, for factory diagnosis of possible issues.

### Bug fixes and improvements

Fixed UploadEdgeSnapshot typo in GraphNav client.

Fixed usage of `SE2Trajectory` robot commands in mission service.

### Known Issues

Same as 3.0.0

## 3.0.1

### New Features

Added `COLORMAP_INFERNO` and `COLORMAP_TURBO` as SpotCAM IR color map options.

### Bug fixes and improvements

The new `base_tform_sensor` fields in SpotCAM protos have the transform in the right direction. The old `base_tfrom_sensor` fields, now deprecated, had the inverse transform.

### Deprecations

Deprecated field `base_tfrom_sensor` in SpotCAM camera proto and added field `base_tform_sensor` so it follows the intended naming convention.

Deprecated field `base_tfrom_sensor` in SpotCAM logging proto and added field `base_tform_sensor` so it follows the intended naming convention.

Deprecated the `decode_token()` and `log_token_time_remaining()` functions in `bosdyn.client.sdk`. The SDK no longer supports decoding tokens. If you need to decode one, use pyjwt directly.

### Known Issues

Same as 3.0.0

### Sample Code

[**Arm Constrained Manipulation (updated)**](../python/examples/arm_constrained_manipulation/README.md)
Cleanup to clamp normalized velocity and also use normalized velocity for knob.

[**GraphNav Command Line (updated)**](../python/examples/graph_nav_command_line/README.md)
Improved handling in certain failure cases

[**Spot Cam (updated)**](../python/examples/spot_cam/README.md)
Handle new IR color map options and removed the usage of the deprecated pose fields

## 3.0.0

### New Features

#### Graph Nav

**Map Processing**
The new map processing service provides two ways to process the data in a graph nav map:

- adding new waypoints and edges to close loops and add connections in a map
- optimizing “anchorings” of a map, which will generate optimized positions of waypoints in the world for display or navigation.

**Navigate to Anchor**
A new NaviagateToAnchor RPC can be used to command GraphNav to drive the robot to a specific place in an anchoring. GraphNav will find the waypoint that has the shortest path length from the robot's current position but is still close to the goal.

See the [Graph Nav](concepts/autonomy/graphnav_map_structure.md) documentation for more information.

#### Auto Return

Auto Return is a service which can be configured to take control of the robot in the event of a communication loss, and return it back along its recently traveled route to attempt to regain communications with its user. See the [Auto Return](concepts/autonomy/auto_return.md) documentation for more details.

#### Choreography

The Choreography API now provides 'choreography logging' which will capture timestamped data about the robot's pose and joint state for either a user defined time period or for the duration of a dance. See the [Choreography Service](concepts/choreography/choreography_service.md) documentation for more details.

Users can now create animated moves using timestamped keyframes; these can be built through common animation software (like Autodesk Maya), handwritten, or constructed from choreography log data. The animated moves can be uploaded to the robot and used within dances like the base moves. See the [Animations Overview](concepts/choreography/animations_in_choreographer.md) documentation for more details.

#### Constrained manipulation

The constrained manipulation API provides the functionality to manipulate objects such as cranks, levers, cabinets and other similar objects with Spot. The API allows for the selection of a task type along with the desired task velocity to manipulate the object.

#### Pushbar Door Opening

API and tablet support for opening pushbar doors. The AutoPush API command takes a push point which the robot uses to detect the door and push it open at the specified location. See door.proto or arm_door.py for more details.

#### SpotCam

New SetPtzFocus and GetPtzFocus RPCs allow for control over the focus of the PTZ camera.

#### Payloads

Payload registration now supports mounting payloads to the wrist or gripper of the arm. The new MountFrameName enum contains the valid mounting locations.

A new UpdatePayloadAttached RPC allows for attaching and detaching payloads while the robot is operating.

#### Missions

Missions have a new `STATUS_STOPPED` state that can be triggered by the new `StopMission` RPC. This state differs from a paused mission in that it means that the mission is no longer running and cannot be resumed.

New mission node types:

- `BosdynNavigateRoute`: Use GraphNav via NavigateRoute
- `BosdynRecordEvent`: Record an API event in the data buffer.
- `SpotCamLed`: Change the brightnesses of the LEDs on a SpotCam.
- `SpotCamResetAutofocus`: Reset the autofocus on a SpotCam PTZ.
- `StoreMetadata`: Attach metadata to some data stored by a DataAcquisition node.
- `RetainLease`: Keep mission leases alive while the mission is running. This allows the mission to run a larger variety of missions without requiring the mission service’s client to keep the lease alive.
- `RestartWhenPaused`: Restarts its child tree when a mission resumes, rather than resuming its child from the state it was in when it paused.

#### Enable and Disable IR Emitters

A new `IREnableDisable` service and request have been added. This request allows clients to enable/disable the robot's IR light emitters in the body and hand sensors. This new service supports special situations where Spot's emitters may interfere with a custom attached payload. Disabling the IR emission will cause a SystemFault to be raised and have a negative effect on mobility since the robot's perception system is hindered.

### Bug fixes and improvements

#### Graph Nav

For RPCs that can fail because the robot is impaired, the response message now includes a RobotImpairedState message providing details about the nature of the impairment.

NavigationFeedbackStatus now includes body_movement_status to make it simple to determine when the body has come to rest after completing navigation.

Directed exploration and alternate route finding can now be disabled using new fields in TravelParams.

RouteFollowingParams have been added to NavigateRouteRequest to specify the desired behavior in certain situations (not starting from the start of the route, resuming a route, and becoming blocked on a route).

New methods `navigate_to_full()` and `navigate_route_full()` has been added to the Graph Nav client which will return the full response instead of just the command id.

Additional statuses have been added to NavigateRouteResponse (`STATUS_NO_PATH` and `STATUS_NOT_LOCALIZED_TO_MAP`) to capture possible errors.

UploadGraph can fail with `STATUS_INVALID_GRAPH` when the specified graph is invalid, for example containing missing waypoints referenced by edges.

DownloadWaypointSnapshotRequest has an additional option to not include point cloud data.
The new has_remote_point_cloud_sensor field in WaypointSnapshot indicates that the point has point cloud data from a remote service.

Starting to record a new map can fail with the new status `STATUS_TOO_FAR_FROM_EXISTING_MAP`.

The RPC for creating a new waypoint can now be provided a list of world objects to include in that waypoint’s snapshot.

#### Missions

For very large missions, a new RPC has been added to the mission service to stream the mission to the robot in chunks, rather than as a single message. The chunks should still deserialize to the same LoadMissionRequest message when assembled.

When a mission node fails to compile, the resulting FailedNode message has a new string that lists the protobuf type of the node implementation.

#### Arm and Gripper Control

We have improved the feedback for ArmJointMoveCommand Requests to now include the status of the underlying trajectory planner and to return the planner’s solved trajectory, which is the trajectory the robot will execute.

The ManipulationFeedbackState contains extra enum values for additional placing states that the robot can be in during manipulation.

By default, the robot will assume all grasped items are not “carriable”. We have modified ApiGraspOverride to be able to override the carry state to one of `CARRIABLE`, `NOT_CARRIABLE`, or `CARRIABLE_AND_STOWABLE`.

If holding an item, the stowing behavior is:

- `NOT_CARRIABLE` and `CARRIABLE` - The arm will not stow, instead it will stop
- `CARRIABLE_AND_STOWABLE` - The arm will stow while continuing to grasp the item

In addition, the communication loss behavior of the arm when it is holding an item is also modified:

- `NOT_CARRIABLE` - The arm will release the item and stow
- `CARRIABLE` - The arm will not stow, instead entering stop
- `CARRIABLE_AND_STOWABLE` - The arm will stow while continuing to grasp the item

#### Docking

The docking state includes additional “in-between” states, `DOCK_STATUS_UNDOCKING` and `LINK_STATUS_DETECTING` that indicate that a process is still ongoing.
Additional errors have been added to DockingCommandResponse for particular ways that docking can fail (`STATUS_ERROR_GRIPPER_HOLDING_ITEM`, `STATUS_ERROR_NOT_AVAILABLE`, `STATUS_ERROR_SYSTEM`).
The feedback also has a new error status: `STATUS_ERROR_NOT_AVAILABLE`.
See the [protobuf documentation](../protos/bosdyn/api/docking/docking.proto) for more details.

The docking python client include a new `docking_command_full()` call which returns the full response instead of only the command id. Additionally a new `docking_command_feedback_full()` returns the full feedback instead of only the status.

#### Network Compute Bridge

Models can now have a list of labels associated with them.

When the image is requested to be rotated, the rotation angle will be returned in the response.

#### Data Acquisition

DataAcquisitionCapabilities can now also report the plugin service name of the service that will be performing that acquisition.

The DataAcquisitionClient has a new `acquire_data_from_request()` that takes a full request proto, instead of building it internally.

The DataService client has been updated to have the correct service name.

#### Robot Commands

Power commands can now report a `STATUS_OVERRIDDEN` if the robot overrides the power command and disables motor power.

Power command responses and feedback will report system faults if a fault blocks the power command from succeeding.

LeaseUseResults have been added to messages for RobotCommand and ManipulationApi

New helpers `safe_power_off_robot()` and `safe_power_cycle_robot()` can completely power off the robot or power cycle the robot from any robot state.

Additional options have been added to ObstacleParams for tuning obstacle avoidance by turning off negative obstacle avoidance or body assist for avoiding foot obstacles.

#### Leases

Leases represent ownership over the robot. Leases have been updated to support ownership over only part of the robot, so that you can delegate control to different services, such as using Graph Nav to control robot mobility while simultaneously controlling the robot’s arm via a user-written script. Details are in the [lease documentation](concepts/lease_service.md), but in general users can just continue to use the “body” lease and everything will work as expected.

#### Other Changes

The image service will now report `PixelFormat` for JPEG image sources even though the pixel format can be determined from the JPEG header.

Spot Check has some additional failure statuses that it can report.

Events logged to the data buffer may now include a LogPreserveHint to tell the robot whether this event is worth preserving a log for.

RobotState now includes additional data about the terrain under each foot.

Additional properties have been added to world objects to assist in image processing.

An additional level of hierarchy has been added for transport-level errors to simplify most error cases. RpcError has two new subclasses: `PersistentRpcError` and `RetryableRpcError`. `PersistentRpcError` indicates an error such that attempting to retry the call will fail again. `RetryableRpcError` means that the call _may_ succeed if retried.

Calling `ensure_secure_channel()` directly will now result in max message sizes not being correctly.

### Breaking Changes

Invalid RobotCommands will no longer result in `STATUS_INVALID_REQUEST` in the RobotCommandResponse message, but will instead use the `CODE_INVALID_REQUEST` error in the common header, like other RPCs do. In the python client library, this will still raise the same `InvalidRequestError` as before.

E-stops may not be unregistered from the estop service while the robot’s motors are powered. This prevents accidentally powering the robot off. A new `STATUS_MOTORS_ON` status will be returned in the response to indicate this error. To unregister an estop, first safely power off the robot.

RPCs to the AuthService and PayloadRegistration service are now rate-limited to 5 and 10 requests/second respectively. Requesting more than that will result in an HTTP 429 error, or raising the `TooManyRequestsError` if using the python client.

The “obstacle_distance” local grid inadvertently included some generated obstacles used only for foot-placement control. These grids no longer include those generated obstacle regions.

The python function `bosdyn.client.lease.test_active_lease` previously took an optional `make_sublease` argument. That has been replaced with an optional `sublease_name` argument so that if a sublease is desired, it gets created with a client name correctly.

The StraightStaircase message has been moved to bosdyn/api/stairs.proto so that it can be used in more places. This is compatible with existing serialized protobufs, but any code that is manually creating these messages will need to be updated.

### Deprecations

#### Robot Control

The `enable_grated_floor` field is superseded by the new `grated_surfaces_mode` which will auto-detect the need for grated surface handling.

The `safe_power_off()` helper has been replaced by the less ambiguous `safe_power_off_motors()` helper.

The `docking_command_feedback()` method of DockingClient incorrectly raised an exception if the docking command had encountered lease errors, and has been replaced by `docking_command_feedback_full()` which returns the full feedback response.

#### Graph Nav

For limiting the speed on an edge, use the `vel_limit` in `mobility_params` instead of the Edge annotation’s `vel_limit`.

#### Missions

Docking nodes should not use the child node anymore. If a mission needs to react to docking results, it should use the responses written into the blackboard by the docking node.

#### Payloads

The `guid` and `secret` fields on payload registration RPCs have been replaced with a standardized `PayloadCredentials` message.

#### Writing services

Many helpers for writing services and filling out responses have been moved from `bosdyn.client.util` to `bosdyn.client.server_util`.

`bosdyn.mission.server_util.set_response_header()` has been moved to `bosdyn.client.server_util.set_response_header()`, so that it can be used by any service, not only those depending on missions.

### Known Issues

**When a network transport failure occurs,** depending on the particular operating system and version of gRPC installed, the error from the python SDK may not always be the most specific error possible, such as `UnknownDnsNameError`. It may instead be raised as either a generic `RpcError`, or another generic failure type such as `UnableToConnectToRobotError`.

**Spot CAM LED illumination levels** are not currently recorded or played back in Autowalk missions.

**If you write a custom data acquisition plugin or image service,** do not change its `DataAcquisitionCapability` or `ImageSource` set once it is running and registered. New capabilities may not be detected, and old capabilities may still be listed as available in the Data Acquisition service. To change the capabilities of a service: unregister it from the directory, wait until its capabilities are no longer listed in the Data Acquisition service, and then re-register it. This waiting also applies to restarting a service if its capabilities will be different upon restart.

**If you write a custom data acquisition plugin without using our helper class,** its `GetStatus()` RPC is expected to complete immediately. If it takes too long to complete it can cause timeouts when requesting `GetStatus()` of the data acquisition service.

**If you register a new service with the robot**, calling `robot.ensure_client()` to create a client for that service may result in a `UnregisteredServiceNameError`.

- Workaround: call `robot.sync_with_directory()` before `robot.ensure_client()`

**SE2VelocityLimits require care**. Correct usage of the `SE2VelocityLimit` message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

### Sample Code

[**Animation Recorder (new)**](../python/examples/animation_recorder/README.md)
Demonstrates recording motion made with the tablet and then playing it back with the choreographer service.

[**Arm Constrained Manipulation (new)**](../python/examples/arm_constrained_manipulation/README.md)
Demonstrates using constrained manipulation to turn a crank.

[**Auto Return (new)**](../python/examples/auto_return/README.md)
Demonstrates setting up and triggering the Auto Return service.

[**Data Buffer (new)**](../python/examples/data_buffer/README.md)
Demonstrates adding several different kinds of data to the data buffer.

[**Get Depth Plus Visual Image (new)**](../python/examples/get_depth_plus_visual_image/README.md)
Demonstrates how to use the `depth_in_visual_frame` image sources to visualize depth in a visual image.

[**Graph Nav Extract Point Cloud (new)**](../python/examples/graph_nav_extract_point_cloud/README.md)
Demonstrates opening and parsing a GraphNav map and extracting a globally consistent point cloud from it.

[**Post-Docking Callbacks (new)**](../python/examples/post_docking_callbacks/README.md)
Builds docker images for mission callbacks that can upload data acquired during a mission.

[**Disable IR Emission (new)**](../python/examples/disable_ir_emission/README.md)
Demonstrates enabling and disabling IR light emitters via the IREnableDisableService Client.

[**Arm Gaze (updated)**](../python/examples/arm_gaze/README.md)
Updated to use `block_until_arm_arrives()` instead of a `sleep()`

[**BDDF Download (updated)**](../python/examples/bddf_download/README.md)
Now provides a Qt-based downloading UI.

[**Data Acquisition Service (updated)**](../python/examples/data_acquisition_service/README.md)
Now provides a plugin for capturing data from the network compute bridge.

[**Frame Trajectory Command (updated)**](../python/examples/frame_trajectory_command/README.md)
Now takes arguments that specify how to move instead of performing fixed motions.

[**Graph Nav Command Line (updated)**](../python/examples/graph_nav_command_line/README.md)
Now can navigate to a position in an anchoring. The recording example provides options to automatically close loops in the map or optimize the map's anchoring.

[**View Map (updated)**](../python/examples/graph_nav_view_map/README.md)
Now can display the map according to the anchoring.

[**Mission Recorder (updated)**](../python/examples//README.md)
New option to build a mission from the graph on the robot.
New command to automatically close loops in the graph.
Uses NavigateRoute to follow waypoints in order.

[**Network Compute Bridge (updated)**](../python/examples/network_compute_bridge/README.md)
Now includes options to run and test a worker without needing a robot. Also includes files to build docker images for deployment.

[**Payloads (updated)**](../python/examples/payloads/README.md)
Now includes an example of how to attach and detach a payload.

[**Replay Mission (updated)**](../python/examples/replay_mission/README.md)
Now includes extra options for playing back Autowalk missions, as well as disabling directed exploration.

[**Ricoh Theta (updated)**](../python/examples/ricoh_theta/README.md)
Now includes a "live stream" option that provides a higher frame rate at the cost of lower-quality stitching. (Thanks Aaron Gokasian!)

[**Spot Cam (updated)**](../python/examples/spot_cam/README.md)
New options for getting and setting PTZ focus, audio capture channel, and audio capture gain. Also an option for enabling congestion control for the stream quality.

[**WASD (updated)**](../python/examples/wasd/README.md)
The Escape key can now be used to stop the robot.

[**Webcam Image Service (updated)**](../python/examples/service_customization/custom_parameter_image_server/README.md)
New resolution options allow for capturing from the webcam at different resolutions.

## 2.3.5

### New Features

#### Spot CAM

Added `InitializeLens` RPC, which resets the PTZ autofocus without needing to power cycle the Spot CAM.

#### Data Buffer

A new `sync` option has been added to `RecordDataBlobsRequest` which specifies that the RPC should not return a response until the data has been fully committed and can be read back.
This is exposed through the optional `write_sync` argument to the `add_blob()` and `add_protobuf()` methods of the `DataBufferClient`.

### Bug fixes and improvements

When running with a Spot CAM+ (PTZ) running 2.3.5, the `SetPowerStatus` and `CyclePower` endpoints will now return an error if the PTZ is specified. These endpoints could previously cause the WebRTC feed to crash. These RPCs are still safe to use for other devices, but due to hardware limitations, resetting the PTZ power can possibly cause the Spot CAM to require a reboot to regain the WebRTC stream.

`RetryableUnavailableError` was raised in more cases than it should have been, and it is now more selectively raised.

The `EstopKeepAlive` expected users to monitor its status by popping entries out of its `status_queue`. If the user did not do so, the queue would continue to grow without bound.
The queue size is now bounded and old unchecked entries will be thrown away. The queue size is specified with the `max_status_queue_size` argument to the constructor.

### Breaking Changes

As stated above, the behavior of `SetPowerStatus` and `CyclePower` endpoints have been changed for Spot CAM+ units when attempting to change the power status of the PTZ. They now return an error instead of modifying the power status of the PTZ. They remain functional for the Spot CAM+IR. Clients using these SDK endpoints to reset the autofocus on the PTZ are recommended to use `InitializeLens` instead. Other clients are encouraged to seek alternative options.

### Deprecations

The `ResponseContext` helper class has been moved to the bosdyn-client package (from the bosdyn-mission package), so that it can be used for gRPC logging in data acquisition plugin services in addition to the mission service. The new import location will be from `bosdyn.client.server_util`, and the original import location of `bosdyn.mission.server_util` has been deprecated.

### Known Issues

Same as 2.3.0

## 2.3.4

### New Features

#### Power Control

New options have been added to the Power Service to allow for power cycling the robot and powering the payload ports or wifi radios on or off. Additional fields have been added to the robot state message to check the payload and wifi power states. Support has also been added to the `bosdyn.client` command line interface for these commands.

These new options will only work on some Enterprise Spot robots. Check the HardwareConfiguration message reported by a particular robot to see if it supports them.

### Bug fixes and improvements

Fixed an issue that could cause payload registration or directory registration keep-alive threads to exit early in certain cases.

Fixed a couple issues with the webcam example: updated the Dockerfile to create a smaller container specifically with python 3.7, added new optional argument to specify the video codec, and programmatically prevent substring arguments other than the `--device-name` argument to avoid accidental confusion with the docker container's `--device` argument.

### Known Issues

Same as 2.3.0

### Sample Code

A new [tutorial](python/fetch_tutorial/fetch1.md) has been added to walk through using machine learning, the Network Compute Bridge, and Manipulation API to play fetch with Spot.

## 2.3.3

### New Features

#### Graph Nav

The python Graph Nav client now allows setting an offset to the destination, for navigating to a position relative to the final waypoint instead of exactly matching the final waypoint position and orientation.

### Bug fixes and improvements

Fixed issues where the data acquisition download helpers did not handle absolute paths on windows and did not clean filenames correctly. (Thanks David from Levatas!)

Zip file names from the data download service no longer contain difficult characters.

Fixed an issue where Graph Nav would sometimes report the robot was impaired on the first usage after restarting the robot.

Errors returned from Network Compute Bridge workers will be better propagated in the Network Compute Bridge response.

Updated background threads for the payload and directory registration helpers to silently ignore transient errors.

Fixed an issue where requesting thermal images with PTZ/Pano images in a single data acquisition action caused thermal images to either not be collected or saved as “blank” images.

### Breaking Changes

The estop service will now refuse to change configuration if the robot is already powered on, returning a status of STATUS_MOTORS_ON. This prevents accidentally cutting power while the robot is in operation.

### Known Issues

Same as 2.3.0

### Sample Code

[**Network Compute Bridge**](../python/examples/network_compute_bridge/README.md)
Updated to provide appropriate error messages from the workers.

## 2.3.2

### New Features

#### SpotCAM

The SpotCAM API has been expanded to support more use cases for the SpotCAM+IR (thermal PTZ variant). This includes the following new endpoints:

- `SetIrColormap`/`GetIrColormap`: Set/get the mapping between radiometric IR samples to color, for video
- `SetIrMeterOverlay`: Set location for the "Spot Meter", which indicates temperature at a point in the thermal video stream.

The SpotCAM Power API now has an additional endpoint to cycle power for any of the components that could previously be toggled using `SetPowerStatus`. `CyclePower` can be used to help the PTZ recover from adverse behavior, such as incorrect auto-focus or poor motor behavior, which can sometimes happen as the result of a robot fall. `CyclePower` will wait the appropriate amount of time between turning components off and turning on again to make sure the power is cycled correctly without the client needing to know the correct interval.

### Known Issues

Same as 2.3.0

### Sample Code

[**Get image (updated)**](../python/examples/get_image/README.md)
Support for the new pixel format of IR images.

[**Ricoh Theta (updated)**](../python/examples/ricoh_theta/README.md)
Improved parsing of timestamp information from the camera.
Correctly set the image proto format field.
Defaults to not capturing continuously. Flags `--capture-continuously` and `--capture-when-requested` can be used to specify the desired behavior.

[**Spot CAM (updated)**](../python/examples/spot_cam/README.md)
Support for IR images and power cycling functionality.

## 2.3.0

### New Features

#### Arm and Gripper Control

One of the main features of the 2.3 release is control and support of Spot's arm and gripper. Arm and gripper commands are included in the `SynchronizedCommand` message, and can be commanded in addition to mobility commands. The `RobotCommandBuilder` in the SDK provides many new helpers for building new arm and gripper commands. The synchro command builder functions now have an optional `build_on_command` argument, which is used to build a mobility/arm/gripper command onto an existing command, merging them correctly.
The arm and gripper state are reported in the new `manipulator_state` field of the robot state. The Python SDK `Robot` class now has a `has_arm()` helper to determine if the robot has an arm or not.
For more information about controlling the arm, see the [arm documentation](concepts/arm/README.md).

**Manipulation API (beta)**
This new API provides some high-level control options for walking to and picking up objects in the world.

**Arm Surface Contact (beta)**
ArmSurfaceContactService lets you accurately move the robot's arm in the world while having some ability to perform force control. This mode is useful for drawing, wiping, and other similar behaviors.

**Doors (beta)**
DoorService will automatically open and move through doors, once provided some information about handles and hinges.

#### Network Compute Bridge

An interface for integrating real-time image processing and machine learning for identifying objects and aiding grasping.
For more information, see the [network compute bridge documentation](concepts/network_compute_bridge.md).

#### Payload Estimation

A new `PayloadEstimationCommand` is available to have Spot try to estimate the mass properties of a payload itself. After moving about to perform its estimation, the mass properties will be reported in the command feedback.

#### SpotCAM

Some SpotCAMs now include an IR camera. There are additional cameras and screens available for those versions, and a new pixel format `PIXEL_FORMAT_GREYSCALE_U16` used to represent those IR images. There are additional RPCs used to set colormaps and overlays of the IR images for live display.

Logpoint `QUEUED` status is now broken up further with the `queue_status` field, which differentiates between when the image has or has not been captured.

#### Arm Support in Choreographer

The new Choreographer executable now includes two new tracks, gripper and arm, and includes new dance moves which control the arm.

#### Docking

A new `PREP_POSE_UNDOCK` command option can be used to undock a docked robot. It will return the new `STATUS_ERROR_NOT_DOCKED` if the robot was not already docked. When successful the status will be `STATUS_AT_PREP_POSE`.

#### Graph Nav

When localizing the robot using `FIDUICIAL_INIT_SPECIFIC`, if the target waypoint does not contain a good measurement of the desired fiducial, nearby waypoints may be used to infer the robot's location. This behavior can be disabled with the new `restrict_fiducial_detections_to_target_waypoint` field to only use the waypoint’s own data.

A new `destination_waypoint_tform_body_goal` is provided for the `NavigateTo` and `NavigateRoute` RPCs. This allows the user to specify a goal position that is offset from the destination waypoint, rather than exactly on the waypoint.

A new `command_id` field can be specified on the `NavigateTo` and `NavigateRoute` RPCs. This is used to continue a previous command without needing to re-specify all the data. An important difference between specifying the `command_id` versus sending a new command is that if the robot has reported itself stuck, continuing a command will result in a `STATUS_STUCK` error, rather than trying again. A new `STATUS_UNRECOGNIZED_COMMAND` will be returned if the `command_id` does not match the currently executing command.

The map representation now tracks the “source” of waypoints and edges. It is possible to override the cost of an edge used when planning paths and to disable the alternate route finding for a particular edge.

#### Leases

Leases now include client names alongside the sequence number for help in debugging. If you are writing a custom client, make sure to append your client name any time that you create a sub-lease.

ListLeases can optionally request to have the full lease information of the latest lease, rather than only the root lease information that was previously reported.

### Bug Fixes and Improvements

In the seconds following modifications to the robot directory to the robot directories existing clients may experience a one time request failure. This failure is transient and can be resolved by retrying the request. This has been an expected failure case and a new error (RetryableUnavailableError) has been put in to better reflect the failure.

`SE3Pose` and `Quat` math helpers have `transform_vec3` members to simplify rotating vectors.

There is a new `get_self_ip()` helper in `common.py` for determining the ip address your client will use to talk to the robot. This is useful for determining the correct registration information for a service, particularly on a machine with multiple network interfaces. This is also available via the python command line program `python3 -m bosdyn.client <robot host> self-ip`.

When listing events from the python command line program, you can now filter by event level and by event type.

### Dependencies

The python SDK now depends on the `Deprecated` package, which is used to mark functions and classes that are deprecated and provide warnings, so that users are made aware that features that they are using may be removed in the future.

### Deprecations

The Deprecated package has been implemented across the SDK so that deprecated features will print out a warning when they are called. Documentation surrounding deprecated features has also been updated.

### Breaking Changes

Spot Check no longer computes the `foot_height_results` or `leg_pair_results` fields.

All RPCs in the Python SDK have a default timeout of 30s. The global timeout can be changed by assigning a new value to `bosdyn.client.common.DEFAULT_RPC_TIMEOUT`, and individual RPC calls can still set their own timeout via a `timeout=sec` optional parameter at any call site.

### Known Issues

**When a network transport failure occurs,** depending on the particular operating system and version of gRPC installed, the error from the python SDK may not always be the most specific error possible, such as `UnknownDnsNameError`. It may instead be raised as either a generic `RpcError`, or another generic failure type such as `UnableToConnectToRobotError`.

**Spot CAM LED illumination levels** are not currently recorded or played back in Autowalk missions.

**When capturing both a PTZ and Panoramic image** in the same action, there may occasionally be two PTZ images captured along with the Panoramic image, rather than just one.

**If you write a custom data acquisition plugin or image service,** do not change its `DataAcquisitionCapability` or `ImageSource` set once it is running and registered. New capabilities may not be detected, and old capabilities may still be listed as available in the Data Acquisition service. To change the capabilities of a service: unregister it from the directory, wait until its capabilities are no longer listed in the Data Acquisition service, and then re-register it. This waiting also applies to restarting a service if its capabilities will be different upon restart.

**If you write a custom data acquisition plugin without using our helper class,** its `GetStatus()` RPC is expected to complete immediately. If it takes too long to complete it can cause timeouts when requesting `GetStatus()` of the data acquisition service.

**If you register a new service with the robot**, calling `robot.ensure_client()` to create a client for that service may result in a `UnregisteredServiceNameError`.

- Workaround: call `robot.sync_with_directory()` before `robot.ensure_client()`

**SE2VelocityLimits require care**. Correct usage of the `SE2VelocityLimit` message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

### Sample Code

[**Arm and Mobility Command (new)**](../python/examples/arm_and_mobility_command/README.md)
Demonstrates how to issue both mobility and arm commands to the robot at the same time.

[**Arm Door (new)**](../python/examples/arm_door/README.md)
Demonstrates how to use the door service to have Spot autonomously open a door. It opens an image display and requires the same use input as when opening a door with the tablet.

[**Arm Force Control (new)**](../python/examples/arm_force_control/README.md)
Demonstrates how to create force controlled trajectories for the arm and gripper.

[**Arm Gaze (new)**](../python/examples/arm_gaze/README.md)
Shows how to command multiple different types of gaze requests.

[**Arm GCode (new)**](../python/examples/arm_gcode/README.md)
Uses the arm surface contact API to write GCode on the ground using sidewalk chalk.

[**Arm Grasp (new)**](../python/examples/arm_grasp/README.md)
Shows how to use the manipulation API to autonomously grasp an object based on the object’s image coordinates in pixel space. It opens an image view and lets a user select an object by clicking on the image, similar to grasping with the tablet.

[**Arm Joint Move (new)**](../python/examples/arm_joint_move/README.md)
Shows how to create and command a joint move trajectory.

[**Arm Simple (new)**](../python/examples/arm_simple/README.md)
A starter example which shows how to issue the robot command RPC with a basic arm command which moves the end effector to a couple different positions.

[**Arm Stow Unstow (new)**](../python/examples/arm_stow_unstow/README.md)
Shows how to issue API commands to stow and unstow the arm.

[**Arm Surface Contact (new)**](../python/examples/arm_surface_contact/README.md)
Uses the arm surface contact API to request an end effector trajectory move which applies some force to the ground.

[**Arm Trajectory (new)**](../python/examples/arm_trajectory/README.md)
Demonstrates how to create an arm command with a position-based trajectory.

[**Arm Walk to Object (new)**](../python/examples/arm_walk_to_object/README.md)
This example shows how to use the manipulation api to command the robot to walk towards an object and prepare to grasp it. The example opens an image view and lets a user select an object by clicking in the image.

[**Arm With Body Follow (new)**](../python/examples/arm_with_body_follow/README.md)
Shows how to issue arm commands that allow the body to move to a good position to achieve the desired arm command.

[**Comms Test (updated)**](../python/examples/comms_test/README.md)
The comms test example can now successfully be run with Docker.

[**Data Acquisition Service Plugins (updated)**](../python/examples/data_acquisition_service/README.md)
The directory structure has changed to create individual directories for each plugin (and the plugin’s Dockerfile and requirements files).

[**Data Service (updated)**](../python/examples/data_service/README.md)
A new example script, delete_pages.py, has been added to remove log pages from robots.

[**Estop (updated)**](../python/examples/estop/README.md)
The estop no-gui example’s logging statements have been improved.

[**GraphNav Command Line (updated)**](../python/examples/graph_nav_command_line/README.md)
Has commands to clear the map on the robot, and to manually close the loop in a map. Updated to properly return the lease when exiting the script. Optimized to only upload snapshots to the robot that are not already present.

[**Mission Recorder (updated)**](../python/examples/mission_recorder/README.md)
Fixed the localization node to use the nearest fiducial.

[**Network Compute Bridge (new)**](../python/examples/network_compute_bridge/README.md)
The example has a network compute bridge work service example, which runs a tensorflow model and registers the service with the robot.
Additionally, the example contains a client-side example that queries the network compute bridge service to identify objects in the robot camera images using the server’s tensorflow model.

[**Replay Mission (updated)**](../python/examples/replay_mission/README.md)
Optimized to only upload snapshots to the robot that are not already present. Has an option to disable alternate route finding when running a mission.

[**Ricoh Theta (updated)**](../python/examples/ricoh_theta/README.md)
Fixes a missing import required to run the continuous capture thread.

[**Self Registration (updated)**](../python/examples/self_registration/README.md)
Updated to create a payload with more realistic sample values.

[**Spot CAM (updated)**](../python/examples/spot_cam/README.md)
The WebRTC example now records audio. The compositor example now includes Spot CAM IR support.

[**Upload Choreographed Sequence (updated)**](../python/examples/upload_choreographed_sequence/README.md)
Returns a clearer error message if being used with an incorrect license.

[**Web Cam Image Service (updated)**](../python/examples/service_customization/custom_parameter_image_server/README.md)
The web cam example now has better support for Windows, and has a debug mode which will show a popup image window of the camera image.

## 2.2.0

### New Features

#### Docking (license dependent)

Automated docking at charging stations is out of beta and available for enterprise customers. There have been a few updates to the protos regarding status reporting and handling "prep" poses.

#### Payload Authorization Faults

Payloads that have been registered with the robot but have not yet been authorized will automatically have service faults raised on their behalf indicating their status. This will help prevent operators from forgetting to authorize payloads after attaching them to the robot.

#### Service and plugin development

**Image Services**
Helper functions for creating image services that reduce the amount of boiler plate code required for creating an image service and ensure the necessary fields of the response RPCs will be populated by the service.

**Data Acquisition Service**
Helper functions for communicating with the on robot data acquisition service to acquire data, monitor the status of the acquisition, cancel requests, and download the data using the REST endpoint. These functions originally were in the data_acquisition_service example, but are now part of the `bosdyn-client` wheel.

#### `SE2TrajectoryCommand` Feedback

Added new status `STATUS_NEAR_GOAL` as well as a new `BodyMovementStatus` to help differentiate between different kinds of states the robot can be in at the end of its trajectory.

#### Missions

The `BosdynGraphNavLocalize` node can now specify a full `SetLocalizationRequest`, rather than only localizing to the nearest fiducial.

When comparing blackboard values, there is a new `HandleStaleness` option to specify what the node should do if the blackboard value is stale.

#### Other Helper Functions\*\*

- `is_estopped()` helper for the estop client and robot.
- Helper functions to create time ranges in the robot’s time.
- Downloader script for bddf log files.

### Bug fixes and improvements

**Data Acquisition**
Data Acquisition Service on robots is now robust to port number changes. The previous workaround to this problem was to always specify the same port when starting/restarting a service. Now, the port argument for external api services can use the default, which will choose an available ephemeral port.

**Image Services**
Robot Cameras image service will respond to GetImage requests with incorrect format (e.g. requesting a depth image as format JPEG) using the `STATUS_UNSUPPORTED_IMAGE_FORMAT_REQUESTED`. Previously, this was returned as `STATUS_IMAGE_DATA_ERROR`.

**The Ricoh Theta image service example improvements**

- Automatically disables sleep mode when putting the ricoh theta into client mode (using `ricoh_client_mode.py`).
- By default, it now runs a background thread capturing images continuously to minimize the delays waiting for an image to appear when viewing from the camera.
- It will wait for the capture to be completely processed before returning an image. This fixes issues where a very old image would be displayed, since it would trigger a take picture, but just return the most recent processed image.

**Command line client**
The "log" and "textmsg" commands now go through the DataBuffer service, and so can be read back by downloading bddf files from the robot.

**EstopService timeout**
The maximum timeout on the EstopService (aka the motor cut authority) has been raised from 65 seconds to just over 18 hours and 10 minutes. The estop service also correctly reports an error if given an invalid timeout.

### Deprecations

BDDF code has moved to the `bosdyn-core` package, so that it can be used separately from the client code. The new import location is `bosdyn.bddf`. The old import path via `bosdyn.client.bddf` is deprecated.

### Dependency Changes

`bosdyn-client` now depends on the `requests` library for making http requests to download data acquisition results and bddf logs.

### Known issues

**When a network transport failure occurs,** depending on the particular operating system and version of gRPC installed, the error from the python SDK may not always be the most specific error possible, such as `UnknownDnsNameError`. It may instead be raised as either a generic `RpcError`, or another generic failure type such as `UnableToConnectToRobotError`.

**Spot CAM LED illumination levels** are not currently recorded or played back in Autowalk missions.

**When capturing both a PTZ and Panoramic image** in the same action, there may occasionally be two PTZ images captured along with the Panoramic image, rather than just one.

**If you write a custom data acquisition plugin or image service,** do not change its `DataAcquisitionCapability` or `ImageSource` set once it is running and registered. New capabilities may not be detected, and old capabilities may still be listed as available in the Data Acquisition service. To change the capabilities of a service: unregister it from the directory, wait until its capabilities are no longer listed in the Data Acquisition service, and then re-register it. This waiting also applies to restarting a service if its capabilities will be different upon restart.

**If you write a custom data acquisition plugin without using our helper class,** its `GetStatus()` RPC is expected to complete immediately. If it takes too long to complete it can cause timeouts when requesting `GetStatus()` of the data acquisition service.

**If you register a new service with the robot**, calling `robot.ensure_client()` to create a client for that service may result in a `UnregisteredServiceNameError`.

- Workaround: call `robot.sync_with_directory()` before `robot.ensure_client()`

**SE2VelocityLimits require care**. Correct usage of the `SE2VelocityLimit` message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

### Sample Code

[**Image service test program (new)**](../python/examples/tester_programs/README.md)
A new tester program for image services is available to help with the development and debugging of new image service implementations.

[**Docking (new)**](../python/examples/docking/README.md)
Shows how to trigger the docking service to safely dock the robot on a charger.

[**Web Cam Image Service (updated)**](../python/examples/service_customization/custom_parameter_image_server/README.md)
The web cam example now uses the new image service helpers.

[**Ricoh Theta Image Service (updated)**](../python/examples/ricoh_theta/README.md)
Uses the new image service helpers. A few extra bug fixes as described above.

[**Data Service (updated)**](../python/examples/data_service/README.md)
Added options to specify a time range, and automatically converts times to robot time.

[**Data acquisition (updated)**](../python/examples/data_acquisition_service/README.md)
Uses the new data acquisition helpers. The data acquisition tester program has been moved to a common [`tester_programs`](../python/examples/tester_programs/README.md) directory.

## 2.1.0

### New Features

#### Spot I/O: [Data Acquisition](concepts/data_acquisition_overview.md)

This release features a new system for acquiring, storing, and retrieving sensor data. It consists of several new services and their associated clients.

**Data Acquisition Service**: The coordinating service that will capture images, robot metadata, and delegate to plugins to capture custom sensor data.

**[Data Acquisition Plugins](concepts/writing_services_for_data_acquisition.md)**: User-implemented services that can capture data from sensors and save it into the store.

**Data Acquisition Store**: Interface for saving data and metadata to disk for later retrieval.

**[Image services](concepts/writing_services_for_data_acquisition.md)**: Existing interface used in a new way. User-implemented image services will now be displayed in the tablet for driving, and be automatically capturable by the Data Acquisition Service.

#### New Mobility Commands

**Stance**: Allows precise placement of the feet of the robot, beyond just positioning the body.

**Battery change pose**: Rolls Spot over so that the battery is accessible removal and replacement.

#### Arm Control Preparation

Several changes have been made in preparation for the release of Spot’s arm. These represent new ways to accomplish the same control as before, but in a way that will be compatible with also controlling the robot’s arm in a future release.

**Synchronized commands and feedback**: A new synchronized_command for combining mobility control with arm and gripper control. This deprecates the `mobility_command` in the `RobotCommand` message. Additionally, the top-level command status has been moved into the individual full-body and mobility command feedback messages so that mobility and arm commands can individually report their state.

**Stop**: The existing full-body `Stop` command still exists, but there is an additional mobility-only `Stop` command that can be used to only stop the mobility without affecting any separate arm control.

#### [Service Faults](concepts/faults.md)

To simplify the development of reliable services and report when problems arise, a new set of reportable faults has been added, usable by all services.

**Fault Service**: Used to report or clear faults pertaining to a service or payload. The Python SDK includes a client library for triggering and clearing faults through this service.

**ServiceFaultState in RobotState**: All reported service faults will be included in the `RobotState` message. Clearing active faults will move them into historical faults. All service faults will automatically be displayed in the tablet interface to inform users.

**Directory and Payload Liveness faults**: New options for directory and payload registration enable liveness monitoring. When this feature is implemented, alongside directory or payload keep-alives, service faults will be automatically raised when a service crashes or a payload disconnects.

**Integrations**: Boston Dynamics supported payloads incorporate service faults and liveness monitoring out of the box.

- Spot CORE will report service faults if it experiences issues during startup, fails to communicate with the robot, detects an invalid payload configuration, or fails to communicate to an expected LiDAR.
- Spot CAM will report service faults if it is disconnected from Spot or if any of its internal services crash.
- The `bosdyn.client` command line interface can show and monitor reported faults.

#### Data Logging

The robot now dedicates some internal storage space to user data and logging. In addition to the data acquisition system, the user can store messages, events, time-series data, or arbitrary binary blobs.

**Data Buffer**: New service interface for storing various kinds of data on the robot.

**Data Service**: Retrieval service that can be used to return the data stored in the data buffer.

**BDDF**: File format for large downloads of stored data, and tools for reading the file.

**Download endpoints**: HTTPS download of a zip file of data acquisition mission datasets or bddf-encoded data.

#### Point Clouds

Point cloud service definitions are provided for retrieving point cloud data from LiDAR sensors, such as from the EAP payload.

#### Spot CAM

Congestion control is now available for WebRTC streaming.
External microphones supported, with control for selecting microphones and setting gain levels individually. Note: External microphone support only available on Spot CAM + IR.

#### Graph Nav

The localization data now includes a transform to a "seed" frame, providing a consistent global frame for use across multiple runs on the same map.

Localization data can be requested relative to a particular waypoint, rather than only the waypoint that the robot is currently localized to.

Additional control for determining whether the robot will navigate through areas with poor quality features.

#### Missions

Additional mission nodes which support new functionality:

- Point the Spot CAM PTZ to a specified orientation.
- Dock the robot at a charging station.
- Capture data through the data acquisition service.
- Manipulate strings in the blackboard.

#### Choreography (License-dependent)

Play advanced choreographed routines for Spot. The choreography service requires a special license to use.

#### Docking (Beta, License-dependent)

The new docking service provides a way to autonomously dock at a charging station. It is currently in beta, and requires a special license to use.

### Bug Fixes and Improvements

**Graph Nav**

- Added fiducial-related status errors in `SetLocalizationResponse`, such as a fiducial being too far away or having poor data.
- Edges now record mobility params that were set during record time, and use them when navigating those edges.
- “Stuck” detection has changed, and the robot will report much sooner when it has no way to make progress.
- Improved `StartRecordingResponse` and `CreateWaypointResponse` to report errors about bad fiducials or point cloud data.

**Fiducial Detection**

- Fiducials now report a filtered pose in addition to the raw detected pose, to avoid jitter in individual detections.
- Fiducial detections include extra information, such as the detection covariance, camera frame, and status regarding ambiguity or error.

**Mission Nodes**

- The `BosdynGraphNavState` node can specify the id of the waypoint to use for the reported localization.

**Spot Check**

- Added status field in `SpotCheckCommandResponse`.
- Improved the list of errors in `SpotCheckFeedbackResponse` message.
- Spot Check now checks and reports results on hip range of motion.

**Python client**

- Blocking “power on” and “power off” helpers report errors correctly, rather than always raising `CommandTimedOutError` if the robot could not power on or off.
- Added helper classes for registering and launching services.
- Added the ability to authenticate the robot instance from payload credentials.
- Printing the Spot SDK exceptions now provides more information.
- Increased default message size limit for receiving and sending messages to 100 MB
- Command line interface supports the new 2.1 functionality
  - Payload commands.
  - Payload registration commands.
  - Fault commands.
  - Data buffer commands.
  - Data service commands.
  - Data acquisition commands.

**Image capture parameters**

- Added exposure and gain parameters associated with an image capture.

**License interface**

- Added `GetFeatureEnabled()` to the `LicenseService` to query for particular license features.

### Breaking changes

**Robot Control**

A behavior fault (`CAUSE_LEASE_TIMEOUT`) is raised when the usage of a lease times out, and must be cleared before the robot can be commanded again. This should have minimal effect on current clients, as this happens near the same time that the robot powers off from comms loss (which clears behavior faults).

**Graph Nav**

When GraphNav reports `STATUS_STUCK` while navigating, the robot will stop walking. It will need to be re-commanded to navigate in order to continue. Previous behavior was that the robot would continue walking when stuck until commanded to stop by a client.

**Missions**

Autowalk mission callback nodes only wait 10 seconds for a response. When a mission calls `Tick()` on a mission callback service, it expects a quick response. In 2.0 it would wait up to 60 seconds for a response before retrying. This has been reduced to 10 seconds in version 2.1. Callbacks that do any significant work should be written to return with `STATUS_RUNNING` quickly, and then continue to do their work on another thread rather than trying to fit in all of their work before returning a response. The service can then base their response to subsequent `Tick()` requests on the status of that thread.

### Known Issues

**When a network transport failure occurs,** depending on the particular operating system and version of gRPC installed, the error from the python SDK may not always be the most specific error possible, such as `UnknownDnsNameError`. It may instead be raised as either a generic `RpcError`, or another generic failure type such as `UnableToConnectToRobotError`.

**Spot CAM LED illumination levels** are not currently recorded or played back in Autowalk missions.

**When capturing both a PTZ and Panoramic image** in the same action, there may occasionally be two PTZ images captured along with the Panoramic image, rather than just one.

**If you write a custom data acquisition plugin or image service,** do not change its `DataAcquisitionCapability` or `ImageSource` set once it is running and registered. New capabilities may not be detected, and old capabilities may still be listed as available in the Data Acquisition service. To change the capabilities of a service: unregister it from the directory, wait until its capabilities are no longer listed in the Data Acquisition service, and then re-register it. This waiting also applies to restarting a service if its capabilities will be different upon restart.

Furthermore, always specify the port that it should run on via the `--port` flag, and do not change it between restarts of your plugin or image service. If you must change the port, then you must reboot the robot.

**If you write a custom data acquisition plugin without using our helper class,** its `GetStatus()` RPC is expected to complete immediately. If it takes too long to complete it can cause timeouts when requesting `GetStatus()` of the data acquisition service.

**If you configure the estop service with custom timeouts** and set an invalid timeout, you will not receive an error, but the robot will set the timeout to something else. The maximum estop timeout is 60 seconds, and the maximum estop cut_power_timeout is 65 seconds.

**If you register a new service with the robot**, calling `robot.ensure_client()` to create a client for that service may result in a `UnregisteredServiceNameError`.

- Workaround: call `robot.sync_with_directory()` before `robot.ensure_client()`

**SE2VelocityLimits require care**. Correct usage of the `SE2VelocityLimit` message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

### Deprecations

The following services, fields, and functions will continue to work, but will be removed in a future version.

#### Services

The `LogAnnotationService` is replaced with the `DataBufferService`, which allows user access to the logged data.

#### Protobuf changes

Mobility commands have been moved from `RobotCommand`, and into `SynchronizedCommand` within `RobotCommand`. When changing clients to use `SynchronizedCommand`, be aware that the feedback will be in the new `SynchronizedCommand` feedback. The top-level command status is also deprecated in favor of a status within individual feedback messages. Changing clients to use the new `SynchronizedCommand` will make them compatible with arm commands in a future release.

The representation of `SE3Covariance` has changed to a matrix. The individual element representation is deprecated.

In the map edge annotations, the `ground_mu_hint` and `grated_floor` fields have moved into the `mobility_params` message.

#### Client changes

The helper functions in `RobotCommandBuilder` have new versions that use the new `SynchronizedCommand`.

`sit_command()` → `synchro_sit_command()`

`stand_command()` → `synchro_stand_command()`

`velocity_command()` → `synchro_velocity_command()`

`trajectory_command()` → `synchro_se2_trajectory_point_command()`

The non-synchro versions are deprecated, and will be removed at the time that the mobility commands are removed from `RobotCommand`.

### Sample Code

#### New

[**Data acquisition (new)**](../python/examples/data_acquisition_service/README.md)

- Example data acquisition plugin implementations.
- Examples for capturing and downloading data.
- Test program to validate a data acquisition plugin.

[**Comms Test (new)**](../python/examples/comms_test/README.md)
Demonstrates how to use the SDK to perform comms testing.

[**Data Service (new)**](../python/examples/data_service/README.md)
Get comments and data index information from the robot.

[**Ricoh theta image service (new)**](../python/examples/ricoh_theta/README.md)
Create a standard Boston Dynamics API `ImageService` that communicates with the Ricoh Theta camera.

[**Service faults (new)**](../python/examples/service_faults/README.md)
Demonstrates raising service faults, clearing service faults, and implementation of directory liveness checks.

[**Spot detect and follow (new)**](../python/examples/spot_detect_and_follow/README.md)
Collects images from the two front Spot cameras and performs object detection on a specified class.

[**Stance (new)**](../python/examples/stance/README.md)
Exercises the stance function to reposition the robots feet.

[**Stitch front images**](../python/examples/stitch_front_images/README.md)
Demonstrate how to stitch the front camera images together into a single image in an OpenGL shader.

[**Upload choreographed sequence (new)**](../python/examples/upload_choreographed_sequence/README.md)
Shows how to use the Choreography service to upload an existing choreographed sequence to the robot, and have the robot execute that uploaded routine.

[**Velodyne client (new)**](../python/examples/velodyne_client/README.md)
Demonstrates how to use the Velodyne service to query for point clouds.

[**Web cam image service (new)**](../python/examples/service_customization/custom_parameter_image_server/README.md)
Implements the standard Boston Dynamics API `ImageService` and communicates to common web cameras using OpenCV.

[**World object with image coords (new)**](../python/examples/world_object_with_image_coordinates/README.md)
Demonstrates adding a world object that exists only in image coordinates, rather than having a full transform.

#### Updated

[**Fiducial follow (updated)**](../python/examples/fiducial_follow/README.md)

- Uses the new `SynchronizedCommand` for robot commands.

[**Frame trajectory command (updated)**](../python/examples/frame_trajectory_command/README.md)

- Uses the new `SynchronizedCommand` for robot commands.

[**Get image (updated)**](../python/examples/get_image/README.md)

- Added an option to auto-rotate images to be rightside-up.
- Added an option to retrieve images from user image services.
- Added support for more pixel formats.

[**GraphNav command-line (updated)**](../python/examples/graph_nav_command_line/README.md)

- Waypoints can be specified by either short codes or waypoint names.
- Waypoints sorted by creation time.

[**Hello spot (updated)**](../python/examples/hello_spot/README.md)

- Uses the new `SynchronizedCommand` for robot commands.

[**Logging (updated)**](../python/examples/logging/README.md)

- Switched to use Data Buffer for logging instead of the deprecated
  `LogAnnotationService`.

[**Mission question answerer (updated)**](../python/examples/mission_question_answerer/README.md)

- Updated to prompt the user on the command line for an answer.

[**Mission recorder (updated)**](../python/examples/mission_recorder/README.md)

- Added support for navigating through feature-poor areas.

[**Payload (updated)**](../python/examples/payloads/README.md)

- Uses the new payload keep-alive.

[**Remote mission service (updated)**](../python/examples/remote_mission_service/README.md)

- Separated example_servicers.py into separate hello_world_mission_service.py and power_off_mission_service.py files.

[**Replay mission (updated)**](../python/examples/replay_mission/README.md)

- Added an option to skip the initial localization.

[**Self Registration (updated)**](../python/examples/self_registration/README.md)

- Uses new helpers for registration.

[**Spot CAM (updated)**](../python/examples/spot_cam/README.md)

- New option to delete all images from the USB drive.
- Support for the IR camera.

[**Spot light (updated)**](../python/examples/spot_light/README.md)

- Uses the new `SynchronizedCommand` for robot commands.

[**Wasd (updated)**](../python/examples/wasd/README.md)

- Uses the new `SynchronizedCommand` for robot commands.
- Supports battery change pose command.

[**Xbox controller (updated)**](../python/examples/xbox_controller/README.md)

- Uses the new `SynchronizedCommand` for robot commands.
- Supports battery change pose command.

#### Removed

**Ricoh Theta remote mission service (removed)**

- This has been removed and replaced with the Ricoh Theta image service, which provides better integration for displaying and capturing data.

**get_depth_plus_visual_image (removed)**

- Example removed because all robot cameras include `depth_in_visual_frame` sources by default.

**Spot check (removed)**

- Users can run Spot Check from the tablet.

## 2.0.2

### New Features

### Bug Fixes and Improvements

#### Power Command Exceptions

- Power Client detects errors during a power command right away and propagates them up to the application before the command timeout is reached.

### Known Issues

Release 2.0.2 contains the same issues as release 2.0.1, listed below.

**If you delete an object from the world object service**, there is a chance that a ListWorldObjects call immediately afterward may still include that object.

- Workaround: wait a short time before expecting the object to be gone.

**If you register a new service with the robot**, calling robot.ensure_client to create a client for that service may result in a UnregisteredServiceNameError.

- Workaround: call robot.sync_with_directory() before robot.ensure_client()

**SE2VelocityLimits require care**. The proto comment states that "if set, limits the min/max velocity," implying that one should not set values for any directions one does not want limited. However, if any of the numeric fields are not set in the message, they will be interpreted as 0. For example, if angular is not set but linear is, then the message will be incorrectly interpreted as having an angular limit of 0 and the robot will fail to rotate (obviously not the intent). Similarly, if the user only sets say the 'x' field of linear, then 'y' will be incorrectly limited to 0 as well.

- Workaround: Correct usage of the SE2VelocityLimit message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

**LogAnnotationClient does not include async versions** of its RPCs.

- Workaround: If you need to call these in an async manner, call them on a separate thread.

## 2.0.1

### New Features

#### License Changes

App tokens are no longer required to authorize applications. Instead, each robot itself will be licensed itself. From a programming perspective, this means that it is no longer necessary to load app tokens into the sdk object, or to fill them out in GetAuthTokenRequest.

If a client attempts to call a function for which the robot is not licensed, the robot will respond with an error related to the license issue. The PowerService and GraphNavService responses now include new error codes for license errors on certain actions.

There is a new LicenseClient which can be used to query the license information for a robot. License information can also be queried from the bosdyn.client command line utility.

### Bug Fixes and Improvements

#### Behavior Faults

- The robot previously accepted new commands when there were behavior faults, but did not execute them and would not provide feedback on them. The robot will now reject them with the new status `STATUS_BEHAVIOR_FAULT`.
- The python SDK will throw the exception `BehaviorFaultError`. 2.0.0 clients will throw a `ResponseError` in these cases.

#### Map Recording

- If the fiducials are not visible, the action will fail with `STATUS_MISSING_FIDUCIALS`. When starting recording or creating a manual waypoint in the GraphNavRecordingService, the client can require certain fiducials to be visible. If the fiducials are not visible, the action will fail with `STATUS_MISSING_FIDUCIALS`.
- When recording a map, grated floor mode and ground friction hints that are set in the recording environment are now correctly recorded into the map and used during playback.

#### Spot CAM

- Added an option to the Spot CAM MediaLogService to retrieve the raw (unstitched) images for a log point.

#### Payload Integration

- When a payload is authorized, it is given full access to the services on the robot, rather than a limited set. For example, a payload could now operate Spot.

#### Additional Fixes

- Removed some obsolete or internal protobuf messages and service RPCs which were not in use in the SDK.
- Fixed an issue where the SDK would continuously try to request new tokens if it lost connection to the robot at the time when it tried to renew its current user token.

### Known Issues

Release 2.0.1 contains the same issues as release 2.0.0, listed below.

**If you delete an object from the world object service**, there is a chance that a ListWorldObjects call immediately afterward may still include that object.

- Workaround: wait a short time before expecting the object to be gone.

**If you register a new service with the robot**, calling robot.ensure_client to create a client for that service may result in a UnregisteredServiceNameError.

- Workaround: call robot.sync_with_directory() before robot.ensure_client()

**SE2VelocityLimits require care**. The proto comment states that "if set, limits the min/max velocity," implying that one should not set values for any directions one does not want limited. However, if any of the numeric fields are not set in the message, they will be interpreted as 0. For example, if angular is not set but linear is, then the message will be incorrectly interpreted as having an angular limit of 0 and the robot will fail to rotate (obviously not the intent). Similarly, if the user only sets say the 'x' field of linear, then 'y' will be incorrectly limited to 0 as well.

- Workaround: Correct usage of the SE2VelocityLimit message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

**LogAnnotationClient does not include async versions** of its RPCs.

- Workaround: If you need to call these in an async manner, call them on a separate thread.

### Sample Code

[**Ricoh Theta (new)**](../python/examples/ricoh_theta/README.md)

- Example that utilizes the 360-degree Ricoh Theta camera during an Autowalk mission.

[**Cloud Upload (new)**](../python/examples/cloud_upload/README.md)

- Example that shows how to upload a file to a Google Cloud Platform (GCP) bucket or an Amazon Web Services (AWS) S3 bucket.

[**WASD**](../python/examples/wasd/README.md)

- Updated to account for the additional state metrics that are reported. Older versions of this example may fail when connecting to updated robots.

[**Spot CAM**](../python/examples/spot_cam/README.md)

- Added support for viewing the WebRTC stream.

[**Replay Mission**](../python/examples/replay_mission/README.md)

- The example script does not localize itself to any map, but assumes the robot is already localized or that the mission has a localization node in it.
- It verifies that an estop is properly connected before trying to run the mission.
- It contains an additional --timeout parameter that can be used to set an overall time limit on mission execution.

[**Mission Recorder**](../python/examples/mission_recorder/README.md)

- Can add relocalization nodes to a mission.

[**Fiducial Follow**](../python/examples/fiducial_follow/README.md)

- Fixed a UI crash on MacOS X.

## 2.0.0

### New Features

#### Autonomous Navigation APIs

The APIs used by Autowalk are now accessible to developers.

- [Overall conceptual documents](concepts/README.md)
- **GraphNavService**: Upload and download maps of the environment, update localizations to that map, and command the robot to autonomously navigate to a location in the map. Example usage can be found in `graph_nav_command_line.py`. Examples of interpreting the map data can be found in `graph_nav_view_map.py`
- **GraphNavRecordingService**: Record maps while the robot walks around. Example usage found in `recording_command_line.py`
- **MissionService**: Load and play autonomous missions. Example mission creation is shown in `mission_recorder.py` with upload and playback usage shown in `replay_mission.py`
- **RemoteMissionService**: A new method for handling mission callbacks, where the mission can trigger user code via an RPC. For building your own callbacks, see the examples in remote_mission_service.

#### Spot CAM API

Control and query all hardware features of the Spot CAM. For examples of using each service, see the [Spot CAM command line example](../python/examples/spot_cam/README.md).

- **CompositorService** and **StreamQualityService**: change the layout and quality of the webrtc stream.
- **PtzService**: Direct PTZ cameras to desired poses.
- **LightingService**: Control the individual brightness of the illuminator LEDs.
- **MediaLogService**: Save and retrieve high-resolution images to and from the internal USB drive for later processing.
- **AudioService**: Upload and play sounds over the Spot CAM speakers.
- **NetworkService**: Adjust networking settings.
- **HealthService**, **VersionService**, **PowerService**: Query the status of the hardware and software, and power components on and off.

#### Payload API integration

[Payloads with a compute component can self-register with Spot and API services](payload/configuring_payload_software.md)

- **DirectoryRegistrationService**: Allows end users to register new gRPC services running on a payload into the robots service directory. This allows for communicating through the robot’s proxy to the service from off-robot, and for registering mission callbacks for integrations with Autowalk missions. See `directory_modification.py` for example usage.
- **PayloadRegistrationService**: Payloads can now register themselves with the robot, providing their properties and awaiting authorization from a robot administrator. See the self_registration and payloads examples for how to register your own payload.

#### Environmental APIs

Learn more about how Spot is perceiving the world around it.

- **WorldObjectService**: Request details of any objects that has been detected in the world, and add your own detections. Example usage can be found in `mutate_world_objects.py`, `fiducial_follow.py`, and `add_image_coordinates.py`.
- **LocalGridService**: Request maps of the area around the robot, including terrain height and obstacle classification. Example usage shown by the bosdyn.client command line utility and the `basic_streaming_visualizer.py` example.
- **depth_in_visual_frame** image sources. These depth map images have the same dimension, extrinsics, and intrinsics as the grayscale image sources, which can help with pixel-depth correspondence issues.

### Bug Fixes and Improvements

#### Expanded and improved documentation

- Python QuickStart has been revamped to streamline getting up and running on the SDK.
- Conceptual documentation has been added to explain key ideas on how to develop for Spot.
- Payload developers guide has been added.
- Generated documents of the API protocol have also been added.

#### Improved performance over poor communication links

- Reduced API request overhead by several hundred bytes/request.
- TimeSync estimator more resilient to outlier latencies and temporary network outages.

#### Additional robot state is exposed

- PowerState: Overall charge percentage and estimated runtime.
- KinematicState: Body velocities are now available in KinematicState.
- RobotState: Foot contact state (in contact vs. not in contact).

#### Clients can specify additional advanced locomotion options

- Can now disable various low-level locomotion defaults for special situations and terrain (stair tracking, pitch limiting, cliff avoidance).
- Body rotation can be specified as an offset to nominal or to horizontal.

#### Consistent Frame usage across API

- See more details in the Breaking Changes section.

#### bosdyn.client command line tool improvements

- Downloading of depth images supported. Depth maps will be written to PGM files.
- Directory listing has improved formatting.

### Breaking changes

Version 2.0 contains several breaking changes. While some clients and programs written for the version 1.\* SDK may still work, expect some updates to be necessary for most programs.

#### Frame handling

[Documentation of frames on Spot](concepts/geometry_and_frames.md):

- Documentation of frames on Spot ([link](concepts/geometry_and_frames.md)):
- The Frame message (`geometry.proto`) and FrameType have been deprecated, and the frame is now described as a string throughout the API.
- When receiving data from the robot (robot state, images, grid maps, world objects, etc.), the data will come with a string describing the frame it is represented in, but also a FrameTreeSnapshot message which describes how to transform the data into other frames.
- Use the helpers in `frame_helpers.py` (in particular `get_a_tform_b`) to compute appropriate transforms for your use case. See `frame_trajectory_command.py` for an example of using transforms to command the robot.
- Code written for version 1 will need to update to the following new convention:

| Version 1 frame enum | Version 2 frame string | frame_helpers.py constant |
| -------------------- | ---------------------- | ------------------------- |
| FRAME_KO             | “odom”                 | ODOM_FRAME_NAME           |
| FRAME_VO             | “vision”               | VISION_FRAME_NAME         |
| FRAME_BODY           | “body”                 | BODY_FRAME_NAME           |

#### New Exceptions

New RpcError exceptions can be raised during RPC calls. If you were already catching RpcErrors, you will catch these. If you were catching individual subclasses, be aware of these new ones.

- PermissionDeniedError
- ResponseTooLargeError
- NotFoundError
- TransientFailureError

There are some new exceptions that can be thrown due to errors with the request before any RPC is made. They generally indicate programmer error, so depending on your use case it may be acceptable to not catch them to find bugs in your program. If it is important to catch all exceptions, be aware that these exist, and all inherit from bosdyn.client.Error

- TimeSyncRequired
- NoSuchLease
- LeaseNotOwnedByWallet

When creating clients or channels from a Robot object, a new class of exceptions inheriting from RobotError may be raised. NonexistentAuthorityError is no longer thrown, but other RpcErrors may be raised.

- UnregisteredServiceError
- UnregisteredServiceNameError
- UnregisteredServiceTypeError

Robot command client will throw a new error if a frame is specified that the robot does not recognize.

- UnknownFrameError

#### Moved or Renamed

- Trajectories must now specify the frame name in the parent message instead of the trajectory itself.
- Trajectory commands can no longer be specified in a body frame since the output behavior can be ambiguous.
- Robot command messages were split into different proto files (basic_command, full_body_command), which will change import/include paths.
- ‘vel’ field in SE3TrajectoryPoint renamed to **velocity** (`trajectory.proto`)
- Updates in `Payload.proto`
  - LabelPrefix field was changed from String to Repeated String
  - body_T_payload renamed to body_tform_payload
  - mount_T_payload renamed to mount_tform_payload

#### Removed

- All Frame messages have been replaced by frame strings where applicable.
- AddLogAnnotationResponse does not have a status field anymore, errors are encoded in the message header information
- ko_tform_body, vo_tform_body, and ground_plane_rt_ko in Kinematic state have been replaced with the transforms_snapshot.
- The SampleCommon message for image captures has been replaced by acquisition time and a FrameTreeSnapshot.

#### Miscellaneous

- bosdyn-client has added a dependency on numpy
- Autowalk missions and maps recorded with version 1.1 are not compatible with version 2.0

### Known issues

**If you delete an object from the world object service**, there is a chance that a ListWorldObjects call immediately afterward may still include that object.

- Workaround: wait a short time before expecting the object to be gone.

**If you register a new service with the robot**, calling robot.ensure_client to create a client for that service may result in a UnregisteredServiceNameError.

- Workaround: call robot.sync_with_directory() before robot.ensure_client()

**SE2VelocityLimits require care**. The proto comment states that "if set, limits the min/max velocity," implying that one should not set values for any directions one does not want limited. However, if any of the numeric fields are not set in the message, they will be interpreted as 0. For example, if angular is not set but linear is, then the message will be incorrectly interpreted as having an angular limit of 0 and the robot will fail to rotate (obviously not the intent). Similarly, if the user only sets say the 'x' field of linear, then 'y' will be incorrectly limited to 0 as well.

- Workaround: Correct usage of the SE2VelocityLimit message requires the user to fully fill out all the fields, setting unlimited values to a large number, say 1e6.

**LogAnnotationClient does not include async versions** of its RPCs.

- Workaround: If you need to call these in an async manner, call them on a separate thread.

### Sample Code

[**directory**](../python/examples/directory/README.md)

- Register, update, and unregister a service.

[**payloads**](../python/examples/payloads/README.md)

- Renamed from `get_payload`.
- Expanded to show payload version handling.

[**self_registration**](../python/examples/self_registration/README.md)

- Example showing how to set up a payload that registers itself with the robot, hosts a service, and registers its service with the robot.

**add_image_coordinates_to_scene** (Renamed to **world_object_with_image_coordinates** in 2.1.0)

- Example using the API demonstrating adding image coordinates to the world object service.

[**estop \(updated\)**](../python/examples/estop/README.md)

- New EstopNoGui as a command-line addition to the GUI version of the E-Stop example.

**get_depth_plus_visual_image** (Removed in 2.1.0)

- Example demonstrates how to use the new depth_in_visual_frame image sources to visualize depth in a fisheye image.

[**get_mission_state**](../python/examples/get_mission_state/README.md)

- Example program demonstrates how to retrieve information about the state of the currently-running mission.

[**frame_trajectory_command**](../python/examples/frame_trajectory_command/README.md)

- Example program shows how to retrieve Spot's location in both the visual and odometry frames. Using these frames, the program shows how to build and execute a command to move Spot to that location plus 1.0 in the x-axis.

[**get_robot_state_async**](../python/examples/get_robot_state_async/README.md)

- Example demonstrates 3 different methods for working with Spot asynchronous functions.

[**get_world_objects**](../python/examples/get_world_objects/README.md)

- Example demonstrate how to use the world object service to list the objects Spot can detect, and filter these lists for specific objects or objects after a certain time stamp.

[**graph_nav_command_line**](../python/examples/graph_nav_command_line/README.md)

- Command line interface for graph nav with options to download/upload a map and to navigate a map.

[**graph_nav_view_map**](../python/examples/graph_nav_view_map/README.md)

- Example shows how to load and view a graph nav map.

[**mission_recorder**](../python/examples/mission_recorder/README.md)

- Example with an interface for operating Spot with your keyboard, recording a mission, and saving it.

[**remote_mission_service**](../python/examples/remote_mission_service/README.md)

- Run a gRPC server that implements the RemoteMissionService service definition.
- Connect a RemoteClient directly to that server.
- Build a mission that talks to that server.

[**replay_mission**](../python/examples/replay_mission/README.md)

- Example on how to replay a mission via the API.

[**spot_cam**](../python/examples/spot_cam/README.md)

- Examples to demonstrate how to interact with the Spot CAM.

[**visualizer**](../python/examples/visualizer/README.md)

- Example to visualize Spot's perception scene in a consistent coordinate frame.

[**world_object_mutations**](../python/examples/world_object_mutations/README.md)

- Examples to demonstrate how to use the world object service to add, change, and delete world objects.

[**xbox_controller** \(updated\)](../python/examples/xbox_controller/README.md)

- Added support for Windows driver.

## 1.1.2

### New features

- **Missions API Beta and Callbacks** When an Autowalk Mission is created with a "Callback" event, a client can detect that change using a beta version of the Mission API, then tell the robot to continue or abort the Mission. Example uses include a sensor payload that detects Callback events and captures sensor information before advancing the mission, and a desktop UI which waits for the user to push a button before advancing the mission.

- **External Forces Beta**. Mobility commands can specify how to handle external forces. Examples of external forces could include an object that Spot is towing, or an object Spot is pushing. The default behavior is to do nothing, but clients can specify whether Spot should estimate external forces and compensate for it, or explicitly specify what the external forces are.

### Bug fixes and improvements

- **Depth image** extrinsics are fixed. In earlier 1.1.x releases, the extrinsics were incorrectly the same as the fisheye cameras.

- **App Token expiration logging**. The Python SDK object logs if the app token will expire in the next 30 days.

### Sample Code

- **mission_question_answerer** demonstrates how to build a client which responds to Mission Callbacks.

## 1.1.1

1.1.1 has no SDK-related changes.

## 1.1.0

The 1.1.0 SDK software is published under a new software license which can be found in the LICENSE file at the top of the SDK directory.

### New features

- **ImageService** exposes depth maps from on-board stereo cameras as additional image sources. Image Sources specify an ImageType to differentiate depth maps from grayscale images.

- **PayloadService** is a new service which lists all known payloads on the robot.

- **SpotCheckService** is a new service which runs actuator and camera calibration.

- **E-Stop soft timeouts.** In prior software release, E-Stop endpoints which stopped checking in would result in the power to the robot's motors being cut immediately. Now the E-Stop endpoint can be configured so Spot will attempt to sit followed by cutting power. The timeout parameter for an E-Stop endpoint specifies when the sitting behavior starts, and the cut_power_timeout parameter specifies when the power will cut off.

- **TerrainParams** can be added to MobilityParams to provide hints about the terrain that Spot will walk on. The coefficient of friction of the ground can be specified. Whether the terrain is grated metal can also be specified.

- **Log Annotations** a new type of log: Blob for large binary data.

### Sample code

The sample code directory structure has changed to directory-per-example under python/examples. Each example includes a requirements.txt file for specifying dependencies.

- **estop** is a desktop GUI which creates an E-Stop endpoint for a robot. This example demonstrates how to use the E-Stop endpoint system, and is a useful utility on its own.

- **follow_fiducial** is an example where Spot will follow an AprilTag fiducial that it can see in its on-board cameras. This demonstrates how to use camera extrinsics and intrinsics to convert pixels to world coordinates, and how to use the trajectory commands.

- **get-image** is a simple example to retrieve images from Spot and save them to disk. It shows how to use the basics of the image service.

- **get-payload** is a simple example which lists all of the payloads on the robot. It shows how to use the payload service.

- **get_robot_state** is a simple example to retrieve robot state.

- **hello_spot** is carried over from prior SDK releases. It is an introductory tutorial showing basic use of the Spot SDK.

- **logging** demonstrates how to add custom annotations to Spot’s log files.

- **spot_check** demonstrates how to use SpotCheck - Spot’s in-the-field calibration behavior.

- **spot_light** is a demo where Spot rotates its body while standing to try to face a flashlight seen in its front cameras.

- **spot_tensorflow_detector** demonstrates how to integrate the Spot SDK with Tensorflow for object classification from images.

- **time_sync** is a simple example demonstrating how to use the TimeSync service.

- **wasd** is carried over from prior SDK releases. It is an interactive program which uses keyboard control for the robot, and demonstrates how to use a variety of commands.

- **xbox_controller** demonstrates how to specify more advanced options for mobility commands.

### Bug fixes and Improvements

- Too many invalid login attempts will lock a user out from being able to authenticate for a temporary period to prevent brute-force attacks. GetAuthTokenResponse indicates this state with a STATUS_TEMPORARILY_LOCKED_OUT.

- Elliptic Curve (ECDSA) cryptography used for user tokens - reducing the size of RPC requests by several hundred bytes.

- gRPC exceptions are correctly handled in Python 3.

- Command-line tool handles unicode robot nicknames correctly.

- Command-line tool supports retrieving robot model information (URDF and object files)

- Command-line tool supports retrieving multiple images at once.

- “Strict Version” support for software version.

- App Token paths which include “~” will automatically expand, rather than fail.

- Mobility Commands which have MobilityParams.vel_limit with only a min or max velocity are correctly handled. In prior releases, these commands would result in no movement at all.

- Mobility Commands which have BodyControlParams.base_offset_rt_footprint.reference_time in the past result in a STATUS_EXPIRED response rather than a STATUS_INVALID_REQUEST.

- SE2VelocityCommands with unset slew_rate_limit are correctly handled. In prior releases, an unset slew_rate_limit would result in the robot walking in place.

### Deprecations and breaking changes

- Removed support for Python 2.7. Only Python 3.6+ is supported due to upcoming Python 2 End-of-Life. Windows 10, MacOS, and Ubuntu LTS are still supported.

- The HINT_PACE LocomotionHint is no longer supported due to physical stability issues. Any commands which specify a HINT_PACE LocomotionHint will be treated like a HINT_JOG LocomotionHint is specified.

- HINT_AUTO_TROT and HINT_AUTO_AMBLE are deprecated as names - use HINT_SPEED_SELECT_TROT and HINT_SPEED_SELECT_AMBLE respectively going forward.

- Protocol Buffer locations changed to split services from messages. Any direct imports of protocol buffers by client applications will need to change to support the 1.1.0 version changes.

## 1.0.1

- Improved documentation on SDK installation.

- Clearer Python dependency requirements.

- RobotId service exposes computer serial number in addition to robot serial number.

- wasd image capture works in Python 3.

- Fixed timing bugs in power service.

## 1.0.0

Initial release of the SDK.
