# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for frame helpers"""

import math
import random
from math import cos, fabs, pi, sin, sqrt

import google.protobuf.text_format
import numpy
import pytest

from bosdyn.api import geometry_pb2
from bosdyn.client.math_helpers import *

# The following set of tests are for the math_helpers
# Still needing tests: Quat class, se3_times_vec3

EPSILON = 0.0001


def test_create_se2_pose():
    # Test creating an SE2Pose from a proto with from_obj()
    proto_se2 = geometry_pb2.SE2Pose(position=geometry_pb2.Vec2(x=1, y=2), angle=.2)
    se2 = SE2Pose.from_obj(proto_se2)
    assert type(se2) == SE2Pose
    assert se2.x == proto_se2.position.x
    assert se2.y == proto_se2.position.y
    assert se2.angle == proto_se2.angle

    # Test proto-like attribute access properties
    pos = se2.position
    assert type(pos) == geometry_pb2.Vec2
    assert pos.x == proto_se2.position.x
    assert pos.y == proto_se2.position.y

    # Test going back to a proto message with to_proto()
    new_proto_se2 = se2.to_proto()
    assert type(new_proto_se2) == geometry_pb2.SE2Pose
    assert new_proto_se2.position.x == proto_se2.position.x
    assert new_proto_se2.position.y == proto_se2.position.y
    assert new_proto_se2.angle == proto_se2.angle

    # Test mutating an existing proto message to_obj()
    proto_mut_se2 = geometry_pb2.SE2Pose()
    se2.to_obj(proto_mut_se2)
    assert se2.x == proto_mut_se2.position.x
    assert se2.y == proto_mut_se2.position.y
    assert se2.angle == proto_mut_se2.angle


def compare_math_helpers_se2(calculated_se2, expected_se2):
    assert fabs(calculated_se2.x - expected_se2.x) < 1e-5
    assert fabs(calculated_se2.y - expected_se2.y) < 1e-5
    assert fabs(calculated_se2.angle - expected_se2.angle) < 1e-5


def test_se2_times_se2():
    # Multiply all-zeros
    a = SE2Pose(x=0, y=0, angle=0)
    b = SE2Pose(x=0, y=0, angle=0)
    c = a * b  #using the operator
    d = a.mult(b)  #using the function
    compare_math_helpers_se2(c, SE2Pose(x=0, y=0, angle=0))
    compare_math_helpers_se2(d, SE2Pose(x=0, y=0, angle=0))

    # A: No translation, only rotation. B: translation and rotation
    a = SE2Pose(x=0, y=0, angle=.2)
    b = SE2Pose(x=1, y=2, angle=1)
    c = a * b  #using the operator
    d = a.mult(b)  #using the function
    compare_math_helpers_se2(
        c, SE2Pose(x=1 * cos(.2) + 2 * -sin(.2), y=1 * sin(.2) + 2 * cos(.2), angle=1.2))
    compare_math_helpers_se2(
        d, SE2Pose(x=1 * cos(.2) + 2 * -sin(.2), y=1 * sin(.2) + 2 * cos(.2), angle=1.2))

    # A: No rotation, only translation. B: translation and rotation
    a = SE2Pose(x=5, y=3.3, angle=0)
    b = SE2Pose(x=1, y=2, angle=1)
    c = a * b  #using the operator
    d = a.mult(b)  #using the function
    compare_math_helpers_se2(c, SE2Pose(x=6, y=5.3, angle=1))
    compare_math_helpers_se2(d, SE2Pose(x=6, y=5.3, angle=1))

    # A: No rotation, only translation. B: No rotation, only translation.
    a = SE2Pose(x=5.2, y=3.3, angle=0)
    b = SE2Pose(x=1.3, y=2, angle=0)
    c = a * b  #using the operator
    d = a.mult(b)  #using the function
    compare_math_helpers_se2(c, SE2Pose(x=6.5, y=5.3, angle=0))
    compare_math_helpers_se2(d, SE2Pose(x=6.5, y=5.3, angle=0))

    # A: Rotation and translation. B: Only rotation, no translation.
    a = SE2Pose(x=5.2, y=3.3, angle=.2)
    b = SE2Pose(x=0, y=0, angle=.3)
    c = a * b  #using the operator
    d = a.mult(b)  #using the function
    compare_math_helpers_se2(c, SE2Pose(x=5.2, y=3.3, angle=.5))
    compare_math_helpers_se2(d, SE2Pose(x=5.2, y=3.3, angle=.5))

    # Both have rotation and translation
    a = SE2Pose(x=5.2, y=3.3, angle=.2)
    b = SE2Pose(x=1.2, y=2, angle=.3)
    c = a * b  #using the operator
    d = a.mult(b)  #using the function
    compare_math_helpers_se2(
        c,
        SE2Pose(x=5.2 + 1.2 * cos(.2) + 2 * -sin(.2), y=3.3 + 1.2 * sin(.2) + 2 * cos(.2),
                angle=.5))
    compare_math_helpers_se2(
        d,
        SE2Pose(x=5.2 + 1.2 * cos(.2) + 2 * -sin(.2), y=3.3 + 1.2 * sin(.2) + 2 * cos(.2),
                angle=.5))


