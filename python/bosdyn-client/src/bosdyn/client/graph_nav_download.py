# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging
from pathlib import Path

from .graph_nav import GraphNavClient

_LOGGER = logging.getLogger(__name__)


def download_to_disk(client: GraphNavClient, download_directory: Path,
                     skip_existing_snapshots=True):
    """Helper function to download a graph and all snapshots from a robot into the standard file
    layout.

    This function does not provide much customization.  If you need more complicated control of
    timeouts, async calls, or anything else, please copy the details out and modify them for your
    use case.

    Args:
        client: GraphNavClient to use for the download.
        download_directory: Path to the directory in which to save the downloaded graph and snapshots.
        skip_existing_snapshots: If true, will not redownload any files that already exist in the snapshot directories.
    """

    # Make sure the directories create successfully before doing anything else.
    download_directory.mkdir(parents=True, exist_ok=True)
    wp_snapshot_dir = download_directory / 'waypoint_snapshots'
    wp_snapshot_dir.mkdir(exist_ok=True)
    edge_snapshot_dir = download_directory / 'edge_snapshots'
    edge_snapshot_dir.mkdir(exist_ok=True)

    graph = client.download_graph()
    (download_directory / 'graph').write_bytes(graph.SerializeToString())

    _LOGGER.info('Downloading snapshots for %d waypoints', len(graph.waypoints))
    for waypoint in graph.waypoints:
        if len(waypoint.snapshot_id) == 0:
            continue
        file = wp_snapshot_dir / waypoint.snapshot_id
        if skip_existing_snapshots and file.exists():
            continue
        waypoint_snapshot = client.download_waypoint_snapshot(waypoint.snapshot_id)
        file.write_bytes(waypoint_snapshot.SerializeToString())

    _LOGGER.info('Downloading snapshots for %d edges', len(graph.edges))
    for edge in graph.edges:
        if len(edge.snapshot_id) == 0:
            continue
        file = edge_snapshot_dir / edge.snapshot_id
        if skip_existing_snapshots and file.exists():
            continue
        edge_snapshot = client.download_edge_snapshot(edge.snapshot_id)
        file.write_bytes(edge_snapshot.SerializeToString())


if __name__ == '__main__':
    import argparse

    from bosdyn.client import create_standard_sdk
    from bosdyn.client.util import add_base_arguments, authenticate

    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description=('Download a graph and all snapshots from a robot.'))
    add_base_arguments(parser)
    parser.add_argument(
        'graph_directory', type=Path, help=
        'Path to the directory in which to save the downloaded graph and snapshots.  Follows the standard file structure and naming conventions.'
    )
    args = parser.parse_args()

    sdk = create_standard_sdk('UploadGraph')
    robot = sdk.create_robot(args.hostname)
    authenticate(robot)
    client = robot.ensure_client(GraphNavClient.default_service_name)

    download_to_disk(client, args.graph_directory)
