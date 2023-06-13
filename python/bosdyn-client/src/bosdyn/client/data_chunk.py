# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from bosdyn.api import data_chunk_pb2


def split_serialized(serialized: bytes, data_chunk_byte_size: int):
    """Split a byte string into appropriately-sized chunks."""
    start_index = 0
    end_index = 0
    total_size = len(serialized)
    while end_index < total_size:
        end_index = start_index + data_chunk_byte_size
        yield serialized[start_index:min(end_index, total_size)]
        start_index = end_index


def chunk_serialized(serialized: bytes, data_chunk_byte_size: int):
    """Yield DataChunks for the given bytes."""
    total_bytes_size = len(serialized)
    for data in split_serialized(serialized, data_chunk_byte_size):
        yield data_chunk_pb2.DataChunk(total_size=total_bytes_size, data=data)


def chunk_message(message, data_chunk_byte_size: int):
    """Take a message, and split it into data chunks

    Args:
        data_chunk_byte_size: max size of each streamed message
    """
    return chunk_serialized(message.SerializeToString(), data_chunk_byte_size)


def parse_from_chunks(iterable_chunks, out_msg):
    """Parse out a message from chunks."""
    return out_msg.ParseFromString(serialized_from_chunks(iterable_chunks))


def serialized_from_messages(iterable_messages):
    """Assemble from messages that define a DataChunk chunk field."""
    return serialized_from_strings(msg.chunk.data for msg in iterable_messages)


def serialized_from_chunks(iterable_chunks):
    """Assemble from data chunks directly without wrapper messages."""
    return serialized_from_strings(chunk.data for chunk in iterable_chunks)


def serialized_from_strings(iterable_strings):
    """Concatenate bytes together."""
    return b''.join(iterable_strings)
