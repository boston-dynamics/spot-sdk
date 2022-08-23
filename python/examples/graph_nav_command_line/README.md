<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# GraphNav and Recording Service Command Line Interfaces

These example programs demonstrate how to use the GraphNav API to record GraphNav Maps, localize against them, and command the robot to navigate to waypoints. See the [Autonomy API documentation](https://dev.bostondynamics.com/docs/concepts/autonomy/readme) for more details about what is available in the SDK.

There are two examples in this directory: `graph_nav_command_line.py`, which is used to localize against a Graph Nav map and navigate on it, and `recording_command_line.py`, which is used to record new Graph Nav maps.

## Setup Dependencies

These examples require the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

# Example Programs

## Recording Service Command Line

This program demonstrates how to record a new Graph Nav map.

### Setting up for Recording

Before you start, make sure that the robot is in a location where it can see a fiducial. The robot will later use this fiducial to _initialize_ to the map.

The recording_command_line example does not require a robot lease, and does not acquire the estop of the robot. It passively runs while another service (such as the tablet, or another example) controls the robot. So, before you run this example, you should be connected to the robot via a tablet (if available), or some other service which is able to drive the robot.

### How to Run

To run the example:

```
python3 -m recording_command_line --download-filepath <path_to_downloaded_map> ROBOT_IP
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

### Using the Example to Record a Map

Running the recording command line example shows a prompt with options. Type a number or letter and press _enter_ to execute one of the options. Here are the options you should see:

```
    Options:
    (0) Clear map.
    (1) Start recording a map.
    (2) Stop recording a map.
    (3) Get the recording service's status.
    (4) Create a default waypoint in the current robot's location.
    (5) Download the map after recording.
    (6) List the waypoint ids and edge ids of the map on the robot.
    (7) Create new edge between existing waypoints using odometry.
    (8) Create new edge from last waypoint to first waypoint using odometry.
    (9) Automatically find and close loops.
    (a) Optimize the map's anchoring.
    (q) Exit.
```

To record a basic map, do the following:

- Using the tablet or another service, stand the robot up.
- Enter _1_ to start recording a map.
- Using the tablet or another service, walk the robot around.
- Enter _2_ to stop recording a map.
- Enter _5_ to download the map. It will be saved to the download directory.
- Enter _q_ to quit the application.

### Advanced Usage

Simply starting and stopping recording will cause the recording service to create a _chain_ of waypoints and edges from the start to the end. This means that the robot can only walk along this chain (as if it were on a rail). However, the recording service is also capable of making _branches_ and _loops_.

To manually create an edge, use option _7_. This will prompt you for two waypoint ids (which you can find using option _6_, or using the view_map.py example after you download the map). It will create an edge using these two waypoints and kinematic odometry as a guess to how those two waypoints are connected.

You can also create an edge between the start and end of a chain by using option _8_. This is commonly used when a robot returns back to the location it started recording in.

Option _9_ allows the recording service to automatically identify and close loops (including at the start and end of the map), using fiducials, odometry, and other methods (see [here](https://dev.bostondynamics.com/docs/concepts/autonomy/graphnav_map_structure#map-processing) for details.)

Option _a_ creates an _anchoring_ for the map, which allows it to be more accurately drawn and used for data export (see [here](https://dev.bostondynamics.com/docs/concepts/autonomy/graphnav_map_structure#anchorings-and-anchoring-optimization) for more details.)

## GraphNav Service Command Line

This program demonstrates how to use the different GraphNav requests to upload maps to the robot, get the current localization of the robot on a map, and navigate the map (using either a specific route or a destination waypoint id), and clear the existing map on robot.

### Setting up for Navigation

The command line example will take control of the robot and navigate autonomously. A body lease and an E-Stop is required for navigation commands, so the tablet or the WASD python example must be disconnected. Additionally, the client must manually start an E-Stop endpoint, which can be run from a second command line terminal in the folder `bosdyn/python/examples/estop/`:

```
python3 -m estop_gui ROBOT_IP
```

Also, ensure that the robot is not currently recording a graph nav map. Recording can be stopped using the above `recording_command_line` example script.

The graph and snapshots can be uploaded to the robot from a folder specified in the `upload-filepath` command line argument. The `upload-filepath` argument must be a full path, and the folder must contain the graph and folders "edge_snapshots" and "waypoint_snapshots".

Note that if you used the `recording_command_line` example, the `download-filepath` is the same as the `upload-filepath` in this example.

Use the map viewer to see the different waypoint ids and the edges between them when issuing navigation commands. This tool will allow you to better visualize where the robot will travel before executing a navigation command. Additionally, you can list all waypoint ids and edge ids (which are represented by the two ids of the connected waypoints) on the command line from the robot's currently loaded map.

### How to Run

To run the example (with example filepath):

```
python3 -m graph_nav_command_line --upload-filepath ~/Downloads/my_graph_folder ROBOT_IP
```

### Using the Example to Navigate

After running the example, you will see the following options:

```
    Options:
    (1) Get localization state.
    (2) Initialize localization to the nearest fiducial (must be in sight of a fiducial).
    (3) Initialize localization to a specific waypoint (must be exactly at the waypoint).
    (4) List the waypoint ids and edge ids of the map on the robot.
    (5) Upload the graph and its snapshots.
    (6) Navigate to. The destination waypoint id is the second argument.
    (7) Navigate route. The (in-order) waypoint ids of the route are the arguments.
    (8) Navigate to in seed frame. The following options are accepted for arguments: [x, y],
        [x, y, yaw], [x, y, z, yaw], [x, y, z, qw, qx, qy, qz]. (Don't type the braces).
        When a value for z is not specified, we use the current z height.
        When only yaw is specified, the quaternion is constructed from the yaw.
        When yaw is not specified, an identity quaternion is used.
    (9) Clear the current graph.
    (q) Exit.
```

To execute a command, type the letter or number next to that command, and press _enter_.

Before the robot can complete any navigation commands, a map must be uploaded (option _5_) to the robot or recorded on the robot recently without powering off the robot. Additionally, the localization must be set: it will automatically be localized to the map if it was just recorded on the robot without any power cycles; otherwise, the localization must manually be initialized (option _2_ is recommended) when the robot is standing near a fiducial in the recorded map.

**Navigation Commands**

The navigation commands (options _6, 7, 8_) will power on and stand the robot up, execute the desired route, and then sit down and power off the robot when the navigation is complete. Use the E-Stop or quit the command line to stop navigation.

When issuing a _navigate to_ request (option _6_), supply the destination waypoint's id as the second argument in the command line. For example, an input could be:

```
> 6 zigzag-filly-8ieN.xz8c9pL5tDZtQYW+w==
```

Note that ids for the waypoints and edges can be shown by listing the graph ids from the command line.

> **NOTE:** instead of using the full waypoint ID, you may use 2 letter "short codes" whenever they are unambiguous. In this example `zigzag-filly-8ieN.xz8c9pL5tDZtQYW+w==` could be just `zf` if that is unique to the map. "Short codes" are only used in this program for convenience of typing. In all API commands, full waypoint IDs are required.

To issue a _navigate route_ (option _7_) command, the listed waypoints must be in order from the starting waypoint to the final destination waypoint. As well, each consecutive pair of waypoints must have an edge between it that is in the map. For example, an input could be:

```
> 7 hammy-skink-iKQI6hGQ.fCBWXJy6mmjqg== unread-beagle-vQfl7NrKVhHPOUoos+ffIg== zigzag-filly-8ieN.xz8c9pL5tDZtQYW+w==
```

In this example, there would also be a known edge (from waypoint id: `hammy-skink-iKQI6hGQ.fCBWXJy6mmjqg==`, to waypoint id: `unread-beagle-vQfl7NrKVhHPOUoos+ffIg==`) and a second edge (from waypoint id: `unread-beagle-vQfl7NrKVhHPOUoos+ffIg==`, to waypoint id: `zigzag-filly-8ieN.xz8c9pL5tDZtQYW+w==`). Note that you would likely be able to simplify this with short codes to `7 hs ub zf`.

To issue a _navigate to anchor_ (option _8_) command, you must first know where you want the robot to go in absolute (x, y) meter coordinates relative to the _seed frame_ (see [here](https://dev.bostondynamics.com/docs/concepts/autonomy/graphnav_map_structure#anchorings-and-anchoring-optimization) for more details). This allows the robot to navigate to a position on the map without necessarily knowing which waypoint is near that location.

For example, this command:

```
> 8 5.2 3.1 0.1
```

Would navigate to an anchor (option _8_), located at `x = 5.2m`, `y = 3.1m`, `yaw=0.1 radians`. The robot would then walk along the path to the nearest waypoint to that location, and then attempt to walk in a straight line to it.

> **NOTE**: use the get localization state command (option _1_) to see where the robot believes it is in the seed frame, and which waypoint it believes it is currently at.
