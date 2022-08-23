# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import math
import os
import sys
import threading
import time

import google.protobuf.timestamp_pb2
import numpy as np
import numpy.linalg
import vtk
from visualization_utils import (add_numpy_to_vtk_object, get_default_color_map,
                                 get_vtk_cube_source, get_vtk_polydata_from_numpy,
                                 make_spot_vtk_hexahedron, se3pose_proto_to_vtk_tf)
from vtk.util import numpy_support

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import geometry_pb2, local_grid_pb2, world_object_pb2
from bosdyn.client.frame_helpers import *
from bosdyn.client.image import ImageClient, depth_image_to_pointcloud
from bosdyn.client.local_grid import LocalGridClient
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.world_object import WorldObjectClient
from bosdyn.util import timestamp_to_nsec


class WorldObjectTimedCallbackEvent(object):
    """VTK Callback event for world objects."""

    def __init__(self, client):
        self.client = client
        self.current_other_world_obj_actors = []
        self.current_fiducial_actor_and_text = []
        self.init_world_object_actor()

    def get_actors(self):
        """Return all VTK actors associated with the set of world objects."""
        actors_list = []
        for fid, txt in self.current_fiducial_actor_and_text:
            actors_list.append(fid)
            actors_list.append(txt)
        for w_obj in self.current_other_world_obj_actors:
            actors_list.append(w_obj)
        return actors_list

    def init_text_actor(self, txt, pt):
        """Initialize a text VTK actor to display fiducial ids."""
        actor = vtk.vtkTextActor()
        actor.SetInput(txt)
        prop = actor.GetTextProperty()
        prop.SetBackgroundColor(1.0, 0.0, 0.0)
        prop.SetBackgroundOpacity(0.65)
        prop.SetFontSize(18)
        coord = actor.GetPositionCoordinate()
        coord.SetCoordinateSystemToWorld()
        coord.SetValue((pt[0], pt[1], pt[2]))
        return actor

    def init_fiducial_actor(self, fiducial_obj):
        """Initialize a plane VTK actor to display the fiducials."""
        plane_source = vtk.vtkPlaneSource()
        plane_source.SetCenter(0.0, 0.0, 0.0)
        plane_source.SetNormal(0.0, 0.0, 1.0)
        plane_source.Update()
        plane = plane_source.GetOutput()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(plane)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1.0, 0.0, 0.0)
        actor.SetScale(fiducial_obj.apriltag_properties.dimensions.x,
                       fiducial_obj.apriltag_properties.dimensions.y, 1.0)
        return actor

    def init_object_actor(self, world_object):
        """Initialize a sphere VTK actor to display world objects (not fiducials)."""
        if world_object.HasField("apriltag_properties"):
            # Use show_fiducial function for apriltags to get a more representative visualization.
            return
        sphere_source = vtk.vtkSphereSource()
        sphere_source.SetCenter(0.0, 0.0, 0.0)
        sphere_source.SetRadius(0.5)
        sphere_source.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(sphere_source.GetOutput())

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(0.0, 0.3, 1.0)
        return actor

    def create_fiducial_and_text_actors(self, objs):
        """Helper function to create a fiducial actor and a text actor for a given apriltag."""
        fiducial_actor = self.init_fiducial_actor(objs)
        vision_tform_fiducial_proto = get_a_tform_b(
            objs.transforms_snapshot, VISION_FRAME_NAME,
            objs.apriltag_properties.frame_name_fiducial).to_proto()
        vision_tform_fiducial = se3pose_proto_to_vtk_tf(vision_tform_fiducial_proto)
        fiducial_actor.SetUserTransform(vision_tform_fiducial)
        text_position = (vision_tform_fiducial_proto.position.x,
                         vision_tform_fiducial_proto.position.y,
                         vision_tform_fiducial_proto.position.z)
        text_actor = self.init_text_actor(str(objs.apriltag_properties.tag_id), text_position)
        return (fiducial_actor, text_actor)

    def init_world_object_actor(self):
        """Initialize VTK actor objects for the current world objects."""
        world_objects = self.client.list_world_objects(
            object_type=[world_object_pb2.WORLD_OBJECT_APRILTAG]).world_objects
        for objs in world_objects:
            if len(objs.transforms_snapshot.child_to_parent_edge_map) < 1:
                # Must have vision_tform_object frame to visualize the object.
                continue
            if objs.HasField("apriltag_properties"):
                fid_and_text = self.create_fiducial_and_text_actors(objs)
                self.current_fiducial_actor_and_text.append(fid_and_text)
            else:
                # This means the object is a set of image coordinates. It must include a transform
                # from vision_tform_object for the object located at the image coordinates.
                frame_name_image_coord_obj = objs.image_properties.frame_name_image_coordinates
                world_obj_actor = self.init_object_actor(objs)
                vision_tform_object_proto = get_a_tform_b(objs.transforms_snapshot,
                                                          VISION_FRAME_NAME,
                                                          frame_name_image_coord_obj).to_proto()
                vision_tform_object = se3pose_proto_to_vtk_tf(vision_tform_object_proto)
                world_obj_actor.SetUserTransform(vision_tform_object)
                self.current_other_world_obj_actors.append(world_obj_actor)
        all_new_actors = self.get_actors()
        return all_new_actors

    def update_world_object_actor(self, renwin, event):
        """Request the most recent world objects and update the VTK renderer."""
        world_objects = self.client.list_world_objects(
            object_type=[world_object_pb2.WORLD_OBJECT_APRILTAG]).world_objects
        # Track how many fiducial VTK actors we have updated.
        added_fiducials_count = 0
        # Track how many other world object VTK actors we have updated.
        added_wo_count = 0
        # Store any entirely new VTK actors.
        new_actors_added = []
        # Iterate through the new set of world objects. If we have existing VTK actors already created, then
        # update that VTK actor's information. Otherwise, create a new VTK actor for the object.
        for objs in world_objects:
            if objs.HasField("apriltag_properties"):
                if added_fiducials_count < len(self.current_fiducial_actor_and_text):
                    # Update an existing fiducial VTK actor.
                    fiducial_actor, text_actor = self.current_fiducial_actor_and_text[
                        added_fiducials_count]
                    vision_tform_fiducial_proto = get_a_tform_b(
                        objs.transforms_snapshot, VISION_FRAME_NAME,
                        objs.apriltag_properties.frame_name_fiducial).to_proto()
                    vision_tform_fiducial = se3pose_proto_to_vtk_tf(vision_tform_fiducial_proto)
                    fiducial_actor.SetUserTransform(vision_tform_fiducial)
                    text_actor.SetInput(str(objs.apriltag_properties.tag_id))
                    text_actor.GetPositionCoordinate().SetValue(
                        (vision_tform_fiducial_proto.position.x,
                         vision_tform_fiducial_proto.position.y,
                         vision_tform_fiducial_proto.position.z))
                    added_fiducials_count += 1
                else:
                    # More than the existing amount. Add new actors.
                    fid_and_text = self.create_fiducial_and_text_actors(objs)
                    self.current_fiducial_actor_and_text.append(fid_and_text)
                    new_actors_added.extend([fid_and_text[0], fid_and_text[1]])
            else:
                # This means the object is a set of image coordinates. It must include a transform
                # from vision_tform_object for the object located at the image coordinates.
                frame_name_image_coord_obj = objs.image_properties.frame_name_image_coordinates
                if added_wo_count < len(self.current_other_world_obj_actors):
                    # Update an existing world object VTK actor.
                    world_obj_actor = self.current_other_world_obj_actors[added_wo_count]
                    vision_tform_object_proto = get_a_tform_b(
                        objs.transforms_snapshot, VISION_FRAME_NAME,
                        frame_name_image_coord_obj).to_proto()
                    vision_tform_object = se3pose_proto_to_vtk_tf(vision_tform_object_proto)
                    world_obj_actor.SetUserTransform(vision_tform_object)
                    added_wo_count += 1
                else:
                    # More than the existing amount. Add new actors.
                    world_obj_actor = self.init_object_actor(objs)
                    vision_tform_object_proto = get_a_tform_b(
                        objs.transforms_snapshot, VISION_FRAME_NAME,
                        frame_name_image_coord_obj).to_proto()
                    vision_tform_object = se3pose_proto_to_vtk_tf(vision_tform_object_proto)
                    world_obj_actor.SetUserTransform(vision_tform_object)
                    self.current_other_world_obj_actors.append(world_obj_actor)
                    new_actors_added.append(world_obj_actor)

        # If we updated less fiducial VTK actors, then remove the remaining VTK actor objects so that
        # we are not rendering old fiducial information.
        if added_fiducials_count < len(self.current_fiducial_actor_and_text):
            renderer = renwin.GetRenderWindow().GetRenderers().GetFirstRenderer()
            for i in range(added_fiducials_count + 1, len(self.current_fiducial_actor_and_text)):
                # Remove these actors from the renderer
                fid, txt = self.current_fiducial_actor_and_text[i]
                renderer.RemoveActor(fid)
                renderer.RemoveActor(txt)
            renderer.ResetCamera()
        # If we updated less world object VTK actors, then remove the remaining VTK actor objects
        # so that we are not rendering old information.
        if added_wo_count < len(self.current_other_world_obj_actors):
            renderer = renwin.GetRenderWindow().GetRenderers().GetFirstRenderer()
            for i in range(added_wo_count + 1, len(self.current_other_world_obj_actors)):
                # Remove these actors from the renderer
                objs = self.current_other_world_obj_actors[i]
                renderer.RemoveActor(objs)
            renderer.ResetCamera()

        # If we added any new VTK actors, then add them to the renderer.
        if len(new_actors_added) > 0:
            renderer = renwin.GetRenderWindow().GetRenderers().GetFirstRenderer()
            for actor in new_actors_added:
                renderer.AddActor(actor)
            renderer.ResetCamera()
        renwin.Render()
        renwin.GetRenderWindow().Render()


