# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Code for reading and writing 'bddf' data files."""
from itertools import product
import logging
import os
import struct
from hashlib import sha1

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
MESSAGE_CHANNEL_SERIES_TYPE = 'bosdyn:message-channel'

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


def _hasher_to_uint64(hasher):
    return struct.unpack('>Q', hasher.digest()[0:8])[0]


class FileIndexer(object):
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

    def index_data_block(self, series_index, timestamp_nsec, file_offset, nbytes,
                         additional_indexes):
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
        data_descriptor.timestamp.FromNanoseconds(timestamp_nsec)
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


class BlockWriter(object):
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
        # Magic bytes at the start of the file
        self._write(MAGIC)
        header_block = bddf.DescriptorBlock()
        file_descriptor = header_block.file_descriptor  # pylint: disable=no-member
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


class DataWriter(object):
    """Class for writing data to a file."""

    # pylint: disable=too-many-arguments

    def __init__(self, outfile, annotations=None):
        """
        Args:
         outfile:       a file-like objet for writing binary data (e.g., from open(fname, 'wb')).
         annotations:   optional dict of key (string) -> value (string) pairs.
        """
        self._writer = BlockWriter(outfile)
        self._indexer = FileIndexer()
        self._annotations = annotations
        self._writer.write_header(annotations)
        self._on_close = []

    def __del__(self):
        self._close()

    def __enter__(self):
        return self

    def __exit__(self, type_, value_, tb_):
        self._close()

    @property
    def file_index(self):
        """Get the FileIndex proto used which describes how to access data in the file."""
        return self._indexer.file_index

    def add_message_series(self, series_type, series_spec, content_type, type_name,
                           is_metadata=False, annotations=None, additional_index_names=None):
        """Add a new series for storing message data.  Message data is variable-sized binary data.

        Args:
         series_type:   the kind of spec, corresponding to the set of keys expected in series_spec.
         series_spec:   dict of {key (string) -> value (string)| describing the series.
         content_type:  data encoding, like http content-type header (string)
         type_name:     string describing the kind of data
         is_metadata:   Metadata messages are needed to interpret other messages which
                         may be stored in the file.  If the file is split into parts,
                         metadata messages must be duplicated into each part. (default=False)
         annotations:   optional dict of key (string) -> value (string) pairs to
                          associate with the message channel
         additional_index_names: names of additional timestamps to store with
                                        each message (list of string).

        Returns series id (int).
        """
        message_type = bddf.MessageTypeDescriptor(content_type=content_type, type_name=type_name,
                                                  is_metadata=is_metadata)
        return self.add_series(series_type, series_spec, message_type=message_type,
                               annotations=annotations,
                               additional_index_names=additional_index_names)

    def add_pod_series(self, series_type, series_spec, type_enum, dimension=None, annotations=None):
        """Add a new series for storing data POD data (float, double, int, etc....).

        Args:
         series_type:   the kind of spec, corresponding to the set of keys expected in series_spec.
         series_spec:   dict of {key (string) -> value (string)} describing the series.
         type_enum:     kind of values stored in the file (PodTypeEnum).
         dimensions:    None or empty-array means elements are single values,
                           [3] means vectors of size 3, [4, 4] is a 4x4 matrix, etc....
         annotations:   optional dict of key (string) -> value (string) pairs to
                            associate with the message channel

        Returns series id (int).
        """
        pod_type = bddf.PodTypeDescriptor(pod_type=type_enum, dimension=dimension)
        return self.add_series(series_type, series_spec, pod_type=pod_type, annotations=annotations)

    def add_series(self, series_type, series_spec, message_type=None, pod_type=None,
                   annotations=None, additional_index_names=None):
        """Register a new series for messages.

        Args:
         series_type:   the kind of spec, corresponding to the set of keys expected in series_spec.
         series_spec:   dict of {key (string) -> value (string)| describing the series.
         message_type:  MessageTypeDescriptor (need EITHER this OR pod_type)
         pod_type:      PodTypeDescriptor (need EITHER this OR pod_type)
         annotations:   optional dict of key (string) -> value (string) pairs to
                            associate with the message channel
         additional_index_names: names of additional timestamps to store with
                                        each message (list of string).

        Returns series id (int).

        Raises SeriesNotUniqueError if a series matching series_spec is already added.
        """
        return self._indexer.add_series(series_type, series_spec, message_type, pod_type,
                                        annotations, additional_index_names, self._writer)

    def write_data(self, series_index, timestamp_nsec, data, additional_indexes=None):
        """Store binary data into the file, under a previously-defined channel.

        Args:
         series_index:   integer returned when series was registered with the file.
         timestamp_nsec: nsec since unix epoch to timestamp the data
         data:           binary data to store
         additional_indexss: additional timestamps if needed for this channel

        Raises DataFormatError if the data or additional_indexes are not valid for this series.
        """
        self._indexer.index_data_block(series_index, timestamp_nsec, self._writer.tell(), len(data),
                                       additional_indexes)
        data_descriptor = self._indexer.make_data_descriptor(series_index, timestamp_nsec,
                                                             additional_indexes)
        self._writer.write_data_block(data_descriptor, data)

    def run_on_close(self, thunk):
        """Register a function to be called when file is closed, before index is written."""
        self._on_close.append(thunk)

    def _close(self):
        if self._writer.closed:
            return
        for thunk in self._on_close:
            thunk()
        self._indexer.write_index(self._writer)
        self._writer.close()


