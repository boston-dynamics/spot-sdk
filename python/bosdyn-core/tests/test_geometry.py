# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import math

import pytest

from bosdyn import geometry  # noqa
from bosdyn.api.geometry_pb2 import Quaternion


def _is_near(x1, x2, thresh):
    return abs(x2 - x1) < thresh


def _dot(q1, q2):
    return q1.w * q2.w + q1.x * q2.x + q1.y * q2.y + q1.z * q2.z


@pytest.mark.parametrize("yrp,wxyz",
                         [([0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]),
                          ([math.pi, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0]),
                          ([0.0, math.pi, 0.0], [0.0, 1.0, 0.0, 0.0]),
                          ([0.0, 0.0, math.pi], [0.0, 0.0, 1.0, 0.0]),
                          ([-math.pi, 0.0, 0.0], [0.0, 0.0, 0.0, -1.0]),
                          ([0.0, -math.pi, 0.0], [0.0, -1.0, 0.0, 0.0]),
                          ([0.0, 0.0, -math.pi], [0.0, 0.0, -1.0, 0.0]),
                          ([-0.25, -0.25, 0.25], [0.9748372, -0.1073143, 0.1381593, -0.1381593]),
                          ([0.0, 0.0, 1.0], [0.8775826, 0, 0.4794255, 0]),
                          ([1.3, 1.1, 1.2], [0.3815301, 0.052105, 0.6442849, 0.6607699])])
def test_ypr_to_quaternion_proto(yrp, wxyz):
    euler_zxy = geometry.EulerZXY(yaw=yrp[0], roll=yrp[1], pitch=yrp[2])
    quat_initial = Quaternion(w=wxyz[0], x=wxyz[1], y=wxyz[2], z=wxyz[3])
    quat = euler_zxy.to_quaternion()
    assert (_is_near(abs(_dot(quat, quat_initial)), 1.0, 1e-6))

    # Do another circular conversion, make sure everything looks ok.
    euler_zxy_final = quat.to_euler_zxy()
    quat_final = euler_zxy_final.to_quaternion()
    assert (_is_near(abs(_dot(quat_final, quat_initial)), 1.0, 1e-6))
