<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Autonomy

The Spot SDK includes APIs, client libraries, and examples that support the development of autonomous navigation behaviors for the Spot robot. Collectively, this service is referred to as GraphNav. Maps are recorded and saved and later can be replayed with any robot in your fleet. During the map recording process, you can assign actions and API callbacks to waypoints along the map route.

For robot operators, autonomous navigation is accessed using the Autowalk feature on the robot's controller tablet. Operators use Autowalk to record and play back missions. Likewise, API callbacks and other actions can be added to waypoints during map recording.

The Autowalk feature is an implementation of the autonomous navigation API. However, the API supports more complex route topologies and autonomous behaviors and therefore provides software engineers the flexibility to develop complex autonomy solutions with the Spot robot.

## Contents

* [Autonomy Technical Summary](graphnav_tech_summary.md)
* [Autonomous navigation code examples](autonomous_navigation_code_examples.md)
* [Components of autonomous navigation](components_of_autonomous_navigation.md)
* [Docking](docking.md)
* [Typical autonomous navigation use case](typical_autonomous_navigation_use_case.md)
* [Autonomous navigation services](autonomous_navigation_services.md)
* [GraphNav service](graphnav_service.md)
* [GraphNav map structure](graphnav_map_structure.md)
* [GraphNav area callbacks](graphnav_area_callbacks.md)
* [Initialization](initialization.md)
* [Localization](localization.md)
* [GraphNav and robot locomotion](graphnav_and_robot_locomotion.md)
* [Missions service](missions_service.md)
* [Autowalk service](autowalk_service.md)
* [Network compute bridge](../network_compute_bridge.md)
* [AutoReturn service](auto_return.md)
* [Directed Exploration](directed_exploration.md)
* [GPS](gps.md)