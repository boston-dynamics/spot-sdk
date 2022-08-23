# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tests for the arm surface contact client."""
import pytest
from google.protobuf import timestamp_pb2

from bosdyn.api import arm_surface_contact_service_pb2
from bosdyn.client.arm_surface_contact import EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME
from bosdyn.client.robot_command import _edit_proto


def test_edit_timestamps():

    def _set_new_time(key, proto):
        """If proto has a field named key, fill set it to end_time_secs as robot time. """
        if key not in proto.DESCRIPTOR.fields_by_name:
            return  # No such field in the proto to be set to the end-time.
        end_time = getattr(proto, key)
        end_time.CopyFrom(timestamp_pb2.Timestamp(seconds=10))

    command = arm_surface_contact_service_pb2.ArmSurfaceContactCommand()
    command.request.pose_trajectory_in_task.reference_time.seconds = 25
    command.request.gripper_command.trajectory.reference_time.seconds = 25
    command.request.maximum_acceleration.value = 5
    _edit_proto(command, EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME, _set_new_time)
    assert command.request.pose_trajectory_in_task.reference_time.seconds == 10
    assert command.request.gripper_command.trajectory.reference_time.seconds == 10
    assert command.request.maximum_acceleration.value == 5
