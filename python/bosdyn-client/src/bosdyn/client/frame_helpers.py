# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from . import math_helpers
from bosdyn.api import geometry_pb2

VISION_FRAME_NAME = "vision"
BODY_FRAME_NAME = "body"
# Note that the frame name for a gravity aligned body frame is "flat_body" to create a shorter
# string identifier.
GRAV_ALIGNED_BODY_FRAME_NAME = "flat_body"
ODOM_FRAME_NAME = "odom"
GROUND_PLANE_FRAME_NAME = "gpe"
UNKNOWN_FRAME_NAME = "unknown"


class Error(Exception):
    pass


class ValidateFrameTreeError(Error):
    pass


class ValidateFrameTreeUnknownFrameError(ValidateFrameTreeError):
    pass


class ValidateFrameTreeCycleError(ValidateFrameTreeError):
    pass


class ValidateFrameTreeDisjointError(ValidateFrameTreeError):
    pass


def validate_frame_tree_snapshot(frame_tree_snapshot):
    """Validates that a FrameTreeSnapshot is well-formed.

    A FrameTreeSnapshot is expected to be a single tree, but poorly written
    services can misuse the syntax to construct other data structures. The
    syntax prevents DAGs from forming, but the data structure could

    Valid FrameTrees must be a single rooted tree. However, the general format of
    repeated edges may not actually be valid - there could be cycles, disjoint
    trees, or missing edges in the actual data structure.

    Inputs:
        frame_tree_snapshot: A snapshot of the data.

    Returns:
        True if valid

    Raises:
        ValidateFrameTreeError in a number of cases: Empty tree, invalid frame names in the tree, missing transforms
          relating the two nodes, cycles in the tree, the tree is actually a DAG, and disconnected trees.
    """
    if not frame_tree_snapshot:
        raise ValueError('No frame_tree_snapshot')

    # For every entry in the map, see if we can walk to the root without
    # cycles. The root should also be identical for each node

    def _walk_up_tree(frame_name):
        cur_frame_name = frame_name
        visited_frames = set()
        visited_frames.add(cur_frame_name)
        while True:
            edge = frame_tree_snapshot.child_to_parent_edge_map.get(cur_frame_name)
            if not edge:
                raise ValidateFrameTreeUnknownFrameError()
            if not edge.parent_frame_name:
                # At the root of the tree
                break
            if edge.parent_frame_name in visited_frames:
                raise ValidateFrameTreeCycleError()
            visited_frames.add(edge.parent_frame_name)
            cur_frame_name = edge.parent_frame_name
        return cur_frame_name

    root = None
    if not frame_tree_snapshot.child_to_parent_edge_map:
        raise ValidateFrameTreeError("Empty edges in FrameTreeSnapshot")
    for frame_name in frame_tree_snapshot.child_to_parent_edge_map:
        if not frame_name:
            raise ValidateFrameTreeError("Empty child frame name")
        cur_root = _walk_up_tree(frame_name)
        if not root:
            root = cur_root
        else:
            if not cur_root == root:
                raise ValidateFrameTreeDisjointError()

    return True


