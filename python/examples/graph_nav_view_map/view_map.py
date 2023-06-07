# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import math
import os
import sys
import time

import google.protobuf.timestamp_pb2
import numpy as np
import numpy.linalg
import vtk
from vtk.util import numpy_support

from bosdyn.api import geometry_pb2
from bosdyn.api.graph_nav import map_pb2
from bosdyn.client.frame_helpers import *
from bosdyn.client.math_helpers import *

"""
This example shows how to load and view a graph nav map.

"""


def numpy_to_poly_data(pts):
    """
    Converts numpy array data into vtk poly data.
    :param pts: the numpy array to convert (3 x N).
    :return: a vtkPolyData.
    """
    pd = vtk.vtkPolyData()
    pd.SetPoints(vtk.vtkPoints())
    # Makes a deep copy
    pd.GetPoints().SetData(numpy_support.numpy_to_vtk(pts.copy()))

    f = vtk.vtkVertexGlyphFilter()
    f.SetInputData(pd)
    f.Update()
    pd = f.GetOutput()

    return pd


def mat_to_vtk(mat):
    """
    Converts a 4x4 homogenous transform into a vtk transform object.
    :param mat: A 4x4 homogenous transform (numpy array).
    :return: A VTK transform object representing the transform.
    """
    t = vtk.vtkTransform()
    t.SetMatrix(mat.flatten())
    return t


def vtk_to_mat(transform):
    """
    Converts a VTK transform object to 4x4 homogenous numpy matrix.
    :param transform: an object of type vtkTransform
    : return: a numpy array with a 4x4 matrix representation of the transform.
    """
    tf_matrix = transform.GetMatrix()
    out = np.array(np.eye(4))
    for r in range(4):
        for c in range(4):
            out[r, c] = tf_matrix.GetElement(r, c)
    return out


def api_to_vtk_se3_pose(se3_pose):
    """
    Convert a bosdyn SDK SE3Pose into a VTK pose.
    :param se3_pose: the bosdyn SDK SE3 Pose.
    :return: A VTK pose representing the bosdyn SDK SE3 Pose.
    """
    return mat_to_vtk(se3_pose.to_matrix())


def create_fiducial_object(world_object, waypoint, renderer):
    """
    Creates a VTK object representing a fiducial.
    :param world_object: A WorldObject representing a fiducial.
    :param waypoint: The waypoint the AprilTag is associated with.
    :param renderer: The VTK renderer
    :return: a tuple of (vtkActor, 4x4 homogenous transform) representing the vtk actor for the fiducial, and its
    transform w.r.t the waypoint.
    """
    fiducial_object = world_object.apriltag_properties
    odom_tform_fiducial_filtered = get_a_tform_b(
        world_object.transforms_snapshot, ODOM_FRAME_NAME,
        world_object.apriltag_properties.frame_name_fiducial_filtered)
    waypoint_tform_odom = SE3Pose.from_proto(waypoint.waypoint_tform_ko)
    waypoint_tform_fiducial_filtered = api_to_vtk_se3_pose(
        waypoint_tform_odom * odom_tform_fiducial_filtered)
    plane_source = vtk.vtkPlaneSource()
    plane_source.SetCenter(0.0, 0.0, 0.0)
    plane_source.SetNormal(0.0, 0.0, 1.0)
    plane_source.Update()
    plane = plane_source.GetOutput()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(plane)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(0.5, 0.7, 0.9)
    actor.SetScale(fiducial_object.dimensions.x, fiducial_object.dimensions.y, 1.0)
    renderer.AddActor(actor)
    return actor, waypoint_tform_fiducial_filtered


