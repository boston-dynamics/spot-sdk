<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Typical Autonomous Use Case

A typical use case for the autonomous navigation API:



1. A client application, the command line, or the controller tablet is used to operate the robot and record a map and any actions taken during the recording process.
2. During recording the client navigates the intended route, assigning actions such as API callbacks to waypoints along the way.
3. At the end of the route, recording is stopped and the recorded map and all of the associated actions and data are saved.
4. Other client applications can use the saved map to operate any robot in your fleet, following the recorded route and carrying out designated actions at waypoints, as defined during the recording process.
5. When the mission is concluded, the client app captures, processes, or stores data that was collected during the mission.
6. Log files and other data may be downloaded for analysis.


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
