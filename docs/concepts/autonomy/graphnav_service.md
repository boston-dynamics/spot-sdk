<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# GraphNav Service

The GraphNav service is a place-based localization and locomotion service. You access the GraphNavService on the robot by making RPC calls to localize the robot, navigate a route, or download snapshot data.

Maps are recorded using the GraphNavRecording service or by operating the robot using the tablet controller and using the Autowalk feature to record a map.

Maps contain waypoints and edges. Together, these are known as graphs. The recorded map is used by the robot to follow a sequence of waypoints and edges. During playback, the robot compares its real-time sensor data with sensor data stored during the recording process. This helps the robot determine its location or pose during playback so it can make adjustments.


## Navigation

The GraphNav service is used to navigate between waypoints that are connected by edges in a recorded map. In general, the service tries to stay as close as possible to the recorded routes. The robot has the ability to adapt its route if obstacles are encountered along the way, unless the deviation takes the robot too far away from the recorded route, in which case the robot declares itself stuck.

This place-based navigation scheme allows the robot to traverse building scale maps. Practical limits are dictated by site conditions. Successful map navigation relies on the ability to avoid drastic changes in the environment between recording and replay operations.

Implementing the GraphNav service APIs requires four phases:



1. Record a map, which can be done by an operator using the Autowalk feature on the controller tablet, by writing a client application that uses the GraphNavRecordingService RPC to record a map, or by using the [`recording_command_line` example](../../../python/examples/graph_nav_command_line/README.md).
2. Upload the recorded map to the robot.
3. Initialize the robot's location to the map.
4. Command the robot to navigate to another waypoint in the map.


## GraphNavService RPCs

| RPC  | Description |
| ---- | ----------- |
| SetLocalization |	Trigger a manual localization. Typically done to provide the initial localization.
| NavigateRoute |	Tell GraphNav to navigate/traverse a given route.
| NavigateTo |	Tell GraphNav to navigate to a waypoint along a route it chooses.
| NavigateToAnchor | Tell GraphNav to navigate to a goal with respect to the current anchoring.
| NavigationFeedback |	Get feedback on the active navigation command.
| GetLocalizationState |	Get the localization status, pose, and optionally, current sensor data.
| ClearGraph |	Clears the graph structure. Also the localization.
| DownloadGraph |	Download the full list of waypoint IDs, graph topology and other small info.
| UploadGraph |	Upload the full list of waypoint IDs, graph topology and other small info.
| UploadWaypointSnapshot |	Uploads sensor data taken at a particular waypoint. Uses a streaming RPC because of the amount of data in the snapshot.
| UploadEdgeSnapshot |	Uploads large edge snapshot as a stream for a particular edge.
| DownloadWaypointSnapshot |	Download waypoint data from the server.
| DownloadEdgeSnapshot |	Download edge data from the server.
| ValidateGraph | Verify that the graph is still valid and all required external services are still available.



## GraphNavRecordingService RPCs

Map recording is provided by the GraphNavRecordingService RPC.

| RPC  | Description |
| ---- | ----------- |
| StartRecording |	Begin recording a chain of waypoints.
| SetRecordingEnvironment |	Define persistent annotations for edges and waypoints.
| GetRecordStatus |	Get feedback on the state of the recording service.
| CreateWaypoint  |	Create a waypoint at the current location.
| CreateEdge |	Create an edge between two waypoints.
| StopRecording |	Pause the recording service.
| GetRecordStatus| Tells the client the internal state of the record service, and the structure of the map that has been recorded so far.


Once StartRecording is called, the recording service starts creating waypoints, edges, and associated snapshots.


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
