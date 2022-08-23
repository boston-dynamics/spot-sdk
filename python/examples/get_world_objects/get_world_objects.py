# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Example using the world objects service. """

from __future__ import print_function

import argparse
import sys
import time

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import world_object_pb2
from bosdyn.client.world_object import WorldObjectClient


def main(argv):
    """An example using the API to list and get specific objects."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args(argv)

    # Create robot object with a world object client.
    sdk = bosdyn.client.create_standard_sdk('WorldObjectClient')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    # Time sync is necessary so that time-based filter requests can be converted.
    robot.time_sync.wait_for_sync()

    # Create the world object client.
    world_object_client = robot.ensure_client(WorldObjectClient.default_service_name)

    # List all world objects in the scene.
    world_objects = world_object_client.list_world_objects().world_objects
    print("World objects: " + str(world_objects))
    # Examine the transform snapshot for the world object!
    for world_obj in world_objects:
        print("ID: " + str(world_obj.id))
        full_snapshot = world_obj.transforms_snapshot
        for edge in full_snapshot.child_to_parent_edge_map:
            print("Child frame name: " + edge + ". Parent frame name: " +
                  full_snapshot.child_to_parent_edge_map[edge].parent_frame_name)

    # Get all fiducial objects (an object of a specific type).
    request_fiducials = [world_object_pb2.WORLD_OBJECT_APRILTAG]
    fiducial_objects = world_object_client.list_world_objects(
        object_type=request_fiducials).world_objects
    print("Fiducial objects: " + str(fiducial_objects))

    # Get all objects detected after this time
    start_time = time.time()
    most_recent_objects = world_object_client.list_world_objects(
        time_start_point=start_time).world_objects
    print("Recent objects after " + str(start_time) + " are: " + str(most_recent_objects))

    # Get all objects detected after this time in the future (so should get no objects).
    start_time = time.time() + float(1e9)
    most_recent_objects = world_object_client.list_world_objects(
        time_start_point=start_time).world_objects
    print("Recent objects after " + str(start_time) + " are: " + str(most_recent_objects))
    print("Clock skew seconds: {} nanos: {}".format(
        world_object_client._timesync_endpoint.clock_skew.seconds,
        world_object_client._timesync_endpoint.clock_skew.nanos))

    return True


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