def test_inverse_se2():
    # Identity/all-zeros
    a = SE2Pose(x=0, y=0, angle=0)
    inv_a = a.inverse()
    compare_math_helpers_se2(inv_a, SE2Pose(x=0, y=0, angle=0))

    # Rotation only
    b = SE2Pose(x=0, y=0, angle=1)
    inv_b = b.inverse()
    compare_math_helpers_se2(inv_b, SE2Pose(x=0, y=0, angle=-1))

    # Translation only
    c = SE2Pose(x=1, y=2, angle=0)
    inv_c = c.inverse()
    compare_math_helpers_se2(inv_c, SE2Pose(x=-1, y=-2, angle=0))

    # Translation and rotation
    d = SE2Pose(x=1, y=2, angle=1)
    inv_d = d.inverse()
    compare_math_helpers_se2(
        inv_d, SE2Pose(x=-1 * cos(1) - 2 * sin(1), y=1 * sin(1) - 2 * cos(1), angle=-1))


def test_matrices_se2():
    # Test making rotation matrix
    # No rotation se2 --> rotation matrix
    a = SE2Pose(x=0, y=0, angle=0)
    rot_a = a.to_rot_matrix()
    assert numpy.array_equal(rot_a, numpy.array([[1, 0], [0, 1]]))

    # Rotation se2 --> rotation matrix
    b = SE2Pose(x=1, y=2, angle=.5)
    rot_b = b.to_rot_matrix()
    assert rot_b.shape == (2, 2)
    assert numpy.array_equal(rot_b, numpy.array([[cos(.5), -sin(.5)], [sin(.5), cos(.5)]]))

    # Test skew matrix
    # No translation se2 --> skew matrix
    d = SE2Pose(x=1, y=2, angle=.1)
    skew_d = skew_matrix_2d(d)
    assert skew_d.shape == (1, 2)
    assert numpy.array_equal(skew_d, numpy.array([[d.y, -d.x]]))

    # Translation se2 --> skew matrix
    e = SE2Pose(x=1, y=2, angle=.1)
    skew_e = skew_matrix_2d(e)
    assert skew_e.shape == (1, 2)
    assert numpy.array_equal(skew_e, numpy.array([[e.y, -e.x]]))

    # Test making adjoint matrices
    # All zeros --> adjoint
    c = SE2Pose(x=0, y=0, angle=0)
    adjoint_c = c.to_adjoint_matrix()
    assert adjoint_c.shape == (3, 3)
    assert numpy.array_equal(
        adjoint_c, numpy.array([[cos(0), -sin(0), c.y], [sin(0), cos(0), -c.x], [0, 0, 1]]))

    # No rotation se2 --> adjoint
    f = SE2Pose(x=1, y=2, angle=0)
    adjoint_f = f.to_adjoint_matrix()
    assert adjoint_f.shape == (3, 3)
    assert numpy.array_equal(
        adjoint_f,
        numpy.array([[cos(f.angle), -sin(f.angle), f.y], [sin(f.angle),
                                                          cos(f.angle), -f.x], [0, 0, 1]]))

    # No translation se2 --> adjoint
    f = SE2Pose(x=0, y=0, angle=.2)
    adjoint_f = f.to_adjoint_matrix()
    assert adjoint_f.shape == (3, 3)
    assert numpy.array_equal(
        adjoint_f,
        numpy.array([[cos(f.angle), -sin(f.angle), f.y], [sin(f.angle),
                                                          cos(f.angle), -f.x], [0, 0, 1]]))

    # Both translation and rotation se2 --> adjoint
    f = SE2Pose(x=2, y=5, angle=.2)
    adjoint_f = f.to_adjoint_matrix()
    assert adjoint_f.shape == (3, 3)
    assert numpy.array_equal(
        adjoint_f,
        numpy.array([[cos(f.angle), -sin(f.angle), f.y], [sin(f.angle),
                                                          cos(f.angle), -f.x], [0, 0, 1]]))


def test_se2_conversions_se3_pose():
    # Test converting se2pose --> se3pose with no height input
    a = SE2Pose(x=1, y=2, angle=.5)
    se3_a = a.get_closest_se3_transform()
    assert type(se3_a) == SE3Pose
    assert a.x == se3_a.x
    assert a.y == se3_a.y
    assert se3_a.z == 0
    assert fabs(se3_a.rot.w - 0.968912) < 1e-5
    assert se3_a.rot.x == 0
    assert se3_a.rot.y == 0
    assert fabs(se3_a.rot.z - 0.2474) < 1e-5

    # Test converting se2pose --> se3pose with height input
    se3_a_with_height = a.get_closest_se3_transform(height_z=5)
    assert type(se3_a_with_height) == SE3Pose
    assert a.x == se3_a_with_height.x
    assert a.y == se3_a_with_height.y
    assert se3_a_with_height.z == 5
    assert fabs(se3_a_with_height.rot.w - 0.968912) < 1e-5
    assert se3_a_with_height.rot.x == 0
    assert se3_a_with_height.rot.y == 0
    assert fabs(se3_a_with_height.rot.z - 0.2474) < 1e-5

    # Test flattening an se3pose to se2pose
    b = SE3Pose(x=1, y=2, z=3, rot=Quat(w=1, x=0, y=.2, z=0))
    se2_b = SE2Pose.flatten(b)
    assert type(se2_b) == SE2Pose
    assert se2_b.x == 1
    assert se2_b.y == 2
    assert se2_b.angle == 0

    # Test that flattening always gives us an angle between [-pi, pi]
    random.seed(2345)
    for i in range(100):
        # Generate a random quaternion (normalizing a 4D Gaussian)
        w = random.gauss(0, 1)
        x = random.gauss(0, 1)
        y = random.gauss(0, 1)
        z = random.gauss(0, 1)
        mag = math.sqrt(w**2 + x**2 + y**2 + z**2)
        b = SE3Pose(0, 0, 0, Quat(w / mag, x / mag, y / mag, z / mag))
        se2_b = SE2Pose.flatten(b)
        assert se2_b.angle <= math.pi
        assert se2_b.angle >= -math.pi

    # Test converting se3pose --> se2pose
    c = SE3Pose(x=1, y=2, z=0, rot=Quat(w=.1, x=.3, y=.2, z=.2))
    se2_c = c.get_closest_se2_transform()
    assert type(se2_c) == SE2Pose
    assert se2_c.x == 1
    assert se2_c.y == 2
    assert fabs(se2_c.angle - 2.214297435588181) < 1e-5

    # Test creating an se3pose using from_se2() with no z height
    se3_d = SE3Pose.from_se2(SE2Pose(x=1, y=2, angle=.5))
    assert type(se3_d) == SE3Pose
    assert se3_d.x == 1
    assert se3_d.y == 2
    assert se3_d.z == 0
    assert fabs(se3_d.rot.w - 0.968912) < 1e-5
    assert se3_d.rot.x == 0
    assert se3_d.rot.y == 0
    assert fabs(se3_d.rot.z - 0.2474) < 1e-5

    # Test creating an se3pose using from_se2() with z height
    se3_e = SE3Pose.from_se2(SE2Pose(x=1, y=2, angle=.5), z=2)
    assert type(se3_e) == SE3Pose
    assert se3_e.x == 1
    assert se3_e.y == 2
    assert se3_e.z == 2
    assert fabs(se3_e.rot.w - 0.968912) < 1e-5
    assert se3_e.rot.x == 0
    assert se3_e.rot.y == 0
    assert fabs(se3_e.rot.z - 0.2474) < 1e-5