def get_a_tform_b(frame_tree_snapshot, frame_a, frame_b, validate=True):
    """Get the SE(3) pose representing the transform between frame_a and frame_b.

    Using frame_tree_snapshot, find the math_helpers.SE3Pose to transform geometry from
    frame_a's representation to frame_b's.

    Args:
        frame_tree_snapshot (dict) dictionary representing the child_to_parent_edge_map
        frame_a (string)
        frame_b (string)
        validate (bool) if the FrameTreeSnapshot should be checked for a valid tree structure

    Returns:
        math_helpers.SE3Pose between frame_a and frame_b if they exist in the tree. None otherwise.
    """
    if validate:
        validate_frame_tree_snapshot(frame_tree_snapshot)

    if frame_a not in frame_tree_snapshot.child_to_parent_edge_map:
        return None
    if frame_b not in frame_tree_snapshot.child_to_parent_edge_map:
        return None

    def _list_parent_edges(leaf_frame):
        parent_edges = []
        cur_frame = leaf_frame
        while True:
            parent_edge = frame_tree_snapshot.child_to_parent_edge_map.get(cur_frame)
            if not parent_edge.parent_frame_name:
                break
            parent_edges.append(parent_edge)
            cur_frame = parent_edge.parent_frame_name
        return parent_edges

    inverse_edges = _list_parent_edges(frame_a)
    forward_edges = _list_parent_edges(frame_b)

    # Possible optimization: Nearest common ancestor pruning.

    def _accumulate_transforms(parent_edges):
        ret = math_helpers.SE3Pose.from_identity()
        for parent_edge in parent_edges:
            ret = math_helpers.SE3Pose.from_obj(parent_edge.parent_tform_child) * ret
        return ret

    frame_a_tform_root_frame = _accumulate_transforms(inverse_edges).inverse()
    root_frame_tform_frame_b = _accumulate_transforms(forward_edges)
    return frame_a_tform_root_frame * root_frame_tform_frame_b


def get_se2_a_tform_b(frame_tree_snapshot, frame_a, frame_b, validate=True):
    """Get the SE(2) pose representing the transform between frame_a and frame_b.

    Using frame_tree_snapshot, find the math_helpers.SE2Pose to transform geometry from
    frame_a's representation to frame_b's.

    Args:
        frame_tree_snapshot (dict) dictionary representing the child_to_parent_edge_map
        frame_a (string)
        frame_b (string)
        validate (bool) if the FrameTreeSnapshot should be checked for a valid tree structure

    Returns:
        math_helpers.SE2Pose between frame_a and frame_b if they exist in the tree and
        frame a is a gravity aligned frame. None otherwise.
    """
    # Validate that the transform is in a gravity aligned frame based on the string name.
    if not is_gravity_aligned_frame_name(frame_a):
        # Frame A is not gravity aligned, and therefore a_tform_b cannot be converted into
        # an SE(2) pose because it will lose height information.
        return None
    # Get the SE(3) pose from the frame tree snapshot representing the desired transform a_tform_b
    se3_a_tform_b = get_a_tform_b(frame_tree_snapshot, frame_a, frame_b, validate)
    if se3_a_tform_b is None:
        # Failed to find the transformation between frames a and b in the frame tree snapshot.
        return None
    return se3_a_tform_b.get_closest_se2_transform()


def express_se2_velocity_in_new_frame(frame_tree_snapshot, frame_b, frame_c, vel_of_a_in_b, validate=True):
    """Convert the SE2 Velocity in frame b to a SE2 Velocity in frame c using
       the frame tree snapshot.

    Args:
        frame_tree_snapshot (dict) dictionary representing the child_to_parent_edge_map
        frame_b (string)
        frame_c (string)
        vel_of_a_in_b (SE2Velocity proto) SE2 Velocity in frame_b
        validate (bool) if the FrameTreeSnapshot should be checked for a valid tree structure

    Returns:
        math_helpers.SE2Velocity velocity_of_a_in_c in frame_c if the frames exist in the tree. None otherwise.
    """
    # Find the SE(3) pose in the frame tree snapshot that represents c_tform_b.
    se3_c_tform_b = get_a_tform_b(frame_tree_snapshot, frame_c, frame_b, validate)
    if se3_c_tform_b is None:
        # If the SE3Pose for c_tform_b does not exist in the frame tree snapshot,
        # then we cannot transform the velocity.
        return None
    # Check that the frame name of frame_c is considered to be a gravity aligned frame.
    if not is_gravity_aligned_frame_name(frame_c):
        # Frame C is not gravity aligned, and therefore c_tform_b cannot be converted into
        # an SE(2) pose because it will lose height information.
        return None
    # Find the closest SE(2) pose for the c_tform_b SE(3) pose found from the snapshot.
    se2_c_tform_b = se3_c_tform_b.get_closest_se2_transform()
    # Transform the velocity into the new frame to get vel_of_a_in_c.
    c_adjoint_b = se2_c_tform_b.to_adjoint_matrix()
    vel_of_a_in_c = math_helpers.transform_se2velocity(c_adjoint_b, vel_of_a_in_b)
    return vel_of_a_in_c

