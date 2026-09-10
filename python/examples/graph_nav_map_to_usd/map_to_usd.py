# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Copyright (c) 2026 Boston Dynamics, Inc.  All rights reserved.

This example shows how to load a graph nav map and export its point cloud to a USD (Universal Scene
Description) file. This requires a map which has been globally optimized using anchoring
optimization.

Use a USD viewer (such as NVIDIA Omniverse, Apple Reality Composer, or usdview) to view the output.
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
from pxr import Gf, Sdf, Usd, UsdGeom, Vt

from bosdyn.api.graph_nav import map_pb2
from bosdyn.client.frame_helpers import ODOM_FRAME_NAME, get_a_tform_b
from bosdyn.client.math_helpers import SE3Pose

# Mapping of depth image names to their corresponding visual image names
STEREO_PAIRS = {
    'back_depth': 'back_fisheye_image',
    'frontleft_depth': 'frontleft_fisheye_image',
    'frontright_depth': 'frontright_fisheye_image',
    'left_depth': 'left_fisheye_image',
    'right_depth': 'right_fisheye_image',
}


def get_point_cloud_data_in_seed_frame(waypoints, snapshots, anchorings, waypoint_id):
    """Create a N x 3 numpy array of points in the seed frame. Note that in graph_nav, "point cloud"
    refers to the feature cloud of a waypoint -- that is, a collection of visual features observed
    by all five cameras at a particular point in time. The visual features are associated with
    points that are rigidly attached to a waypoint.

    :param waypoints: dict of waypoint ID to waypoint.
    :param snapshots: dict of waypoint snapshot ID to waypoint snapshot.
    :param anchorings: dict of waypoint ID to the anchoring of that waypoint w.r.t the map.
    :param waypoint_id: the waypoint ID of the waypoint whose point cloud we want to extract.
    :return: a N x 3 numpy array in the seed frame.
    """
    wp = waypoints[waypoint_id]
    snapshot = snapshots[wp.snapshot_id]
    cloud = snapshot.point_cloud
    odom_tform_cloud = get_a_tform_b(cloud.source.transforms_snapshot, ODOM_FRAME_NAME,
                                     cloud.source.frame_name_sensor)
    waypoint_tform_odom = SE3Pose.from_proto(wp.waypoint_tform_ko)
    waypoint_tform_cloud = waypoint_tform_odom * odom_tform_cloud
    if waypoint_id not in anchorings:
        raise Exception(f'{waypoint_id} not found in anchorings. Does the map have anchoring data?')
    seed_tform_cloud = SE3Pose.from_proto(
        anchorings[waypoint_id].seed_tform_waypoint) * waypoint_tform_cloud
    point_cloud_data = np.frombuffer(cloud.data, dtype=np.float32).reshape(int(cloud.num_points), 3)
    return seed_tform_cloud.transform_cloud(point_cloud_data)


def get_intrinsics_from_source(source):
    """Extract camera intrinsics from an ImageSource.

    :param source: ImageSource proto.
    :return: tuple of (focal_length_x, focal_length_y, principal_point_x, principal_point_y).
    """
    if source.HasField('pinhole'):
        intr = source.pinhole.intrinsics
    elif source.HasField('pinhole_brown_conrady'):
        intr = source.pinhole_brown_conrady.intrinsics.pinhole_intrinsics
    elif source.HasField('kannala_brandt'):
        intr = source.kannala_brandt.intrinsics.pinhole_intrinsics
    else:
        raise ValueError(f"Unknown camera model for source: {source.name}")
    return (intr.focal_length.x, intr.focal_length.y, intr.principal_point.x,
            intr.principal_point.y)


def depth_image_to_pointcloud(depth_image, depth_source, max_depth=None):
    """Convert a depth image to a 3D point cloud in the camera frame.

    :param depth_image: 2D numpy array of depth values (uint16 in mm).
    :param depth_source: ImageSource proto for the depth camera.
    :param max_depth: Optional maximum depth in meters. Points beyond this are filtered out.
    :return: Nx3 numpy array of 3D points in the camera frame.
    """
    fx, fy, cx, cy = get_intrinsics_from_source(depth_source)
    rows, cols = depth_image.shape

    # Create pixel coordinate grids
    u, v = np.meshgrid(np.arange(cols), np.arange(rows))

    # Convert depth to meters (depth_scale is the value representing 1 meter)
    depth_meters = depth_image.astype(np.float32) / depth_source.depth_scale

    # Backproject to 3D
    # x = (u - cx) * z / fx
    # y = (v - cy) * z / fy
    # z = depth
    z = depth_meters
    x = (u - cx) * z / fx
    y = (v - cy) * z / fy

    # Stack into Nx3 array, filtering out invalid depth (0 or very small)
    valid_mask = depth_meters > 0.01  # At least 1cm depth
    if max_depth is not None:
        valid_mask &= depth_meters <= max_depth
    points = np.stack([x[valid_mask], y[valid_mask], z[valid_mask]], axis=1)

    return points, valid_mask


