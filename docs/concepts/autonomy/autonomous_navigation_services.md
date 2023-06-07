<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Navigation Services

GraphNav and Missions APIs allow client applications to localize the robot and define tasks for the robot to carry out during autonomous operation. While these services can be used independently, it's far more likely that your application will access these services in a coordinated fashion.

Review [the extensive catalog of code examples](../../../python/examples/README.md) in the Spot SDK to learn about accessing robot services with the Spot API.

The autonomous navigation and related services include:


*   GraphNavService
*   GraphNavRecordingService
*   MissionService
*   RemoteMissionService


 Refer to the [Python API Reference](../../../protos/bosdyn/api/README.md) for details about the APIs available for each service.


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
