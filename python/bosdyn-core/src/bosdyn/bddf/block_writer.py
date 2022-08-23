# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""BlockWriter writes basic data structures in the bddf file."""

import struct
from hashlib import sha1

import bosdyn.api.bddf_pb2 as bddf

from .common import (BLOCK_HEADER_SIZE_MASK, DATA_BLOCK_TYPE, DESCRIPTOR_BLOCK_TYPE, END_BLOCK_TYPE,
                     END_MAGIC, MAGIC, SHA1_DIGEST_NBYTES, DataFormatError)


class BlockWriter:
    """Writes data structures in the data file."""

    def __init__(self, outfile):
        self._outfile = outfile
        self._hasher = sha1()

    def tell(self):
        """Return location from start of file."""
        return self._outfile.tell()

    def write_descriptor_block(self, block):
        """Write a DescriptorBlock to the file."""
        serialized = block.SerializeToString()
        self._write_block_header(DESCRIPTOR_BLOCK_TYPE, len(serialized))
        self._write(serialized)

    def write_data_block(self, desc_block, data):
        """Write a block of data to the file."""
        serialized_desc = desc_block.SerializeToString()
        self._write_block_header(DATA_BLOCK_TYPE, len(data) + len(serialized_desc))
        self._write(struct.pack('<I', len(serialized_desc)))
        self._write(serialized_desc)
        self._write(data)

    def _write(self, data):
        self._hasher.update(data)
        self._outfile.write(data)

    def close(self):
        """Close the file, if not already closed."""
        if self.closed:
            return
        self._outfile.close()
        self._outfile = None

    @property
    def closed(self):
        """Returns True if the writer has been closed."""
        return self._outfile is None

    def write_header(self, annotations):
        """Write the header of the data file, including annotations."""
        # pylint: disable=no-member
        # Magic bytes at the start of the file
        self._write(MAGIC)
        header_block = bddf.DescriptorBlock()
        file_descriptor = header_block.file_descriptor
        file_descriptor.version.major_version = 1
        file_descriptor.version.minor_version = 0
        file_descriptor.version.patch_level = 0
        if annotations:
            file_descriptor.annotations.update(annotations)
        file_descriptor.checksum_type = bddf.FileFormatDescriptor.CHECKSUM_TYPE_SHA1
        file_descriptor.checksum_num_bytes = SHA1_DIGEST_NBYTES
        self.write_descriptor_block(header_block)

    def write_file_end(self, index_offset):
        """Write the end of the data file."""
        self._write_block_header(END_BLOCK_TYPE, 24)
        self._write(struct.pack('<Q', index_offset))
        self._outfile.write(self._hasher.digest())
        self._outfile.write(END_MAGIC)

    def _write_block_header(self, block_type, block_len):
        if block_len > BLOCK_HEADER_SIZE_MASK:
            raise DataFormatError('block size ({}) is too big (> {})'.format(
                block_len, BLOCK_HEADER_SIZE_MASK))
        block_descriptor = block_type << 56 | block_len  # mark this as a desc block
        self._write(struct.pack('<Q', block_descriptor))