def project_points_to_image(points_3d, visual_source):
    """Project 3D points onto an image using camera intrinsics.

    :param points_3d: Nx3 numpy array of 3D points in the camera frame.
    :param visual_source: ImageSource proto for the visual camera.
    :return: Nx2 numpy array of pixel coordinates (u, v).
    """
    fx, fy, cx, cy = get_intrinsics_from_source(visual_source)

    # Project: u = fx * x / z + cx, v = fy * y / z + cy
    x, y, z = points_3d[:, 0], points_3d[:, 1], points_3d[:, 2]

    # Avoid division by zero
    z = np.maximum(z, 1e-6)

    u = fx * x / z + cx
    v = fy * y / z + cy

    return np.stack([u, v], axis=1)


def sample_colors_from_image(pixel_coords, visual_image, visual_source):
    """Sample colors from an image at the given pixel coordinates.

    :param pixel_coords: Nx2 numpy array of pixel coordinates (u, v).
    :param visual_image: 2D or 3D numpy array of image values (grayscale or RGB/RGBA uint8). Shape
        is (H, W) for grayscale or (H, W, C) for color.
    :param visual_source: ImageSource proto for the visual camera.
    :return: Nx3 numpy array of RGB colors (normalized 0-1), and a valid mask.
    """
    rows, cols = visual_source.rows, visual_source.cols
    is_color = len(visual_image.shape) == 3

    u = pixel_coords[:, 0]
    v = pixel_coords[:, 1]

    # Check bounds
    valid_mask = (u >= 0) & (u < cols - 1) & (v >= 0) & (v < rows - 1)

    # Initialize colors (default gray for invalid points)
    colors = np.full((len(pixel_coords), 3), 0.5, dtype=np.float32)

    if np.any(valid_mask):
        # Bilinear interpolation for smooth sampling
        u_valid = u[valid_mask]
        v_valid = v[valid_mask]

        u0 = np.floor(u_valid).astype(int)
        v0 = np.floor(v_valid).astype(int)
        u1 = u0 + 1
        v1 = v0 + 1

        # Clip to bounds
        u1 = np.minimum(u1, cols - 1)
        v1 = np.minimum(v1, rows - 1)

        # Interpolation weights
        wu = u_valid - u0
        wv = v_valid - v0

        if is_color:
            # Handle RGB or RGBA images (sample first 3 channels for RGB)
            num_channels = min(visual_image.shape[2], 3)
            for c in range(num_channels):
                c00 = visual_image[v0, u0, c].astype(np.float32)
                c01 = visual_image[v0, u1, c].astype(np.float32)
                c10 = visual_image[v1, u0, c].astype(np.float32)
                c11 = visual_image[v1, u1, c].astype(np.float32)

                interpolated = (c00 * (1 - wu) * (1 - wv) + c01 * wu * (1 - wv) + c10 *
                                (1 - wu) * wv + c11 * wu * wv) / 255.0
                colors[valid_mask, c] = interpolated
        else:
            # Handle grayscale images
            c00 = visual_image[v0, u0].astype(np.float32)
            c01 = visual_image[v0, u1].astype(np.float32)
            c10 = visual_image[v1, u0].astype(np.float32)
            c11 = visual_image[v1, u1].astype(np.float32)

            interpolated = (c00 * (1 - wu) * (1 - wv) + c01 * wu * (1 - wv) + c10 *
                            (1 - wu) * wv + c11 * wu * wv) / 255.0

            # Convert grayscale to RGB
            colors[valid_mask, 0] = interpolated
            colors[valid_mask, 1] = interpolated
            colors[valid_mask, 2] = interpolated

    return colors, valid_mask


