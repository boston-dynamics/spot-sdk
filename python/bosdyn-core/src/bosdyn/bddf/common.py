# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Basic constants and structures for parsing/writing bddf."""
import logging

import bosdyn.api.bddf_pb2 as bddf

# These are the first 4 bytes at the start of the file.
MAGIC = b'BDDF'

# These are the last 4 bytes at the end of the file.
# The little-endian 8 byte offset of the FileIndex Descriptor Block is written
#  immediately before this (-12 byte offset from the end of the file).
END_MAGIC = b'FDDB'

BLOCK_HEADER_SIZE_MASK = 0x00FFFFFFFFFFFFFF
BLOCK_HEADER_TYPE_MASK = 0xFF00000000000000

DATA_BLOCK_TYPE = 0x00  # First 4 bits of the block-header for a data block
DESCRIPTOR_BLOCK_TYPE = 0x01  # First 4 bits of the block-header for a descriptor block
END_BLOCK_TYPE = 0x02  # First 4 bits of the block-header for end-of-file material

# Message series named by a 'channel_name'

PROTOBUF_CONTENT_TYPE = 'application/protobuf'

SHA1_DIGEST_NBYTES = 20
INDEX_OFFSET_OFFSET = len(MAGIC) + SHA1_DIGEST_NBYTES + 8

LOGGER = logging.getLogger('bddf')

POD_TYPE_TO_STRUCT = {
    bddf.TYPE_INT8: 'b',
    bddf.TYPE_INT16: 'h',
    bddf.TYPE_INT32: 'i',
    bddf.TYPE_INT64: 'q',
    bddf.TYPE_UINT8: 'B',
    bddf.TYPE_UINT16: 'H',
    bddf.TYPE_UINT32: 'I',
    bddf.TYPE_UINT64: 'Q',
    bddf.TYPE_FLOAT32: 'f',
    bddf.TYPE_FLOAT64: 'd',
}

POD_TYPE_TO_NUM_BYTES = {
    bddf.TYPE_INT8: 1,
    bddf.TYPE_INT16: 2,
    bddf.TYPE_INT32: 4,
    bddf.TYPE_INT64: 8,
    bddf.TYPE_UINT8: 1,
    bddf.TYPE_UINT16: 2,
    bddf.TYPE_UINT32: 4,
    bddf.TYPE_UINT64: 8,
    bddf.TYPE_FLOAT32: 4,
    bddf.TYPE_FLOAT64: 8,
}


class DataError(Exception):
    """Errors related to the DataWriter/DataReader system."""


class AddSeriesError(Exception):
    """Errors related to registering a series in a DataWriter."""


class SeriesNotUniqueError(AddSeriesError):
    """The series_spec is not unique within the file."""


class ChecksumError(DataError):
    """The file checksum does not match the computed value."""


class DataFormatError(DataError):
    """Data to be stored has the wrong format."""


class ParseError(DataError):
    """Data file has incorrect format."""


# pylint: disable=too-few-public-methods


class SeriesIdentifier:
    """Base class for series identifier names."""

    SERIES_TYPE = ''
    KEYS = ()
