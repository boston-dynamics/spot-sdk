# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Class for reading data from a file-like object which is seekable."""
import os
import struct

from .base_data_reader import BaseDataReader
from .common import END_MAGIC, INDEX_OFFSET_OFFSET, MAGIC, ParseError


class DataReader(BaseDataReader):  # pylint: disable=too-many-instance-attributes
    """Class for reading data from a file-like object which is seekable.

    Methods raise ParseError if there is a problem with the format of the file.
    """

    def __init__(self, infile=None, filename=None):
        """
        At least one of the following arguments must be specified.

        Args:
         infile:      binary file-like object for reading (e.g., from open(fname, "rb")).
         filename:    path of input file, if applicable.
        """
        super(DataReader, self).__init__(infile, filename)
        self._series_index_to_descriptor = {}
        self._series_index_to_block_index = {}  # {series_index -> SeriesBlockIndex}
        self._read_index()

    def series_descriptor(self, series_index):
        """Return SeriesDescriptor for given series index, loading it if necessary."""
        try:
            return self._series_index_to_descriptor[series_index]
        except KeyError:
            pass

        series_block_index = self.series_block_index(series_index)
        desc = self._read_desc_block_at("series_descriptor",
                                        series_block_index.descriptor_file_offset)
        self._series_index_to_descriptor[series_index] = desc
        return desc

    def num_data_blocks(self, series_index):
        """Returns the number of data blocks for a given series in the file."""
        return len(self.series_block_index(series_index).block_entries)

    def total_bytes(self, series_index):
        """Returns the total number of bytes for data in a given series in the file."""
        return self.series_block_index(series_index).total_bytes

    def read(self, series_index, index_in_series):
        """Retrieves a message and related information from the file.

        Args:
         series_index: int selecting from which series to read the message.
         index_in_series: The index number of the message within the channel.

        Returns: DataTypeDescriptor for channel, timestamp_nsec (int), message-data (bytes)

        Raises ParseError if there is a problem with the format of the file.
        """
        series_block_index = self.series_block_index(series_index)
        msg_idx = series_block_index.block_entries[index_in_series]
        desc, data = self._read_data_block_at(msg_idx.file_offset)
        return desc, msg_idx.timestamp.ToNanoseconds(), data

    def series_block_index(self, series_index):
        """Returns the SeriesBlockIndexes for the given series_index, loading it as needed."""
        try:
            return self._series_index_to_block_index[series_index]
        except KeyError:
            pass
        # Need to load the block index for this series.
        offset = self.file_index.series_block_index_offsets[series_index]
        block_index = self._read_desc_block_at('series_block_index', offset)
        self._series_index_to_block_index[series_index] = block_index
        return block_index

    def _read_index(self):
        self._file.seek(-len(END_MAGIC), os.SEEK_END)
        end_magic = self._read(len(END_MAGIC))
        if end_magic != END_MAGIC:
            raise ParseError("Bad magic bytes at the end of the file.")
        self._file.seek(-INDEX_OFFSET_OFFSET, os.SEEK_END)
        self._index_offset, self._checksum = struct.unpack('<QQ', self._read(16))
        if self._index_offset < len(MAGIC):
            raise ParseError('Invalid offset to index: {})'.format(self._index_offset))
        self._file_index = self._read_desc_block_at("file_index", self._index_offset)
        self._spec_index = [{key: value
                             for key, value in desc.spec.items()}
                            for desc in self._file_index.series_identifiers]

    def _seek_to(self, location):
        if location < len(MAGIC):
            raise ParseError('Invalid offset for block: {})'.format(location))
        self._file.seek(location)

    def _read_data_block_at(self, location):
        self._seek_to(location)
        return self._read_data_block()

    def _read_desc_block_at(self, descriptor_type_name, location):
        self._seek_to(location)
        return self._read_desc_block(descriptor_type_name)
