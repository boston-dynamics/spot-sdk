# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for frame helpers"""

import math

import google.protobuf.text_format
import pytest

import bosdyn.api.geometry_pb2 as geom_protos
from bosdyn.client import frame_helpers, math_helpers


def _create_snapshot(frame_tree_snapshot_string):
    frame_tree_snapshot = geom_protos.FrameTreeSnapshot()
    google.protobuf.text_format.Parse(frame_tree_snapshot_string, frame_tree_snapshot)
    return frame_tree_snapshot


# The following set of tests are for validating valid FrameTreeSnapshots.


def test_validate_snapshot_single_child():
    """Tests that a single edge tree is valid."""
    snapshot_text = """child_to_parent_edge_map {
      key: "beta"
      value: {
        parent_frame_name: "alpha"
      }
    }
    child_to_parent_edge_map {
      key: "alpha"
      value: {
        parent_frame_name: ""
      }
    }"""
    assert frame_helpers.validate_frame_tree_snapshot(_create_snapshot(snapshot_text))


def test_validate_snapshot_two_children():
    """Tests that a tree with two children off of the root is valid."""
    snapshot_text = """child_to_parent_edge_map {
      key: "beta"
      value: {
        parent_frame_name: "alpha"
      }
    }
    child_to_parent_edge_map {
      key: "gamma"
      value: {
        parent_frame_name: "alpha"
      }
    }
    child_to_parent_edge_map {
      key: "alpha"
      value: {
        parent_frame_name: ""
      }
    }"""
    assert frame_helpers.validate_frame_tree_snapshot(_create_snapshot(snapshot_text))


def test_validate_snapshot_linear_chain():
    """Tests that a tree with a linear chain is parsed correctly."""
    snapshot_text = """child_to_parent_edge_map {
      key: "beta"
      value: {
        parent_frame_name: "alpha"
      }
    }
    child_to_parent_edge_map {
      key: "gamma"
      value: {
        parent_frame_name: "beta"
      }
    }
    child_to_parent_edge_map {
      key: "alpha"
      value: {
        parent_frame_name: ""
      }
    }"""
    assert frame_helpers.validate_frame_tree_snapshot(_create_snapshot(snapshot_text))


# The following tests are for validating invalid FrameTreeSnapshots


def test_validate_snapshot_empty_frame_tree():
    """Tests that an empty frame tree does not validate."""
    snapshot_text = """"""
    with pytest.raises(frame_helpers.ValidateFrameTreeError):
        frame_helpers.validate_frame_tree_snapshot(_create_snapshot(snapshot_text))


def test_validate_snapshot_empty_key_name():
    """Tests that a frame tree with an empty child frame name does not validate."""
    snapshot_text = """child_to_parent_edge_map {
      key: ""
      value: {
        parent_frame_name: "alpha"
      }
    }"""
    with pytest.raises(frame_helpers.ValidateFrameTreeError):
        frame_helpers.validate_frame_tree_snapshot(_create_snapshot(snapshot_text))


def test_validate_snapshot_single_edge_cycle():
    """Tests that a frame tree with a single edge that has a cycle does not validate."""
    snapshot_text = """child_to_parent_edge_map {
      key: "alpha"
      value: {
        parent_frame_name: "alpha"
      }
    }"""
    with pytest.raises(frame_helpers.ValidateFrameTreeCycleError):
        frame_helpers.validate_frame_tree_snapshot(_create_snapshot(snapshot_text))


def test_validate_snapshot_multi_edge_cycle():
    """Tests that a frame tree with a multi-edge cycle does not validate."""
    snapshot_text = """child_to_parent_edge_map {
      key: "beta"
      value: {
        parent_frame_name: "alpha"
      }
    }
    child_to_parent_edge_map {
      key: "alpha"
      value: {
        parent_frame_name: "beta"
      }
    }"""
    with pytest.raises(frame_helpers.ValidateFrameTreeCycleError):
        frame_helpers.validate_frame_tree_snapshot(_create_snapshot(snapshot_text))


def test_validate_snapshot_disjoint():
    """Tests that a frame tree that is disconnected does not validate."""
    snapshot_text = """child_to_parent_edge_map {
      key: "beta"
      value: {
        parent_frame_name: "alpha"
      }
    }
    child_to_parent_edge_map {
      key: "delta"
      value: {
        parent_frame_name: "gamma"
      }
    }
    child_to_parent_edge_map {
      key: "alpha"
      value: {
        parent_frame_name: ""
      }
    }
    child_to_parent_edge_map {
      key: "gamma"
      value: {
        parent_frame_name: ""
      }
    }"""
    with pytest.raises(frame_helpers.ValidateFrameTreeDisjointError):
        frame_helpers.validate_frame_tree_snapshot(_create_snapshot(snapshot_text))