class ProtoSeriesWriter(object):  # pylint: disable=too-many-instance-attributes
    """A class for registering a series which stores protobuf messages in a message series.

    The series is named by a 'channel_name' which defaults to the full type name of the
     protobuf type.
    """

    def __init__(  # pylint: disable=too-many-arguments
            self, data_writer, protobuf_type, channel_name=None, is_metadata=False,
            annotations=None, additional_index_names=None):
        self._data_writer = data_writer
        self._protobuf_type = protobuf_type
        self._type_name = protobuf_type.DESCRIPTOR.full_name
        self._channel_name = channel_name or self._type_name
        self._series_spec = {'bosdyn:channel': self._channel_name}
        self._series_index = self._data_writer.add_message_series(
            self.series_type, self.series_spec, content_type=PROTOBUF_CONTENT_TYPE,
            type_name=self._type_name, is_metadata=is_metadata, annotations=annotations,
            additional_index_names=additional_index_names)

    def write(self, timestamp_nsec, protobuf, additional_indexs=None):
        """Store protobuf in the file.

        Args
         timestamp_nsec:      nsec since unix epoch to timestamp the data
         protobuf:            a protobuf message, not serialized.
         additional_indexes:  additional timestamps if needed for this channel

        Raises DataFormatError if the data or additional_indexes are not valid for this series.
        """
        self._data_writer.write_data(self._series_index, timestamp_nsec,
                                     protobuf.SerializeToString(), additional_indexs)

    @property
    def series_type(self):
        """Return the series type string."""
        return MESSAGE_CHANNEL_SERIES_TYPE

    @property
    def series_spec(self):
        """Return the series_spec for the series."""
        return self._series_spec


class PodSeriesWriter(object):  # pylint: disable=too-many-instance-attributes
    """A class to assist with writing POD data values into a series, within a DataWriter."""

    def __init__(  # pylint: disable=too-many-arguments
            self, data_writer, series_type, series_spec, pod_type, dimensions=None,
            annotations=None, data_block_size=2048):
        self._data_writer = data_writer
        self._series_type = series_type
        self._series_spec = series_spec
        self._pod_type = pod_type
        self._dimensions = dimensions or []
        self._series_index = self._data_writer.add_pod_series(self.series_type, self.series_spec,
                                                              type_enum=self._pod_type,
                                                              dimension=self._dimensions,
                                                              annotations=annotations)

        self._data_block_size = data_block_size
        self._num_values_per_sample = 1
        for dim in self._dimensions:
            self._num_values_per_sample *= dim
        self._bytes_per_sample = POD_TYPE_TO_NUM_BYTES[pod_type] * self._num_values_per_sample
        self._block = b''
        self._timestamp_nsec = None
        self._format_str = '<{}{}'.format(self._num_values_per_sample, POD_TYPE_TO_STRUCT[pod_type])
        self._data_writer.run_on_close(self.finish_block)

    def write(self, timestamp_nsec, sample):
        """Add sample to data block, and write block if block is full.

        A block is full if there is no room for an additional sample within the data_block_size.

        Args:
         timestamp_nsec:  nsec since unix epoch to timestamp the data
         sample:          array/vector of POD values to write

        Raises DataFormatError if the data is invalid for this series.
        """
        serialized_sample = struct.pack(self._format_str, sample)
        if len(serialized_sample) != self._bytes_per_sample:
            raise DataFormatError('{} expect {} elements but got {})'.format(
                self._series_spec, self._bytes_per_sample, len(serialized_sample)))
        if self._bytes_per_sample >= self._data_block_size:
            # We should always immediately write data data
            self._data_writer.write_data(self._series_index, timestamp_nsec, serialized_sample)
            return

        if not self._block:
            # New block, starts with current timestamp.
            self._timestamp_nsec = timestamp_nsec
            self._block = serialized_sample
        else:
            # Add data to pre-existing block
            self._block += serialized_sample

        if len(self._block) + self._bytes_per_sample > self._data_block_size:
            # No room for more samples before the data must be written.
            self._data_writer.write_data(self._series_index, self._timestamp_nsec, self._block)
            self._block = b''

    def finish_block(self):
        """If there are samples which haven't been written to the file, write them now."""
        if not self._block:
            return
        self._data_writer.write_data(self._series_index, self._timestamp_nsec, self._block)
        self._block = b''

    @property
    def series_type(self):
        """Return the series_type (string) with which the series was registered."""
        return MESSAGE_CHANNEL_SERIES_TYPE

    @property
    def series_spec(self):
        """Return the series_spec ({key -> value}) with which the series was registered."""
        return self._series_spec


