# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Example using the world objects service. """

from __future__ import print_function

import argparse
import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import geometry_pb2 as geom
from bosdyn.api import world_object_pb2 as wo
from bosdyn.client.world_object import WorldObjectClient, make_add_world_object_req
from bosdyn.util import now_timestamp


def main(argv):
    """An example using the API demonstrating adding image coordinates to the world object service."""
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

    # List all world objects in the scene before any mutation.
    world_objects = world_object_client.list_world_objects().world_objects
    print("Current World objects before mutations: " + str([obj for obj in world_objects]))

    # Set the detection time for the additional april tag. The client library will convert the time into robot time.
    # Uses a function to get google.protobuf.Timestamp of the current system time.
    timestamp = now_timestamp()

    # Create the image coordinate object. This type of object does not require a base frame for the world object.
    # Since we are not providing a transform to the object expressed by the image coordinates, it is not necessary
    # to set the frame_name_image_properties, as this describes the frame used in a transform (such as world_tform_image_coords).
    img_coord = wo.ImageProperties(camera_source="back",
                                   coordinates=geom.Polygon(vertexes=[geom.Vec2(x=100, y=100)]))
    wo_obj = wo.WorldObject(id=2, name="img_coord_tester", acquisition_time=timestamp,
                            image_properties=img_coord)

    # Request to add the image coordinates detection to the world object service.
    add_coords = make_add_world_object_req(wo_obj)
    resp = world_object_client.mutate_world_objects(mutation_req=add_coords)

    # List all world objects in the scene after the mutation was applied.
    world_objects = world_object_client.list_world_objects().world_objects
    print("Current World objects after adding coordinates: " + str([obj for obj in world_objects]))

    return True


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