def test_create_se3_pose():
    # Test creating an SE3Pose from a proto with from_obj()
    proto_se3 = geometry_pb2.SE3Pose(position=geometry_pb2.Vec3(x=1, y=2, z=3),
                                     rotation=geometry_pb2.Quaternion(w=.1, x=.2, y=.2, z=.1))
    se3 = SE3Pose.from_obj(proto_se3)
    assert type(se3) == SE3Pose
    assert se3.x == proto_se3.position.x
    assert se3.y == proto_se3.position.y
    assert se3.z == proto_se3.position.z
    assert se3.rot.w == proto_se3.rotation.w
    assert se3.rot.x == proto_se3.rotation.x
    assert se3.rot.y == proto_se3.rotation.y
    assert se3.rot.z == proto_se3.rotation.z

    # Test proto-like attribute access properties
    pos = se3.position
    assert type(pos) == geometry_pb2.Vec3
    assert pos.x == proto_se3.position.x
    assert pos.y == proto_se3.position.y
    assert pos.z == proto_se3.position.z
    quat = se3.rotation
    assert type(quat) == Quat
    assert quat.w == proto_se3.rotation.w
    assert quat.x == proto_se3.rotation.x
    assert quat.y == proto_se3.rotation.y
    assert quat.z == proto_se3.rotation.z

    # Test going back to a proto message with to_proto()
    new_proto_se3 = se3.to_proto()
    assert type(new_proto_se3) == geometry_pb2.SE3Pose
    assert new_proto_se3.position.x == proto_se3.position.x
    assert new_proto_se3.position.y == proto_se3.position.y
    assert new_proto_se3.position.z == proto_se3.position.z
    assert new_proto_se3.rotation.w == proto_se3.rotation.w
    assert new_proto_se3.rotation.x == proto_se3.rotation.x
    assert new_proto_se3.rotation.y == proto_se3.rotation.y
    assert new_proto_se3.rotation.z == proto_se3.rotation.z

    # Test mutating an existing proto message to_obj()
    proto_mut_se3 = geometry_pb2.SE3Pose()
    se3.to_obj(proto_mut_se3)
    assert se3.x == proto_mut_se3.position.x
    assert se3.y == proto_mut_se3.position.y
    assert se3.z == proto_mut_se3.position.z
    assert se3.rot.w == proto_mut_se3.rotation.w
    assert se3.rot.x == proto_mut_se3.rotation.x
    assert se3.rot.y == proto_mut_se3.rotation.y
    assert se3.rot.z == proto_mut_se3.rotation.z

    # Test identity SE3Pose
    identity = SE3Pose.from_identity()
    assert identity.x == 0
    assert identity.y == 0
    assert identity.z == 0
    assert identity.rot.w == 1
    assert identity.rot.x == 0
    assert identity.rot.y == 0
    assert identity.rot.z == 0


def compare_math_helpers_se3(calculated_se3, expected_se3):
    assert fabs(calculated_se3.x - expected_se3.x) < 1e-5
    assert fabs(calculated_se3.y - expected_se3.y) < 1e-5
    assert fabs(calculated_se3.z - expected_se3.z) < 1e-5
    assert fabs(calculated_se3.rot.w - expected_se3.rot.w) < 1e-5
    assert fabs(calculated_se3.rot.x - expected_se3.rot.x) < 1e-5
    assert fabs(calculated_se3.rot.y - expected_se3.rot.y) < 1e-5
    assert fabs(calculated_se3.rot.z - expected_se3.rot.z) < 1e-5


