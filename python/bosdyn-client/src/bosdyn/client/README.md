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
| [**Auth**](./auth.py) | [auth_service.proto](../../../../../protos/bosdyn/api/auth_service.proto) |
| [**DirectoryRegistration**](./directory_registration.py) | [directory_registration_service.proto](../../../../../protos/bosdyn/api/directory_registration_service.proto) |
| [**Directory**](./directory.py) | [directory_service.proto](../../../../../protos/bosdyn/api/directory_service.proto) |
| [**Estop**](./estop.py) | [estop_service.proto](../../../../../protos/bosdyn/api/estop_service.proto) |
| [**GraphNav**](./graph_nav.py) | [graph_nav/graph_nav_service.proto](../../../../../protos/bosdyn/api/graph_nav/graph_nav_service.proto) |
| [**Image**](./image.py) | [image_service.proto](../../../../../protos/bosdyn/api/image_service.proto) |
| [**Lease**](./lease.py) | [lease_service.proto](../../../../../protos/bosdyn/api/lease_service.proto) |
| [**LocalGrid**](./local_grid.py) | [local_grid_service.proto](../../../../../protos/bosdyn/api/local_grid_service.proto) |
| [**LogAnnotation**](./log_annotation.py) | [log_annotation_service.proto](../../../../../protos/bosdyn/api/log_annotation_service.proto) |
| [**PayloadRegistration**](./payload_registration.py) | [payload_registration_service.proto](../../../../../protos/bosdyn/api/payload_registration_service.proto) |
| [**Payload**](./payload.py) | [payload_service.proto](../../../../../protos/bosdyn/api/payload_service.proto) |
| [**Power**](./power.py) | [power_service.proto](../../../../../protos/bosdyn/api/power_service.proto) |
| [**Recording**](./recording.py) | [graph_nav/recording_service.proto](../../../../../protos/bosdyn/api/graph_nav/recording_service.proto) |
| [**RobotCommand**](./robot_command.py) | [robot_command_service.proto](../../../../../protos/bosdyn/api/robot_command_service.proto) |
| [**RobotId**](./robot_id.py) | [robot_id_service.proto](../../../../../protos/bosdyn/api/robot_id_service.proto) |
| [**RobotState**](./robot_state.py) | [robot_state_service.proto](../../../../../protos/bosdyn/api/robot_state_service.proto) |
| [**SpotCam**](./spot_cam/README.py) | [spot_cam/service.proto](../../../../../protos/bosdyn/api/spot_cam/service.proto) |
| [**SpotCheck**](./spot_check.py) | [spot/spot_check_service.proto](../../../../../protos/bosdyn/api/spot/spot_check_service.proto) |
| [**TimeSync**](./time_sync.py) | [time_sync_service.proto](../../../../../protos/bosdyn/api/time_sync_service.proto) |
| [**WorldObject**](./world_object.py) | [world_object_service.proto](../../../../../protos/bosdyn/api/world_object_service.proto) |
