<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# GraphNav Point Cloud Extractor

This is an example program for opening and parsing a GraphNav map and extracting a globally consistent point cloud from it. This requires the map to have been run through Anchoring Optimization first (see the graph_nav_anchoring_optimization example. Note that if the map was recorded using Autowalk, it will automatically meet the prerequisites). The data is expected to be in XYZ32F format.

## Setup Dependencies

This example requires Numpy, and requires python 3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Running the Example

1. Record a map using AutoWalk or the Command Line interface. (If using Autowalk, transfer the map from Documents/bosdyn/autowalk/your_map.walk to your local machine using a USB cable). The map should be a directory of the form:

```
- /your_map.walk
    + graph
    - waypoint_snapshots
    - edge_snapshots
```

2. Run the point cloud extractor

```
python3 -m extract_point_cloud --path <path_to_your_map_directory> --output <output PLY file>
```

## Understanding the Point Cloud Extractor

This example

1. Loads a Graph Nav Map from a directory.
2. Extracts the data from each waypoint.
3. Transforms the data into the seed frame using the anchoring of each waypoint.
4. Saves the data to a .PLY file.

To view the data, use a 3D model viewer (such as MeshLab or CloudCompare).

## What is actually in the point cloud?

For base platform robots, the data in the point cloud will be visual feature data. It will be sparse, and correspond to 3D points with high contrast near the robot. For robots with LIDAR, the data will be a combination of visual feature data and LIDAR data. LIDAR data is down-sampled to a 10cm resolution, and some horizontal surfaces (e.g. the floor or ceiling) are intentionally filtered out.

These data are used for localization purposes and shouldn't be used as, for example, a "digital twin".