class RobotStateTimedCallbackEvent(object):
    """VTK Callback event for robot state."""

    def __init__(self, client):
        self.client = client
        self.robot_state = None
        self.state_actor = self.init_state_actor()

    def get_actor(self):
        """Get the VTK actor for the robot state."""
        return self.state_actor

    def init_state_actor(self):
        """Initialize VTK actor objects for the current robot state."""
        body_source = make_spot_vtk_hexahedron()
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(body_source)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1.0, 1.0, 0.0)  # yellow
        return actor

    def update_state_actor(self, renwin, event):
        """Request the most recent robot state and update the VTK renderer."""
        self.robot_state = self.client.get_robot_state()
        # Update the transform for the robot state actor in world frame.
        vision_tform_body_proto = get_vision_tform_body(
            self.robot_state.kinematic_state.transforms_snapshot).to_proto()
        vision_tform_body = se3pose_proto_to_vtk_tf(vision_tform_body_proto)
        self.state_actor.SetUserTransform(vision_tform_body)
        renwin.Render()
        renwin.GetRenderWindow().Render()


class ImageServiceTimedCallbackEvent(object):
    """VTK Callback event for Images."""

    def __init__(self, client, image_sources):
        self.client = client
        self.image_sources = image_sources
        self.point_cloud_data = vtk.vtkPolyData()
        self.image_actor = self.init_image_actor()

    def get_actor(self):
        """Get the VTK actor for the robot state."""
        return self.image_actor

    def init_image_actor(self):
        """Initialize VTK actor objects for the current image."""
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.point_cloud_data)
        mapper.SetScalarVisibility(1)
        mapper.SetColorModeToDefault()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        return actor

    def update_image_actor(self, renwin, event):
        """Request the most recent image and update the VTK renderer."""
        image_responses = self.client.get_image_from_sources(self.image_sources)

        # Create storage for the point cloud.
        vtkPoints = vtk.vtkPoints()
        vtkCells = vtk.vtkCellArray()
        vtkDepth = vtk.vtkDoubleArray()
        vtkDepth.SetName('DepthArray')
        self.point_cloud_data.SetPoints(vtkPoints)
        self.point_cloud_data.SetVerts(vtkCells)
        self.point_cloud_data.GetPointData().SetScalars(vtkDepth)
        self.point_cloud_data.GetPointData().SetActiveScalars('DepthArray')

        # We requested a single image (hand depth) in the get_image_from_sources call, the first response returned is the result.
        image = image_responses[0]
        pts_in_sensor = depth_image_to_pointcloud(image)

        for pt in pts_in_sensor:
            pointId = vtkPoints.InsertNextPoint(pt[:])
            vtkDepth.InsertNextValue(pt[2])
            vtkCells.InsertNextCell(1)
            vtkCells.InsertCellPoint(pointId)

        # Use the transforms snapshot to get the vision_T_sensor transform to draw the points in the correct reference frame.
        vision_tform_sensor_proto = get_a_tform_b(image.shot.transforms_snapshot, VISION_FRAME_NAME,
                                                  image.shot.frame_name_image_sensor).to_proto()
        vision_tform_sensor = se3pose_proto_to_vtk_tf(vision_tform_sensor_proto)
        self.image_actor.SetUserTransform(vision_tform_sensor)

        renwin.Render()
        renwin.GetRenderWindow().Render()


