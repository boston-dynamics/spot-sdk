<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Autonomous navigation code examples

GraphNav provides place-based localization and locomotion services. Developers can record and play back maps for the robot to follow, navigating between waypoints and traversing edges between waypoints on the map.

The Spot SDK includes [python code examples](../../../python/examples/README.md) to help you get started with autonomous navigation. Refer to the following examples to learn about exercising the GraphNav API.

| Code example | Description                                   |
| ------------ | --------------------------------------------- |
| [recording_command_line](../../../python/examples/graph_nav_command_line/README.md) |	Demonstrates graphnav recording service requests to record, create, and download a map from the robot. |
| [graph_nav_command_line](../../../python/examples/graph_nav_command_line/README.md) |	Demonstrates how to use GraphNav requests to: <ul><li>Upload maps to the robot<li>Initialize the robot<li>Get the current localization of the robot on a map<li>Navigate the map (using either a specific route or a destination waypoint id)<li>Clear the existing map on the robot</ul> |
| [remote_mission_service](../../../python/examples/remote_mission_service/README.md) |	Demonstrates how to implement a RemoteMissionService and run it. This is how we support triggering off-robot code as part of Autowalk. |
| [view_map](../../../python/examples/graph_nav_view_map/README.md) |	An example program for opening, parsing, and viewing a GraphNav map. This example can be used with GraphNav maps generated using Autowalk or using the GraphNav APIs. |
| [area_callbacks](../../../python/examples/area_callback/README.md) |	An example program for writing [Area Callbacks](graphnav_area_callbacks.md) which can extend the capabilities of GraphNav by triggering callbacks to user code when entering, crossing, and leaving a region of the map. |


<!--- image and page reference link definitions --->
[autonomous-top]: Readme.md "Spot SDK: Autonomy, GraphNav, and Missions"
[code-examples]: autonomous_navigation_code_examples.md "Autonomous navigation code examples"
[components]: components_of_autonomous_navigation.md "Components of autonomous navigation"
[typical]: typical_autonomous_navigation_use_case.md "Typical autonomous navigation use cases"
[autonomous-services]: autonomous_navigation_services.md "Autonomous navigation services"
[service]: graphnav_service.md "GraphNav service"
[map-structure]: graphnav_map_structure.md "GraphNav map structure"
[initialization]: initialization.md "Initialization"
[localization]: localization.md "Localization"
[locomotion]: graphnav_and_robot_locomotion.md "GraphNav and robot locomotion"
[missions]: missions_service.md "Missions service"
