# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Assists with writing POD data values into a series, within a DataWriter."""
import struct

from .bosdyn import MessageChannel
from .common import POD_TYPE_TO_NUM_BYTES, POD_TYPE_TO_STRUCT, DataFormatError


class PodSeriesWriter:  # pylint: disable=too-many-instance-attributes
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
            # We should always immediately write data.
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
        return MessageChannel.SERIES_TYPE

    @property
    def series_spec(self):
        """Return the series_spec ({key -> value}) with which the series was registered."""
        return self._series_spec