def get_colorized_point_cloud_from_stereo(waypoints, snapshots, anchorings, waypoint_id,
                                          max_depth=3.0, voxel_size=0):
    """Extract colorized point clouds from all stereo camera pairs in a waypoint snapshot.

    :param waypoints: dict of waypoint ID to waypoint.
    :param snapshots: dict of waypoint snapshot ID to waypoint snapshot.
    :param anchorings: dict of waypoint ID to the anchoring of that waypoint w.r.t the map.
    :param waypoint_id: the waypoint ID of the waypoint whose point cloud we want to extract.
    :param max_depth: Maximum depth in meters from the depth camera. Points beyond this are filtered
        out. Default is 3.0 meters.
    :param voxel_size: Size of voxel grid for downsampling in meters. Default is 0 (no downsampling,
        full resolution). Set to e.g. 0.01 for 1cm voxels.
    :return: tuple of (Nx3 points array, Nx3 colors array) in the seed frame.
    """
    wp = waypoints[waypoint_id]
    snapshot = snapshots[wp.snapshot_id]

    if waypoint_id not in anchorings:
        raise Exception(f'{waypoint_id} not found in anchorings. Does the map have anchoring data?')

    # Build a dict of images by name for easy lookup
    images_by_name = {img.source.name: img for img in snapshot.images}

    all_points = []
    all_colors = []

    for depth_name, visual_name in STEREO_PAIRS.items():
        if depth_name not in images_by_name or visual_name not in images_by_name:
            continue

        depth_response = images_by_name[depth_name]
        visual_response = images_by_name[visual_name]

        depth_source = depth_response.source
        visual_source = visual_response.source
        depth_shot = depth_response.shot
        visual_shot = visual_response.shot

        # Read frame names from the image protos
        depth_frame = depth_shot.frame_name_image_sensor
        visual_frame = visual_shot.frame_name_image_sensor

        # Parse depth image (uint16 raw)
        depth_data = np.frombuffer(depth_shot.image.data, dtype=np.uint16)
        depth_image = depth_data.reshape(depth_source.rows, depth_source.cols)

        # Parse visual image based on pixel format
        # Pixel formats: 1=GREYSCALE_U8, 3=RGB_U8, 4=RGBA_U8
        visual_data = np.frombuffer(visual_shot.image.data, dtype=np.uint8)
        pixel_format = visual_shot.image.pixel_format
        if pixel_format == 3:  # RGB_U8
            visual_image = visual_data.reshape(visual_source.rows, visual_source.cols, 3)
        elif pixel_format == 4:  # RGBA_U8
            visual_image = visual_data.reshape(visual_source.rows, visual_source.cols, 4)
        else:  # GREYSCALE_U8 or unknown - treat as grayscale
            visual_image = visual_data.reshape(visual_source.rows, visual_source.cols)

        # Convert depth to 3D points in depth camera frame
        # Filter out points beyond max_depth meters as they tend to be noisy
        points_depth_frame, valid_depth = depth_image_to_pointcloud(depth_image, depth_source,
                                                                    max_depth=max_depth)

        if len(points_depth_frame) == 0:
            continue

        # Get transform from depth camera to visual camera
        # Use the visual shot's transform snapshot which includes both frames
        try:
            depth_tform_visual = get_a_tform_b(visual_shot.transforms_snapshot, depth_frame,
                                               visual_frame)
        except Exception as e:
            print(f"Warning: Could not get transform from {depth_frame} to {visual_frame}: {e}")
            continue

        # Transform points to visual camera frame
        # visual_tform_depth = depth_tform_visual.inverse()
        # points_visual_frame = visual_tform_depth.transform_cloud(points_depth_frame)
        # Actually we need points in visual frame, so: p_visual = visual_tform_depth * p_depth
        visual_tform_depth = depth_tform_visual.inverse()
        points_visual_frame = visual_tform_depth.transform_cloud(points_depth_frame)

        # Project onto visual image
        pixel_coords = project_points_to_image(points_visual_frame, visual_source)

        # Sample colors
        colors, valid_proj = sample_colors_from_image(pixel_coords, visual_image, visual_source)

        # Transform points to seed frame
        # Get transform from depth camera to odom (using depth shot's transforms)
        odom_tform_depth = get_a_tform_b(depth_shot.transforms_snapshot, ODOM_FRAME_NAME,
                                         depth_frame)
        waypoint_tform_odom = SE3Pose.from_proto(wp.waypoint_tform_ko)
        seed_tform_waypoint = SE3Pose.from_proto(anchorings[waypoint_id].seed_tform_waypoint)
        seed_tform_depth = seed_tform_waypoint * waypoint_tform_odom * odom_tform_depth

        points_seed_frame = seed_tform_depth.transform_cloud(points_depth_frame)

        all_points.append(points_seed_frame)
        all_colors.append(colors)

    if not all_points:
        return np.empty((0, 3)), np.empty((0, 3))

    points = np.concatenate(all_points, axis=0)
    colors = np.concatenate(all_colors, axis=0)

    # Downsample to at most 1 point per voxel using voxel grid
    if voxel_size > 0:
        points, colors = voxel_downsample(points, colors, voxel_size=voxel_size)

    return points, colors