def expand_data_by_rle_count(local_grid_proto, data_type=np.int16):
    """Expand local grid data to full bytes data using the RLE count."""
    cells_pz = np.frombuffer(local_grid_proto.local_grid.data, dtype=data_type)
    cells_pz_full = []
    # For each value of rle_counts, we expand the cell data at the matching index
    # to have that many repeated, consecutive values.
    for i in range(0, len(local_grid_proto.local_grid.rle_counts)):
        for j in range(0, local_grid_proto.local_grid.rle_counts[i]):
            cells_pz_full.append(cells_pz[i])
    return np.array(cells_pz_full)


def get_terrain_grid(local_grid_proto):
    """Generate a 3xN set of points representing the terrain local grid."""
    cells_pz_full = unpack_grid(local_grid_proto).astype(np.float32)
    # Populate the x,y values with a complete combination of all possible pairs for the dimensions in the grid extent.
    ys, xs = np.mgrid[0:local_grid_proto.local_grid.extent.num_cells_x,
                      0:local_grid_proto.local_grid.extent.num_cells_y]
    # Numpy vstack makes it so that each column is (x,y,z) for a single terrain point. The height values (z) come from the
    # terrain grid's data field.
    pts = np.vstack(
        [np.ravel(xs).astype(np.float32),
         np.ravel(ys).astype(np.float32), cells_pz_full]).T
    pts[:, [0, 1]] *= (local_grid_proto.local_grid.extent.cell_size,
                       local_grid_proto.local_grid.extent.cell_size)
    return pts


