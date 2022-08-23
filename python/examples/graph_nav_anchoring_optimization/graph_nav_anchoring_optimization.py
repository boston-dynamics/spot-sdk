# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import os
import sys

import matplotlib.image as plt_img
import matplotlib.pyplot as plt
import numpy as np
from google.protobuf.wrappers_pb2 import BoolValue

import bosdyn
from bosdyn.api import geometry_pb2
from bosdyn.api.graph_nav import map_pb2, map_processing_pb2
from bosdyn.client import util
from bosdyn.client.graph_nav import GraphNavClient
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.map_processing import MapProcessingServiceClient
from bosdyn.client.math_helpers import Quat, SE3Pose


class OptInfo:

    def __init__(self, fiducial_id, pixels_per_meter, fiducial_position, fiducial_rotation):
        """
        Info needed to run the optimization.
        :param fiducial_id: The ID of the fiducial to constrain to the blueprint.
        :param pixels_per_meter: The number of pixels in a meter in the blueprint.
        :param fiducial_position: a tuple containing the pixel location of the fiducial.
        :param fiducial_rotation: rotation in degrees of the fiducial on the blueprint page.
        """
        self.pixels_per_meter = pixels_per_meter
        self.fiducial_position = fiducial_position
        self.fiducial_rotation = fiducial_rotation
        self.fiducial_id = fiducial_id

    def get_fiducial_origin(self):
        """
        Get an SE3Pose proto defining the origin of the fiducial in the world frame.
        The world frame starts at the bottom left of the image, with positive y up, positive x
        to the right, and positive z out of the page.
        :return: the SE3Pose proto defining the fiducial in this origin.
        """
        theta = np.deg2rad(self.fiducial_rotation)
        # Fiducial frame:
        # Assume x is up, and z points out. The rotation matrix
        # therefore has x pointed directly out of the page, and
        # the zy vectors pointing to the left and up respectively.
        # Note that the image origin has z pointing out of the page,
        # y up and x to the right.
        # Therefore the z axis is equal to (cos(t), sin(t)) and the y axis is
        #  (sin(t), -cos(t)).
        rot_matrix = np.array([[0, np.sin(theta), np.cos(theta)],
                               [0, -np.cos(theta), np.sin(theta)], [1, 0, 0]])
        world_tform_fiducial = SE3Pose(rot=Quat.from_matrix(rot_matrix),
                                       x=self.fiducial_position[0] / self.pixels_per_meter,
                                       y=self.fiducial_position[1] / self.pixels_per_meter, z=0)
        return world_tform_fiducial.to_proto()

    def meter_to_pixel(self, pos):
        """Converts a proto with pos.x, pos.y in meters to a tuple of (x,y) pixels."""
        return (pos.x * self.pixels_per_meter, pos.y * self.pixels_per_meter)


def get_current_directory():
    """
    Get the directory of the script.
    """
    return os.path.dirname(os.path.realpath(__file__))


def get_data_directory():
    """
    Get the local data directory.
    """
    return os.path.join(get_current_directory(), 'data')


def show_blueprint(path):
    """
    Loads an image file and plots it.
    :param path: the full path to the image file.
    """
    img = plt_img.imread(path)
    # We want a coordinate system that is right handed, with y going up,
    # and x to the right, with z pointing out of the page. This requires us
    # to flip the image vertically, and set the origin of the plot to the lower
    # left corner. This is because images in matplotlib are plotted from the top
    # left corner as (0,0), with x going to the right and y down.
    img = np.flipud(img)
    plt.imshow(img, origin='lower')


def load_graph_and_snapshots(filepath):
    """
    Load the graph and snapshots from a directory.
    :param filepath: The full file path to the directory.
    :return: a tuple containing the graph, waypoint snapshots and edge snapshots.
    """
    print("Loading the graph from disk into local storage at {}".format(filepath))
    graph = map_pb2.Graph()
    waypoint_snapshots = {}
    edge_snapshots = {}
    with open(os.path.join(filepath, "graph"), "rb") as graph_file:
        # Load the graph from disk.
        data = graph_file.read()
        graph.ParseFromString(data)
        print("Loaded graph has {} waypoints and {} edges".format(len(graph.waypoints),
                                                                  len(graph.edges)))
    for waypoint in graph.waypoints:
        if len(waypoint.snapshot_id) == 0:
            continue
        # Load the waypoint snapshots from disk.
        with open(os.path.join(filepath, "waypoint_snapshots", waypoint.snapshot_id),
                  "rb") as snapshot_file:
            waypoint_snapshot = map_pb2.WaypointSnapshot()
            waypoint_snapshot.ParseFromString(snapshot_file.read())
            waypoint_snapshots[waypoint_snapshot.id] = waypoint_snapshot
    for edge in graph.edges:
        if len(edge.snapshot_id) == 0:
            continue
        # Load the edge snapshots from disk.
        with open(os.path.join(filepath, "edge_snapshots", edge.snapshot_id),
                  "rb") as snapshot_file:
            edge_snapshot = map_pb2.EdgeSnapshot()
            edge_snapshot.ParseFromString(snapshot_file.read())
            edge_snapshots[edge_snapshot.id] = edge_snapshot

    return (graph, waypoint_snapshots, edge_snapshots)