def voxel_downsample(points, colors, voxel_size=0.01):
    """Downsample a point cloud using voxel grid filtering.

    Keeps at most one point per voxel (cubic cell). For each voxel, the first point encountered is
    kept along with its color.

    :param points: Nx3 numpy array of point positions.
    :param colors: Nx3 numpy array of RGB colors (0-1 range).
    :param voxel_size: Size of each voxel in meters. Default is 0.01 (1cm).
    :return: tuple of (downsampled points, downsampled colors).
    """
    if len(points) == 0:
        return points, colors

    # Compute voxel indices for each point
    voxel_indices = np.floor(points / voxel_size).astype(np.int64)

    # Create a unique key for each voxel using a hash-like approach
    # Shift indices to handle negative values
    min_indices = voxel_indices.min(axis=0)
    shifted = voxel_indices - min_indices

    # Create unique voxel keys
    # Use a large prime multiplier to create unique keys
    max_dim = shifted.max(axis=0) + 1
    keys = (shifted[:, 0] * (max_dim[1] * max_dim[2]) + shifted[:, 1] * max_dim[2] + shifted[:, 2])

    # Find unique voxels and keep first point in each
    _, unique_indices = np.unique(keys, return_index=True)

    return points[unique_indices], colors[unique_indices]


def load_map(path):
    """Load a map from the given file path.

    :param path: Path to the root directory of the map.
    :return: the graph, waypoints, waypoint snapshots, edge snapshots, anchorings, and anchored
        world objects.
    """
    current_graph = map_pb2.Graph()
    current_graph.ParseFromString((path / "graph").read_bytes())

    # Set up maps from waypoint ID to waypoints, edges, snapshots, etc.
    current_waypoints = {}
    current_waypoint_snapshots = {}
    current_edge_snapshots = {}
    current_anchors = {}
    current_anchored_world_objects = {}

    # Load the anchored world objects first so we can look in each waypoint snapshot
    # as we load it.
    for anchored_world_object in current_graph.anchoring.objects:
        current_anchored_world_objects[anchored_world_object.id] = (anchored_world_object,)

    # For each waypoint, load any snapshot associated with it.
    for waypoint in current_graph.waypoints:
        current_waypoints[waypoint.id] = waypoint

        if len(waypoint.snapshot_id) == 0:
            continue
        # Load the snapshot. Note that snapshots contain all of the raw data in a waypoint
        # and may be large.
        file_name = path / "waypoint_snapshots" / waypoint.snapshot_id
        if not file_name.exists():
            continue
        waypoint_snapshot = map_pb2.WaypointSnapshot()
        waypoint_snapshot.ParseFromString(file_name.read_bytes())

        current_waypoint_snapshots[waypoint_snapshot.id] = waypoint_snapshot

        for fiducial in waypoint_snapshot.objects:
            if not fiducial.HasField("apriltag_properties"):
                continue

            str_id = str(fiducial.apriltag_properties.tag_id)
            if (str_id in current_anchored_world_objects and
                    len(current_anchored_world_objects[str_id]) == 1):
                # Replace the placeholder tuple with a tuple of (wo, waypoint, fiducial).
                anchored_wo = current_anchored_world_objects[str_id][0]
                current_anchored_world_objects[str_id] = (anchored_wo, waypoint, fiducial)

    # Similarly, edges have snapshot data.
    for edge in current_graph.edges:
        if len(edge.snapshot_id) == 0:
            continue
        file_name = path / "edge_snapshots" / edge.snapshot_id
        if not file_name.exists():
            continue
        edge_snapshot = map_pb2.EdgeSnapshot()
        edge_snapshot.ParseFromString(file_name.read_bytes())
        current_edge_snapshots[edge_snapshot.id] = edge_snapshot

    for anchor in current_graph.anchoring.anchors:
        current_anchors[anchor.id] = anchor

    print(f'Loaded graph with {len(current_graph.waypoints)} waypoints, '
          f'{len(current_graph.edges)} edges, {len(current_graph.anchoring.anchors)} anchors, '
          f'and {len(current_graph.anchoring.objects)} anchored world objects')

    return (current_graph, current_waypoints, current_waypoint_snapshots, current_edge_snapshots,
            current_anchors, current_anchored_world_objects)


