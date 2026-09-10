<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Graph Nav Map to USD

This example demonstrates how to extract point cloud data from a Graph Nav map and export it to a USD (Universal Scene Description) file.

## Overview

The `map_to_usd.py` script loads a Graph Nav map that has been globally optimized using anchoring optimization, extracts all point cloud data from the waypoint snapshots, and exports the combined point cloud to a USD file.

USD files can be viewed in various applications including:

- NVIDIA Omniverse
- Apple Reality Composer
- Pixar's usdview
- Blender (with USD support)

## Requirements

This example requires the `usd-core` package (which provides the `pxr` module) for USD file writing:

```shell
python3 -m pip install -r requirements.txt
```

## Usage

```shell
python3 map_to_usd.py --path <map_directory> --output <output.usd>
```

### Arguments

| Argument              | Description                                                                                                                                                                                                                                           |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--path`              | Path to the Graph Nav map directory (required)                                                                                                                                                                                                        |
| `--output`            | Output USD file path (required). Should end in `.usd`, `.usda` (ASCII), or `.usdc` (binary). Defaults to `.usdc` if no extension is provided. The `.usda` extension creates human-readable ASCII files, while `.usdc` creates optimized binary files. |
| `--up-axis`           | Up axis for the USD scene. Choices: `Y` or `Z` (default: `Z`)                                                                                                                                                                                         |
| `--meters-per-unit`   | Scale factor for the scene (default: `1.0` for meters)                                                                                                                                                                                                |
| `--max-depth`         | Maximum distance from depth camera for raw point clouds in meters. Does not apply to lidar data (default: `3.0`)                                                                                                                                      |
| `--voxel-size`        | Voxel size for point cloud downsampling in meters. Applies to both localization and raw point clouds. `0` disables downsampling (default: `0`)                                                                                                        |
| `--exclude-waypoints` | Exclude waypoint marker disks from the output                                                                                                                                                                                                         |
| `--exclude-edges`     | Exclude edge lines connecting waypoints from the output                                                                                                                                                                                               |

### Examples

Export a map to a USD file with default settings:

```shell
python3 map_to_usd.py --path ~/my_map --output point_cloud.usdc
```

Export with Y-up axis (common for some 3D applications):

```shell
python3 map_to_usd.py --path ~/my_map --output point_cloud.usdc --up-axis Y
```

Export with downsampling for smaller file size:

```shell
python3 map_to_usd.py --path ~/my_map --output point_cloud.usdc --max-depth 2.5 --voxel-size 0.01
```

Export without waypoint and edge geometry (point clouds only):

```shell
python3 map_to_usd.py --path ~/my_map --output point_cloud.usdc --exclude-waypoints --exclude-edges
```

## Output

The script creates a USD file containing:

- A root Xform at `/World`
- `/World/Waypoints/<waypoint_id>/`: Parent Xform for each waypoint containing:
  - `Disk`: Flat cylindrical disk (10cm radius) marking the waypoint location (green)
  - `LocalizationPointCloud`: Visual feature point cloud colored by height gradient (blue to red)
  - `RawPointCloud`: Point cloud from stereo depth cameras with RGB colors from visual images
- `/World/Edges/EdgeLines`: Lines connecting adjacent waypoints (orange)
- `Points` primitives with per-vertex display colors

## Notes

- The map must have anchoring data. If your map doesn't have anchoring, run anchoring optimization first using the Graph Nav Anchoring Optimization example.
- Localization point clouds refer to the point clouds Graph Nav has processed to be used for navigation.
- Raw point clouds are generated from the raw images stored in each graph_nav waypoint snapshot. By default, these will not be included. API clients must set "include_images" to true in the DownloadWaypointSnapshot.
