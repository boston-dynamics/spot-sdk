# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tests for bosdyn.util"""
from google.protobuf.timestamp_pb2 import Timestamp

from bosdyn import util


def test_time_converter():
    """tests for RobotTimeConverter """
    converter = util.RobotTimeConverter(100)
    timestamp = converter.robot_timestamp_from_local_nsecs(100)
    assert timestamp.seconds == 0
    assert timestamp.nanos == 200
    timestamp = converter.robot_timestamp_from_local_secs(100.0)
    assert timestamp.seconds == 100
    assert timestamp.nanos == 100


def test_timestamp_conversion():
    """Check timestamp conversion functions."""
    sec = util.timestamp_to_sec(Timestamp(seconds=2, nanos=5 * 10**8))
    assert sec == 2.5
