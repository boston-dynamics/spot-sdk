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
from bosdyn.api import geometry_pb2 as geom
from bosdyn.api import world_object_pb2
from bosdyn.client.frame_helpers import *
from bosdyn.client.world_object import (WorldObjectClient, make_add_world_object_req,
                                        make_change_world_object_req, make_delete_world_object_req)
from bosdyn.util import now_timestamp


def create_drawable_sphere_object():
    """Create a drawable sphere world object that can be added through a mutation request."""
    # Add an edge where the transform vision_tform_object is only a position transform with no rotation.
    vision_tform_drawable = geom.SE3Pose(position=geom.Vec3(x=2, y=3, z=2),
                                         rotation=geom.Quaternion(x=0, y=0, z=0, w=1))
    # Create a map between the child frame name and the parent frame name/SE3Pose parent_tform_child
    edges = {}
    # Create an edge in the frame tree snapshot that includes vision_tform_drawable
    drawable_frame_name = "drawing_sphere"
    edges = add_edge_to_tree(edges, vision_tform_drawable, VISION_FRAME_NAME, drawable_frame_name)
    snapshot = geom.FrameTreeSnapshot(child_to_parent_edge_map=edges)

    # Set the acquisition time for the sphere using a function to get google.protobuf.Timestamp of the current system time.
    time_now = now_timestamp()

    # Create the sphere drawable object
    sphere = world_object_pb2.DrawableSphere(radius=1)
    red_color = world_object_pb2.DrawableProperties.Color(r=255, b=0, g=0, a=1)
    sphere_drawable_prop = world_object_pb2.DrawableProperties(
        color=red_color, label="red sphere", wireframe=False, sphere=sphere,
        frame_name_drawable=drawable_frame_name)

    # Create the complete world object with transform information, a unique name, and the drawable sphere properties.
    world_object_sphere = world_object_pb2.WorldObject(id=16, name="red_sphere_ball",
                                                       transforms_snapshot=snapshot,
                                                       acquisition_time=time_now,
                                                       drawable_properties=[sphere_drawable_prop])
    return world_object_sphere


def create_apriltag_object():
    """Create an apriltag world object that can be added through a mutation request."""
    # Set the acquisition time for the additional april tag in robot time using a function to
    # get google.protobuf.Timestamp of the current system time.
    time_now = now_timestamp()

    # The apriltag id for the object we want to add.
    tag_id = 308

    # Set the frame names used for the two variants of the apriltag (filtered, raw)
    frame_name_fiducial = "fiducial_" + str(tag_id)
    frame_name_fiducial_filtered = "filtered_fiducial_" + str(tag_id)

    # Make the april tag (slightly offset from the first tag detection) as a world object. Create the
    # different edges necessary to create an expressive tree. The root node will be the world frame.
    default_a_tform_b = geom.SE3Pose(position=geom.Vec3(x=.2, y=.2, z=.2),
                                     rotation=geom.Quaternion(x=.1, y=.1, z=.1, w=.1))
    # Create a map between the child frame name and the parent frame name/SE3Pose parent_tform_child
    edges = {}
    # Create an edge for the raw fiducial detection in the world.
    vision_tform_fiducial = update_frame(tf=default_a_tform_b, position_change=(0, 0, -.2),
                                         rotation_change=(0, 0, 0, 0))
    edges = add_edge_to_tree(edges, vision_tform_fiducial, VISION_FRAME_NAME, frame_name_fiducial)
    # Create a edge for the filtered version of the fiducial in the world.
    vision_tform_filtered_fiducial = update_frame(tf=default_a_tform_b, position_change=(0, 0, -.2),
                                                  rotation_change=(0, 0, 0, 0))
    edges = add_edge_to_tree(edges, vision_tform_filtered_fiducial, VISION_FRAME_NAME,
                             frame_name_fiducial_filtered)
    # Create the transform to express vision_tform_odom
    vision_tform_odom = update_frame(tf=default_a_tform_b, position_change=(0, 0, -.2),
                                     rotation_change=(0, 0, 0, 0))
    edges = add_edge_to_tree(edges, vision_tform_odom, VISION_FRAME_NAME, ODOM_FRAME_NAME)
    # Can also add custom frames into the frame tree snapshot as long as they keep the tree structure,
    # so the parent_frame must also be in the tree.
    vision_tform_special_frame = update_frame(tf=default_a_tform_b, position_change=(0, 0, -.2),
                                              rotation_change=(0, 0, 0, 0))
    edges = add_edge_to_tree(edges, vision_tform_special_frame, VISION_FRAME_NAME,
                             "my_special_frame")
    snapshot = geom.FrameTreeSnapshot(child_to_parent_edge_map=edges)

    # Create the specific properties for the apriltag including the frame names for the transforms
    # describing the apriltag's position.
    tag_prop = world_object_pb2.AprilTagProperties(
        tag_id=tag_id, dimensions=geom.Vec2(x=.2, y=.2), frame_name_fiducial=frame_name_fiducial,
        frame_name_fiducial_filtered=frame_name_fiducial_filtered)

    #Create the complete world object with transform information and the apriltag properties.
    wo_obj_to_add = world_object_pb2.WorldObject(id=21, transforms_snapshot=snapshot,
                                                 acquisition_time=time_now,
                                                 apriltag_properties=tag_prop)
    return wo_obj_to_add