def create_vtk_no_step_grid(proto, robot_state_client):
    """Generate VTK polydata for the no step grid from the local grid response."""
    for local_grid_found in proto:
        if local_grid_found.local_grid_type_name == "no_step":
            local_grid_proto = local_grid_found
            cell_size = local_grid_found.local_grid.extent.cell_size
    # Unpack the data field for the local grid.
    cells_no_step = unpack_grid(local_grid_proto).astype(np.float32)
    # Populate the x,y values with a complete combination of all possible pairs for the dimensions in the grid extent.
    ys, xs = np.mgrid[0:local_grid_proto.local_grid.extent.num_cells_x,
                      0:local_grid_proto.local_grid.extent.num_cells_y]
    # Get the estimated height (z value) of the ground in the vision frame as if the robot was standing.
    transforms_snapshot = local_grid_proto.local_grid.transforms_snapshot
    vision_tform_body = get_a_tform_b(transforms_snapshot, VISION_FRAME_NAME, BODY_FRAME_NAME)
    z_ground_in_vision_frame = compute_ground_height_in_vision_frame(robot_state_client)
    # Numpy vstack makes it so that each column is (x,y,z) for a single no step grid point. The height values come
    # from the estimated height of the ground plane.
    cell_count = local_grid_proto.local_grid.extent.num_cells_x * local_grid_proto.local_grid.extent.num_cells_y
    cells_est_height = np.ones(cell_count) * z_ground_in_vision_frame
    pts = np.vstack(
        [np.ravel(xs).astype(np.float32),
         np.ravel(ys).astype(np.float32), cells_est_height]).T
    pts[:, [0, 1]] *= (local_grid_proto.local_grid.extent.cell_size,
                       local_grid_proto.local_grid.extent.cell_size)
    # Determine the coloration based on whether or not the region is steppable. The regions that Spot considers it
    # cannot safely step are colored red, and the regions that are considered safe to step are colored blue.
    color = np.zeros([cell_count, 3], dtype=np.uint8)
    color[:, 0] = (cells_no_step <= 0.0)
    color[:, 2] = (cells_no_step > 0.0)
    color *= 255
    # Offset the grid points to be in the vision frame instead of the local grid frame.
    vision_tform_local_grid = get_a_tform_b(transforms_snapshot, VISION_FRAME_NAME,
                                            local_grid_proto.local_grid.frame_name_local_grid_data)
    pts = offset_grid_pixels(pts, vision_tform_local_grid, cell_size)
    # Create the VTK actors for the local grid.
    polydata = get_vtk_polydata_from_numpy(pts)
    add_numpy_to_vtk_object(data_object=polydata, numpy_array=color, array_name='RGBA')
    return polydata


