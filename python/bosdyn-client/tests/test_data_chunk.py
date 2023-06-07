# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from bosdyn.api.graph_nav import map_pb2
from bosdyn.client import data_chunk


def test_serialized_round_trip():
    """Test round-trip of binary data."""
    input_serialized = b' '.join(bytes(i) for i in range(1000))
    chunks = list(data_chunk.chunk_serialized(input_serialized, 100))
    output_serialized = data_chunk.serialized_from_chunks(chunks)
    assert input_serialized == output_serialized


def test_single_chunk():
    """Test that small data is a single chunk."""
    input_serialized = b'meow'
    chunks = list(data_chunk.chunk_serialized(input_serialized, 100))
    assert len(chunks) == 1
    output_serialized = data_chunk.serialized_from_chunks(chunks)
    assert input_serialized == output_serialized


def test_empty_data():
    """Test that no data results in no chunks."""
    input_serialized = b''
    chunks = list(data_chunk.chunk_serialized(input_serialized, 100))
    assert len(chunks) == 0
    output_serialized = data_chunk.serialized_from_chunks(chunks)
    assert input_serialized == output_serialized


def test_messages():
    """Test using that things work with a message."""

    message = map_pb2.WaypointSnapshot()
    message.id = 'id'
    message.robot_id.nickname = 'A' * 1000

    out = map_pb2.WaypointSnapshot()
    data_chunk.parse_from_chunks(data_chunk.chunk_message(message, 100), out)

    assert out == message
