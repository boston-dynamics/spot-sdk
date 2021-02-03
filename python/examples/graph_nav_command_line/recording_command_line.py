# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Command line interface integrating options to record maps with WASD controls. """
import argparse
import grpc
import logging
import os
import sys
import time

from bosdyn.api.graph_nav import map_pb2, recording_pb2
from bosdyn.client import create_standard_sdk, ResponseError, RpcError
import bosdyn.client.channel
from bosdyn.client.graph_nav import GraphNavClient
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive, LeaseWallet
from bosdyn.client.math_helpers import SE3Pose, Quat
from bosdyn.client.recording import GraphNavRecordingServiceClient
import bosdyn.client.util
import google.protobuf.timestamp_pb2

import graph_nav_util

class RecordingInterface(object):
    """Recording service command line interface."""

    def __init__(self, robot, download_filepath):
        # Keep the robot instance and it's ID.
        self._robot = robot
        # Force trigger timesync.
        self._robot.time_sync.wait_for_sync()

        # Filepath for the location to put the downloaded graph and snapshots.
        if download_filepath[-1] == "/":
            self._download_filepath = download_filepath + "downloaded_graph"
        else:
            self._download_filepath = download_filepath + "/downloaded_graph"

        # Setup the recording service client.
        self._recording_client = self._robot.ensure_client(
            GraphNavRecordingServiceClient.default_service_name)

        # Setup the graph nav service client.
        self._graph_nav_client = robot.ensure_client(GraphNavClient.default_service_name)

        # Store the most recent knowledge of the state of the robot based on rpc calls.
        self._current_graph = None
        self._current_edges = dict()  #maps to_waypoint to list(from_waypoint)
        self._current_waypoint_snapshots = dict()  # maps id to waypoint snapshot
        self._current_edge_snapshots = dict()  # maps id to edge snapshot
        self._current_annotation_name_to_wp_id = dict()

        # Add recording service properties to the command line dictionary.
        self._command_dictionary = {
            '0': self._clear_map,
            '1': self._start_recording,
            '2': self._stop_recording,
            '3': self._get_recording_status,
            '4': self._create_default_waypoint,
            '5': self._download_full_graph,
            '6': self._list_graph_waypoint_and_edge_ids,
            '7': self._create_new_edge,
            '8': self._create_loop
        }

    def should_we_start_recording(self):
        # Before starting to record, check the state of the GraphNav system.
        graph = self._graph_nav_client.download_graph()
        if graph is not None:
            # Check that the graph has waypoints. If it does, then we need to be localized to the graph
            # before starting to record
            if len(graph.waypoints) > 0:
                localization_state = self._graph_nav_client.get_localization_state()
                if not localization_state.localization.waypoint_id:
                    # Not localized to anything in the map. The best option is to clear the graph or
                    # attempt to localize to the current map.
                    # Returning false since the GraphNav system is not in the state it should be to
                    # begin recording.
                    return False
        # If there is no graph or there exists a graph that we are localized to, then it is fine to
        # start recording, so we return True.
        return True

    def _clear_map(self, *args):
        """Clear the state of the map on the robot, removing all waypoints and edges."""
        self._lease_client = self._robot.ensure_client(LeaseClient.default_service_name)
        self._lease = self._lease_client.acquire()
        return self._graph_nav_client.clear_graph(lease=self._lease.lease_proto)

    def _start_recording(self, *args):
        """Start recording a map."""
        should_start_recording = self.should_we_start_recording()
        if not should_start_recording:
            print("The system is not in the proper state to start recording.", \
                   "Try using the graph_nav_command_line to either clear the map or", \
                   "attempt to localize to the map.")
            return
        try:
            status = self._recording_client.start_recording()
            print("Successfully started recording a map.")
        except Exception as err:
            print("Start recording failed: "+str(err))

    def _stop_recording(self, *args):
        """Stop or pause recording a map."""
        try:
            status = self._recording_client.stop_recording()
            print("Successfully stopped recording a map.")
        except Exception as err:
            print("Stop recording failed: "+str(err))

    def _get_recording_status(self, *args):
        """Get the recording service's status."""
        status = self._recording_client.get_record_status()
        if status.is_recording:
            print("The recording service is on.")
        else:
            print("The recording service is off.")

    def _create_default_waypoint(self, *args):
        """Create a default waypoint at the robot's current location."""
        resp = self._recording_client.create_waypoint(waypoint_name="default")
        if resp.status == recording_pb2.CreateWaypointResponse.STATUS_OK:
            print("Successfully created a waypoint.")
        else:
            print("Could not create a waypoint.")

    def _download_full_graph(self, *args):
        """Download the graph and snapshots from the robot."""
        graph = self._graph_nav_client.download_graph()
        if graph is None:
            print("Failed to download the graph.")
            return
        self._write_full_graph(graph)
        print("Graph downloaded with {} waypoints and {} edges".format(
            len(graph.waypoints), len(graph.edges)))
        # Download the waypoint and edge snapshots.
        self._download_and_write_waypoint_snapshots(graph.waypoints)
        self._download_and_write_edge_snapshots(graph.edges)

    def _write_full_graph(self, graph):
        """Download the graph from robot to the specified, local filepath location."""
        graph_bytes = graph.SerializeToString()
        self._write_bytes(self._download_filepath, '/graph', graph_bytes)

    def _download_and_write_waypoint_snapshots(self, waypoints):
        """Download the waypoint snapshots from robot to the specified, local filepath location."""
        num_waypoint_snapshots_downloaded = 0
        for waypoint in waypoints:
            try:
                waypoint_snapshot = self._graph_nav_client.download_waypoint_snapshot(
                    waypoint.snapshot_id)
            except Exception:
                # Failure in downloading waypoint snapshot. Continue to next snapshot.
                print("Failed to download waypoint snapshot: " + waypoint.snapshot_id)
                continue
            self._write_bytes(self._download_filepath + '/waypoint_snapshots',
                              '/' + waypoint.snapshot_id, waypoint_snapshot.SerializeToString())
            num_waypoint_snapshots_downloaded += 1
            print("Downloaded {} of the total {} waypoint snapshots.".format(
                num_waypoint_snapshots_downloaded, len(waypoints)))

    def _download_and_write_edge_snapshots(self, edges):
        """Download the edge snapshots from robot to the specified, local filepath location."""
        num_edge_snapshots_downloaded = 0
        for edge in edges:
            try:
                edge_snapshot = self._graph_nav_client.download_edge_snapshot(edge.snapshot_id)
            except Exception:
                # Failure in downloading edge snapshot. Continue to next snapshot.
                print("Failed to download edge snapshot: " + edge.snapshot_id)
                continue
            self._write_bytes(self._download_filepath + '/edge_snapshots', '/' + edge.snapshot_id,
                              edge_snapshot.SerializeToString())
            num_edge_snapshots_downloaded += 1
            print("Downloaded {} of the total {} edge snapshots.".format(
                num_edge_snapshots_downloaded, len(edges)))

    def _write_bytes(self, filepath, filename, data):
        """Write data to a file."""
        os.makedirs(filepath, exist_ok=True)
        with open(filepath + filename, 'wb+') as f:
            f.write(data)
            f.close()

    def _list_graph_waypoint_and_edge_ids(self, *args):
        """List the waypoint ids and edge ids of the graph currently on the robot."""

        # Download current graph
        graph = self._graph_nav_client.download_graph()
        if graph is None:
            print("Empty graph.")
            return
        self._current_graph = graph

        localization_id = self._graph_nav_client.get_localization_state().localization.waypoint_id

        # Update and print waypoints and edges
        self._current_annotation_name_to_wp_id, self._current_edges = graph_nav_util.update_waypoints_and_edges(
            graph, localization_id)

    def _create_new_edge(self, *args):
        """Create new edge between existing waypoints in map."""

        if len(args[0]) != 2:
            print("ERROR: Specify the two waypoints to connect (short code or annotation).")
            return

        if self._current_graph is None:
            self._current_graph = self._graph_nav_client.download_graph()

        from_id = graph_nav_util.find_unique_waypoint_id(args[0][0], self._current_graph,
                                                         self._current_annotation_name_to_wp_id)
        to_id = graph_nav_util.find_unique_waypoint_id(args[0][1], self._current_graph,
                                                       self._current_annotation_name_to_wp_id)

        print("Creating edge from {} to {}.".format(from_id, to_id))

        from_wp = self._get_waypoint(from_id)
        if from_wp is None:
            return

        to_wp = self._get_waypoint(to_id)
        if to_wp is None:
            return

        # Get edge transform based on kinematic odometry
        edge_transform = self._get_transform(from_wp, to_wp)

        # Define new edge
        new_edge = map_pb2.Edge()
        new_edge.id.from_waypoint = from_id
        new_edge.id.to_waypoint = to_id
        new_edge.from_tform_to.CopyFrom(edge_transform)

        print("edge transform =", new_edge.from_tform_to)

        # Send request to add edge to map
        self._recording_client.create_edge(edge=new_edge)

    def _create_loop(self, *args):
        """Create edge from last waypoint to first waypoint."""

        if self._current_graph is None:
            self._current_graph = self._graph_nav_client.download_graph()

        if len(self._current_graph.waypoints) < 2:
            self._add_message(
                "Graph contains {} waypoints -- at least two are needed to create loop.".format(
                    len(self._current_graph.waypoints)))
            return False

        sorted_waypoints = graph_nav_util.sort_waypoints_chrono(self._current_graph)
        edge_waypoints = [sorted_waypoints[-1][0], sorted_waypoints[0][0]]

        self._create_new_edge(edge_waypoints)

    def _get_waypoint(self, id):
        '''Get waypoint from graph (return None if waypoint not found)'''

        if self._current_graph is None:
            self._current_graph = self._graph_nav_client.download_graph()

        for waypoint in self._current_graph.waypoints:
            if waypoint.id == id:
                return waypoint

        print('ERROR: Waypoint {} not found in graph.'.format(id))
        return None

    def _get_transform(self, from_wp, to_wp):
        '''Get transform from from-waypoint to to-waypoint.'''

        from_se3 = from_wp.waypoint_tform_ko
        from_tf = SE3Pose(from_se3.position.x, from_se3.position.y, from_se3.position.z,
            Quat(w=from_se3.rotation.w, x=from_se3.rotation.x, y=from_se3.rotation.y, z=from_se3.rotation.z))

        to_se3 = to_wp.waypoint_tform_ko
        to_tf = SE3Pose(to_se3.position.x, to_se3.position.y, to_se3.position.z,
            Quat(w=to_se3.rotation.w, x=to_se3.rotation.x, y=to_se3.rotation.y, z=to_se3.rotation.z))

        from_T_to = from_tf.mult(to_tf.inverse())
        return from_T_to.to_proto()


    def run(self):
        """Main loop for the command line interface."""
        while True:
            print("""
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
            (q) Exit.
            """)
            try:
                inputs = input('>')
            except NameError:
                pass
            req_type = str.split(inputs)[0]

            if req_type == 'q':
                break

            if req_type not in self._command_dictionary:
                print("Request not in the known command dictionary.")
                continue
            try:
                cmd_func = self._command_dictionary[req_type]
                cmd_func(str.split(inputs)[1:])
            except Exception as e:
                print(e)


def main(argv):
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument('-d', '--download-filepath',
                        help='Full filepath for where to download graph and snapshots.',
                        default=os.getcwd())
    options = parser.parse_args(argv)

    # Create robot object.
    sdk = bosdyn.client.create_standard_sdk('RecordingClient')
    robot = sdk.create_robot(options.hostname)
    robot.authenticate(options.username, options.password)
    recording_command_line = RecordingInterface(robot, options.download_filepath)

    try:
        recording_command_line.run()
        return True
    except Exception as exc:  # pylint: disable=broad-except
        print(exc)
        print("Recording command line client threw an error.")
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
