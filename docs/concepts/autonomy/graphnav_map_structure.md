<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# GraphNav Map Structure

GraphNav maps consist of waypoints and edges between the waypoints. A waypoint consists of a reference frame, a name, a unique ID, annotations, and sensor data. Each waypoint contains a snapshot, which bundles the various sensor data into one unit.

*   Waypoint data includes feature clouds, AprilTag detections, imagery, terrain maps, etc.
*   Edges consist of a directed edge from one waypoint to another and a transform that estimates the relationship in 3D space between the two waypoints.


## View Map Python Example

Use the [`view_map` example](../../../python/examples/graph_nav_view_map/README.md) in the Spot SDK to view maps recorded using Autowalk on the controller tablet, or using the Spot GraphNav service.

Point cloud data is captured at each waypoint. These data depict features that the robot encountered during the map recording process. The point clouds are colored by height, where blue is higher and red is lower.

The viewer also shows fiducials that were detected during the map recording process. Fiducials are shown as blue squares labeled with the fiducial ID. If multiple fiducials with the same ID are displayed near each other, this represents multiple detections taken at different times during recording.

Maps do not have a global coordinate system (like GPS coordinates, for example). Only the relative transformations between waypoints are known.


## Creating waypoints

Waypoints are created by the robot every two meters during map recording. However, they can be created in areas where the robot’s path has more curvature as it navigates around corners and obstacles.

Call the `CreateWaypoint` RPC at specific locations in order to perform some action in a mission or when you want to explicitly maintain some mapping between a user event and a waypoint ID. Example: creating a waypoint at an inspection point.


## Downloading maps

Waypoints and edges have associated snapshots that store data the robot uses to compute localization and inform the robot’s locomotion.

*   Waypoint snapshots contain geometry and image data for localization.
*   Edge snapshots contain only the robot's footstep locations.
*   Edge annotations contain hints such as 'this edge traverses stairs' which informs the lower level locomotion systems on the robot.

The recording process creates waypoints, edges between them, and snapshot data on the robot.

Snapshot data are recorded and cached on the robot. To preserve and reuse a map, it must be downloaded from the robot. Graph data is not cached. Though the cache is large (up to 5GB) and persists across reboots, recording new maps might move waypoints and edges in a recorded map out of the cache. As a rule, we recommend downloading a recorded map at the conclusion of the recording process.

Because graph data is not cached, this data is lost when the robot is rebooted. Downloading snapshot data using DownloadSnapshot may work but should be downloaded before rebooting the robot.

Saving the map for reuse involves two steps:

1. Download the structure of the map by calling the `DownloadGraph` RPC.
2. Download snapshot data by calling the `DownloadWaypointSnapshot` and `DownloadEdgeSnapshot` RPCs.

Two steps are needed because snapshot data is very large. Snapshots are downloaded via a streaming RPC. The request is initiated by specifying which snapshot ID to download and, for waypoint snapshots, whether or not to include full image data in the download. Note that the full image data is not needed for the robot to navigate.


## Download a map from the controller tablet

To download a map recorded using Autowalk on the tablet, transfer the map to your local machine from the following location on the controller:


    Documents/bosdyn/autowalk/your_map.walk

Attach a USB cable between tablet or computer to transfer files. The map files should have the following directory structure on your local system:

    /your_map.walk
        graph
        waypoint_snapshots
        edge_snapshots


## Uploading maps

Maps stored on client computers can be uploaded to the robot for reuse in two steps:


1. The map structure is uploaded as a graph to the robot using the `UploadGraphRequest` RPC.
2. Snapshot data is uploaded to the robot using the streaming `UploadWaypointSnapshot` and `UploadEdgeSnapshot` RPCs.

See the [`graph_nav_command_line` and `recording_command_line` examples](../../../python/examples/graph_nav_command_line/README.md) for details about uploading edge snapshots, waypoint snapshots, and graphs to the robot.


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