def create_point_cloud_object(waypoints, snapshots, waypoint_id):
    """
    Create a VTK object representing the point cloud in a snapshot. Note that in graph_nav, "point cloud" refers to the
    feature cloud of a waypoint -- that is, a collection of visual features observed by all five cameras at a particular
    point in time. The visual features are associated with points that are rigidly attached to a waypoint.
    :param waypoints: dict of waypoint ID to waypoint.
    :param snapshots: dict of waypoint snapshot ID to waypoint snapshot.
    :param waypoint_id: the waypoint ID of the waypoint whose point cloud we want to render.
    :return: a vtkActor containing the point cloud data.
    """
    wp = waypoints[waypoint_id]
    snapshot = snapshots[wp.snapshot_id]
    cloud = snapshot.point_cloud
    odom_tform_cloud = get_a_tform_b(cloud.source.transforms_snapshot, ODOM_FRAME_NAME,
                                     cloud.source.frame_name_sensor)
    waypoint_tform_odom = SE3Pose.from_proto(wp.waypoint_tform_ko)
    waypoint_tform_cloud = api_to_vtk_se3_pose(waypoint_tform_odom * odom_tform_cloud)

    point_cloud_data = np.frombuffer(cloud.data, dtype=np.float32).reshape(int(cloud.num_points), 3)
    poly_data = numpy_to_poly_data(point_cloud_data)
    arr = vtk.vtkFloatArray()
    for i in range(cloud.num_points):
        arr.InsertNextValue(point_cloud_data[i, 2])
    arr.SetName('z_coord')
    poly_data.GetPointData().AddArray(arr)
    poly_data.GetPointData().SetActiveScalars('z_coord')
    actor = vtk.vtkActor()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly_data)
    mapper.ScalarVisibilityOn()
    actor.SetMapper(mapper)
    actor.GetProperty().SetPointSize(2)
    actor.SetUserTransform(waypoint_tform_cloud)
    return actor


def create_waypoint_object(renderer, waypoints, snapshots, waypoint_id):
    """
    Creates a VTK object representing a waypoint and its point cloud.
    :param renderer: The VTK renderer.
    :param waypoints: dict of waypoint ID to waypoint.
    :param snapshots: dict of snapshot ID to snapshot.
    :param waypoint_id: the waypoint id of the waypoint object we wish to create.
    :return: A vtkAssembly representing the waypoint (an axis) and its point cloud.
    """
    assembly = vtk.vtkAssembly()
    actor = vtk.vtkAxesActor()
    actor.SetXAxisLabelText('')
    actor.SetYAxisLabelText('')
    actor.SetZAxisLabelText('')
    actor.SetTotalLength(0.2, 0.2, 0.2)
    point_cloud_actor = create_point_cloud_object(waypoints, snapshots, waypoint_id)
    assembly.AddPart(actor)
    assembly.AddPart(point_cloud_actor)
    renderer.AddActor(assembly)
    return assembly