def save_graph_and_snapshots(filepath, graph, waypoint_snapshots, edge_snapshots):
    """
    Save the full graph nav map to disk.
    :param filepath: Directory (will be created) for the map.
    :param graph: the graph of waypoints and edges.
    :param waypoint_snapshots: Large data associated with waypoints.
    :param edge_snapshots: Large data associated with edges.
    """
    print("Saving the graph to local storage at {}".format(filepath))
    os.makedirs(filepath, exist_ok=True)
    os.makedirs(os.path.join(filepath, "waypoint_snapshots"), exist_ok=True)
    os.makedirs(os.path.join(filepath, "edge_snapshots"), exist_ok=True)
    with open(os.path.join(filepath, "graph"), "wb") as graph_file:
        graph_file.write(graph.SerializeToString())
    for snapshot_id, waypoint_snapshot in waypoint_snapshots.items():
        # Save the waypoint snapshots to disk.
        with open(os.path.join(filepath, "waypoint_snapshots", snapshot_id), "wb") as snapshot_file:
            snapshot_file.write(waypoint_snapshot.SerializeToString())
    for snapshot_id, edge_snapshot in edge_snapshots.items():
        # Save the edge snapshots to disk.
        with open(os.path.join(filepath, "edge_snapshots", snapshot_id), "wb") as snapshot_file:
            snapshot_file.write(edge_snapshot.SerializeToString())


def show_fiducial_origin(opt_info):
    """
    Draws the fiducial as a frame on the map.
    :param opt_info: info about the optimization.
    """
    VEC_LENGTH = 30.0
    world_T_fiducial = opt_info.get_fiducial_origin()
    world_T_fiducial_mat = SE3Pose.from_obj(world_T_fiducial).rotation.to_matrix()
    plt.plot([
        world_T_fiducial.position.x * opt_info.pixels_per_meter,
        world_T_fiducial.position.x * opt_info.pixels_per_meter +
        world_T_fiducial_mat[0, 2] * VEC_LENGTH
    ], [
        world_T_fiducial.position.y * opt_info.pixels_per_meter,
        world_T_fiducial.position.y * opt_info.pixels_per_meter +
        world_T_fiducial_mat[1, 2] * VEC_LENGTH
    ], 'b-')

    plt.plot([
        world_T_fiducial.position.x * opt_info.pixels_per_meter,
        world_T_fiducial.position.x * opt_info.pixels_per_meter +
        world_T_fiducial_mat[0, 1] * VEC_LENGTH
    ], [
        world_T_fiducial.position.y * opt_info.pixels_per_meter,
        world_T_fiducial.position.y * opt_info.pixels_per_meter +
        world_T_fiducial_mat[1, 1] * VEC_LENGTH
    ], 'g-')


def draw_graph(opt_info, graph, color, anchoring):
    """
    Draws the graph with the given anchoring on the blueprint.
    :param opt_info: Info about the optimization process.
    :param graph: The graph of waypoints and edges.
    :param color: matplotlib color string.
    :param anchoring: The anchoring to use.
    """
    waypoint_id_to_waypoint = {}
    waypoint_id_to_anchoring = {}
    for wp in graph.waypoints:
        waypoint_id_to_waypoint[wp.id] = wp
    for wp in anchoring.anchors:
        waypoint_id_to_anchoring[wp.id] = wp
    for edge in graph.edges:
        anchor_from = waypoint_id_to_anchoring[edge.id.from_waypoint]
        anchor_to = waypoint_id_to_anchoring[edge.id.to_waypoint]
        pos_from = opt_info.meter_to_pixel(anchor_from.seed_tform_waypoint.position)
        pos_to = opt_info.meter_to_pixel(anchor_to.seed_tform_waypoint.position)
        plt.plot([pos_from[0], pos_to[0]], [pos_from[1], pos_to[1]], color)


def upload_graph_and_snapshots(client, graph, waypoint_snapshots, edge_snapshots):
    """
    Upload the graph nav map to the robot.
    :param client: the graph nav client.
    :param graph: The graph of waypoints and edges.
    :param waypoint_snapshots: large data associated with waypoints.
    :param edge_snapshots: large data associated with edges.
    """
    # Upload the graph to the robot.
    print("Uploading the graph and snapshots to the robot...")
    response = client.upload_graph(lease=None, graph=graph, generate_new_anchoring=False)
    # Upload the snapshots to the robot.
    for snapshot_id in response.unknown_waypoint_snapshot_ids:
        if snapshot_id not in waypoint_snapshots:
            continue
        waypoint_snapshot = waypoint_snapshots[snapshot_id]
        client.upload_waypoint_snapshot(waypoint_snapshot)
        print("Uploaded {}".format(waypoint_snapshot.id))
    for snapshot_id in response.unknown_edge_snapshot_ids:
        if snapshot_id not in edge_snapshots:
            continue
        edge_snapshot = edge_snapshots[snapshot_id]
        client.upload_edge_snapshot(edge_snapshot)
        print("Uploaded {}".format(edge_snapshot.id))