def write_usd(data, output_path, up_axis='Z', meters_per_unit=1.0, colors=None):
    """Writes a point cloud to a USD file.

    :param data: Nx3 numpy array of point positions.
    :param output_path: Path to the output USD file.
    :param up_axis: The up axis for the scene ('Y' or 'Z'). Default is 'Z'.
    :param meters_per_unit: Scale factor for the scene. Default is 1.0 (meters).
    :param colors: Optional Nx3 numpy array of RGB colors (0-1 range). If not provided, colors are
        generated based on height (Z coordinate).
    """
    print(f'Saving {data.shape[0]} points to {output_path}')

    # Create a new USD stage
    stage = Usd.Stage.CreateNew(str(output_path))

    # Set up the stage metadata
    if up_axis.upper() == 'Y':
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    else:
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    UsdGeom.SetStageMetersPerUnit(stage, meters_per_unit)

    # Create the root xform
    root_xform = UsdGeom.Xform.Define(stage, '/World')
    stage.SetDefaultPrim(root_xform.GetPrim())

    # Create a Points primitive for the point cloud
    points_prim = UsdGeom.Points.Define(stage, '/World/PointCloud')

    # Convert numpy array to Vt array for USD
    # USD expects Gf.Vec3f for points
    points_vt = Vt.Vec3fArray(data.shape[0])
    for i in range(data.shape[0]):
        points_vt[i] = Gf.Vec3f(float(data[i, 0]), float(data[i, 1]), float(data[i, 2]))

    # Set the points attribute
    points_prim.GetPointsAttr().Set(points_vt)

    # Set point widths (size of each point for rendering)
    widths = Vt.FloatArray([0.01] * data.shape[0])  # 1cm point size
    points_prim.GetWidthsAttr().Set(widths)

    # Set display colors with vertex interpolation for per-point colors
    colors_vt = Vt.Vec3fArray(data.shape[0])
    if colors is not None:
        # Use provided colors
        for i in range(data.shape[0]):
            colors_vt[i] = Gf.Vec3f(float(colors[i, 0]), float(colors[i, 1]), float(colors[i, 2]))
    else:
        # Generate colors based on height (Z coordinate)
        z_values = data[:, 2]
        z_min, z_max = z_values.min(), z_values.max()
        z_range = z_max - z_min if z_max != z_min else 1.0

        for i in range(data.shape[0]):
            # Create a color gradient from blue (low) to red (high)
            t = (z_values[i] - z_min) / z_range
            colors_vt[i] = Gf.Vec3f(t, 0.2, 1.0 - t)

    # Use primvars API to set displayColor with vertex interpolation
    primvars_api = UsdGeom.PrimvarsAPI(points_prim)
    color_primvar = primvars_api.CreatePrimvar('displayColor', Sdf.ValueTypeNames.Color3fArray,
                                               UsdGeom.Tokens.vertex)
    color_primvar.Set(colors_vt)

    # Save the stage
    stage.GetRootLayer().Save()
    print(f'Successfully saved USD file: {output_path}')


def sanitize_prim_name(name):
    """Sanitize a string for use as a USD prim name.

    USD prim names must start with a letter or underscore and contain only alphanumeric characters
    and underscores.
    """
    # Replace invalid characters with underscores
    sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in name)
    # Ensure it starts with a letter or underscore
    if sanitized and sanitized[0].isdigit():
        sanitized = '_' + sanitized
    return sanitized or 'unnamed'


