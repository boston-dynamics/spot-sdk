# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
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

from bosdyn.api.graph_nav import recording_pb2
from bosdyn.client import create_standard_sdk, ResponseError, RpcError
import bosdyn.client.channel
from bosdyn.client.graph_nav import GraphNavClient
from bosdyn.client.lease import LeaseClient
from bosdyn.client.recording import GraphNavRecordingServiceClient
import bosdyn.client.util
import google.protobuf.timestamp_pb2


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

        # Add recording service properties to the command line dictionary.
        self._command_dictionary = {
            '1': self._start_recording,
            '2': self._stop_recording,
            '3': self._get_recording_status,
            '4': self._create_default_waypoint,
            '5': self._download_full_graph
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

    def _start_recording(self):
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

    def _stop_recording(self):
        """Stop or pause recording a map."""
        try:
            status = self._recording_client.stop_recording()
            print("Successfully stopped recording a map.")
        except Exception as err:
            print("Stop recording failed: "+str(err))

    def _get_recording_status(self):
        """Get the recording service's status."""
        status = self._recording_client.get_record_status()
        if status.is_recording:
            print("The recording service is on.")
        else:
            print("The recording service is off.")

    def _create_default_waypoint(self):
        """Create a default waypoint at the robot's current location."""
        resp = self._recording_client.create_waypoint(waypoint_name="default")
        if resp.status == recording_pb2.CreateWaypointResponse.STATUS_OK:
            print("Successfully created a waypoint.")
        else:
            print("Could not create a waypoint.")

    def _download_full_graph(self):
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

    def run(self):
        """Main loop for the command line interface."""
        while True:
            print("""
            Options:
            (1) Start recording a map.
            (2) Stop recording a map.
            (3) Get the recording service's status.
            (4) Create a default waypoint in the current robot's location.
            (5) Download the map after recording.
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
                cmd_func()
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
    sdk.load_app_token(options.app_token)
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
