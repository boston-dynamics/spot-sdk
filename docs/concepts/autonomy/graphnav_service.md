<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# [Spot SDK](../../../README.md) > [Concepts](../README.md) > [Autonomy](README.md) > <br/> GraphNav Service

The GraphNav service is a place-based localization and locomotion service. You access the GraphNavService on the robot by making RPC calls to localize the robot, navigate a route, or download snapshot data.

Maps are recorded using the GraphNavRecording service or by operating the robot using the tablet controller and using the Autowalk feature to record a map.

Maps contain waypoints and edges. Together, these are known as graphs. The recorded map is used by the robot to follow a sequence of waypoints and edges. During playback, the robot compares its real-time sensor data with sensor data stored during the recording process. This helps the robot determine its location or pose during playback so it can make adjustments.


## Navigation

The GraphNav service is used to navigate between waypoints that are connected by edges in a recorded map. In general, the service tries to stay as close as possible to the recorded routes. The robot has the ability to adapt its route if obstacles are encountered along the way, unless the deviation takes the robot too far away from the recorded route, in which case the robot declares itself stuck.

This place-based navigation scheme allows the robot to traverse building scale maps. Practical limits are dictated by site conditions. Successful map navigation relies on the ability to avoid drastic changes in the environment between recording and replay operations.

Implementing the GraphNav service APIs requires four phases:



1. Record a map, which can be done by an operator using the Autowalk feature on the controller tablet, by writing a client application that uses the GraphNavRecordingService RPC to record a map, or by using the [recording_command_line example](../../../python/examples/graph_nav_command_line/recording_command_line.py).
2. Upload the recorded map to the robot.
3. Initialize the robot's location to the map.
4. Command the robot to navigate to another waypoint in the map.


## GraphNavService RPCs


<table>
  <tr>
   <td><strong>RPC</strong>
   </td>
   <td><strong>Description</strong>
   </td>
  </tr>
  <tr>
   <td>SetLocalization
   </td>
   <td>Trigger a manual localization. Typically done to provide the initial localization.
   </td>
  </tr>
  <tr>
   <td>NavigateRoute
   </td>
   <td>Tell GraphNav to navigate/traverse a given route.
   </td>
  </tr>
  <tr>
   <td>NavigateTo
   </td>
   <td>Tell GraphNav to navigate to a waypoint along a route it chooses.
   </td>
  </tr>
  <tr>
   <td>NavigationFeedback
   </td>
   <td>Get feedback on the active navigation command.
   </td>
  </tr>
  <tr>
   <td>GetLocalizationState
   </td>
   <td>Get the localization status, pose, and optionally, current sensor data.
   </td>
  </tr>
  <tr>
   <td>ClearGraph
   </td>
   <td>Clears the graph structure. Also the localization.
   </td>
  </tr>
  <tr>
   <td>DownloadGraph
   </td>
   <td>Download the full list of waypoint IDs, graph topology and other small info.
   </td>
  </tr>
  <tr>
   <td>UploadGraph
   </td>
   <td>Upload the full list of waypoint IDs, graph topology and other small info.
   </td>
  </tr>
  <tr>
   <td>UploadWaypointSnapshot
   </td>
   <td>Uploads sensor data taken at a particular waypoint. Uses a streaming RPC because of the amount of data in the snapshot.
   </td>
  </tr>
  <tr>
   <td>UploadEdgeSnapshot
   </td>
   <td>Uploads large edge snapshot as a stream for a particular edge.
   </td>
  </tr>
  <tr>
   <td>DownloadWaypointSnapshot
   </td>
   <td>Download waypoint data from the server.
   </td>
  </tr>
  <tr>
   <td>DownloadEdgeSnapshot
   </td>
   <td>Download edge data from the server.
   </td>
  </tr>
</table>



## GraphNavRecordingService RPCs

Map recording is provided by the GraphNavRecordingService RPC.


<table>
  <tr>
   <td><strong>RPC</strong>
   </td>
   <td><strong>Description</strong>
   </td>
  </tr>
  <tr>
   <td>StartRecording
   </td>
   <td>Begin recording a chain of waypoints.
   </td>
  </tr>
  <tr>
   <td>SetRecordingEnvironment
   </td>
   <td>Define persistent annotations for edges and waypoints.
   </td>
  </tr>
  <tr>
   <td>GetRecordStatus
   </td>
   <td>Get feedback on the state of the recording service.
   </td>
  </tr>
  <tr>
   <td>CreateWaypoint
   </td>
   <td>Create a waypoint at the current location.
   </td>
  </tr>
  <tr>
   <td>CreateEdge
   </td>
   <td>Create an edge between two waypoints.
   </td>
  </tr>
  <tr>
   <td>StopRecording
   </td>
   <td>Pause the recording service.
   </td>
  </tr>
</table>


Once StartRecording is called, the recording service starts creating waypoints, edges, and associated snapshots.


<br />

<a href="autonomous_navigation_services.md" class="previous">&laquo; Previous</a>  |  <a href="graphnav_map_structure.md" class="next">Next &raquo;</a>


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