def make_line(pt_A, pt_B, renderer):
    """
    Creates a VTK object which is a white line between two points.
    :param pt_A: starting point of the line.
    :param pt_B: ending point of the line.
    :param renderer: the VTK renderer.
    :return: A VTK object that is a while line between pt_A and pt_B.
    """
    line_source = vtk.vtkLineSource()
    line_source.SetPoint1(pt_A[0], pt_A[1], pt_A[2])
    line_source.SetPoint2(pt_B[0], pt_B[1], pt_B[2])
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(line_source.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetLineWidth(2)
    actor.GetProperty().SetColor(0.7, 0.7, 0.7)
    renderer.AddActor(actor)
    return actor


def make_text(name, pt, renderer):
    """
    Creates white text on a black background at a particular point.
    :param name: The text to display.
    :param pt: The point in the world where the text will be displayed.
    :param renderer: The VTK renderer
    :return: the vtkActor representing the text.
    """
    actor = vtk.vtkTextActor()
    actor.SetInput(name)
    prop = actor.GetTextProperty()
    prop.SetBackgroundColor(0.0, 0.0, 0.0)
    prop.SetBackgroundOpacity(0.5)
    prop.SetFontSize(16)
    coord = actor.GetPositionCoordinate()
    coord.SetCoordinateSystemToWorld()
    coord.SetValue((pt[0], pt[1], pt[2]))

    renderer.AddActor(actor)
    return actor


def create_edge_object(curr_wp_tform_to_wp, world_tform_curr_wp, renderer):
    # Concatenate the edge transform.
    world_tform_to_wp = np.dot(world_tform_curr_wp, curr_wp_tform_to_wp)
    # Make a line between the current waypoint and the neighbor.
    make_line(world_tform_curr_wp[:3, 3], world_tform_to_wp[:3, 3], renderer)
    return world_tform_to_wp


def load_map(path):
    """
    Load a map from the given file path.
    :param path: Path to the root directory of the map.
    :return: the graph, waypoints, waypoint snapshots and edge snapshots.
    """
    with open(os.path.join(path, 'graph'), 'rb') as graph_file:
        # Load the graph file and deserialize it. The graph file is a protobuf containing only the waypoints and the
        # edges between them.
        data = graph_file.read()
        current_graph = map_pb2.Graph()
        current_graph.ParseFromString(data)

        # Set up maps from waypoint ID to waypoints, edges, snapshots, etc.
        current_waypoints = {}
        current_waypoint_snapshots = {}
        current_edge_snapshots = {}
        current_anchors = {}
        current_anchored_world_objects = {}

        # Load the anchored world objects first so we can look in each waypoint snapshot as we load it.
        for anchored_world_object in current_graph.anchoring.objects:
            current_anchored_world_objects[anchored_world_object.id] = (anchored_world_object,)
        # For each waypoint, load any snapshot associated with it.
        for waypoint in current_graph.waypoints:
            current_waypoints[waypoint.id] = waypoint

            if len(waypoint.snapshot_id) == 0:
                continue
            # Load the snapshot. Note that snapshots contain all of the raw data in a waypoint and may be large.
            file_name = os.path.join(path, 'waypoint_snapshots', waypoint.snapshot_id)
            if not os.path.exists(file_name):
                continue
            with open(file_name, 'rb') as snapshot_file:
                waypoint_snapshot = map_pb2.WaypointSnapshot()
                waypoint_snapshot.ParseFromString(snapshot_file.read())
                current_waypoint_snapshots[waypoint_snapshot.id] = waypoint_snapshot

                for fiducial in waypoint_snapshot.objects:
                    if not fiducial.HasField('apriltag_properties'):
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
            file_name = os.path.join(path, 'edge_snapshots', edge.snapshot_id)
            if not os.path.exists(file_name):
                continue
            with open(file_name, 'rb') as snapshot_file:
                edge_snapshot = map_pb2.EdgeSnapshot()
                edge_snapshot.ParseFromString(snapshot_file.read())
                current_edge_snapshots[edge_snapshot.id] = edge_snapshot
        for anchor in current_graph.anchoring.anchors:
            current_anchors[anchor.id] = anchor
        print(
            f'Loaded graph with {len(current_graph.waypoints)} waypoints, {len(current_graph.edges)} edges, '
            f'{len(current_graph.anchoring.anchors)} anchors, and {len(current_graph.anchoring.objects)} anchored world objects'
        )
        return (current_graph, current_waypoints, current_waypoint_snapshots,
                current_edge_snapshots, current_anchors, current_anchored_world_objects)


def create_anchored_graph_objects(current_graph, current_waypoint_snapshots, current_waypoints,
                                  current_anchors, current_anchored_world_objects, renderer):
    """
    Creates all the VTK objects associated with the graph, in seed frame, if they are anchored.
    :param current_graph: the graph to use.
    :param current_waypoint_snapshots: dict from snapshot id to snapshot.
    :param current_waypoints: dict from waypoint id to waypoint.
    :param renderer: The VTK renderer
    :return: the average position in world space of all the waypoints.
    """
    waypoint_objects = {}
    avg_pos = np.array([0.0, 0.0, 0.0])
    waypoints_in_anchoring = 0
    # Create VTK objects associated with each waypoint.
    for waypoint in current_graph.waypoints:
        if waypoint.id in current_anchors:
            waypoint_object = create_waypoint_object(renderer, current_waypoints,
                                                     current_waypoint_snapshots, waypoint.id)
            seed_tform_waypoint = SE3Pose.from_proto(
                current_anchors[waypoint.id].seed_tform_waypoint).to_matrix()
            waypoint_object.SetUserTransform(mat_to_vtk(seed_tform_waypoint))
            make_text(waypoint.annotations.name, seed_tform_waypoint[:3, 3], renderer)
            avg_pos += seed_tform_waypoint[:3, 3]
            waypoints_in_anchoring += 1

    avg_pos /= waypoints_in_anchoring

    # Create VTK objects associated with each edge.
    for edge in current_graph.edges:
        if edge.id.from_waypoint in current_anchors and edge.id.to_waypoint in current_anchors:
            seed_tform_from = SE3Pose.from_proto(
                current_anchors[edge.id.from_waypoint].seed_tform_waypoint).to_matrix()
            from_tform_to = SE3Pose.from_proto(edge.from_tform_to).to_matrix()
            create_edge_object(from_tform_to, seed_tform_from, renderer)

    # Create VTK objects associated with each anchored world object.
    for anchored_wo in current_anchored_world_objects.values():
        # anchored_wo is a tuple of (anchored_world_object, waypoint, fiducial).
        (fiducial_object, _) = create_fiducial_object(anchored_wo[2], anchored_wo[1], renderer)
        seed_tform_fiducial = SE3Pose.from_proto(anchored_wo[0].seed_tform_object).to_matrix()
        fiducial_object.SetUserTransform(mat_to_vtk(seed_tform_fiducial))
        make_text(anchored_wo[0].id, seed_tform_fiducial[:3, 3], renderer)

    return avg_pos


def create_graph_objects(current_graph, current_waypoint_snapshots, current_waypoints, renderer):
    """
    Creates all the VTK objects associated with the graph.
    :param current_graph: the graph to use.
    :param current_waypoint_snapshots: dict from snapshot id to snapshot.
    :param current_waypoints: dict from waypoint id to waypoint.
    :param renderer: The VTK renderer
    :return: the average position in world space of all the waypoints.
    """
    waypoint_objects = {}
    # Create VTK objects associated with each waypoint.
    for waypoint in current_graph.waypoints:
        waypoint_objects[waypoint.id] = create_waypoint_object(renderer, current_waypoints,
                                                               current_waypoint_snapshots,
                                                               waypoint.id)
    # Now, perform a breadth first search of the graph starting from an arbitrary waypoint. Graph nav graphs
    # have no global reference frame. The only thing we can say about waypoints is that they have relative
    # transformations to their neighbors via edges. So the goal is to get the whole graph into a global reference
    # frame centered on some waypoint as the origin.
    queue = []
    queue.append((current_graph.waypoints[0], np.eye(4)))
    visited = {}
    # Get the camera in the ballpark of the right position by centering it on the average position of a waypoint.
    avg_pos = np.array([0.0, 0.0, 0.0])

    # Breadth first search.
    while len(queue) > 0:
        # Visit a waypoint.
        curr_element = queue[0]
        queue.pop(0)
        curr_waypoint = curr_element[0]
        if curr_waypoint.id in visited:
            continue
        visited[curr_waypoint.id] = True

        # We now know the global pose of this waypoint, so set the pose.
        waypoint_objects[curr_waypoint.id].SetUserTransform(mat_to_vtk(curr_element[1]))
        world_tform_current_waypoint = curr_element[1]
        # Add text to the waypoint.
        make_text(curr_waypoint.annotations.name, world_tform_current_waypoint[:3, 3], renderer)

        # For each fiducial in the waypoint's snapshot, add an object at the world pose of that fiducial.
        if (curr_waypoint.snapshot_id in current_waypoint_snapshots):
            snapshot = current_waypoint_snapshots[curr_waypoint.snapshot_id]
            for fiducial in snapshot.objects:
                if fiducial.HasField('apriltag_properties'):
                    (fiducial_object, curr_wp_tform_fiducial) = create_fiducial_object(
                        fiducial, curr_waypoint, renderer)
                    world_tform_fiducial = np.dot(world_tform_current_waypoint,
                                                  vtk_to_mat(curr_wp_tform_fiducial))
                    fiducial_object.SetUserTransform(mat_to_vtk(world_tform_fiducial))
                    make_text(str(fiducial.apriltag_properties.tag_id), world_tform_fiducial[:3, 3],
                              renderer)

        # Now, for each edge, walk along the edge and concatenate the transform to the neighbor.
        for edge in current_graph.edges:
            # If the edge is directed away from us...
            if edge.id.from_waypoint == curr_waypoint.id and edge.id.to_waypoint not in visited:
                current_waypoint_tform_to_waypoint = SE3Pose.from_proto(
                    edge.from_tform_to).to_matrix()
                world_tform_to_wp = create_edge_object(current_waypoint_tform_to_waypoint,
                                                       world_tform_current_waypoint, renderer)
                # Add the neighbor to the queue.
                queue.append((current_waypoints[edge.id.to_waypoint], world_tform_to_wp))
                avg_pos += world_tform_to_wp[:3, 3]
            # If the edge is directed toward us...
            elif edge.id.to_waypoint == curr_waypoint.id and edge.id.from_waypoint not in visited:
                current_waypoint_tform_from_waypoint = (SE3Pose.from_proto(
                    edge.from_tform_to).inverse()).to_matrix()
                world_tform_from_wp = create_edge_object(current_waypoint_tform_from_waypoint,
                                                         world_tform_current_waypoint, renderer)
                # Add the neighbor to the queue.
                queue.append((current_waypoints[edge.id.from_waypoint], world_tform_from_wp))
                avg_pos += world_tform_from_wp[:3, 3]

    # Compute the average waypoint position to place the camera appropriately.
    avg_pos /= len(current_waypoints)
    return avg_pos


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=str, help='Map to draw.')
    parser.add_argument('-a', '--anchoring', action='store_true',
                        help='Draw the map according to the anchoring (in seed frame).')
    options = parser.parse_args(argv)
    # Load the map from the given file.
    (current_graph, current_waypoints, current_waypoint_snapshots, current_edge_snapshots,
     current_anchors, current_anchored_world_objects) = load_map(options.path)

    # Create the renderer.
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.05, 0.1, 0.15)

    if options.anchoring:
        if len(current_graph.anchoring.anchors) == 0:
            print('No anchors to draw.')
            sys.exit(-1)
        avg_pos = create_anchored_graph_objects(current_graph, current_waypoint_snapshots,
                                                current_waypoints, current_anchors,
                                                current_anchored_world_objects, renderer)
    else:
        avg_pos = create_graph_objects(current_graph, current_waypoint_snapshots, current_waypoints,
                                       renderer)

    camera_pos = avg_pos + np.array([-1, 0, 5])

    camera = renderer.GetActiveCamera()
    camera.SetViewUp(0, 0, 1)
    camera.SetPosition(camera_pos[0], camera_pos[1], camera_pos[2])

    # Create the VTK renderer and interactor.
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetWindowName(options.path)
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)
    renderWindow.SetSize(1280, 720)
    style = vtk.vtkInteractorStyleTerrain()
    renderWindowInteractor.SetInteractorStyle(style)
    renderer.ResetCamera()

    # Start rendering.
    renderWindow.Render()
    renderWindow.Start()
    renderWindowInteractor.Start()


if __name__ == '__main__':
    main(sys.argv[1:])
