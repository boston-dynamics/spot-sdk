# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""BaseDataReader is a shared parent class for DataReader and StreamedDataReader."""
import struct

import bosdyn.api.bddf_pb2 as bddf

from .common import (BLOCK_HEADER_SIZE_MASK, BLOCK_HEADER_TYPE_MASK, DATA_BLOCK_TYPE,
                     DESCRIPTOR_BLOCK_TYPE, END_BLOCK_TYPE, LOGGER, MAGIC, SHA1_DIGEST_NBYTES,
                     ChecksumError, DataFormatError, ParseError)


class BaseDataReader:  # pylint: disable=too-many-instance-attributes
    """Shared parent class for DataReader and StreamedDataReader."""

    def __init__(self, infile=None, filename=None):
        """
        At least one of the following arguments must be specified.

        Args:
         infile:      binary file-like object for reading (e.g., from open(fname, "rb")).
         filename:    path of input file, if applicable.
        """
        self._file = infile
        self._filename = filename
        if not self._file:
            if not self._filename:
                raise ValueError("One of infile or filename must be specified")
            self._file = open(self._filename, 'rb')
        self._file_descriptor = None
        self._spec_index = None
        self._index_offset = None
        self._checksum = None
        self._read_checksum = None
        self._eof = False
        self._file_index = None
        self._read_header()

    @property
    def filename(self):
        """Return input file name, if specified, or None if not."""
        return self._filename

    @property
    def file_descriptor(self):
        """Return the file descriptor from the start of the file/stream."""
        return self._file_descriptor

    @property
    def version(self):
        """Return file version as a bosdyn.api.FileFormatVersion proto."""
        return self._file_descriptor.version

    @property
    def annotations(self):
        """Return {key -> value} dict for file annotations."""
        return self._file_descriptor.annotations

    @property
    def file_index(self):
        """Get the FileIndex proto used which describes how to access data in the file."""
        return self._file_index

    @property
    def checksum(self):
        """160-bit checksum read from the end of the file, or None if not yet read."""
        return self._checksum

    @property
    def read_checksum(self):
        """Override to compute checksum on reading, in stream-readers."""
        return self._read_checksum

    def _computed_checksum(self):  # pylint: disable=no-self-use
        """Override to compute checksum on reading, in stream-readers."""
        return None

    def series_spec_to_index(self, series_spec):
        """Given a series spec (map {key -> value}), return the series index for that series.

        Raises ValueError if no such series exists.
        """
        return self._spec_index.index(series_spec)

    def __del__(self):
        self._close()

    def __enter__(self):
        return self

    def _close(self):
        if not self._file:
            return
        self._file.close()
        self._file = None

    def __exit__(self, type_, value_, tb_):
        self._close()

    def _read(self, nbytes):
        assert nbytes
        block = self._file.read(nbytes)
        if not block:
            raise EOFError("Unexpected end of bddf file")
        return block

    def _read_header(self):
        magic = self._read(len(MAGIC))
        if magic != MAGIC:
            raise ParseError("Bad magic bytes at the start of the file.")
        self._file_descriptor = self._read_desc_block("file_descriptor")
        if (self._file_descriptor.version.major_version != 1 or
                self._file_descriptor.version.minor_version != 0 or
                self._file_descriptor.version.patch_level != 0):
            raise DataFormatError("Unsupported file version: {}.{}.{}".format(
                self._file_descriptor.version.major_version,
                self._file_descriptor.version.minor_version,
                self._file_descriptor.version.patch_level))
        checksum_type = self._file_descriptor.checksum_type
        # pylint: disable=no-member
        if checksum_type == bddf.FileFormatDescriptor.CHECKSUM_TYPE_UNKNOWN:
            raise DataFormatError("Unset checksum type in file descriptor")
        if checksum_type == bddf.FileFormatDescriptor.CHECKSUM_TYPE_NONE:
            LOGGER.debug("No checksum in bddf stream")
        elif checksum_type != bddf.FileFormatDescriptor.CHECKSUM_TYPE_SHA1:
            raise DataFormatError("Unknown checksum type {}".format(checksum_type))
        if self._file_descriptor.checksum_num_bytes != SHA1_DIGEST_NBYTES:
            raise DataFormatError("Unexpected checksum num_bytes ({} != {}).".format(
                self._file_descriptor.checksum_num_bytes, SHA1_DIGEST_NBYTES))

    def _read_proto(self, proto_type, nbytes):
        block = self._read(nbytes)
        descriptor = proto_type()
        descriptor.ParseFromString(block)
        return descriptor

    def _read_data_block(self):
        is_data, desc, data = self._read_block()
        assert is_data
        return desc, data

    def _read_desc_block(self, descriptor_type_name):
        is_data, desc, _data = self._read_block()
        assert not is_data
        assert not _data
        if desc.WhichOneof("DescriptorType") != descriptor_type_name:
            raise ParseError("Expected DescriptorType {} but got {}.".format(
                descriptor_type_name, desc.WhichOneof("DescriptorType")))
        return getattr(desc, descriptor_type_name)

    def _read_block(self):
        (block_header,) = struct.unpack('<Q', self._read(8))
        block_size = block_header & BLOCK_HEADER_SIZE_MASK
        block_type = (block_header & BLOCK_HEADER_TYPE_MASK) >> 56
        if block_type == END_BLOCK_TYPE:
            self._index_offset = struct.unpack('<Q', self._read(8))[0]
            self._read_checksum = self._computed_checksum()  # pylint: disable=assignment-from-none
            self._checksum = self._read(self._file_descriptor.checksum_num_bytes)
            self._eof = True
            # pylint: disable=no-member
            if (self._file_descriptor.checksum_type == bddf.FileFormatDescriptor.CHECKSUM_TYPE_SHA1
                    and self._read_checksum is not None and self._checksum != self._read_checksum):
                raise ChecksumError("File checksum 0x{} does not match computed value 0x{}".format(
                    ''.join('{:02X}'.format(x) for x in self._checksum),
                    ''.join('{:02X}'.format(x) for x in self._read_checksum)))
            raise EOFError("Normal end of bddf file")
        is_data_block = (block_type == DATA_BLOCK_TYPE)
        if not is_data_block:
            if block_type != DESCRIPTOR_BLOCK_TYPE:
                raise ParseError("Expected block_type {} but got {}.".format(
                    DESCRIPTOR_BLOCK_TYPE, block_type))
            return is_data_block, self._read_proto(bddf.DescriptorBlock, block_size), None

        (desc_size,) = struct.unpack('<I', self._read(4))
        if desc_size > block_size:
            raise ParseError("Data block descriptor size {} > block size {}.".format(
                desc_size, block_size))
        data_desc = self._read_proto(bddf.DataDescriptor, desc_size)
        data_size = block_size - desc_size
        data = self._read(data_size)
        return is_data_block, data_desc, data
