# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging
from pathlib import Path
from typing import Optional

from bosdyn.api.graph_nav import graph_nav_pb2, map_pb2

from .graph_nav import GraphNavClient

_LOGGER = logging.getLogger(__name__)


def upload_from_disk(client: GraphNavClient, graph_directory: Path,
                     graph_file: Optional[Path] = None):
    """Helper function to upload a graph and all snapshots to a robot.  Only supports robots running
    5.1.0 or later.

    This function does not provide much customization.  If you need more complicated control of
    timeouts, async calls, or anything else, please copy the details out and modify them for your
    use case.

    Args:
        client: GraphNavClient to use for the upload.
        graph_directory: Path to the directory containing the graph and snapshots.
            Follows the standard file structure and naming conventions.
        graph_file: Optional path to the graph file.  If the path is not absolute, it will be
            interpreted as relative to the graph_directory.
    """

    if graph_file is None:
        graph_file = Path('graph')
    if not graph_file.is_absolute():
        graph_file = graph_directory / graph_file
    graph = map_pb2.Graph()
    graph.ParseFromString(graph_file.read_bytes())
    _LOGGER.info('Uploading graph with %d waypoints and %d edges', len(graph.waypoints),
                 len(graph.edges))
    upload_response = client.upload_graph(graph=graph, replace_graph=True)

    # Upload in groups of 16MB.
    MAX_BYTES = 16 * 1024 * 1024

    def upload_batches(name, snapshot_type, snapshot_dir, ids, upload_fn):
        snapshots = []
        num_bytes = 0
        for snapshot_id in ids:
            snapshot = snapshot_type()
            snapshot.ParseFromString((snapshot_dir / snapshot_id).read_bytes())
            this_bytes = snapshot.ByteSize()
            if len(snapshots) > 0 and this_bytes + num_bytes > MAX_BYTES:
                _LOGGER.info('Uploading %d %s snapshots', len(snapshots), name)
                upload_fn(snapshots)
                snapshots = []
                num_bytes = 0
            snapshots.append(snapshot)
            num_bytes += this_bytes
        if len(snapshots) > 0:
            _LOGGER.info('Uploading %d %s snapshots', len(snapshots), name)
            upload_fn(snapshots)

    # Upload waypoint snapshots.
    upload_batches(
        'waypoint', map_pb2.WaypointSnapshot, graph_directory / 'waypoint_snapshots',
        upload_response.unknown_waypoint_snapshot_ids, lambda snapshots: client.upload_snapshots(
            graph_nav_pb2.UploadSnapshotsRequest.Snapshots(waypoint_snapshots=snapshots)))

    # Upload edge snapshots.
    upload_batches(
        'edge', map_pb2.EdgeSnapshot, graph_directory / 'edge_snapshots',
        upload_response.unknown_edge_snapshot_ids, lambda snapshots: client.upload_snapshots(
            graph_nav_pb2.UploadSnapshotsRequest.Snapshots(edge_snapshots=snapshots)))


if __name__ == '__main__':
    import argparse

    from bosdyn.client import create_standard_sdk
    from bosdyn.client.util import add_base_arguments, authenticate
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description=(
        'Upload a graph and all snapshots to a robot.  Only supports robots running 5.1.0 or later.'
    ))
    add_base_arguments(parser)
    parser.add_argument(
        'graph_directory', type=Path, help=
        ('Path to the directory containing the graph and snapshots.  Follows the standard file structure and naming conventions.'
        ))
    parser.add_argument(
        '--graph_file', type=Path, default=None, help=
        ('Optional path to the graph file.  If the path is not absolute, it will be interpreted as relative to the graph_directory.'
        ))
    args = parser.parse_args()

    sdk = create_standard_sdk('UploadGraph')
    robot = sdk.create_robot(args.hostname)
    authenticate(robot)
    client = robot.ensure_client(GraphNavClient.default_service_name)

    upload_from_disk(client, args.graph_directory, args.graph_file)
