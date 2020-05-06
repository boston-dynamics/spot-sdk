<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# [Spot SDK](../../../README.md) > [Concepts](../README.md) > [Autonomy](README.md) > <br/> GraphNav Initialization

When a map is initially loaded, GraphNav is unaware of the robot’s location relative to it. The GraphNav service provides a set of basic primitives to initialize the robot’s location to the map. Each one requires various levels of help from the user.



*   Using fiducials to initialize the robot’s localization
*   Using local geometry and texture around the robot to initialize the robot’s location


## Initializing with fiducials

This is the easiest method of initializing the robot's pose to the map.

FiducialInit enums:



*   FIDUCIAL_INIT_NEAREST = 2; // Localize to the nearest fiducial in any waypoint.
*   FIDUCIAL_INIT_NEAREST_AT_TARGET = 3; // Localize to nearest fiducial at the target waypoint.
*   FIDUCIAL_INIT_SPECIFIC = 4; // Localize to the given fiducial at the target waypoint.


## About fiducials

Fiducials are specially designed images similar to QR codes that Spot uses to match its internal map to the world around it.

Fiducials are required:



*   At the beginning of every mission (Autowalk only)
*   In "feature desert" areas where there is not enough information for Spot’s sensors to determine its location in the environment, fiducials might help prevent the robot getting lost

Spot recognizes AprilTag fiducials that meet the following requirements:



*   Fiducials that are part of the AprilTag Tag36h11 set
*   Image size: 146mm square
*   Printed on white non-glossy US-letter size sheets

Spot is configured to treat fiducials as 146mm squares and computes the distance based on that size. If a fiducial is printed at another size, Spot will infer the wrong position.

Boston Dynamics provides a small sample of correctly sized AprilTag fiducials that are recognized by the Spot robot in _Spot Autowalk: Using AprilTag Fiducials_, part of the Spot user documentation. Printing this set at 100% scaling will produce the correctly sized fiducial images.

Background information about AprilTags can be found at the University of Michigan April Robotics Lab: https://april.eecs.umich.edu/software/apriltag


## Placing fiducials

When placing fiducials, be sure to:



*   Place one at the mission’s starting location.
*   Tape fiducials flat against a vertical wall, as securely as possible. If fiducials move after recording, the mission may no longer replay.
*   Place them low on the wall. The top of the fiducial image should be at human knee height, 45-60cm (18-24") above the ground.
*   Place them in a permanent location where they will persist for as long as you plan to replay the mission.
*   Place them in areas which are feature deserts, for example a span of over 3m of featureless white wall.

When placing fiducials, avoid the following:



*   Repeating the same fiducial multiple times in a single mission. Each fiducial in a mission must be unique, however the same fiducial can be used in multiple missions.
*   Placing fiducials in areas with inconsistent lighting. Shadowed or unevenly lit fiducials can have unreliable detections.
*   Placing fiducials so that they are backlit by a bright background, such as on a window.
*   Placing fiducials where they will be blocked, damaged, moved, or removed.

Note: Areas with intersecting walls, corners, furniture, equipment, and other visually distinguishing features do not typically require a fiducial (unless the mission starts in that location). Using a LIDAR payload for navigation will reduce the number of fiducials required.


## Initializing with search

If fiducials aren’t available and the client program doesn’t have a close initial guess as to the robot’s pose relative to a known waypoint, then GraphNav can perform a brute force search.

The parameters of that search are set via max_distance and max_yaw as well as the waypoint to initialize to. Depending on those parameters, SetLocalization can take a long time to complete.


## Initializing with local geometry and texture

Spot can run a proprietary initialization algorithm that compares local geometry and texture from where the robot is now, to similar data collected at record time. In the API, we call this a _Scan Match_. This technique is best suited in areas with unique features: corners, doorways; it will work poorly in areas with non unique features / no features: bland hallways, big open spaces.

For your reference, the Spot base platform considers anything &lt; 3 meters away “local geometry.” Spot with Lidar considers anything &lt; 100 meters away “local geometry.”

The client must provide a reasonable guess as to where the robot is relative to a known waypoint on the map. If that guess is reasonably close, and the features around the robot are rich enough, scan match initialization can establish initial map pose without needing fiducials.

This is accomplished by leaving max_distance and max_yaw unset in the SetLocalizationRequest and by specifying FIDUCIAL_INIT_NO_FIDUCIAL.

<br />

<a href="graphnav_map_structure.md" class="previous">&laquo; Previous</a>  |  <a href="localization.md" class="next">Next &raquo;</a>


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
