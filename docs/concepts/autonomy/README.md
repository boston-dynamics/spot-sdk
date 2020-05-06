<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# [Spot SDK](../../../README.md) > [Concepts](../README.md) > Autonomy

The Spot SDK includes a set of APIs, client libraries, and examples that support the development of autonomous navigation behaviors for the Spot robot. Collectively, this service is referred to as GraphNav. Maps are recorded and saved and later can be replayed with any robot in your fleet. During the map recording process, you can assign actions and API callbacks to waypoints along the map route.

For robot operators, autonomous navigation is accessed using the Autowalk feature on the controller tablet. Operators use Autowalk to record and play back missions. Likewise, API callbacks and other actions can be added to waypoints during map recording.

The Autowalk feature is an implementation of the autonomous navigation API. However, the API supports more complex route topologies and autonomous behaviors and therefore provides software engineers the flexibility to develop complex autonomy solutions with the Spot robot.

Contents:

*   [Autonomous navigation code examples][code-examples]
*   [Components of autonomous navigation][components]
*   [Typical autonomous navigation use case][typical]
*   [Autonomous navigation services][autonomous-services]
*   [GraphNav service][service]
*   [GraphNav map structure][map-structure]
*   [Initialization][initialization]
*   [Localization][localization]
*   [GraphNav and robot locomotion][locomotion]
*   [Missions service][missions]
*   [WorldObject service][worldObject]


<br />

<a href="autonomous_navigation_code_examples.md" class="next">Next &raquo;</a>

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
[worldobject]: worldobject_service.md "WorldObject service"