def test_se3_times_se3():
    # All zeros.
    a = SE3Pose(x=0, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0))
    b = SE3Pose(x=0, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0))
    c = a * b  #using the operator
    d = a.mult(b)  #using the function
    compare_math_helpers_se3(c, SE3Pose(x=0, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0)))
    compare_math_helpers_se3(d, SE3Pose(x=0, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0)))

    # x+1 X yaw+90 -> x+1,yaw+90
    a = SE3Pose(x=1, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0))
    b = SE3Pose(x=0, y=0, z=0, rot=Quat(sqrt(2.0) / 2.0, 0, 0, sqrt(2.0) / 2.0))
    c = a * b  #using the operator
    d = a.mult(b)  #using the function
    compare_math_helpers_se3(
        c, SE3Pose(x=1, y=0, z=0, rot=Quat(w=sqrt(2.0) / 2.0, x=0, y=0, z=sqrt(2.0) / 2.0)))
    compare_math_helpers_se3(
        d, SE3Pose(x=1, y=0, z=0, rot=Quat(w=sqrt(2.0) / 2.0, x=0, y=0, z=sqrt(2.0) / 2.0)))

    # yaw+90 X x+1 -> y+1,yaw+90
    a = SE3Pose(x=0, y=0, z=0, rot=Quat(sqrt(2.0) / 2.0, 0, 0, sqrt(2.0) / 2.0))
    b = SE3Pose(x=1, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0))
    c = a * b  #using the operator
    d = a.mult(b)  #using the function
    compare_math_helpers_se3(
        c, SE3Pose(x=0, y=1, z=0, rot=Quat(w=sqrt(2.0) / 2.0, x=0, y=0, z=sqrt(2.0) / 2.0)))
    compare_math_helpers_se3(
        d, SE3Pose(x=0, y=1, z=0, rot=Quat(w=sqrt(2.0) / 2.0, x=0, y=0, z=sqrt(2.0) / 2.0)))


def test_se3_inverse():
    # Identity/all-zeros
    a = SE3Pose(x=0, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0))
    inv_a = a.inverse()
    compare_math_helpers_se3(inv_a, SE3Pose(x=0, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0)))

    # Translation only
    b = SE3Pose(x=1, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0))
    inv_b = b.inverse()
    compare_math_helpers_se3(inv_b, SE3Pose(x=-1, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0)))

    # Rotation only
    c = SE3Pose(x=0, y=0, z=0, rot=Quat(sqrt(2.0) / 2.0, 0, 0, sqrt(2.0) / 2.0))
    inv_c = c.inverse()
    compare_math_helpers_se3(
        inv_c, SE3Pose(x=0, y=0, z=0, rot=Quat(sqrt(2.0) / 2.0, 0, 0, -sqrt(2.0) / 2.0)))

    # Translation and rotation
    d = SE3Pose(x=1, y=0, z=0, rot=Quat(sqrt(2.0) / 2.0, 0, 0, sqrt(2.0) / 2.0))
    inv_d = d.inverse()
    compare_math_helpers_se3(
        inv_d, SE3Pose(x=0, y=1, z=0, rot=Quat(sqrt(2.0) / 2.0, 0, 0, -sqrt(2.0) / 2.0)))


def test_matrices_se3():
    # Test making skew matrix
    # No translation se2 --> rotation matrix
    a = SE3Pose(x=0, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0))
    skew_a = skew_matrix_3d(a)
    assert skew_a.shape == (3, 3)
    assert numpy.array_equal(skew_a, numpy.zeros((3, 3)))

    # Translation se2 --> skew matrix
    b = SE3Pose(x=1, y=2, z=3, rot=Quat(w=1, x=0, y=0, z=0))
    skew_b = skew_matrix_3d(b.position)
    assert skew_b.shape == (3, 3)
    assert numpy.array_equal(skew_b, numpy.array([[0, -3, 2], [3, 0, -1], [-2, 1, 0]]))

    # Test making adjoint matrices
    # All zeros --> adjoint
    c = SE3Pose(x=0, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0))
    adjoint_c = c.to_adjoint_matrix()
    assert adjoint_c.shape == (6, 6)
    assert numpy.array_equal(adjoint_c, numpy.identity(6))

    # No rotation se2 --> adjoint
    c = SE3Pose(x=1, y=2, z=3, rot=Quat(w=1, x=0, y=0, z=0))
    adjoint_c = c.to_adjoint_matrix()
    assert adjoint_c.shape == (6, 6)
    assert numpy.array_equal(
        adjoint_c,
        numpy.array([[1, 0, 0, 0, -3, 2], [0, 1, 0, 3, 0, -1], [0, 0, 1, -2, 1, 0],
                     [0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 1, 0], [0, 0, 0, 0, 0, 1]]))

    # No translation se2 --> adjoint
    c = SE3Pose(x=0, y=0, z=0, rot=Quat(w=.1, x=.2, y=.3, z=.4))
    adjoint_c = c.to_adjoint_matrix()
    assert adjoint_c.shape == (6, 6)
    print(adjoint_c)
    assert numpy.allclose(
        adjoint_c,
        numpy.array([[.5, .04, .22, 0, 0, 0], [.2, .6, .2, 0, 0, 0], [.1, .28, .74, 0, 0, 0],
                     [0, 0, 0, .5, .04, .22], [0, 0, 0, .2, .6, .2], [0, 0, 0, .1, .28, .74]]))

    # Both translation and rotation se2 --> adjoint
    c = SE3Pose(x=1, y=2, z=3, rot=Quat(w=.1, x=.2, y=.3, z=.4))
    adjoint_c = c.to_adjoint_matrix()
    assert adjoint_c.shape == (6, 6)
    assert numpy.allclose(
        adjoint_c,
        numpy.array([[.5, .04, .22, -.4, -1.24, .88], [.2, .6, .2, 1.4, -.16, -.08],
                     [.1, .28, .74, -.8, .52, -.24], [0, 0, 0, .5, .04, .22], [0, 0, 0, .2, .6, .2],
                     [0, 0, 0, .1, .28, .74]]))