def optimize_anchoring(opt_info, client):
    """
    Sends an RPC to the robot which optimizes the anchoring and links it to the position of the
    fiducial in the blueprint.
    :param opt_info: info needed for the optimization.
    :param client: the map processing client.
    :return: the response to the process_anchoring rpc.
    """
    initial_hint = map_processing_pb2.AnchoringHint()
    object_hint = initial_hint.world_objects.add()
    object_hint.object_anchor.id = str(opt_info.fiducial_id)
    object_hint.object_anchor.seed_tform_object.CopyFrom(opt_info.get_fiducial_origin())
    return client.process_anchoring(
        params=map_processing_pb2.ProcessAnchoringRequest.Params(
            optimize_existing_anchoring=BoolValue(value=False)), modify_anchoring_on_server=False,
        stream_intermediate_results=False, initial_hint=initial_hint)


def main(argv):
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--input-map', help='Full filepath of the map directory.',
                        default=os.path.join(get_data_directory(), 'blueprint_example.walk'))
    parser.add_argument(
        '-o', '--output-map', help='Full filepath of the directory to save the optimized map to.',
        default=os.path.join(get_data_directory(), 'blueprint_example_optimized.walk'))
    parser.add_argument(
        '-b', '--blueprint', help=
        'Full filepath to a blueprint image. Should be a raster type, like jpg, png, etc. pdf/svg etc. types are not supported.',
        default=os.path.join(get_data_directory(), 'house_plans.png'))
    parser.add_argument(
        '-p', '--pixels-per-meter', type=float,
        help='In the blueprint, the number of pixels in a meter.',
        default=49.2)  # This default is taken from the scale on the example blueprint.
    parser.add_argument('-f', '--fiducial-id', type=int,
                        help='The ID of the fiducial to constrain to the blueprint.', default=320)
    parser.add_argument(
        '-fx', '--fiducial-position-pixels-x', type=float, help=
        'The x (left-right) position in the blueprint of the fiducial in pixels from the bottom left corner.',
        default=168)
    parser.add_argument(
        '-fy', '--fiducial-position-pixels-y', type=float, help=
        'The y (up-down) position in the blueprint of the fiducial in pixels from the bottom left corner.',
        default=920)
    parser.add_argument(
        '-fr', '--fiducial-rotation-degrees', type=float, default=180.0, help=
        'The rotation of the fiducial, assuming 0 degrees is pointing to the right. The fiducial will be assumed to be vertically mounted on a wall, perfectly orthogonal to the ground.'
    )

    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args(argv)

    opt_info = OptInfo(
        fiducial_id=options.fiducial_id, pixels_per_meter=options.pixels_per_meter,
        fiducial_position=(options.fiducial_position_pixels_x, options.fiducial_position_pixels_y),
        fiducial_rotation=options.fiducial_rotation_degrees)

    # Setup and authenticate the robot.
    sdk = bosdyn.client.create_standard_sdk('GraphNavClient')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    _lease_client = robot.ensure_client(LeaseClient.default_service_name)

    # We need a lease for the robot to access the map services. This prevents multiple
    # clients from fighting over the map data.
    _lease_wallet = _lease_client.lease_wallet
    with LeaseKeepAlive(_lease_client, must_acquire=True, return_at_exit=True):
        (graph, waypoint_snapshots, edge_snapshots) = load_graph_and_snapshots(options.input_map)
        graph_nav_client = robot.ensure_client(GraphNavClient.default_service_name)
        map_processing_client = robot.ensure_client(MapProcessingServiceClient.default_service_name)
        upload_graph_and_snapshots(graph_nav_client, graph, waypoint_snapshots, edge_snapshots)

        print("Optimizing...")
        anchoring_response = optimize_anchoring(opt_info, map_processing_client)
        print("Status: {}, Iterations: {}, Cost: {}".format(anchoring_response.status,
                                                            anchoring_response.iteration,
                                                            anchoring_response.cost))

    # Extract the anchoring from the RPC response.
    optimized_anchoring = map_pb2.Anchoring()
    for wp in anchoring_response.waypoint_results:
        optimized_anchoring.anchors.add().CopyFrom(wp)
    for obj in anchoring_response.world_object_results:
        optimized_anchoring.objects.add().CopyFrom(obj)

    # Plot the results.
    show_blueprint(options.blueprint)
    show_fiducial_origin(opt_info)
    draw_graph(opt_info, graph, 'r-', graph.anchoring)
    draw_graph(opt_info, graph, 'g-', optimized_anchoring)

    # Apply the new anchoring.
    graph.anchoring.CopyFrom(optimized_anchoring)
    # Save the optimized graph.
    save_graph_and_snapshots(options.output_map, graph, waypoint_snapshots, edge_snapshots)
    plt.show()


main(sys.argv[1:])