def test_validate_snapshot_unknown_parent():
    """Tests that a frame tree with an unknown parent does not validate."""
    snapshot_text = """child_to_parent_edge_map {
      key: "beta"
      value: {
        parent_frame_name: "foo"
      }
    }"""
    with pytest.raises(frame_helpers.ValidateFrameTreeUnknownFrameError):
        frame_helpers.validate_frame_tree_snapshot(_create_snapshot(snapshot_text))


# The following tests are for frame math in valid FrameTreeSnapshots


def _do_poses_match(x, y, z, pose_b):
    # Hacky approach with string representation
    pose_a = math_helpers.SE3Pose(x, y, z, math_helpers.Quat())
    return str(pose_a) == str(pose_b)


def test_frame_tree_math_single_edge():
    snapshot_text = """child_to_parent_edge_map {
      key: "beta"
      value: {
        parent_frame_name: "alpha"
        parent_tform_child: {
          position: {
            x: 10
            y: 0
            z: 0
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "alpha"
      value: {
        parent_frame_name: ""
      }
    }"""
    frame_tree = _create_snapshot(snapshot_text)
    assert frame_helpers.validate_frame_tree_snapshot(frame_tree)
    assert _do_poses_match(10, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'beta'))
    assert _do_poses_match(-10, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'beta', 'alpha'))
    assert _do_poses_match(0, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'alpha'))
    assert _do_poses_match(0, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'beta', 'beta'))
    assert not frame_helpers.get_a_tform_b(frame_tree, 'omega', 'alpha')
    assert not frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'omega')
    assert not frame_helpers.get_a_tform_b(frame_tree, 'omega', 'omega')
    assert not frame_helpers.get_a_tform_b(frame_tree, 'omega', 'psi')


def test_frame_tree_math_two_edges():
    snapshot_text = """child_to_parent_edge_map {
      key: "beta"
      value: {
        parent_frame_name: "alpha"
        parent_tform_child: {
          position: {
            x: 10
            y: 0
            z: 0
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "gamma"
      value: {
        parent_frame_name: "alpha"
        parent_tform_child: {
          position: {
            x: 0
            y: 0
            z: 10
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "alpha"
      value: {
        parent_frame_name: ""
      }
    }"""
    frame_tree = _create_snapshot(snapshot_text)
    assert frame_helpers.validate_frame_tree_snapshot(frame_tree)
    assert _do_poses_match(10, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'beta'))
    assert _do_poses_match(0, 0, 10, frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'gamma'))
    assert _do_poses_match(-10, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'beta', 'alpha'))
    assert _do_poses_match(-10, 0, 10, frame_helpers.get_a_tform_b(frame_tree, 'beta', 'gamma'))
    assert _do_poses_match(0, 0, -10, frame_helpers.get_a_tform_b(frame_tree, 'gamma', 'alpha'))
    assert _do_poses_match(10, 0, -10, frame_helpers.get_a_tform_b(frame_tree, 'gamma', 'beta'))


def test_frame_tree_math_chain():
    snapshot_text = """child_to_parent_edge_map {
      key: "beta"
      value: {
        parent_frame_name: "alpha"
        parent_tform_child: {
          position: {
            x: 10
            y: 0
            z: 0
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "gamma"
      value: {
        parent_frame_name: "beta"
        parent_tform_child: {
          position: {
            x: 0
            y: 0
            z: 10
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "alpha"
      value: {
        parent_frame_name: ""
      }
    }"""
    frame_tree = _create_snapshot(snapshot_text)
    assert frame_helpers.validate_frame_tree_snapshot(frame_tree)
    assert _do_poses_match(10, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'beta'))
    assert _do_poses_match(10, 0, 10, frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'gamma'))
    assert _do_poses_match(-10, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'beta', 'alpha'))
    assert _do_poses_match(0, 0, 10, frame_helpers.get_a_tform_b(frame_tree, 'beta', 'gamma'))
    assert _do_poses_match(-10, 0, -10, frame_helpers.get_a_tform_b(frame_tree, 'gamma', 'alpha'))
    assert _do_poses_match(0, 0, -10, frame_helpers.get_a_tform_b(frame_tree, 'gamma', 'beta'))