class BaseDataReader(object):
    """Shared parent class for DataReader and StreamedDataReader."""

    def __init__(self, outfile):
        """
        Args:
         outfile:      binary file-like object for reading (e.g., from open(fname, "rb")).
        """
        self._file = outfile
        self._file_descriptor = None
        self._spec_index = None
        self._index_offset = None
        self._checksum = None
        self._read_checksum = None
        self._eof = False
        self._file_index = None
        self._read_header()

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

    def _computed_checksum(self):
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
        if checksum_type == bddf.FileFormatDescriptor.CHECKSUM_TYPE_UNKNOWN:
            raise DataFormatError("Unset checksum type in file descriptor")
        elif checksum_type == bddf.FileFormatDescriptor.CHECKSUM_TYPE_NONE:
            LOGGER.debug("No checksum in bddf stream")
        elif checksum_type != bddf.FileFormatDescriptor.CHECKSUM_TYPE_SHA1:
            raise DataFormatError("Unknown checksum type {}".format(checksum_type))
        if self._file_descriptor.checksum_num_bytes != SHA1_DIGEST_NBYTES:
            raise DataFormatError("Uexpected checksm num_bytes ({} != {}).".format(
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
            self._read_checksum = self._computed_checksum()
            self._checksum = self._read(self._file_descriptor.checksum_num_bytes)
            self._eof = True
            if (self._file_descriptor.checksum_type == bddf.FileFormatDescriptor.CHECKSUM_TYPE_SHA1
                    and self._read_checksum is not None and self._checksum != self._read_checksum):
                raise ChecksumError(
                    "File checksum 0x{} does not match computed value 0x{}".format(
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


class DataReader(BaseDataReader):  # pylint: disable=too-many-instance-attributes
    """Class for reading data from a file-like object which is seekable.

    Methods raise ParseError if there is a problem with the format of the file.
    """

    def __init__(self, outfile):
        """
        Args:
         outfile:      binary file-like object for reading (e.g., from open(fname, "rb")).
        """
        super(DataReader, self).__init__(outfile)
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
        """Retreives a message and related information from the file.

        Args:
         series_index: int selecting from which series to read the message.
         index:        The index number of the message within the channel.

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


class ProtobufReader(object):
    """A class for reading Protobuf data from a DataFile.

    Methods raise ParseError if there is a problem with the format of the file.
    """

    def __init__(self, data_reader):
        self._data_reader = data_reader
        self._channel_name_to_series_descriptor = {}
        self._channel_name_to_series_index = {}
        for series_index, series_identifier in enumerate(data_reader.file_index.series_identifiers):
            try:
                channel_name = series_identifier.spec["bosdyn:channel"]
            except KeyError:
                continue  # Not a protobuf series
            series_descriptor = self._data_reader.series_descriptor(series_index)
            if series_descriptor.WhichOneof("DataType") != "message_type":
                continue  # Not a protobuf series
            message_type = series_descriptor.message_type
            if message_type.content_type != PROTOBUF_CONTENT_TYPE:
                continue  # Not a protobuf series
            self._channel_name_to_series_descriptor[channel_name] = series_descriptor
            self._channel_name_to_series_index[channel_name] = series_descriptor.series_index

    @property
    def data_reader(self):
        """Return underlying DataReader this object is using."""
        return self._data_reader

    def series_index(self, channel_name):
        """Return the series index (int) by which SeriesDescriptors and messages can be accessed.

        Args:
         channel_name: name of the channel of messsages.
        """
        return self._channel_name_to_series_index[channel_name]

    def series_index_to_descriptor(self, series_index):
        """Given a series index, return the associated SeriesDescriptor

        Args:
         series_index:  index (int) from the series_index() call
        """
        return self._data_reader.file_index.series_descriptor(series_index)

    def get_message(self, series_index, protobuf_type, index_in_series):
        """Return a deserialized protobuf from bytes stored in the file.

        Args:
         series_index:     index (int) from the series_index() call
         protobuf_type:    class of the protobuf we want to deserialize
         index_in_series:  the index of the message within the series

        Returns: DataTypeDescriptor for channel, timestamp_nsec (int), deserialized protobuf object
        """
        desc, timestamp_nsec, data = self._data_reader.read(series_index, index_in_series)
        protobuf = protobuf_type()
        protobuf.ParseFromString(data)
        return desc, timestamp_nsec, protobuf


class ProtobufChannelReader(object):
    """A class for reading a single channel of Protobuf data from a DataFile."""

    def __init__(self, protobuf_reader, protobuf_type, channel_name=None):
        self._protobuf_reader = protobuf_reader
        self._protobuf_type = protobuf_type
        self._channel_name = channel_name or protobuf_type.DESCRIPTOR.full_name
        self._series_index = self._protobuf_reader.series_index(self._channel_name)
        self._descriptor = None
        self._num_messages = None

    @property
    def series_descriptor(self):
        """SeriesDescriptor for this series"""
        if self._descriptor is None:
            self._descriptor = self._protobuf_reader.series_index_to_descriptor(self._series_index)
        return self._descriptor

    @property
    def num_messages(self):
        """Number of messages in this series."""
        if self._num_messages is None:
            self._num_messages = self._protobuf_reader.data_reader.num_data_blocks(
                self._series_index)
        return self._num_messages

    def get_message(self, index_in_series):
        """Get the specified message in the series, as a deserialized protobuf.

        Args:
         index_in_series:  the index of the message within the series

        Returns: timestamp_nsec (int), deserialized protobuf object
        """
        _desc, timestamp, msg = self._protobuf_reader.get_message(self._series_index,
                                                                  self._protobuf_type,
                                                                  index_in_series)
        return timestamp, msg


class PodSeriesReader(object):
    """A class for reading a series of POD data from a DataFile.

    Methods raise ParseError if there is a problem with the format of the file.
    """

    def __init__(self, data_reader, series_spec):
        self._data_reader = data_reader
        self._series_index = self._data_reader.series_spec_to_index(series_spec)
        self._series_descriptor = self._data_reader.series_descriptor(self._series_index)
        if self._series_descriptor.WhichOneof("DataType") != "pod_type":
            raise ParseError("Expected DataType 'pod_type' but got {}.".format(
                self._series_descriptor.WhichOneof("DataType")))

        self._pod_type = self._series_descriptor.pod_type
        self._num_values_per_sample = 1
        for dim in self._pod_type.dimension:
            self._num_values_per_sample *= dim
        pod_type = self._pod_type.pod_type
        self._bytes_per_sample = POD_TYPE_TO_NUM_BYTES[pod_type] * self._num_values_per_sample
        self._num_data_blocks = None

    @property
    def pod_type(self):
        """Return the PodTypeDescriptor for the series."""
        return self._pod_type

    @property
    def series_descriptor(self):
        """Return the SeriesDescriptor for the series."""
        return self._series_descriptor

    @property
    def num_data_blocks(self):
        """Number of data blocks in this series."""
        if self._num_data_blocks is None:
            self._num_data_blocks = self._data_reader.num_data_blocks(self._series_index)
        return self._num_data_blocks

    def read_samples(self, index_in_series):
        """Return the POD data values from the data block of the given index.

        Returns: timestamp_nsec (int), POD data values (array of (array ... (of POD values)))
        """
        _desc, timestamp_nsec, data = self._data_reader.read(self._series_index, index_in_series)
        num_samples = len(data) // self._bytes_per_sample
        expected_size = num_samples * self._bytes_per_sample
        if len(data) != expected_size:
            raise ParseError('{} idx={} expect {} elements but got {})'.format(
                self._series_descriptor.series_identifier, index_in_series, expected_size,
                len(data)))

        num_values = num_samples * self._num_values_per_sample
        format_str = '<{}{}'.format(num_values, POD_TYPE_TO_STRUCT[self._pod_type.pod_type])
        pod_data = list(struct.unpack(format_str, data))

        def _split(vals, dims):
            if not dims:
                return vals
            els_per_sample = product(dims)
            assert els_per_sample
            next_dims = dims[1:]
            return [
                _split(vals[i:i + els_per_sample], next_dims)
                for i in range(0, len(vals), els_per_sample)
            ]

        split_data = _split(pod_data, self._pod_type.dimension)

        return timestamp_nsec, split_data


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