def test_create_se2_vel():
    # Test creating an SE2Velocity from a proto with from_obj()
    proto_se2 = geometry_pb2.SE2Velocity(linear=geometry_pb2.Vec2(x=1, y=2), angular=.2)
    se2 = SE2Velocity.from_obj(proto_se2)
    assert type(se2) == SE2Velocity
    assert se2.linear_velocity_x == proto_se2.linear.x
    assert se2.linear_velocity_y == proto_se2.linear.y
    assert se2.angular_velocity == proto_se2.angular

    # Test proto-like attribute access properties
    lin = se2.linear
    assert type(lin) == geometry_pb2.Vec2
    assert lin.x == proto_se2.linear.x
    assert lin.y == proto_se2.linear.y
    ang = se2.angular
    assert ang == proto_se2.angular

    # Test going back to a proto message with to_proto()
    new_proto_se2 = se2.to_proto()
    assert type(new_proto_se2) == geometry_pb2.SE2Velocity
    assert new_proto_se2.linear.x == proto_se2.linear.x
    assert new_proto_se2.linear.y == proto_se2.linear.y
    assert new_proto_se2.angular == proto_se2.angular

    # Test mutating an existing proto message to_obj()
    proto_mut_se2 = geometry_pb2.SE2Velocity()
    se2.to_obj(proto_mut_se2)
    assert se2.linear_velocity_x == proto_mut_se2.linear.x
    assert se2.linear_velocity_y == proto_mut_se2.linear.y
    assert se2.angular_velocity == proto_mut_se2.angular

    # Test creating the velocity vector
    vec = se2.to_vector()
    assert type(vec) == numpy.ndarray
    assert vec[0] == proto_se2.linear.x
    assert vec[1] == proto_se2.linear.y
    assert vec[2] == proto_se2.angular

    # Test creating the SE2Velocity from a array
    vel_arr = numpy.array([1, 2, 3]).reshape((3, 1))
    se2 = SE2Velocity.from_vector(vel_arr)
    assert type(se2) == SE2Velocity
    assert se2.linear_velocity_x == 1
    assert se2.linear_velocity_y == 2
    assert se2.angular_velocity == 3

    # Test creating the SE2Velocity from a list
    vel_list = [1, 2, 3]
    se2 = SE2Velocity.from_vector(vel_list)
    assert type(se2) == SE2Velocity
    assert se2.linear_velocity_x == 1
    assert se2.linear_velocity_y == 2
    assert se2.angular_velocity == 3


def test_create_se3_vel():
    # Test creating an SE3Velocity from a proto with from_obj()
    proto_se3 = geometry_pb2.SE3Velocity(linear=geometry_pb2.Vec3(x=1, y=2, z=3),
                                         angular=geometry_pb2.Vec3(x=1, y=2, z=3))
    se3 = SE3Velocity.from_obj(proto_se3)
    assert type(se3) == SE3Velocity
    assert se3.linear_velocity_x == proto_se3.linear.x
    assert se3.linear_velocity_y == proto_se3.linear.y
    assert se3.linear_velocity_z == proto_se3.linear.z
    assert se3.angular_velocity_x == proto_se3.angular.x
    assert se3.angular_velocity_y == proto_se3.angular.y
    assert se3.angular_velocity_z == proto_se3.angular.z

    # Test proto-like attribute access properties
    lin = se3.linear
    assert type(lin) == geometry_pb2.Vec3
    assert lin.x == proto_se3.linear.x
    assert lin.y == proto_se3.linear.y
    assert lin.z == proto_se3.linear.z
    ang = se3.angular
    assert type(ang) == geometry_pb2.Vec3
    assert ang.x == proto_se3.angular.x
    assert ang.y == proto_se3.angular.y
    assert ang.z == proto_se3.angular.z

    # Test going back to a proto message with to_proto()
    new_proto_se3 = se3.to_proto()
    assert type(new_proto_se3) == geometry_pb2.SE3Velocity
    assert new_proto_se3.linear.x == proto_se3.linear.x
    assert new_proto_se3.linear.y == proto_se3.linear.y
    assert new_proto_se3.linear.z == proto_se3.linear.z
    assert new_proto_se3.angular.x == proto_se3.angular.x
    assert new_proto_se3.angular.y == proto_se3.angular.y
    assert new_proto_se3.angular.z == proto_se3.angular.z

    # Test mutating an existing proto message to_obj()
    proto_mut_se3 = geometry_pb2.SE3Velocity()
    se3.to_obj(proto_mut_se3)
    assert type(proto_mut_se3) == geometry_pb2.SE3Velocity
    assert proto_mut_se3.linear.x == proto_se3.linear.x
    assert proto_mut_se3.linear.y == proto_se3.linear.y
    assert proto_mut_se3.linear.z == proto_se3.linear.z
    assert proto_mut_se3.angular.x == proto_se3.angular.x
    assert proto_mut_se3.angular.y == proto_se3.angular.y
    assert proto_mut_se3.angular.z == proto_se3.angular.z

    # Test creating the velocity vector
    vec = se3.to_vector()
    assert type(vec) == numpy.ndarray
    assert vec[0] == proto_se3.linear.x
    assert vec[1] == proto_se3.linear.y
    assert vec[2] == proto_se3.linear.z
    assert vec[3] == proto_se3.angular.x
    assert vec[4] == proto_se3.angular.y
    assert vec[5] == proto_se3.angular.z

    # Test creating the SE3Velocity from a array
    vel_arr = numpy.array([1, 2, 3, 4, 5, 6]).reshape((6, 1))
    se3 = SE3Velocity.from_vector(vel_arr)
    assert type(se3) == SE3Velocity
    assert se3.linear_velocity_x == 1
    assert se3.linear_velocity_y == 2
    assert se3.linear_velocity_z == 3
    assert se3.angular_velocity_x == 4
    assert se3.angular_velocity_y == 5
    assert se3.angular_velocity_z == 6

    # Test creating the SE2Velocity from a list
    vel_list = [1, 2, 3, 4, 5, 6]
    se3 = SE3Velocity.from_vector(vel_list)
    assert type(se3) == SE3Velocity
    assert se3.linear_velocity_x == 1
    assert se3.linear_velocity_y == 2
    assert se3.linear_velocity_z == 3
    assert se3.angular_velocity_x == 4
    assert se3.angular_velocity_y == 5
    assert se3.angular_velocity_z == 6