def main(argv):
    """An example using the API to apply mutations to world objects."""
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
    print("Current World objects' ids " + str([obj.id for obj in world_objects]))

    # If there are any world objects in Spot's perception scene, then attempt to mutate one.
    # This should fail and return a STATUS_NO_PERMISSION since a client cannot mutate
    # objects that they did not add into the scene.
    if len(world_objects) > 0:
        obj_to_mutate = world_objects[0]
        # Attempt to delete the object.
        delete_req = make_delete_world_object_req(obj_to_mutate)
        status = world_object_client.mutate_world_objects(delete_req).status
        assert (status == world_object_pb2.MutateWorldObjectResponse.STATUS_NO_PERMISSION)

        # Attempt to change the object.
        for edge in obj_to_mutate.transforms_snapshot.child_to_parent_edge_map:
            obj_to_mutate.transforms_snapshot.child_to_parent_edge_map[
                edge].parent_tform_child.position.x = 1.0
        change_req = make_change_world_object_req(obj_to_mutate)
        status = world_object_client.mutate_world_objects(change_req).status
        assert (status == world_object_pb2.MutateWorldObjectResponse.STATUS_NO_PERMISSION)

    # Request to add the new april tag detection to the world object service.
    wo_obj_to_add = create_apriltag_object()
    add_apriltag = make_add_world_object_req(wo_obj_to_add)
    resp = world_object_client.mutate_world_objects(mutation_req=add_apriltag)
    # Get the world object ID set by the service, so that we can make additional changes to this object.
    added_apriltag_world_obj_id = resp.mutated_object_id

    # List all world objects in the scene after the mutation was applied.
    world_objects = world_object_client.list_world_objects().world_objects
    print("World object IDs after object addition: " +
          str([obj.apriltag_properties.tag_id for obj in world_objects]))

    for world_obj in world_objects:
        if world_obj.id == added_apriltag_world_obj_id:
            # Look for the custom frame that was included in the add-request, where the child frame name was "my_special_frame"
            full_snapshot = world_obj.transforms_snapshot
            for edge in full_snapshot.child_to_parent_edge_map:
                if edge == "my_special_frame":
                    print(
                        "The world object includes the custom frame vision_tform_my_special_frame!")

    # Request to change an existing apriltag's dimensions. This will succeed because it is changing
    # an object that was added by a client program. We are using the ID returned by the service to
    # change the correct apriltag.
    time_now = now_timestamp()
    tag_prop_modified = world_object_pb2.AprilTagProperties(tag_id=308,
                                                            dimensions=geom.Vec2(x=.35, y=.35))
    wo_obj_to_change = world_object_pb2.WorldObject(
        id=added_apriltag_world_obj_id, name="world_obj_apriltag",
        transforms_snapshot=wo_obj_to_add.transforms_snapshot, acquisition_time=time_now,
        apriltag_properties=tag_prop_modified)
    print("World object X dimension of apriltag size before change: " +
          str([obj.apriltag_properties.dimensions.x for obj in world_objects]))

    change_apriltag = make_change_world_object_req(wo_obj_to_change)
    resp = world_object_client.mutate_world_objects(mutation_req=change_apriltag)
    assert (resp.status == world_object_pb2.MutateWorldObjectResponse.STATUS_OK)

    # List all world objects in the scene after the mutation was applied.
    world_objects = world_object_client.list_world_objects().world_objects
    print("World object X dimension of apriltag size after change: " +
          str([obj.apriltag_properties.dimensions.x for obj in world_objects]))

    # Add a apriltag and then delete it. This will succeed because it is deleting an object added by
    # a client program and not specific to Spot's perception
    add_apriltag = make_add_world_object_req(wo_obj_to_add)
    resp = world_object_client.mutate_world_objects(mutation_req=add_apriltag)
    assert (resp.status == world_object_pb2.MutateWorldObjectResponse.STATUS_OK)
    apriltag_to_delete_id = resp.mutated_object_id

    # Update the list of world object's after adding a apriltag
    world_objects = world_object_client.list_world_objects().world_objects

    # Delete the april tag that was just added. This will succeed because it is changing an object that was
    # just added by a client program (and not an object Spot's perception system detected). The world object
    # can be identified by the ID returned from the service after the mutation request succeeded.
    wo_obj_to_delete = world_object_pb2.WorldObject(id=apriltag_to_delete_id)
    delete_apriltag = make_delete_world_object_req(wo_obj_to_delete)
    resp = world_object_client.mutate_world_objects(mutation_req=delete_apriltag)
    assert (resp.status == world_object_pb2.MutateWorldObjectResponse.STATUS_OK)

    # List all world objects in the scene after the deletion was applied.
    world_objects = world_object_client.list_world_objects().world_objects
    print("World object IDs after object deletion: " +
          str([obj.apriltag_properties.tag_id for obj in world_objects]))

    # Add a drawable sphere into the perception scene with a custom frame and unique name.
    x = 0.5
    y = 0
    z = 0
    # The sphere's position will all be described relative to the robot's body frame.
    frame = BODY_FRAME_NAME

    # Set the drawing properties of the sphere.
    radius = 0.05
    color = (255, 0, 0, 1)  # red, solid sphere

    resp = world_object_client.draw_sphere("debug_sphere", x, y, z, frame, radius, color)
    print('Added a world object sphere at (' + str(x) + ', ' + str(y) + ', ' + str(z) + ')')

    # Get the world object ID set by the service.
    sphere_id = resp.mutated_object_id

    # List all world objects in the scene after the mutation was applied. Find the sphere in the list
    # and see the transforms added into the frame tree snapshot by Spot in addition to the custom frame.
    world_objects = world_object_client.list_world_objects().world_objects
    for world_obj in world_objects:
        if world_obj.id == sphere_id:
            print("Found sphere named " + world_obj.name)
            full_snapshot = world_obj.transforms_snapshot
            for edge in full_snapshot.child_to_parent_edge_map:
                print("Child frame name: " + edge + ". Parent frame name: " +
                      full_snapshot.child_to_parent_edge_map[edge].parent_frame_name)
    return True


def update_frame(tf, position_change, rotation_change):
    return geom.SE3Pose(
        position=geom.Vec3(
            x=tf.position.x + position_change[0], y=tf.position.y + position_change[1],
            z=tf.position.z + position_change[2]), rotation=geom.Quaternion(
                x=tf.rotation.x + rotation_change[0], y=tf.rotation.y + rotation_change[1],
                z=tf.rotation.z + rotation_change[2], w=tf.rotation.w + rotation_change[3]))


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