def create_vtk_obstacle_grid(proto, robot_state_client):
    """Generate VTK polydata for the obstacle distance grid from the local grid response."""
    for local_grid_found in proto:
        if local_grid_found.local_grid_type_name == "obstacle_distance":
            local_grid_proto = local_grid_found
            cell_size = local_grid_found.local_grid.extent.cell_size
    # Unpack the data field for the local grid.
    cells_obstacle_dist = unpack_grid(local_grid_proto).astype(np.float32)
    # Populate the x,y values with a complete combination of all possible pairs for the dimensions in the grid extent.
    ys, xs = np.mgrid[0:local_grid_proto.local_grid.extent.num_cells_x,
                      0:local_grid_proto.local_grid.extent.num_cells_y]

    # Get the estimated height (z value) of the ground in the vision frame.
    transforms_snapshot = local_grid_proto.local_grid.transforms_snapshot
    vision_tform_body = get_a_tform_b(transforms_snapshot, VISION_FRAME_NAME, BODY_FRAME_NAME)
    z_ground_in_vision_frame = compute_ground_height_in_vision_frame(robot_state_client)
    # Numpy vstack makes it so that each column is (x,y,z) for a single no step grid point. The height values come
    # from the estimated height of the ground plane as if the robot was standing.
    cell_count = local_grid_proto.local_grid.extent.num_cells_x * local_grid_proto.local_grid.extent.num_cells_y
    z = np.ones(cell_count, dtype=np.float32)
    z *= z_ground_in_vision_frame
    pts = np.vstack([np.ravel(xs).astype(np.float32), np.ravel(ys).astype(np.float32), z]).T
    pts[:, [0, 1]] *= (local_grid_proto.local_grid.extent.cell_size,
                       local_grid_proto.local_grid.extent.cell_size)
    # Determine the coloration of the obstacle grid. Set the inside of the obstacle as a red hue, the outside of the obstacle
    # as a blue hue, and the border of an obstacle as a green hue. Note that the inside of an obstacle is determined by a
    # negative distance value in a grid cell, and the outside of an obstacle is determined by a positive distance value in a
    # grid cell. The border of an obstacle is considered a distance of [0,.33] meters for a grid cell value.
    color = np.ones([cell_count, 3], dtype=np.uint8)
    color[:, 0] = (cells_obstacle_dist <= 0.0)
    color[:, 1] = np.logical_and(0.0 < cells_obstacle_dist, cells_obstacle_dist < 0.33)
    color[:, 2] = (cells_obstacle_dist >= 0.33)
    color *= 255
    # Offset the grid points to be in the vision frame instead of the local grid frame.
    vision_tform_local_grid = get_a_tform_b(transforms_snapshot, VISION_FRAME_NAME,
                                            local_grid_proto.local_grid.frame_name_local_grid_data)
    pts = offset_grid_pixels(pts, vision_tform_local_grid, cell_size)
    # Create the VTK actors for the local grid.
    polydata = get_vtk_polydata_from_numpy(pts)
    add_numpy_to_vtk_object(data_object=polydata, numpy_array=color, array_name='RGBA')
    return polydata


def get_valid_pts(local_grid_proto):
    """Generate a 1xN set of binary indicators whether terrain height grid data point is valid."""
    cell_flags = unpack_grid(local_grid_proto)
    return cell_flags


def get_intensity_grid(local_grid_proto):
    """Generate a 3xN set of color intensities for the local grid points."""
    intensity = unpack_grid(local_grid_proto)
    # Repeat the same intensity for the (x,y,z) coordinates of an individual cell of the local grid.
    cell_count = local_grid_proto.local_grid.extent.num_cells_x * local_grid_proto.local_grid.extent.num_cells_y
    cells_color = np.zeros([cell_count, 4], dtype=np.uint8)
    cells_color[:, :3] = np.repeat(intensity, 3).reshape(-1, 3)
    return cells_color