def express_se3_velocity_in_new_frame(frame_tree_snapshot, frame_b, frame_c, vel_of_a_in_b, validate=True):
    """Convert the SE(3) Velocity in frame b to an SE(3) Velocity in frame c using
       the frame tree snapshot.

    Args:
        frame_tree_snapshot (dict) dictionary representing the child_to_parent_edge_map
        frame_b (string)
        frame_c (string)
        vel_of_a_in_b (SE3Velocity proto) SE(3) Velocity in frame_b
        validate (bool) if the FrameTreeSnapshot should be checked for a valid tree structure

    Returns:
        math_helpers.SE3Velocity velocity_of_a_in_c in frame_c if the frames exist in the tree. None otherwise.
    """
    # Find the SE(3) pose in the frame tree snapshot that represents c_tform_b.
    se3_c_tform_b = get_a_tform_b(frame_tree_snapshot, frame_c, frame_b, validate)
    if se3_c_tform_b is None:
        # If the SE3Pose for c_tform_b does not exist in the frame tree snapshot,
        # then we cannot transform the velocity.
        return None
    # Transform the velocity into the new frame to get vel_of_a_in_c.
    c_adjoint_b = se3_c_tform_b.to_adjoint_matrix()
    vel_of_a_in_c = math_helpers.transform_se3velocity(c_adjoint_b, vel_of_a_in_b)
    return vel_of_a_in_c

def get_odom_tform_body(frame_tree_snapshot):
    """Get the transformation between "odom" frame and "body" frame from the FrameTreeSnapshot."""
    return get_a_tform_b(frame_tree_snapshot, ODOM_FRAME_NAME, BODY_FRAME_NAME)


def get_vision_tform_body(frame_tree_snapshot):
    """Get the transformation between "vision" frame and "body" frame from the FrameTreeSnapshot."""
    return get_a_tform_b(frame_tree_snapshot, VISION_FRAME_NAME, BODY_FRAME_NAME)


class GenerateTreeError(Error):
    pass


class ChildFrameInTree(GenerateTreeError):
    pass


def add_edge_to_tree(frame_tree_snapshot, parent_tform_child, parent_frame_name, child_frame_name):
    """Appends a child/parent and the transform to the FrameTreeSnapshot.
       Args:
            frame_tree_snapshot (dict) dictionary representing the child_to_parent_edge_map
            parent_tform_child (SE3Pose proto)
            parent_frame_name (string)
            child_frame_name (string)
    """
    if child_frame_name in frame_tree_snapshot:
        raise ChildFrameInTree
    # Can add additional validation checks, such as if the parent frame will make a cycle,
    # or if this will be completely disconnected
    frame_tree_snapshot[child_frame_name] = geometry_pb2.FrameTreeSnapshot.ParentEdge(
        parent_frame_name=parent_frame_name, parent_tform_child=parent_tform_child)
    return frame_tree_snapshot


def get_frame_names(frame_tree_snapshot):
    """Returns a list of all known child or parent frames in the FrameTreeSnapshot."""
    frame_names = []
    for child_frame in frame_tree_snapshot.child_to_parent_edge_map:
        if child_frame not in frame_names:
            frame_names.append(child_frame)
        parent_frame = frame_tree_snapshot.child_to_parent_edge_map[child_frame].parent_frame_name
        if parent_frame not in frame_names:
            frame_names.append(parent_frame)
    return [frame_name for frame_name in frame_names if frame_name != ""]


def is_gravity_aligned_frame_name(frame_name):
    """Checks if the string frame name is a known gravity aligned frame."""
    if frame_name == VISION_FRAME_NAME or frame_name == GRAV_ALIGNED_BODY_FRAME_NAME or frame_name == ODOM_FRAME_NAME:
        return True
    return False