<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# [Spot SDK](../../../README.md) > [Concepts](../README.md) > [Autonomy](README.md) > <br/> Examples

GraphNav provides place-based localization and locomotion services. Developers can record and play back maps for the robot to follow, navigating between waypoints and traversing edges between waypoints on the map.

The Spot SDK includes [python code examples](../../../python/examples) to help you get started with autonomous navigation. Refer to the following examples to learn about exercising the GraphNav API.


<table>
  <tr>
   <td>
   <a href="../../../python/examples/graph_nav_command_line/recording_command_line.py">recording_command_line.py</a>
   </td>
   <td>Demonstrates graphnav recording service requests to record, create, and download a map from the robot.
   </td>
  </tr>
  <tr>
   <td>
   <a href="../../../python/examples/graph_nav_command_line/graph_nav_command_line.py">graph_nav_command_line.py</a>
   </td>
   <td>Demonstrates how to use GraphNav requests to:
<ul>

<li>Upload maps to the robot

<li>Initialize the robot

<li>Get the current localization of the robot on a map

<li>Navigate the map (using either a specific route or a destination waypoint id)

<li>Clear the existing map on the robot
</li>
</ul>
   </td>
  </tr>
  <tr>
   <td>
   <a href="../../../python/examples/remote_mission_service/remote_mission_service.py">remote_mission_service.py</a>
   </td>
   <td>Demonstrates how to implement a RemoteMissionService and run it. This is how we support triggering off-robot code as part of Autowalk.
   </td>
  </tr>
  <tr>
   <td>
   <a href="../../../python/examples/graph_nav_view_map/view_map.py">view_map.py</a>
   </td>
   <td>An example program for opening, parsing, and viewing a GraphNav map. This example can be used with GraphNav maps generated using Autowalk or using the GraphNav APIs.
   </td>
  </tr>
</table>


<br />

<a href="README.md" class="previous">&laquo; Previous</a>  |  <a href="components_of_autonomous_navigation.md" class="next">Next &raquo;</a>



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
