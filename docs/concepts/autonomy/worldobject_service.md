<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# [Spot SDK](../../../README.md) > [Concepts](../README.md) > [Autonomy](README.md) > <br/> World Object Service

The WorldObjectService allows clients to list all of the objects that the robot is tracking via the ListWorldObjects RPC. The service can also inform the robot of world objects that it might not be able to detect itself via the MutateWorldObjects RPC.

World objects are higher-level items in the scene that have some amount of semantic information associated with them. For example, a WorldObject could be an AprilTag fiducial, a door handle, or a virtual object drawn for debugging purposes.

Currently, the most common use case is to capture AprilTag fiducials detections from the robot’s cameras. Fiducials are commonly used as ground truth reference objects, notably to initialize the robot's localization. Any fiducials detected by the robot’s cameras will be returned as WorldObjects with a timestamp, an ID, a name, and a frame object describing the fiducial location.

If a payload or other client can detect objects the robot can’t, for example, a payload camera that can spot fiducials on the ceiling, then the client can inform the robot of that object which might be referenced by other behaviors.


<table>
  <tr>
   <td><strong>RPC</strong>
   </td>
   <td><strong>Description</strong>
   </td>
  </tr>
  <tr>
   <td>ListWorldObjects
   </td>
   <td>List all world objects
   </td>
  </tr>
  <tr>
   <td>MutateWorldObjects
   </td>
   <td>Mutate the world objects
   </td>
  </tr>
</table>


Refer to these Python code examples for details.

*   [mutate_world_objects](../../../python/examples/world_object_mutations/mutate_world_objects.py)
*   [add_image_coordinates](../../../python/examples/add_image_coordinates_to_scene/add_image_coordinates.py)
*   [fiducial_follow](../../../python/examples/fiducial_follow/fiducial_follow.py)
*   [get_world_objects](../../../python/examples/get_world_objects/get_world_objects.py)


<br />

<a href="missions_service.md" class="previous">&laquo; Previous</a>


<!--- image and page reference link definitions --->
[autonomous-top]: README.md "Spot SDK: Autonomy, GraphNav, and Missions"
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