def create_vtk_full_terrain_grid(proto):
    """Generate VTK polydata for the terrain (height) grid from the local grid response."""
    # Parse each local grid response to create numpy arrays for each.
    for local_grid_found in proto:
        if local_grid_found.local_grid_type_name == "terrain":
            vision_tform_local_grid = get_a_tform_b(
                local_grid_found.local_grid.transforms_snapshot, VISION_FRAME_NAME,
                local_grid_found.local_grid.frame_name_local_grid_data).to_proto()
            cell_size = local_grid_found.local_grid.extent.cell_size
            terrain_pts = get_terrain_grid(local_grid_found)
        if local_grid_found.local_grid_type_name == "terrain_valid":
            valid_inds = get_valid_pts(local_grid_found)
        if local_grid_found.local_grid_type_name == "intensity":
            color = get_intensity_grid(local_grid_found)

    # Possibly mask invalid cells (filtering the terrain points by validity).
    color[valid_inds != 0, 3] = 255
    # Offset the local grid's pixels to be in the world frame instead of the local grid frame.
    terrain_pts = offset_grid_pixels(terrain_pts, vision_tform_local_grid, cell_size)
    # Create the VTK actors for the local grid.
    polydata = get_vtk_polydata_from_numpy(terrain_pts)
    add_numpy_to_vtk_object(data_object=polydata, numpy_array=color, array_name='RGBA')
    return polydata


def offset_grid_pixels(pts, vision_tform_local_grid, cell_size):
    """Offset the local grid's pixels to be in the world frame instead of the local grid frame."""
    x_base = vision_tform_local_grid.position.x + cell_size * 0.5
    y_base = vision_tform_local_grid.position.y + cell_size * 0.5
    pts[:, 0] += x_base
    pts[:, 1] += y_base
    return pts


def unpack_grid(local_grid_proto):
    """Unpack the local grid proto."""
    # Determine the data type for the bytes data.
    data_type = get_numpy_data_type(local_grid_proto.local_grid)
    if data_type is None:
        print("Cannot determine the dataformat for the local grid.")
        return None
    # Decode the local grid.
    if local_grid_proto.local_grid.encoding == local_grid_pb2.LocalGrid.ENCODING_RAW:
        full_grid = np.frombuffer(local_grid_proto.local_grid.data, dtype=data_type)
    elif local_grid_proto.local_grid.encoding == local_grid_pb2.LocalGrid.ENCODING_RLE:
        full_grid = expand_data_by_rle_count(local_grid_proto, data_type=data_type)
    else:
        # Return nothing if there is no encoding type set.
        return None
    # Apply the offset and scaling to the local grid.
    if local_grid_proto.local_grid.cell_value_scale == 0:
        return full_grid
    full_grid_float = full_grid.astype(np.float64)
    full_grid_float *= local_grid_proto.local_grid.cell_value_scale
    full_grid_float += local_grid_proto.local_grid.cell_value_offset
    return full_grid_float


def get_numpy_data_type(local_grid_proto):
    """Convert the cell format of the local grid proto to a numpy data type."""
    if local_grid_proto.cell_format == local_grid_pb2.LocalGrid.CELL_FORMAT_UINT16:
        return np.uint16
    elif local_grid_proto.cell_format == local_grid_pb2.LocalGrid.CELL_FORMAT_INT16:
        return np.int16
    elif local_grid_proto.cell_format == local_grid_pb2.LocalGrid.CELL_FORMAT_UINT8:
        return np.uint8
    elif local_grid_proto.cell_format == local_grid_pb2.LocalGrid.CELL_FORMAT_INT8:
        return np.int8
    elif local_grid_proto.cell_format == local_grid_pb2.LocalGrid.CELL_FORMAT_FLOAT64:
        return np.float64
    elif local_grid_proto.cell_format == local_grid_pb2.LocalGrid.CELL_FORMAT_FLOAT32:
        return np.float32
    else:
        return None


def get_vtk_from_local_grid_proto(proto, robot_state_client):
    """Generate VTK polydata for all different grid types from the local grid proto."""
    # Generate the obstacle distance grid
    obstacle_distance = create_vtk_obstacle_grid(proto, robot_state_client)
    # Generate the no step grid
    no_step = create_vtk_no_step_grid(proto, robot_state_client)
    # Generate the terrain grid
    terrain = create_vtk_full_terrain_grid(proto)
    return obstacle_distance, no_step, terrain


