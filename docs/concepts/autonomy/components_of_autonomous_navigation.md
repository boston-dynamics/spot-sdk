<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# [Spot SDK](../../../README.md) > [Concepts](../README.md) > [Autonomy](README.md) > <br/> Components of Navigation

To get started with autonomous navigation, you'll need a grasp of the following concepts:


*   Maps
*   Waypoints
*   Edges
*   Localization
*   Initialization
*   Missions


## Maps


Maps are topological graphs consisting of waypoints and edges. Maps are recorded either by operators using the tablet controller or by client applications using RPC calls to the GraphNavRecordingService.


## Waypoints

Waypoints define the route a robot follows on map. Each waypoint stores a pointer to a snapshot of data captured during the recording process. During the recording process, robots place waypoints at approximately 2m intervals and otherwise as needed. A waypoint may be created explicitly via the API, either from the tablet or a client application.


## Edges

Edges connect waypoints. They contain both a transform describing where one waypoint is with respect to another waypoint, and annotations that control how the robot should move between them. For example, annotations can indicate stairs mode or a speed restriction.


## Localization

Localization is a process used by the robot to determine its location relative to a single waypoint in the graph. The robot updates its location continuously by comparing its real-time sensory data with the sensory data recorded in map waypoints. An initial localization is required, commonly aided by a fiducial.


## Initialization

When a map is initially loaded, GraphNav is unaware of the robot’s location relative to it and the user must help initialize the robot's localization. If using fiducials, you can elect to initialize to a specific fiducial or a waypoint. If not using a fiducial, you must initialize to a particular waypoint, and may elect to provide an initial guess or search area.



## Missions

Missions are expressed as behavior trees, which are composed of nodes arranged in a hierarchy. Behavior trees are executed inside the mission loop. Each iteration of a mission loop is referred to as a tick. For any given tick, mission execution starts at the root of the tree and proceeds down particular branches based on the type of node and the state of each node: failed, running, or success (see the NodeState Result enum defined in the [SDK mission.proto](../../../protos/bosdyn/api/mission/mission.proto) file). A failed node does not necessarily result in a failed mission. For example, a node could check for low battery and 'fails' when the robot is fully charged.

The mission is complete once the root node has changed from running to failed or success.


See [Missions service][missions] for details.


<br />

<a href="autonomous_navigation_code_examples.md" class="previous">&laquo; Previous</a>  |  <a href="typical_autonomous_navigation_use_case.md" class="next">Next &raquo;</a>

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