def add_points_to_stage(stage, parent_path, name, data, colors=None):
    """Add a point cloud prim to a USD stage.

    :param stage: The USD stage to add points to.
    :param parent_path: The parent prim path (e.g., '/World/RawPointCloud').
    :param name: Name for this point cloud prim.
    :param data: Nx3 numpy array of point positions.
    :param colors: Optional Nx3 numpy array of RGB colors (0-1 range).
    """
    if data.shape[0] == 0:
        return

    prim_name = sanitize_prim_name(name)
    prim_path = f'{parent_path}/{prim_name}'

    # Create a Points primitive
    points_prim = UsdGeom.Points.Define(stage, prim_path)

    # Convert numpy array to Vt array for USD
    points_vt = Vt.Vec3fArray(data.shape[0])
    for i in range(data.shape[0]):
        points_vt[i] = Gf.Vec3f(float(data[i, 0]), float(data[i, 1]), float(data[i, 2]))

    points_prim.GetPointsAttr().Set(points_vt)

    # Set point widths
    widths = Vt.FloatArray([0.01] * data.shape[0])
    points_prim.GetWidthsAttr().Set(widths)

    # Set display colors with vertex interpolation for per-point colors
    colors_vt = Vt.Vec3fArray(data.shape[0])
    if colors is not None:
        for i in range(data.shape[0]):
            colors_vt[i] = Gf.Vec3f(float(colors[i, 0]), float(colors[i, 1]), float(colors[i, 2]))
    else:
        # Generate colors based on height (Z coordinate)
        z_values = data[:, 2]
        z_min, z_max = z_values.min(), z_values.max()
        z_range = z_max - z_min if z_max != z_min else 1.0

        for i in range(data.shape[0]):
            t = (z_values[i] - z_min) / z_range
            colors_vt[i] = Gf.Vec3f(t, 0.2, 1.0 - t)

    # Use primvars API to set displayColor with vertex interpolation
    primvars_api = UsdGeom.PrimvarsAPI(points_prim)
    color_primvar = primvars_api.CreatePrimvar('displayColor', Sdf.ValueTypeNames.Color3fArray,
                                               UsdGeom.Tokens.vertex)
    color_primvar.Set(colors_vt)


def add_waypoint_disk_to_stage(stage, parent_path, position, radius=0.1, height=0.02):
    """Add a flat cylindrical disk representing a waypoint.

    :param stage: The USD stage to add the disk to.
    :param parent_path: The parent prim path (waypoint Xform).
    :param position: (x, y, z) position in the seed frame.
    :param radius: Radius of the disk in meters. Default is 0.1 (10cm).
    :param height: Height of the disk in meters. Default is 0.02 (2cm).
    """
    prim_path = f'{parent_path}/Disk'

    # Create a cylinder primitive
    cylinder = UsdGeom.Cylinder.Define(stage, prim_path)
    cylinder.GetRadiusAttr().Set(radius)
    cylinder.GetHeightAttr().Set(height)

    # Set the position via transform
    xformable = UsdGeom.Xformable(cylinder)
    xformable.AddTranslateOp().Set(
        Gf.Vec3d(float(position[0]), float(position[1]), float(position[2])))

    # Set a distinct color (green for waypoints)
    cylinder.GetDisplayColorAttr().Set([Gf.Vec3f(0.2, 0.8, 0.2)])


def add_edges_to_stage(stage, parent_path, graph, waypoints, anchorings):
    """Add edges as lines connecting waypoints.

    :param stage: The USD stage to add edges to.
    :param parent_path: The parent prim path.
    :param graph: The Graph proto containing edges.
    :param waypoints: dict of waypoint ID to waypoint.
    :param anchorings: dict of waypoint ID to anchoring.
    """
    # Collect all edge line segments
    points = []
    vertex_counts = []

    for edge in graph.edges:
        from_id = edge.id.from_waypoint
        to_id = edge.id.to_waypoint

        if from_id not in anchorings or to_id not in anchorings:
            continue

        # Get positions from anchorings
        from_pose = SE3Pose.from_proto(anchorings[from_id].seed_tform_waypoint)
        to_pose = SE3Pose.from_proto(anchorings[to_id].seed_tform_waypoint)

        points.append(Gf.Vec3f(float(from_pose.x), float(from_pose.y), float(from_pose.z)))
        points.append(Gf.Vec3f(float(to_pose.x), float(to_pose.y), float(to_pose.z)))
        vertex_counts.append(2)

    if not points:
        return

    # Create a BasisCurves primitive for the edges
    curves = UsdGeom.BasisCurves.Define(stage, f'{parent_path}/EdgeLines')
    curves.GetPointsAttr().Set(Vt.Vec3fArray(points))
    curves.GetCurveVertexCountsAttr().Set(Vt.IntArray(vertex_counts))
    curves.GetTypeAttr().Set(UsdGeom.Tokens.linear)

    # Set line width
    curves.GetWidthsAttr().Set(Vt.FloatArray([0.02] * len(points)))  # 2cm width

    # Set color (orange for edges)
    curves.GetDisplayColorAttr().Set([Gf.Vec3f(1.0, 0.6, 0.2)])