def test_frame_tree_math_big_tree():
    snapshot_text = """child_to_parent_edge_map {
      key: "beta"
      value: {
        parent_frame_name: "alpha"
        parent_tform_child: {
          position: {
            x: 10
            y: 0
            z: 0
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "gamma"
      value: {
        parent_frame_name: "alpha"
        parent_tform_child: {
          position: {
            x: 0
            y: 0
            z: 10
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "delta"
      value: {
        parent_frame_name: "beta"
        parent_tform_child: {
          position: {
            x: 100
            y: 0
            z: 0
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "epsilon"
      value: {
        parent_frame_name: "beta"
        parent_tform_child: {
          position: {
            x: 1000
            y: 0
            z: 0
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "zeta"
      value: {
        parent_frame_name: "gamma"
        parent_tform_child: {
          position: {
            x: 0
            y: 0
            z: 100
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "eta"
      value: {
        parent_frame_name: "gamma"
        parent_tform_child: {
          position: {
            x: 0
            y: 0
            z: 1000
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "alpha"
      value: {
        parent_frame_name: ""
      }
    }"""
    frame_tree = _create_snapshot(snapshot_text)
    assert frame_helpers.validate_frame_tree_snapshot(frame_tree)

    # alpha as source frame
    assert _do_poses_match(0, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'alpha'))
    assert _do_poses_match(10, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'beta'))
    assert _do_poses_match(0, 0, 10, frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'gamma'))
    assert _do_poses_match(110, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'delta'))
    assert _do_poses_match(1010, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'epsilon'))
    assert _do_poses_match(0, 0, 110, frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'zeta'))
    assert _do_poses_match(0, 0, 1010, frame_helpers.get_a_tform_b(frame_tree, 'alpha', 'eta'))

    # beta as source frame
    assert _do_poses_match(-10, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'beta', 'alpha'))
    assert _do_poses_match(0, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'beta', 'beta'))
    assert _do_poses_match(-10, 0, 10, frame_helpers.get_a_tform_b(frame_tree, 'beta', 'gamma'))
    assert _do_poses_match(100, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'beta', 'delta'))
    assert _do_poses_match(1000, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'beta', 'epsilon'))
    assert _do_poses_match(-10, 0, 110, frame_helpers.get_a_tform_b(frame_tree, 'beta', 'zeta'))
    assert _do_poses_match(-10, 0, 1010, frame_helpers.get_a_tform_b(frame_tree, 'beta', 'eta'))

    # gamma as source frame
    assert _do_poses_match(0, 0, -10, frame_helpers.get_a_tform_b(frame_tree, 'gamma', 'alpha'))
    assert _do_poses_match(10, 0, -10, frame_helpers.get_a_tform_b(frame_tree, 'gamma', 'beta'))
    assert _do_poses_match(0, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'gamma', 'gamma'))
    assert _do_poses_match(110, 0, -10, frame_helpers.get_a_tform_b(frame_tree, 'gamma', 'delta'))
    assert _do_poses_match(1010, 0, -10, frame_helpers.get_a_tform_b(frame_tree, 'gamma',
                                                                     'epsilon'))
    assert _do_poses_match(0, 0, 100, frame_helpers.get_a_tform_b(frame_tree, 'gamma', 'zeta'))
    assert _do_poses_match(0, 0, 1000, frame_helpers.get_a_tform_b(frame_tree, 'gamma', 'eta'))

    # delta as source frame
    assert _do_poses_match(-110, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'delta', 'alpha'))
    assert _do_poses_match(-100, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'delta', 'beta'))
    assert _do_poses_match(-110, 0, 10, frame_helpers.get_a_tform_b(frame_tree, 'delta', 'gamma'))
    assert _do_poses_match(0, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'delta', 'delta'))
    assert _do_poses_match(900, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'delta', 'epsilon'))
    assert _do_poses_match(-110, 0, 110, frame_helpers.get_a_tform_b(frame_tree, 'delta', 'zeta'))
    assert _do_poses_match(-110, 0, 1010, frame_helpers.get_a_tform_b(frame_tree, 'delta', 'eta'))

    # epsilon as source frame
    assert _do_poses_match(-1010, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'epsilon', 'alpha'))
    assert _do_poses_match(-1000, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'epsilon', 'beta'))
    assert _do_poses_match(-1010, 0, 10, frame_helpers.get_a_tform_b(frame_tree, 'epsilon',
                                                                     'gamma'))
    assert _do_poses_match(-900, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'epsilon', 'delta'))
    assert _do_poses_match(0, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'epsilon', 'epsilon'))
    assert _do_poses_match(-1010, 0, 110, frame_helpers.get_a_tform_b(frame_tree, 'epsilon',
                                                                      'zeta'))
    assert _do_poses_match(-1010, 0, 1010,
                           frame_helpers.get_a_tform_b(frame_tree, 'epsilon', 'eta'))

    # zeta as source frame
    assert _do_poses_match(0, 0, -110, frame_helpers.get_a_tform_b(frame_tree, 'zeta', 'alpha'))
    assert _do_poses_match(10, 0, -110, frame_helpers.get_a_tform_b(frame_tree, 'zeta', 'beta'))
    assert _do_poses_match(0, 0, -100, frame_helpers.get_a_tform_b(frame_tree, 'zeta', 'gamma'))
    assert _do_poses_match(110, 0, -110, frame_helpers.get_a_tform_b(frame_tree, 'zeta', 'delta'))
    assert _do_poses_match(1010, 0, -110, frame_helpers.get_a_tform_b(frame_tree, 'zeta',
                                                                      'epsilon'))
    assert _do_poses_match(0, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'zeta', 'zeta'))
    assert _do_poses_match(0, 0, 900, frame_helpers.get_a_tform_b(frame_tree, 'zeta', 'eta'))

    # eta as source frame
    assert _do_poses_match(0, 0, -1010, frame_helpers.get_a_tform_b(frame_tree, 'eta', 'alpha'))
    assert _do_poses_match(10, 0, -1010, frame_helpers.get_a_tform_b(frame_tree, 'eta', 'beta'))
    assert _do_poses_match(0, 0, -1000, frame_helpers.get_a_tform_b(frame_tree, 'eta', 'gamma'))
    assert _do_poses_match(110, 0, -1010, frame_helpers.get_a_tform_b(frame_tree, 'eta', 'delta'))
    assert _do_poses_match(1010, 0, -1010,
                           frame_helpers.get_a_tform_b(frame_tree, 'eta', 'epsilon'))
    assert _do_poses_match(0, 0, -900, frame_helpers.get_a_tform_b(frame_tree, 'eta', 'zeta'))
    assert _do_poses_match(0, 0, 0, frame_helpers.get_a_tform_b(frame_tree, 'eta', 'eta'))


