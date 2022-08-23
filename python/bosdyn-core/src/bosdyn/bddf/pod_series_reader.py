# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A class for reading a series of POD data from a DataFile."""
import struct
from itertools import product

from .common import POD_TYPE_TO_NUM_BYTES, POD_TYPE_TO_STRUCT, ParseError


class PodSeriesReader:
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