def write_usd_hierarchical(raw_clouds, colorized_clouds, output_path, up_axis='Z',
                           meters_per_unit=1.0, graph=None, waypoints=None, anchorings=None,
                           include_waypoints=True, include_edges=True):
    """Writes point clouds to a USD file with hierarchical structure.

    Creates a USD file with waypoints as parent objects, each containing their point clouds and an
    optional waypoint disk marker.

    :param raw_clouds: dict of waypoint_id -> (points Nx3, colors Nx3 or None)
    :param colorized_clouds: dict of waypoint_id -> (points Nx3, colors Nx3)
    :param output_path: Path to the output USD file.
    :param up_axis: The up axis for the scene ('Y' or 'Z'). Default is 'Z'.
    :param meters_per_unit: Scale factor for the scene. Default is 1.0 (meters).
    :param graph: Optional Graph proto for adding waypoints and edges.
    :param waypoints: Optional dict of waypoint ID to waypoint.
    :param anchorings: Optional dict of waypoint ID to anchoring.
    :param include_waypoints: Whether to include waypoint disks. Default is True.
    :param include_edges: Whether to include edge lines. Default is True.
    """
    total_raw = sum(pts.shape[0] for pts, _ in raw_clouds.values() if pts is not None)
    total_colorized = sum(pts.shape[0] for pts, _ in colorized_clouds.values() if pts is not None)

    print(f'Saving {total_raw} raw points and {total_colorized} colorized points to {output_path}')

    # Create a new USD stage
    stage = Usd.Stage.CreateNew(str(output_path))

    # Set up the stage metadata
    if up_axis.upper() == 'Y':
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    else:
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    UsdGeom.SetStageMetersPerUnit(stage, meters_per_unit)

    # Create the root xform
    root_xform = UsdGeom.Xform.Define(stage, '/World')
    stage.SetDefaultPrim(root_xform.GetPrim())

    # Create waypoints group
    UsdGeom.Xform.Define(stage, '/World/Waypoints')

    # Collect all waypoint IDs from both point cloud dicts
    all_waypoint_ids = set(raw_clouds.keys()) | set(colorized_clouds.keys())

    waypoint_count = 0
    for waypoint_id in all_waypoint_ids:
        prim_name = sanitize_prim_name(waypoint_id)
        waypoint_path = f'/World/Waypoints/{prim_name}'

        # Create the waypoint Xform
        UsdGeom.Xform.Define(stage, waypoint_path)

        # Add waypoint disk marker if enabled and we have anchoring for this waypoint
        if include_waypoints and anchorings and waypoint_id in anchorings:
            pose = SE3Pose.from_proto(anchorings[waypoint_id].seed_tform_waypoint)
            add_waypoint_disk_to_stage(stage, waypoint_path, (pose.x, pose.y, pose.z))
            waypoint_count += 1

        # Add localization point cloud (visual features) as child
        if waypoint_id in raw_clouds:
            points, colors = raw_clouds[waypoint_id]
            if points is not None and points.shape[0] > 0:
                add_points_to_stage(stage, waypoint_path, 'LocalizationPointCloud', points, colors)

        # Add raw point cloud (from depth cameras) as child
        if waypoint_id in colorized_clouds:
            points, colors = colorized_clouds[waypoint_id]
            if points is not None and points.shape[0] > 0:
                add_points_to_stage(stage, waypoint_path, 'RawPointCloud', points, colors)

    if include_waypoints and waypoint_count > 0:
        print(f'Added {waypoint_count} waypoint disks')

    # Add edge lines
    if include_edges and graph and anchorings:
        UsdGeom.Xform.Define(stage, '/World/Edges')
        add_edges_to_stage(stage, '/World/Edges', graph, waypoints, anchorings)
        print(f'Added {len(graph.edges)} edges')

    # Save the stage
    stage.GetRootLayer().Save()
    print(f'Successfully saved USD file: {output_path}')


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--path', type=Path, help='Path to the graph nav map directory.',
                        required=True)
    parser.add_argument('--output', type=Path, help='Output USD file path.', required=True)
    parser.add_argument('--up-axis', type=str, default='Z', choices=['Y', 'Z'],
                        help='Up axis for the USD scene (default: Z).')
    parser.add_argument('--meters-per-unit', type=float, default=1.0,
                        help='Meters per unit for the USD scene (default: 1.0).')
    parser.add_argument('--colorized', action='store_true',
                        help='Export colorized point clouds from stereo depth/visual image pairs.')
    parser.add_argument(
        '--flat', action='store_true',
        help='Export as a single flat point cloud instead of per-snapshot hierarchy.')
    parser.add_argument(
        '--max-depth', type=float, default=3.0,
        help='Maximum depth from camera in meters for colorized point cloud '
        '(default: 3.0).')
    parser.add_argument(
        '--voxel-size', type=float, default=0,
        help='Voxel size in meters for downsampling colorized point cloud. '
        'Default is 0 (no downsampling, full resolution). '
        'Set to e.g. 0.01 for 1cm voxels.')
    parser.add_argument('--exclude-waypoints', action='store_true',
                        help='Exclude waypoint disks from the output.')
    parser.add_argument('--exclude-edges', action='store_true',
                        help='Exclude edge lines from the output.')

    options = parser.parse_args()

    # Validate output path
    if options.output.suffix not in ('.usd', '.usda', '.usdc'):
        if options.output.suffix:
            # User specified a wrong extension
            print(
                "Warning: Output file should have .usd, .usda (ASCII), or .usdc (binary) extension."
            )
            print("Adding .usdc extension.")
        options.output = options.output.with_suffix(options.output.suffix + '.usdc')

    # Load the map from the given directory
    (current_graph, current_waypoints, current_waypoint_snapshots, current_edge_snapshots,
     current_anchors, current_anchored_world_objects) = load_map(options.path)

    if len(current_anchors) == 0:
        print("Error: Map has no anchoring data. Run anchoring optimization first.")
        sys.exit(1)

    # Collect point cloud data per waypoint
    raw_clouds = {}  # waypoint_id -> (points, colors)
    colorized_clouds = {}  # waypoint_id -> (points, colors)
    waypoints_processed = 0

    for wp in current_graph.waypoints:
        waypoint_id = wp.id

        # Extract raw feature point cloud (localization)
        try:
            raw_data = get_point_cloud_data_in_seed_frame(current_waypoints,
                                                          current_waypoint_snapshots,
                                                          current_anchors, waypoint_id)
            # Apply voxel downsampling if specified
            if options.voxel_size > 0:
                # Generate height-based colors before downsampling
                z_values = raw_data[:, 2]
                z_min, z_max = z_values.min(), z_values.max()
                z_range = z_max - z_min if z_max != z_min else 1.0
                t = (z_values - z_min) / z_range
                raw_colors = np.column_stack([t, np.full_like(t, 0.2), 1.0 - t])
                raw_data, raw_colors = voxel_downsample(raw_data, raw_colors,
                                                        voxel_size=options.voxel_size)
                raw_clouds[waypoint_id] = (raw_data, raw_colors)
            else:
                raw_clouds[waypoint_id] = (raw_data, None)
        except Exception as e:
            print(f"Warning: Could not process raw point cloud for {waypoint_id}: {e}")

        # Extract colorized point cloud from stereo pairs
        try:
            colorized_data, colorized_colors = get_colorized_point_cloud_from_stereo(
                current_waypoints, current_waypoint_snapshots, current_anchors, waypoint_id,
                max_depth=options.max_depth, voxel_size=options.voxel_size)
            if colorized_data.shape[0] > 0:
                colorized_clouds[waypoint_id] = (colorized_data, colorized_colors)
        except Exception as e:
            print(f"Warning: Could not process colorized point cloud for {waypoint_id}: {e}")

        if waypoint_id in raw_clouds or waypoint_id in colorized_clouds:
            waypoints_processed += 1

    if not raw_clouds and not colorized_clouds:
        print("Error: No point cloud data found in the map.")
        sys.exit(1)

    total_raw = sum(pts.shape[0] for pts, _ in raw_clouds.values())
    total_colorized = sum(pts.shape[0] for pts, _ in colorized_clouds.values())
    print(f'Processed {waypoints_processed} waypoints: '
          f'{total_raw} raw points, {total_colorized} colorized points')

    # Export to USD
    if options.flat:
        # Flatten into single point clouds (legacy behavior)
        if options.colorized:
            data = np.concatenate([pts for pts, _ in colorized_clouds.values()])
            colors = np.concatenate([clr for _, clr in colorized_clouds.values()])
        else:
            data = np.concatenate([pts for pts, _ in raw_clouds.values()])
            colors = None

        write_usd(data, options.output, options.up_axis, options.meters_per_unit, colors=colors)
    else:
        # Hierarchical structure with per-snapshot point clouds
        write_usd_hierarchical(raw_clouds, colorized_clouds, options.output, options.up_axis,
                               options.meters_per_unit, graph=current_graph,
                               waypoints=current_waypoints, anchorings=current_anchors,
                               include_waypoints=not options.exclude_waypoints,
                               include_edges=not options.exclude_edges)


if __name__ == '__main__':
    main()