def test_get_a_tform_b_se2():
    snapshot_text = """
    child_to_parent_edge_map {
      key: "vision"
      value: {
        parent_frame_name: "body"
        parent_tform_child: {
          position: {
            x: 1
            y: 0
            z: 10
          }
          rotation: {
            w: 1
            x: 0
            y: 0
            z: 0
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "special"
      value: {
        parent_frame_name: "body"
        parent_tform_child: {
          position: {
            x: 3
            y: 0
            z: 10
          }
          rotation: {
            w: 1
            x: 0
            y: 0
            z: 0
          }
        }
      }
    }
      child_to_parent_edge_map {
      key: "fiducial_404"
      value: {
        parent_frame_name: "vision"
        parent_tform_child: {
          position: {
            x: 4
            y: 0
            z: 0
          }
          rotation: {
            w: 1
            x: 0
            y: 0
            z: 0
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "body"
      value: {
        parent_frame_name: ""
      }
    }
    """
    frame_tree = _create_snapshot(snapshot_text)
    assert frame_helpers.validate_frame_tree_snapshot(frame_tree)

    # Check that a non gravity aligned frame gets rejected.
    special_tform_body = frame_helpers.get_se2_a_tform_b(frame_tree, "special", "body")
    assert special_tform_body is None

    # Check that a non-existent (gravity aligned) frame is rejected
    odom_tform_body = frame_helpers.get_se2_a_tform_b(frame_tree, "odom", "body")
    assert odom_tform_body is None

    # Check that a gravity aligned frame is used and properly computed.
    vision_tform_fiducial_404 = frame_helpers.get_se2_a_tform_b(frame_tree, "vision",
                                                                "fiducial_404")
    assert vision_tform_fiducial_404 is not None
    assert math.fabs(vision_tform_fiducial_404.position.x - 4) < 1e-6
    assert math.fabs(vision_tform_fiducial_404.position.y) < 1e-6
    assert math.fabs(vision_tform_fiducial_404.angle) < 1e-6