def compare_se2_velocity(expected_vel, calculated_vel):
    assert fabs(expected_vel.linear_velocity_x - calculated_vel.linear_velocity_x) < 1e-6
    assert fabs(expected_vel.linear_velocity_y - calculated_vel.linear_velocity_y) < 1e-6
    assert fabs(expected_vel.angular_velocity - calculated_vel.angular_velocity) < 1e-6


def compare_se3_velocity(expected_vel, calculated_vel, threshold=1e-6):
    assert fabs(expected_vel.linear_velocity_x - calculated_vel.linear_velocity_x) < threshold
    assert fabs(expected_vel.linear_velocity_y - calculated_vel.linear_velocity_y) < threshold
    assert fabs(expected_vel.linear_velocity_z - calculated_vel.linear_velocity_z) < threshold
    assert fabs(expected_vel.angular_velocity_x - calculated_vel.angular_velocity_x) < threshold
    assert fabs(expected_vel.angular_velocity_y - calculated_vel.angular_velocity_y) < threshold
    assert fabs(expected_vel.angular_velocity_z - calculated_vel.angular_velocity_z) < threshold


def test_transform_velocity():
    # Note this test assumes the adjoint matrix test passes.
    # Identity SE(2)
    a = SE2Pose(x=0, y=0, angle=0)
    vel_a = SE2Velocity(1, 2, .2)
    adjoint_a = a.to_adjoint_matrix()
    transformed_a = transform_se2velocity(adjoint_a, vel_a)
    compare_se2_velocity(vel_a, transformed_a)

    # Identity SE(3)
    b = SE3Pose(x=0, y=0, z=0, rot=Quat(w=1, x=0, y=0, z=0))
    vel_b = SE3Velocity(1, 2, 3, .1, .2, .3)
    adjoint_b = b.to_adjoint_matrix()
    print(type(vel_b))
    print(type(vel_b) == SE3Velocity)
    transformed_b = transform_se3velocity(adjoint_b, vel_b)
    print(transformed_b)
    compare_se3_velocity(vel_b, transformed_b)

    # Full SE(2) transformation
    c = SE2Pose(2, 3, pi)
    vel_c = SE2Velocity(1, 1, 2)
    adjoint_c = c.to_adjoint_matrix()
    transformed_c = transform_se2velocity(adjoint_c, vel_c)
    compare_se2_velocity(transformed_c, SE2Velocity(5, -5, 2))

    # Full SE(3) transformations
    d = SE3Pose(x=1, y=2, z=1, rot=Quat(.707, .707, 0, 0))
    vel_d = SE3Velocity(1, 2, 3, 1, 2, 3)
    adjoint_d = d.to_adjoint_matrix()
    transformed_d = transform_se3velocity(adjoint_d, vel_d)
    compare_se3_velocity(
        transformed_d,
        SE3Velocity(1 + 1.99909 * 2 + 1.0003 * 3,
                    2 * .000302 + 5 * (-0.999698) + 1 + 3 * (-.000302),
                    -0.999698 + 5 * .000302 + -2, 1, .000302 * 2 - 0.999698 * 3,
                    0.999698 * 2 + .000302 * 3), 1e-4)


