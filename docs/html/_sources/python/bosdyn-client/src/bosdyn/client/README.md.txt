<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Python Client

Client code and interfaces for the Boston Dynamics robot API.

## Contents

* [Async Tasks](async_tasks)
* [Auth](auth)
* [Channel](channel)
* [Command ](command_line)
* [Common](common)
* [Directory Registration](directory_registration)
* [Directory](directory)
* [E-Stop](estop)
* [Exceptions](exceptions)
* [Frame Helpers](frame_helpers)
* [Graph Nav](graph_nav)
* [Image](image)
* [Lease](lease)
* [Local Grid](local_grid)
* [Log Annotation](log_annotation)
* [Math Helpers](math_helpers)
* [Payload Registration](payload_registration)
* [Payload](payload)
* [Power](power)
* [Processors](processors)
* [Recording](recording)
* [Robot Command](robot_command)
* [Robot ID](robot_id)
* [Robot](robot)
* [Robot State](robot_state)
* [SDK](sdk)
* [Spot CAM](spot_cam/README)
* [Spot Check](spot_check)
* [Time Sync](time_sync)
* [Token Cache](token_cache)
* [Token Manager](token_manager)
* [Util](util)
* [World Object](world_object)

<p>&nbsp;</p>

## RPC Clients
The table below specifies the protobuf service definitions supported by each client.

| Client | RPCs Supported |
|:------:|:-------------:|
| [**Auth**](auth) | [auth_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#auth-service-proto) |
| [**DirectoryRegistration**](directory_registration) | [directory_registration_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#directory-registration-proto) |
| [**Directory**](directory) | [directory_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#directory-service-proto) |
| [**Estop**](estop) | [estop_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#estop-service-proto) |
| [**GraphNav**](graph_nav) | [graph_nav/graph_nav_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#graph-nav-graph-nav-service-proto) |
| [**Image**](image) | [image_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#image-service-proto) |
| [**Lease**](lease) | [lease_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#lease-service-proto) |
| [**LocalGrid**](local_grid) | [local_grid_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#local-grid-service-proto) |
| [**LogAnnotation**](log_annotation) | [log_annotation_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#log-annotation-service-proto) |
| [**PayloadRegistration**](payload_registration) | [payload_registration_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#payload-registration-service-proto) |
| [**Payload**](payload) | [payload_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#payload-service-proto) |
| [**Power**](power) | [power_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#power-service-proto) |
| [**Recording**](recording) | [graph_nav/recording_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#graph-nav-recording-service-proto) |
| [**RobotCommand**](robot_command) | [robot_command_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#robot-command-service-proto) |
| [**RobotId**](robot_id) | [robot_id_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#robot-id-service-proto) |
| [**RobotState**](robot_state) | [robot_state_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#robot-state-service-proto) |
| [**SpotCam**](spot_cam/README) | [spot_cam/service.proto](../../../../../protos/bosdyn/api/proto_reference.html#spot-cam-service-proto) |
| [**SpotCheck**](spot_check) | [spot/spot_check_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#spot-spot-check-service-proto) |
| [**TimeSync**](time_sync) | [time_sync_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#time-sync-service-proto) |
| [**WorldObject**](world_object) | [world_object_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#world-object-service-proto) |
