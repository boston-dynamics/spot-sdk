<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# GraphNav and Recording Service Command Line Interfaces

These example programs demonstrate how to use the GraphNav API by creating command line interfaces to record maps and then localize and navigate these maps.

## Setup Dependencies

These examples require the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Recording Service Command Line
This interface exposes the recording service's requests to record and create a map. The recording service must be put into 'recording mode' to be able to add waypoints to the map (both automatically and manually). While recording a map, the robot can be driven (and have E-Stop) using either the app on the tablet or the WASD python example. As the robot walks around, waypoints will be added to the map automatically based on the path the robot walks. There is also an option to create a waypoint manually at the location the robot is currently standing.

When starting to record a map, it is recommended that the robot is able to see a fiducial (see the Spot User Guide and documentation for specifics on the fiducial's size and type) and be standing up for better initialization.

Once the map is completely recorded, it can be downloaded such that it can be used by the GraphNav command line interface or the map viewer.

### Example Execution
To run the example:
```
python3 -m recording_command_line --username USER --password PASSWORD --download-filepath <path_to_downloaded_map> ROBOT_IP
```

Note that the `download-filepath` command line argument must be a full path. This argument is optional; if not provided, then the current working directory will be used. When a map is downloaded, it will be downloaded into a subfolder called `downloaded_graph` in the specified folder the layout is:

```
download-filepath
    - downloaded_graph
        - graph              # Serialized protobuf containing the waypoints and edges.
        - waypoint_snapshots # Large sensor data associated with waypoints.
            - snapshot_...   # Waypoints may share snapshots. The IDs of snapshots are unrelated to the IDs of waypoints.
            - snapshot_...
        - edge_snapshots     # Large sensor data associated with edges.
            - edge_snapshot_...
```


## GraphNav Service Command Line
This interface demonstrates how to use the different GraphNav requests to upload maps to the robot, get the current localization of the robot on a map, and navigate the map (using either a specific route or a destination waypoint id), and clear the existing map on robot. A body lease and an E-Stop is required for navigation commands, so the tablet or the WASD python example must be disconnected. Additionally, the client must manually start an E-Stop endpoint, which can be run from a second command line terminal in the folder `bosdyn/python/examples/estop/`:

```
python3 -m estop_gui --username USER --password PASSWORD ROBOT_IP
```

The graph and snapshots can be uploaded to the robot from a folder specified in the `upload-filepath` command line argument. The `upload-filepath` argument must be a full path, and the folder must contain the graph and folders "edge_snapshots" and "waypoint_snapshots".

Use the map viewer to see the different waypoint ids and the edges between them when issuing navigation commands. This tool will allow you to better visualize where the robot will travel before executing a navigation command. Additionally, you can list all waypoint ids and edge ids (which are represented by the two ids of the connected waypoints) on the command line from the robot's currently loaded map.

### Example Execution
To run the example (with example filepath):
```
python3 -m graph_nav_command_line --username USER --password PASSWORD --upload-filepath ~/Downloads/my_graph_folder ROBOT_IP
```

Before the robot can complete any navigation commands, a map must be uploaded to the robot or recorded on the robot recently without powering off the robot. Additionally, the localization must be set: it will automatically be localized to the map if it was just recorded on the robot without any power cycles; otherwise, the localization must manually be initialized when the robot is standing near a fiducial in the recorded map. 

The navigation commands will power on and stand the robot up, execute the desired route, and then sit down and power off the robot when the navigation is complete. Use the E-Stop or quit the command line to stop navigation.

When issuing a navigate to request, supply the destination waypoint's id as the second argument in the command line. For example, an input could be:
```
> 6 zigzag-filly-8ieN.xz8c9pL5tDZtQYW+w==
```
Note that ids for the waypoints and edges can be shown by listing the graph ids from the command line.
Also note that you may use 2 letter short codes whenever they are unambiguous.  In this example "zigzag-filly-8ieN.xz8c9pL5tDZtQYW+w==" could be just "zf" if that is unique.

To issue a navigate route command, the listed waypoints must be in order from the starting waypoint to the final destination waypoint. As well, each consecutive pair of waypoints must have an edge between it that is in the map. For example, an input could be:

```
> 7 hammy-skink-iKQI6hGQ.fCBWXJy6mmjqg== unread-beagle-vQfl7NrKVhHPOUoos+ffIg== zigzag-filly-8ieN.xz8c9pL5tDZtQYW+w==
```
In this example, there would also be a known edge (from waypoint id: hammy-skink-iKQI6hGQ.fCBWXJy6mmjqg==, to waypoint id: unread-beagle-vQfl7NrKVhHPOUoos+ffIg==) and a second edge (from waypoint id: unread-beagle-vQfl7NrKVhHPOUoos+ffIg==, to waypoint id: zigzag-filly-8ieN.xz8c9pL5tDZtQYW+w==).  Note that you would likely be able to simplify this with short codes to "7 hs ub zf".