<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Python Client

Client code and interfaces for the Boston Dynamics robot API.

## Contents

- [Area Callback](area_callback)
- [Area Callback Region Handler](area_callback_region_handler_base)
- [Area Callback Service Runner](area_callback_service_runner)
- [Area Callback Servicer](area_callback_service_servicer)
- [Area Callback Service Utils](area_callback_service_utils)
- [Arm Surface Contact](arm_surface_contact)
- [Async Tasks](async_tasks)
- [Auth](auth)
- [Auto Return](auto_return)
- [Autowalk](autowalk)
- [BDDF](bddf)
- [BDDF Download](bddf_download)
- [Channel](channel)
- [Command ](command_line)
- [Common](common)
- [Data Acquisition](data_acquisition)
- [Data Acquisition Helpers](data_acquisition_helpers)
- [Data Acquisition Plugin](data_acquisition_plugin)
- [Data Acquisition Plugin Service](data_acquisition_plugin_service)
- [Data Acquisition Store](data_acquisition_store)
- [Data Buffer](data_buffer)
- [Data Chunk](data_chunk)
- [Data Service](data_service)
- [Directory Registration](directory_registration)
- [Directory](directory)
- [Docking](docking)
- [Door](door)
- [E-Stop](estop)
- [Exceptions](exceptions)
- [Fault](fault)
- [Frame Helpers](frame_helpers)
- [Graph Nav](graph_nav)
- [Gripper Camera Params](gripper_camera_param)
- [GPS](gps/README)
- [Image](image)
- [Image Service Helpers](image_service_helpers)
- [Inverse Kinematics](inverse_kinematics)
- [IR Enable/Disable](ir_enable_disable)
- [Keep Alive](keepalive)
- [Lease](lease)
- [Lease Resource Hierarchy](lease_resource_hierarchy)
- [Lease Validator](lease_validator)
- [License](license)
- [Local Grid](local_grid)
- [Log Status](log_status)
- [Math Helpers](math_helpers)
- [Manipulation API](manipulation_api_client)
- [Map Processing](map_processing)
- [Metrics Logging](metrics_logging)
- [Network Compute Bridge](network_compute_bridge_client)
- [Payload Registration](payload_registration)
- [Payload](payload)
- [Point Cloud](point_cloud)
- [Power](power)
- [Processors](processors)
- [Ray casting](ray_cast)
- [Recording](recording)
- [Robot Command](robot_command)
- [Robot ID](robot_id)
- [Robot](robot)
- [Robot State](robot_state)
- [SDK](sdk)
- [Server Util](server_util)
- [Service Customization Helpers](service_customization_helpers)
- [Signals Helpers](signals_helpers)
- [Spot CAM](spot_cam/README)
- [Spot Check](spot_check)
- [Time Sync](time_sync)
- [Token Cache](token_cache)
- [Token Manager](token_manager)
- [Units Helpers](units_helpers)
- [Util](util)
- [World Object](world_object)

<p>&nbsp;</p>

## RPC Clients

The table below specifies the protobuf service definitions supported by each client.

