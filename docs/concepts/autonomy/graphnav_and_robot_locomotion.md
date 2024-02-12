<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# GraphNav and Robot Locomotion

The GraphNav service provides three RPCs for navigating to different locations on the prior map:

*   NavigateTo
*   NavigateRoute
*   NavigateToAnchor

These RPCs let the client specify maximum speed as well as the size of the goal region at the final waypoint.

## NavigateTo

The `NavigateTo` RPC is the simplest way to command a robot to go to a destination on the map once the robot is localized. GraphNav will decide which route to take, currently the one with the fewest number of edges.


## NavigateRoute

The `NavigateRoute` RPC allows the client to directly specify the path of the robot. This lets the client command the robot to take a longer path as needed. Routes are specified as a list of waypoints and edges. For example, you could make a path that doubles back on itself, allowing the robot to go to a distant waypoint and then back to the start.

Clients that maintain contact with the robot are encouraged to continuously resend the command with a deadline in the near future. This results in the robot stopping quickly if the client stops checking in. Clients that disconnect from an autonomous robot should set a longer deadline and rely on an alternate mechanism to maintain safety.


## NavigateToAnchor

The `NavigateToAnchor` RPC allows the client to command the robot go to an approximate `x, y, z` position relative to the seed frame. This position can also be specified in a global coordinate system (like GPS coordinates, for example).


## Status and feedback

API clients should periodically query for navigation status during map replay using the `NavigationFeedback` RPC.

*   Unless an error is returned, `NavigationFeedbackResponse` is returned with status `STATUS_FOLLOWING_ROUTE` and the remaining list of waypoints and edges in the route.
*   On successful completion, the navigation status changes to `STATUS_REACHED_GOAL` when the robot reaches the end of the commanded route, matching both the position and yaw of the final waypoint.

Clients requiring high precision should check localization with `GetLocalizationState` RPC even after reaching the goal, as the robot will be close but not exactly on the goal.


## Autonomous navigation errors

The following error types can interrupt an autonomous route:

| Error code | Description |
| ---------- | ----------- |
| STATUS_NO_ROUTE |	Indicates the client changed something that invalidated the route. |
| STATUS_NO_LOCALIZATION |	The robot is not localized to the map. |
| STATUS_NOT_LOCALIZED_TO_ROUTE |	Localized and not lost but not on the commanded route. |
| STATUS_COMMAND_OVERRIDDEN |	A new GraphNav command has overridden the command that the user is asking for feedback about. |
| STATUS_LOST |	Lost means the robot is no longer confident in its localization, and must be re-localized. |
| STATUS_STUCK |	Stuck means that the robot is still localized but is having trouble reaching the destination (usually because of an obstacle in the way). |
| STATUS_ROBOT_FROZEN <br> STATUS_ROBOT_FAULTED |	Indicates the robot fell or has a hardware problem. |
| STATUS_CONSTRAINT_FAULT |	Indicates the route is over-constrained. Choose a different route. |
| STATUS_LEASE_ERROR |	Indicates the lease given to GraphNav is no longer valid. |
| STATUS_COMMAND_TIMED_OUT |	Indicates a comms problem or the timeout deadline was reached. |
| STATUS_ROBOT_IMPAIRED |   Indicates a crtical perception fault, behavior fault, or LIDAR not working. |
| STATUS_AREA_CALLBACK_ERROR |  Indicates an error occurred with an Area Callback. |


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