def test_quat_to_euler():
    # Converted quat_0 should result in the yaw, pitch, roll shown in euler_zyx_0
    quat_0 = Quat(1, 0, 0, 0)
    euler_zyx_0 = (0, 0, 0)
    euler_zyx = quat_to_eulerZYX(quat_0)
    assert euler_zyx_0 == euler_zyx

    # Converted quat_1 should result in the yaw, pitch, roll shown in euler_zyx_1
    quat_1 = Quat(0.0, 1.0, 0.0, 0.0)
    euler_zyx_1 = [0, 0, 180]
    euler_zyx = [math.degrees(a) for a in quat_to_eulerZYX(quat_1)]
    assert euler_zyx_1 == euler_zyx

    # Converted quat_2 should result in the yaw, pitch, roll shown in euler_zyx_2
    quat_2 = Quat(0.0, 0.0, 1.0, 0.0)
    euler_zyx_2 = [180, 0, 180]
    euler_zyx = [math.degrees(a) for a in quat_to_eulerZYX(quat_2)]
    assert euler_zyx_2 == euler_zyx

    # Converted quat_3 should result in the yaw, pitch, roll shown in euler_zyx_3
    quat_3 = Quat(0.0, 0.0, 0.0, 1.0)
    euler_zyx_3 = [180, 0, 0]
    euler_zyx = [math.degrees(a) for a in quat_to_eulerZYX(quat_3)]
    assert euler_zyx_3 == euler_zyx

    # Converted quat_4 should result in the yaw, pitch, roll shown in euler_zyx_4
    quat_4 = Quat(0.183, 0.365, 0.548, 0.730)
    euler_zyx_4 = [134.9686404, -19.4120353, 81.9012582]
    euler_zyx = [math.degrees(a) for a in quat_to_eulerZYX(quat_4)]
    for i in range(3):
        assert abs(euler_zyx_4[i] - euler_zyx[i]) < 0.1

    # Including or excluding the roll should not affect yaw or pitch
    quat_5 = Quat(0.8098232, 0.069881, 0.4989135, 0.3006466)  # with roll
    euler_zyx_5 = quat_to_eulerZYX(quat_5)
    euler_zyx_5 = [round(a, 3) for a in euler_zyx_5]
    quat_6 = Quat(0.7848856, -0.2113091, 0.3659982, 0.4531539)  # without roll
    euler_zyx_6 = quat_to_eulerZYX(quat_6)
    euler_zyx_6 = [round(a, 3) for a in euler_zyx_6]
    assert euler_zyx_5[0] == euler_zyx_6[0]
    assert euler_zyx_5[1] == euler_zyx_6[1]


def test_vec2():
    a_proto = geometry_pb2.Vec2(x=1, y=2)
    b_proto = geometry_pb2.Vec2(x=-3, y=6)

    # Test from_proto()
    a = Vec2.from_proto(a_proto)
    b = Vec2.from_proto(b_proto)

    # Test addition operand
    result = a + b
    assert result.x == -2
    assert result.y == 8

    # Test subtraction operand
    result = a - b
    assert result.x == 4
    assert result.y == -4

    # Test mult operand
    result = a * 3
    assert result.x == 3
    assert result.y == 6

    # Test division operand
    result = a / 0.5 + b
    assert result.x == -1
    assert result.y == 10

    # Test negative operand
    result = -b
    assert result.x == 3
    assert result.y == -6

    # Test rmult
    result = -2 * b
    assert result.x == 6
    assert result.y == -12

    # Test to_proto()
    a_proto_2 = a.to_proto()
    assert a_proto_2.x == a_proto.x
    assert a_proto_2.y == a_proto.y

    # Test .length()
    assert a.length() == sqrt(5)

    # Test .dot()
    assert a.dot(b) == 9

    # Test .cross()
    assert a.cross(b) == 12
    assert b.cross(a) == -12


def test_vec3():
    a_proto = geometry_pb2.Vec3(x=1, y=2, z=3)
    b_proto = geometry_pb2.Vec3(x=-3, y=6, z=-9)

    # Test from_proto()
    a = Vec3.from_proto(a_proto)
    b = Vec3.from_proto(b_proto)

    # Test addition operand
    result = a + b
    assert result.x == -2
    assert result.y == 8
    assert result.z == -6

    # Test subtraction operand
    result = a - b
    assert result.x == 4
    assert result.y == -4
    assert result.z == 12

    # Test mult operand
    result = a * 3
    assert result.x == 3
    assert result.y == 6
    assert result.z == 9

    # Test division operand
    result = a / 0.5 + b
    assert result.x == -1
    assert result.y == 10
    assert result.z == -3

    # Test negative operand
    result = -b
    assert result.x == 3
    assert result.y == -6
    assert result.z == 9

    # Test rmult
    result = -2 * b
    assert result.x == 6
    assert result.y == -12
    assert result.z == 18

    # Test to_proto()
    a_proto_2 = a.to_proto()
    assert a_proto_2.x == a_proto.x
    assert a_proto_2.y == a_proto.y
    assert a_proto_2.z == a_proto.z

    # Test .length()
    assert a.length() == sqrt(14)

    # Test .dot()
    assert a.dot(b) == -18

    # Test .cross()
    assert a.cross(b).x == -36
    assert a.cross(b).y == 0
    assert a.cross(b).z == 12
    assert b.cross(a).x == 36
    assert b.cross(a).y == 0
    assert b.cross(a).z == -12


def test_vec3_cross():
    a = Vec3(x=1, y=0, z=0)
    b = Vec3(x=1, y=0, z=0)
    assert a.cross(b).x == 0
    assert a.cross(b).y == 0
    assert a.cross(b).z == 0

    b = Vec3(x=0, y=1, z=0)
    assert a.cross(b).x == 0
    assert a.cross(b).y == 0
    assert a.cross(b).z == 1

    b = Vec3(x=0, y=0, z=1)
    assert a.cross(b).x == 0
    assert a.cross(b).y == -1
    assert a.cross(b).z == 0

    a = Vec3(x=0, y=1, z=0)
    b = Vec3(x=1, y=0, z=0)
    assert a.cross(b).x == 0
    assert a.cross(b).y == 0
    assert a.cross(b).z == -1

    b = Vec3(x=0, y=1, z=0)
    assert a.cross(b).x == 0
    assert a.cross(b).y == 0
    assert a.cross(b).z == 0

    b = Vec3(x=0, y=0, z=1)
    assert a.cross(b).x == 1
    assert a.cross(b).y == 0
    assert a.cross(b).z == 0

    a = Vec3(x=0, y=0, z=1)
    b = Vec3(x=1, y=0, z=0)
    assert a.cross(b).x == 0
    assert a.cross(b).y == 1
    assert a.cross(b).z == 0

    b = Vec3(x=0, y=1, z=0)
    assert a.cross(b).x == -1
    assert a.cross(b).y == 0
    assert a.cross(b).z == 0

    b = Vec3(x=0, y=0, z=1)
    assert a.cross(b).x == 0
    assert a.cross(b).y == 0
    assert a.cross(b).z == 0