def compute_ground_height_in_vision_frame(robot_state_client):
    """Get the z-height of the ground plane in vision frame from the current robot state."""
    robot_state = robot_state_client.get_robot_state()
    vision_tform_ground_plane = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot,
                                              VISION_FRAME_NAME, GROUND_PLANE_FRAME_NAME)
    return vision_tform_ground_plane.position.z


class LocalGridTimedCallbackEvent(object):
    """VTK Callback event for local grids."""

    def __init__(self, local_grid_client, robot_state_client, local_grid_types):
        self.local_grid_client = local_grid_client
        self.robot_state_client = robot_state_client
        self.local_grid_types = local_grid_types
        self.robot_state = None
        self.terrain_grid_actor = None
        self.obstacle_grid_actor = None
        self.no_step_grid_actor = None
        # Initialize VTK actors for the primary local grid sources.
        self.init_local_grid_actors()
        if 'no-step' in self.local_grid_types:
            self.no_step_polydata = self.no_step_grid_actor.GetMapper().GetInput()
        if 'obstacle-distance' in self.local_grid_types:
            self.obstacle_polydata = self.obstacle_grid_actor.GetMapper().GetInput()
        if 'terrain' in self.local_grid_types:
            self.terrain_polydata = self.terrain_grid_actor.GetMapper().GetInput()

    def get_actors(self):
        """Return the VTK actor for the local grids."""
        grid_actors = []
        if 'no-step' in self.local_grid_types:
            grid_actors.append(self.no_step_grid_actor)
        if 'obstacle-distance' in self.local_grid_types:
            grid_actors.append(self.obstacle_grid_actor)
        if 'terrain' in self.local_grid_types:
            grid_actors.append(self.terrain_grid_actor)
        return grid_actors

    def update_local_grid_actors(self, renwin, event):
        """Request the most recent local grid and update the VTK renderer."""
        proto = self.local_grid_client.get_local_grids(
            ['terrain', 'terrain_valid', 'intensity', 'no_step', 'obstacle_distance'])
        # Generate the polydata for each local grid source.
        obstacle_distance, no_step, terrain = get_vtk_from_local_grid_proto(
            proto, self.robot_state_client)
        # Update the polydata with the newest local grid data and re-render the windows.
        if 'no-step' in self.local_grid_types:
            self.update_polydata_points(self.no_step_polydata, no_step)
        if 'obstacle-distance' in self.local_grid_types:
            self.update_polydata_points(self.obstacle_polydata, obstacle_distance)
        if 'terrain' in self.local_grid_types:
            self.update_polydata_points(self.terrain_polydata, terrain)
        renwin.Render()
        renwin.GetRenderWindow().Render()

    def update_polydata_points(self, old_polydata, new_polydata):
        """Update the polydata of the existing VTK actor with the new local grid data."""
        old_polydata_pts = old_polydata.GetPoints()
        # Update the polydata with the new terrain points and intensities.
        for i in range(0, new_polydata.GetNumberOfPoints()):
            new_point = new_polydata.GetPoint(i)
            if i < old_polydata.GetNumberOfPoints():
                old_polydata_pts.SetPoint(i, new_point)
            else:
                old_polydata_pts.InsertNextPoint(new_point)
        old_polydata.Modified()

    def init_local_grid_actors(self):
        """Initialize VTK actor objects for the current local grids."""
        # Request the different local grids to create a local grid.
        proto = self.local_grid_client.get_local_grids(
            ['terrain', 'terrain_valid', 'intensity', 'no_step', 'obstacle_distance'])
        # Generate the polydata for each local grid source.
        obstacle_distance, no_step, terrain = get_vtk_from_local_grid_proto(
            proto, self.robot_state_client)
        # Create a VTK actor for the local grid.
        for local_grid in proto:
            if local_grid.local_grid_type_name == "terrain" and 'terrain' in self.local_grid_types:
                terrain_cell_size = local_grid.local_grid.extent.cell_size
                self.terrain_grid_actor = self.create_local_grid_actor(terrain_cell_size, terrain)
            if local_grid.local_grid_type_name == "no_step" and 'no-step' in self.local_grid_types:
                no_step_cell_size = local_grid.local_grid.extent.cell_size
                self.no_step_grid_actor = self.create_local_grid_actor(no_step_cell_size, no_step)
            if local_grid.local_grid_type_name == "obstacle_distance" and 'obstacle-distance' in self.local_grid_types:
                obstacle_distance_cell_size = local_grid.local_grid.extent.cell_size
                self.obstacle_grid_actor = self.create_local_grid_actor(
                    obstacle_distance_cell_size, obstacle_distance)

    def create_local_grid_actor(self, cell_size, polydata):
        """Create a default voxel map VTK actor with a local grid polydata and cell dimensions."""
        array_name = polydata.GetPointData().GetArrayName(0)
        polydata.GetPointData().SetActiveScalars(array_name)
        colors = get_default_color_map()

        cube_source = get_vtk_cube_source(cell_size)
        mapper = vtk.vtkGlyph3DMapper()
        mapper.SetSourceConnection(cube_source.GetOutputPort())
        mapper.SetScaleModeToNoDataScaling()
        mapper.SetInputData(polydata)

        mapper.ScalarVisibilityOn()
        mapper.SetUseLookupTableScalarRange(True)
        mapper.SetLookupTable(colors)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.SetUserTransform(vtk.vtkTransform())
        return actor