|                              Client                              |                                                 RPCs Supported                                                  |
| :--------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------: |
|             [**Area Callback**](./area_callback.py)              |      [area_callback_service.proto](../../../../../protos/bosdyn/api/graph_nav/area_callback_service.proto)      |
|       [**Arm Surface Contact**](./arm_surface_contact.py)        |     [arm_surface_contact_service.proto](../../../../../protos/bosdyn/api/arm_surface_contact_service.proto)     |
|                      [**Auth**](./auth.py)                       |                    [auth_service.proto](../../../../../protos/bosdyn/api/auth_service.proto)                    |
|               [**Auto Return**](./auto_return.py)                |       [auto_return_service.proto](../../../../../protos/bosdyn/api/auto_return/auto_return_service.proto)       |
|                  [**Data**](./data_service.py)                   |                    [data_service.proto](../../../../../protos/bosdyn/api/data_service.proto)                    |
|          [**Data Acquisition**](./data_acquisition.py)           |        [data_acquisition_service.proto](../../../../../protos/bosdyn/api/data_acquisition_service.proto)        |
|   [**Data Acquisition Plugin**](./data_acquisition_plugin.py)    | [data_acquisition_plugin_service.proto](../../../../../protos/bosdyn/api/data_acquisition_plugin_service.proto) |
|    [**Data Acquisition Store**](./data_acquisition_store.py)     |  [data_acquisition_store_service.proto](../../../../../protos/bosdyn/api/data_acquisition_store_service.proto)  |
|               [**Data Buffer**](./data_buffer.py)                |             [data_buffer_service.proto](../../../../../protos/bosdyn/api/data_buffer_service.proto)             |
|    [**Directory Registration**](./directory_registration.py)     |  [directory_registration_service.proto](../../../../../protos/bosdyn/api/directory_registration_service.proto)  |
|                 [**Directory**](./directory.py)                  |               [directory_service.proto](../../../../../protos/bosdyn/api/directory_service.proto)               |
|                   [**Docking**](./docking.py)                    |         [docking/docking_service.proto](../../../../../protos/bosdyn/api/docking/docking_service.proto)         |
|                      [**Door**](./door.py)                       |                 [door_service.proto](../../../../../protos/bosdyn/api/spot/door_service.proto)                  |
|                     [**Estop**](./estop.py)                      |                   [estop_service.proto](../../../../../protos/bosdyn/api/estop_service.proto)                   |
|                     [**Fault**](./fault.py)                      |                   [fault_service.proto](../../../../../protos/bosdyn/api/fault_service.proto)                   |
|                  [**GraphNav**](./graph_nav.py)                  |     [graph_nav/graph_nav_service.proto](../../../../../protos/bosdyn/api/graph_nav/graph_nav_service.proto)     |
|      [**Gripper Camera Params**](./gripper_camera_param.py)      |    [gripper_camera_param_service.proto](../../../../../protos/bosdyn/api/gripper_camera_param_service.proto)    |
|                     [**Image**](./image.py)                      |                   [image_service.proto](../../../../../protos/bosdyn/api/image_service.proto)                   |
|         [**Inverse Kinematics**](inverse_kinematics.py)          |   [inverse_kinematics_service.proto](../../../../../protos/bosdyn/api/spot/inverse_kinematics_service.proto)    |
|         [**IR Enable/Disable**](./ir_enable_disable.py)          |       [ir_enable_disable_service.proto](../../../../../protos/bosdyn/api/ir_enable_disable_service.proto)       |
|                     [**Lease**](./lease.py)                      |                   [lease_service.proto](../../../../../protos/bosdyn/api/lease_service.proto)                   |
|                   [**License**](./license.py)                    |                 [license_service.proto](../../../../../protos/bosdyn/api/license_service.proto)                 |
|                [**Local Grid**](./local_grid.py)                 |              [local_grid_service.proto](../../../../../protos/bosdyn/api/local_grid_service.proto)              |
|                [**Log Status**](./log_status.py)                 |        [log_status_service.proto](../../../../../protos/bosdyn/api/log_status/log_status_service.proto)         |
|       [**Manipulation API**](./manipulation_api_client.py)       |        [manipulation_api_service.proto](../../../../../protos/bosdyn/api/manipulation_api_service.proto)        |
|            [**Map Processing**](./map_processing.py)             |     [map_processing_service.proto](../../../../../protos/bosdyn/api/graph_nav/map_processing_service.proto)     |
| [**Network Compute Bridge**](./network_compute_bridge_client.py) |  [network_compute_bridge_service.proto](../../../../../protos/bosdyn/api/network_compute_bridge_service.proto)  |
|      [**Payload Registration**](./payload_registration.py)       |    [payload_registration_service.proto](../../../../../protos/bosdyn/api/payload_registration_service.proto)    |
|                   [**Payload**](./payload.py)                    |                 [payload_service.proto](../../../../../protos/bosdyn/api/payload_service.proto)                 |
|               [**Point Cloud**](./point_cloud.py)                |             [point_cloud_service.proto](../../../../../protos/bosdyn/api/point_cloud_service.proto)             |
|                     [**Power**](./power.py)                      |                   [power_service.proto](../../../../../protos/bosdyn/api/power_service.proto)                   |
|                 [**Ray Casting**](./ray_cast.py)                 |                [ras_cast_service.proto](../../../../../protos/bosdyn/api/ray_cast_service.proto)                |
|                 [**Recording**](./recording.py)                  |     [graph_nav/recording_service.proto](../../../../../protos/bosdyn/api/graph_nav/recording_service.proto)     |
|             [**Robot Command**](./robot_command.py)              |           [robot_command_service.proto](../../../../../protos/bosdyn/api/robot_command_service.proto)           |
|                  [**Robot Id**](./robot_id.py)                   |                [robot_id_service.proto](../../../../../protos/bosdyn/api/robot_id_service.proto)                |
|               [**Robot State**](./robot_state.py)                |             [robot_state_service.proto](../../../../../protos/bosdyn/api/robot_state_service.proto)             |
|               [**SpotCam**](./spot_cam/README.py)                |                [spot_cam/service.proto](../../../../../protos/bosdyn/api/spot_cam/service.proto)                |
|                [**Spot Check**](./spot_check.py)                 |         [spot/spot_check_service.proto](../../../../../protos/bosdyn/api/spot/spot_check_service.proto)         |
|                 [**Time Sync**](./time_sync.py)                  |               [time_sync_service.proto](../../../../../protos/bosdyn/api/time_sync_service.proto)               |
|              [**World Object**](./world_object.py)               |            [world_object_service.proto](../../../../../protos/bosdyn/api/world_object_service.proto)            |
