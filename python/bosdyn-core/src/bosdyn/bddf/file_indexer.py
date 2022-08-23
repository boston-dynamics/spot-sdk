# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A FileIndexer is an object which keeps an index of series and blocks within series"""

import struct
from hashlib import sha1

import bosdyn.api.bddf_pb2 as bddf

from .common import AddSeriesError, DataFormatError, SeriesNotUniqueError


def _hasher_to_uint64(hasher):
    return struct.unpack('>Q', hasher.digest()[0:8])[0]


class FileIndexer:
    """An object which keeps an index of series and blocks within series.

    It can write a block index at the end of a data file.
    """

    def __init__(self):
        # DescriptorBlock proto for the FileIndex
        self._descriptor_index = bddf.DescriptorBlock()
        self._series_descriptors = []  # series_idx -> SeriesDescriptor
        self._series_block_indexes = []  # series_index -> SeriesBlockIndex

    @property
    def file_index(self):
        """Get the FileIndex proto used which describes how to access data in the file."""
        return self._descriptor_index.file_index  # pylint: disable=no-member

    @property
    def descriptor_index(self):
        """Get the Descriptor proto containing the FileIndex."""
        return self._descriptor_index

    @property
    def series_block_indexes(self):
        """Returns the current list of SeriesBlockIndexes: series_index -> SeriesBlockIndex."""
        return self._series_block_indexes

    def series_descriptor(self, series_index):
        """Return SeriesDescriptor for given series index."""
        return self._series_descriptors[series_index]

    @staticmethod
    def series_identifier_to_hash(series_identifier):
        """Given a SeriesIdentifier, return a 64-bit hash."""
        hasher = sha1()
        hasher.update(series_identifier.series_type.encode('utf-8'))
        for key in sorted(series_identifier.spec.keys()):
            hasher.update(key.encode('utf-8'))
            hasher.update((series_identifier.spec[key]).encode('utf-8'))
        return _hasher_to_uint64(hasher)

    def add_series_descriptor(self, series_descriptor, series_block_file_offset):
        """Add the given series_descriptor to the index, with the given file offset.

        Args:
         series_descriptor         SeriesDescriptor to add to the index
         series_block_file_offset  Location in file where SeriesDescriptor will be written, or
                                    was read from.
        """
        assert series_descriptor.series_index == len(self._series_descriptors)
        # Update the file index.
        self.file_index.series_identifiers.add().CopyFrom(series_descriptor.series_identifier)
        self.file_index.series_identifier_hashes.append(series_descriptor.identifier_hash)
        self._series_descriptors.append(series_descriptor)
        self._series_block_indexes.append(
            bddf.SeriesBlockIndex(series_index=series_descriptor.series_index,
                                  descriptor_file_offset=series_block_file_offset))

    def add_series(  # pylint: disable=too-many-arguments
            self, series_type, series_spec, message_type, pod_type, annotations,
            additional_index_names, writer):
        """Register a new series for messages for a DataWriter.

        Args:
         series_type:   the kind of spec, corresponding to the set of keys expected in series_spec.
         series_spec:   dict of {key (string) -> value (string)| describing the series.
         message_type:  MessageTypeDescriptor (need EITHER this OR pod_type)
         pod_type:      PodTypeDescriptor (need EITHER this OR pod_type)
         annotations:   optional dict of key (string) -> value (string) pairs to
                            associate with the message channel
         additional_index_names: names of additional timestamps to store with
                                        each message (list of string).
         writer:        BlockWriter owned by the DataWriter.

        Returns series id (int).

        Raises SeriesNotUniqueError if a series matching series_spec is already added.
        """
        # pylint: disable=no-member

        series_index = len(self._series_descriptors)

        # Write the descriptor block.
        descriptor = bddf.DescriptorBlock()
        series_descriptor = descriptor.series_descriptor
        series_descriptor.series_index = series_index

        series_identifier = series_descriptor.series_identifier
        series_identifier.series_type = series_type
        series_identifier.spec.update(series_spec)

        series_descriptor.identifier_hash = self.series_identifier_to_hash(series_identifier)

        # Ensure the series_spec is unique in the file.
        for prev_series_identifier in self.file_index.series_identifiers:
            if prev_series_identifier.spec == series_identifier.spec:
                raise SeriesNotUniqueError(
                    "Spec %s is not unique within the data file" % series_identifier.spec)

        if message_type:
            if pod_type:
                raise AddSeriesError("Specified both message_type ({}) and pod_type ({})".format(
                    message_type, pod_type))
            series_descriptor.message_type.CopyFrom(message_type)
        else:
            if not pod_type:
                raise AddSeriesError("Specified neither message_type nor pod_type")
            series_descriptor.pod_type.CopyFrom(pod_type)
        if annotations:
            series_descriptor.annotations.update(annotations)
        if additional_index_names:
            for name in additional_index_names:
                series_descriptor.additional_index_names.append(name)
        series_block_file_offset = writer.tell()
        writer.write_descriptor_block(descriptor)
        self.add_series_descriptor(series_descriptor, series_block_file_offset)
        return series_index

    def index_data_block(  # pylint: disable=too-many-arguments
            self, series_index, timestamp_nsec, file_offset, nbytes, additional_indexes):
        """Add a an entry to the data block index of the series identified by series_index."""
        series_block_index = self._series_block_indexes[series_index]
        block_entry = series_block_index.block_entries.add(file_offset=file_offset)
        block_entry.timestamp.FromNanoseconds(timestamp_nsec)
        series_block_index.total_bytes += nbytes
        if additional_indexes:
            for idx_val in additional_indexes:
                block_entry.additional_indexes.append(idx_val)  # pylint: disable=no-member

    def make_data_descriptor(self, series_index, timestamp_nsec, additional_indexes):
        """Return DataDescriptor for writing a data block, and add the block to the series index."""
        series_descriptor = self._series_descriptors[series_index]
        data_descriptor = bddf.DataDescriptor(series_index=series_index)
        data_descriptor.timestamp.FromNanoseconds(timestamp_nsec)  # pylint: disable=no-member
        additional_indexes = additional_indexes or []
        if len(additional_indexes) != len(series_descriptor.additional_index_names):
            raise DataFormatError('Series {} needs {} additional indexes, but {} provided.'.format(
                series_descriptor, len(series_descriptor.additional_index_names),
                len(additional_indexes)))
        if additional_indexes:
            for idx_val in additional_indexes:
                data_descriptor.additional_indexes.append(idx_val)  # pylint: disable=no-member
        return data_descriptor

    def write_index(self, block_writer):
        """Write all the indexes of the data file, and the file end."""
        # Write all the block indexes
        for block_index in self.series_block_indexes:
            # Record the location of the block index.
            self.file_index.series_block_index_offsets.append(block_writer.tell())
            # Write the block index.
            block = bddf.DescriptorBlock()
            block.series_block_index.CopyFrom(block_index)  # pylint: disable=no-member
            block_writer.write_descriptor_block(block)
        index_offset = block_writer.tell()
        block_writer.write_descriptor_block(self.descriptor_index)
        block_writer.write_file_end(index_offset)
