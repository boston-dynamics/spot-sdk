# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Data reader which reads the file format from a stream, without seeking."""
from hashlib import sha1

from .base_data_reader import BaseDataReader
from .common import ParseError
from .file_indexer import FileIndexer


class StreamDataReader(BaseDataReader):
    """Data reader which reads the file format from a stream, without seeking."""

    def __init__(self, outfile):
        """
        Args:
         outfile:      binary file-like object for reading (e.g., from open(fname, "rb")).
        """
        self._hasher = sha1()  # This computes a checksum
        super(StreamDataReader, self).__init__(outfile)
        self._indexer = FileIndexer()
        self._series_index_to_block_index = {}  # {series_index -> SeriesBlockIndex}

    def _read(self, nbytes):
        block = BaseDataReader._read(self, nbytes)
        self._hasher.update(block)
        return block

    @property
    def read_checksum(self):
        """64-bit checksum read from the end of the file, or None if not yet read."""
        return self._read_checksum

    @property
    def stream_file_index(self):
        """Return the file index as parsed from the stream."""
        return self._indexer.file_index

    def _computed_checksum(self):
        return self._hasher.digest()

    def series_descriptor(self, series_index):
        """Return SeriesDescriptor for given series index.

        Returns KeyError if no such series exists.
        """
        return self._indexer.series_descriptor(series_index)

    def read_data_block(self):
        """Read and return next data block.

        Returns: DataDescriptor, SeriesDescriptor, data (bytes)

        Raises ParseError if there is a problem with the format of the file,
               EOFError if the end of the file is reached.
        """
        while True:
            is_data, desc, data = self.read_next_block()
            if not is_data:
                continue
            return desc, self.series_descriptor(desc.series_index), data

    def read_next_block(self):
        """Read and return next block.

        Returns: True, DataDescriptor, data (bytes)   for data block
        Returns: False, DescriptorBlock, None         for descriptor block

        Raises ParseError if there is a problem with the format of the file,
               EOFError if the end of the file is reached.
        """
        file_offset = self._file.tell()
        try:
            is_data, desc, data = self._read_block()
        except EOFError as err:
            self._eof = True
            raise err
        if is_data:
            self._indexer.index_data_block(desc.series_index, desc.timestamp.ToNanoseconds(),
                                           len(data), file_offset, desc.additional_indexes)
        else:
            desc_type = desc.WhichOneof("DescriptorType")
            if desc_type == 'file_index':
                self._file_index = desc.file_index
            elif desc_type == 'file_descriptor':
                pass  # Don't expect this after the first block, though.
            elif desc_type == 'series_descriptor':
                series_descriptor = desc.series_descriptor
                self._indexer.add_series_descriptor(series_descriptor, file_offset)
            elif desc_type == 'series_block_index':
                series_block_index = desc.series_block_index
                self._series_index_to_block_index[
                    series_block_index.series_index] = series_block_index
            else:
                raise ParseError("Unknown DescriptorType %s" % desc_type)
        return is_data, desc, data

    @property
    def series_block_indexes(self):
        """Returns the current list of SeriesBlockIndexes: series_index -> SeriesBlockIndex."""
        return self._indexer.series_block_indexes

    def series_block_index(self, series_index):
        """Returns the SeriesBlockIndexes for the given series_index."""
        return self._indexer.series_block_indexes[series_index]

    @property
    def eof(self):
        """Returns True if all blocks in the file have been read."""
        return self._eof