def main(argv):
    """Main rendering loop for the API streaming visualizer."""
    # Setup the robot.
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('--local-grid', choices=['no-step', 'obstacle-distance', 'terrain'],
                        help='Which local grid to visualize', default=['terrain'], action='append')
    parser.add_argument('--show-hand-depth',
                        help='Draw the hand depth data as a point cloud (requires SpotArm)',
                        action='store_true')
    options = parser.parse_args(argv)
    sdk = bosdyn.client.create_standard_sdk('SpotViz')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    # Set up the clients for getting Spot's perception scene.
    local_grid_client = robot.ensure_client(LocalGridClient.default_service_name)
    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    world_object_client = robot.ensure_client(WorldObjectClient.default_service_name)
    image_service_client = robot.ensure_client(ImageClient.default_service_name)

    # Create the renderer and camera.
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.05, 0.1, 0.15)
    camera = renderer.GetActiveCamera()
    camera.SetViewUp(0, 0, 1)
    camera.SetPosition(0, 0, 5)

    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetWindowName("API Visualizer")
    renderWindow.SetSize(1280, 720)

    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)
    renderWindowInteractor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

    # Setup the time-based event callbacks for each vtk actor to be visualized.
    robot_state_timer = RobotStateTimedCallbackEvent(robot_state_client)
    robot_state_actor = robot_state_timer.get_actor()
    renderer.AddActor(robot_state_actor)

    local_grid_timer = LocalGridTimedCallbackEvent(local_grid_client, robot_state_client,
                                                   options.local_grid)
    grid_actors = local_grid_timer.get_actors()
    for actor in grid_actors:
        renderer.AddActor(actor)

    world_object_timer = WorldObjectTimedCallbackEvent(world_object_client)
    world_object_actors = world_object_timer.get_actors()
    for actor in world_object_actors:
        renderer.AddActor(actor)

    if robot.has_arm() and options.show_hand_depth:
        image_service_timer = ImageServiceTimedCallbackEvent(image_service_client, ["hand_depth"])
        image_service_actor = image_service_timer.get_actor()
        renderer.AddActor(image_service_actor)

    renderWindow.AddRenderer(renderer)
    renderer.ResetCamera()
    renderWindow.Render()

    # Initialize the render windows and set the timed callbacks.
    renderWindowInteractor.Initialize()
    renderWindowInteractor.AddObserver(vtk.vtkCommand.TimerEvent,
                                       robot_state_timer.update_state_actor)
    renderWindowInteractor.AddObserver(vtk.vtkCommand.TimerEvent,
                                       local_grid_timer.update_local_grid_actors)
    renderWindowInteractor.AddObserver(vtk.vtkCommand.TimerEvent,
                                       world_object_timer.update_world_object_actor)
    if robot.has_arm() and options.show_hand_depth:
        renderWindowInteractor.AddObserver(vtk.vtkCommand.TimerEvent,
                                           image_service_timer.update_image_actor)

    timerId = renderWindowInteractor.CreateRepeatingTimer(100)
    renderWindowInteractor.Start()
    return True


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        os._exit(1)
