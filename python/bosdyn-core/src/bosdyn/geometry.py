# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import math

from bosdyn.api.geometry_pb2 import Quaternion


class EulerZXY(object):
    """Orientation represented by Yaw('Z')-Roll('X')-Pitch('Y') order Euler angles.
    Each angle is expressed in radians."""

    def __init__(self, yaw=0.0, roll=0.0, pitch=0.0):
        self.yaw = yaw
        self.roll = roll
        self.pitch = pitch

    def to_quaternion(self):
        cy = math.cos(0.5 * self.yaw)
        cr = math.cos(0.5 * self.roll)
        cp = math.cos(0.5 * self.pitch)
        sy = math.sin(0.5 * self.yaw)
        sr = math.sin(0.5 * self.roll)
        sp = math.sin(0.5 * self.pitch)

        w = cp * cr * cy - sp * sr * sy
        x = cp * cy * sr - sp * cr * sy
        y = cp * sr * sy + cr * cy * sp
        z = cp * cr * sy + sp * cy * sr

        return Quaternion(w=w, x=x, y=y, z=z)


def _matrix_from_quaternion(q):
    rot_matrix = [[0 for x in range(3)] for y in range(3)]
    rot_matrix[0][0] = 1.0 - 2.0 * q.y * q.y - 2.0 * q.z * q.z
    rot_matrix[0][1] = 2.0 * q.x * q.y - 2.0 * q.z * q.w
    rot_matrix[0][2] = 2.0 * q.x * q.z + 2.0 * q.y * q.w
    rot_matrix[1][0] = 2.0 * q.x * q.y + 2.0 * q.z * q.w
    rot_matrix[1][1] = 1.0 - 2.0 * q.x * q.x - 2.0 * q.z * q.z
    rot_matrix[1][2] = 2.0 * q.y * q.z - 2.0 * q.x * q.w
    rot_matrix[2][0] = 2.0 * q.x * q.z - 2.0 * q.y * q.w
    rot_matrix[2][1] = 2.0 * q.y * q.z + 2.0 * q.x * q.w
    rot_matrix[2][2] = 1.0 - 2.0 * q.x * q.x - 2.0 * q.y * q.y
    return rot_matrix


def to_euler_zxy(self):
    if not isinstance(self, Quaternion):
        raise ValueError('Must input object of type Quaternion')

    m = _matrix_from_quaternion(self)
    euler_angle = EulerZXY()
    sin_roll = m[2][1]
    cos_roll = math.sqrt((m[2][0] * m[2][0]) + (m[2][2] * m[2][2]))
    euler_angle.roll = math.atan2(sin_roll, cos_roll)

    if (cos_roll < 1e-22):
        euler_angle.yaw = math.atan2(m[1][0], m[0][0])
        euler_angle.pitch = 0
    else:
        euler_angle.yaw = math.atan2(-m[0][1], m[1][1])
        euler_angle.pitch = math.atan2(-m[2][0], m[2][2])

    return euler_angle


setattr(Quaternion, "to_euler_zxy", to_euler_zxy)