@pytest.mark.parametrize('x, y, angle', [
    (3, 7, 1.047198),
    (5, 5, -1.047198),
])
def test_se2_to_and_from_matrix(x, y, angle):
    # Test that going to and from a matrix doesn't change anything
    se2 = SE2Pose(x, y, angle)
    new_se2 = SE2Pose.from_matrix(se2.to_matrix())
    assert abs(new_se2.x - x) < EPSILON
    assert abs(new_se2.y - y) < EPSILON
    assert angle_diff(new_se2.angle, angle) < EPSILON


def test_se2_angle_stuff():
    # Test that we handle large angles and wrap around
    random.seed(1234)
    for i in range(100):
        # Generate SE2Pose with potentially large positive or negative angles
        angle1 = random.uniform(-math.pi, math.pi)
        angle2 = random.uniform(-math.pi, math.pi)
        x1 = random.uniform(-2.0, 2.0)
        y1 = random.uniform(-2.0, 2.0)
        x2 = random.uniform(-2.0, 2.0)
        y2 = random.uniform(-2.0, 2.0)
        p1 = random.randint(-20, 20) * 2 * math.pi
        p2 = random.randint(-20, 20) * 2 * math.pi

        # Check that we get 0 when we multiply a pose with its inverse
        should_be_identity = SE2Pose(x1, y1, angle1) * SE2Pose(x1, y1, angle1 + p1).inverse()
        assert abs(should_be_identity.angle) < EPSILON
        assert abs(should_be_identity.x) < EPSILON
        assert abs(should_be_identity.y) < EPSILON

        # Check that we don't get a giant angle when multiplying poses together
        new_pose = SE2Pose(x1, y1, angle1 + p1) * SE2Pose(x2, y2, angle2 + p2)
        assert new_pose.angle <= math.pi
        assert new_pose.angle >= -math.pi
        assert abs(new_pose.angle - recenter_angle_mod(angle1 + angle2, 0.0)) < EPSILON


@pytest.mark.parametrize(
    'desired_x, desired_y, angle',
    [
        # Rotate 45 degrees, and see an offset of y on x axis
        (3, 7, 0.785398),
        # Rotate -45 degrees, and see an offset of 2 on x axis
        (5, 5, -0.785398),
    ])
def test_se2_vec2_mult(desired_x, desired_y, angle):
    vec_proto = geometry_pb2.Vec2(x=sqrt(2), y=sqrt(2))
    vec = Vec2.from_proto(vec_proto)
    se2_proto = geometry_pb2.SE2Pose(position=geometry_pb2.Vec2(x=3, y=5), angle=angle)
    se2 = SE2Pose.from_proto(se2_proto)
    result = se2 * vec
    assert abs(result.x - desired_x) < EPSILON
    assert abs(result.y - desired_y) < EPSILON
    assert isinstance(result, Vec2)


def test_se3_vec3_mult():
    vec_proto = geometry_pb2.Vec3(x=sqrt(3), y=sqrt(3), z=sqrt(3))
    vec = Vec3.from_proto(vec_proto)

    root2o2 = sqrt(2) / 2
    se3_proto = geometry_pb2.SE3Pose(
        position=geometry_pb2.Vec3(x=1, y=2, z=3),
        rotation=geometry_pb2.Quaternion(w=0, x=root2o2, y=0, z=-root2o2))
    se3 = SE3Pose.from_proto(se3_proto)
    result = se3 * vec
    assert abs(result.x - -0.7320508) < EPSILON
    assert abs(result.y - 0.2679491) < EPSILON
    assert abs(result.z - 1.2679491) < EPSILON
    assert isinstance(result, Vec3)


def test_se2_vec2_mult_exceptions():
    vec_proto = geometry_pb2.Vec2(x=sqrt(2), y=sqrt(2))
    vec = Vec2.from_proto(vec_proto)
    se2_proto = geometry_pb2.SE2Pose(position=geometry_pb2.Vec2(x=3, y=5), angle=0.7)
    se2 = SE2Pose.from_proto(se2_proto)
    with pytest.raises(TypeError):
        vec + " "
    with pytest.raises(TypeError):
        vec - " "
    with pytest.raises(TypeError):
        vec * " "
    with pytest.raises(TypeError):
        vec / " "
    with pytest.raises(TypeError):
        " " * vec
    with pytest.raises(TypeError):
        se2 * ""


def test_se3_vec3_mult_exceptions():
    vec_proto = geometry_pb2.Vec3(x=sqrt(2), y=sqrt(2), z=10)
    vec = Vec3.from_proto(vec_proto)
    se3 = SE3Pose.from_proto(geometry_pb2.SE3Pose())
    with pytest.raises(TypeError):
        vec + " "
    with pytest.raises(TypeError):
        vec - " "
    with pytest.raises(TypeError):
        vec * " "
    with pytest.raises(TypeError):
        vec / " "
    with pytest.raises(TypeError):
        " " * vec
    with pytest.raises(TypeError):
        se3 * ""