def test_express_velocity_new_frame():
    snapshot_text = """
    child_to_parent_edge_map {
      key: "vision"
      value: {
        parent_frame_name: "body"
        parent_tform_child: {
          position: {
            x: 1
            z: 10
          }
          rotation: {
            w: 1
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "odom"
      value: {
        parent_frame_name: "vision"
        parent_tform_child: {
          position: {
            x: 2
            z: 10
          }
          rotation: {
            w: 1
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "special"
      value: {
        parent_frame_name: "body"
        parent_tform_child: {
          position: {
            x: 3
            z: 10
          }
          rotation: {
            w: 1
          }
        }
      }
    }
      child_to_parent_edge_map {
      key: "fiducial_404"
      value: {
        parent_frame_name: "vision"
        parent_tform_child: {
          position: {
            x: 4
            z: 0
          }
          rotation: {
            w: 1
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "body"
      value: {
        parent_frame_name: ""
      }
    }
    """
    frame_tree = _create_snapshot(snapshot_text)
    assert frame_helpers.validate_frame_tree_snapshot(frame_tree)

    # Transform SE(2) velocity
    vel_of_body_in_vision = math_helpers.SE2Velocity(1, 1, 2)
    vel_of_body_in_odom = frame_helpers.express_se2_velocity_in_new_frame(
        frame_tree, "vision", "odom", vel_of_body_in_vision)
    assert vel_of_body_in_odom is not None
    assert type(vel_of_body_in_vision) == math_helpers.SE2Velocity
    assert math.fabs(vel_of_body_in_odom.angular - 2) < 1e-6
    assert math.fabs(vel_of_body_in_odom.linear.x - 1) < 1e-6
    assert math.fabs(vel_of_body_in_odom.linear.y - 5) < 1e-6

    # Transform SE(3) velocity
    vel_of_body_in_vision = math_helpers.SE3Velocity(1, 2, 3, 1, 2, 3)
    vel_of_body_in_odom = frame_helpers.express_se3_velocity_in_new_frame(
        frame_tree, "vision", "odom", vel_of_body_in_vision)
    assert vel_of_body_in_odom is not None
    assert type(vel_of_body_in_vision) == math_helpers.SE3Velocity
    assert math.fabs(vel_of_body_in_odom.angular.x - 1) < 1e-6
    assert math.fabs(vel_of_body_in_odom.angular.y - 2) < 1e-6
    assert math.fabs(vel_of_body_in_odom.angular.z - 3) < 1e-6
    assert math.fabs(vel_of_body_in_odom.linear.x - 21) < 1e-6
    assert math.fabs(vel_of_body_in_odom.linear.y - (-2)) < 1e-6
    assert math.fabs(vel_of_body_in_odom.linear.z - (-1)) < 1e-6


def test_express_velocity_types():
    snapshot_text = """
    child_to_parent_edge_map {
      key: "vision"
      value: {
        parent_frame_name: "body"
        parent_tform_child: {
          position: {
            x: 1
            z: 10
          }
          rotation: {
            w: 1
          }
        }
      }
    }
    child_to_parent_edge_map {
      key: "body"
      value: {
        parent_frame_name: ""
      }
    }
    """
    frame_tree = _create_snapshot(snapshot_text)
    assert frame_helpers.validate_frame_tree_snapshot(frame_tree)
    test_vel1 = math_helpers.SE3Velocity(1.1, 2.2, 3.3, 4.4, 5.5, 6.6)
    assert type(test_vel1.linear_velocity_x) == float
    assert test_vel1.linear_velocity_x == 1.1
    assert test_vel1.linear.x == 1.1
    test_vel2 = math_helpers.SE3Velocity(1.1, 2.2, 3.3, 4.4, 5.5, 6.6)
    test_vel2_proto = test_vel2.to_proto()

    body_vel = frame_helpers.express_se3_velocity_in_new_frame(frame_tree, "body", "vision",
                                                               test_vel2)
    assert body_vel is not None
    assert type(body_vel.linear.x) == float
    assert type(body_vel.linear_velocity_x) == float
    assert body_vel.linear_velocity_x == 56.1
    assert body_vel.linear.x == 56.1
    body_vel = frame_helpers.express_se3_velocity_in_new_frame(frame_tree, "body", "vision",
                                                               test_vel2_proto)
    assert body_vel is not None
    assert type(body_vel.linear.x) == float
    assert type(body_vel.linear_velocity_x) == float
    assert body_vel.linear_velocity_x == 56.1
    assert body_vel.linear.x == 56.1

    test_vel3 = math_helpers.SE2Velocity(1.1, 2.2, 3.3)
    test_vel3_proto = test_vel3.to_proto()
    body_vel = frame_helpers.express_se2_velocity_in_new_frame(frame_tree, "body", "vision",
                                                               test_vel3)
    assert body_vel is not None
    assert type(body_vel.linear.x) == float
    assert type(body_vel.linear_velocity_x) == float
    assert body_vel.linear_velocity_x == 1.1
    assert body_vel.linear.x == 1.1
    body_vel = frame_helpers.express_se2_velocity_in_new_frame(frame_tree, "body", "vision",
                                                               test_vel3_proto)
    assert body_vel is not None
    assert type(body_vel.linear.x) == float
    assert type(body_vel.linear_velocity_x) == float
    assert body_vel.linear_velocity_x == 1.1
    assert body_vel.linear.x == 1.1
