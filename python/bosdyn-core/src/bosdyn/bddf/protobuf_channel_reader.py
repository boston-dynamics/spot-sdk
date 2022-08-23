# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A class for reading a single channel of Protobuf data from a DataFile."""


class ProtobufChannelReader:
    """A class for reading a single channel of Protobuf data from a DataFile."""

    def __init__(self, protobuf_reader, protobuf_type, channel_name=None):
        self._protobuf_reader = protobuf_reader
        self._protobuf_type = protobuf_type
        self._channel_name = channel_name or protobuf_type.DESCRIPTOR.full_name
        self._series_index = self._protobuf_reader.series_index(
            self._channel_name, message_type=protobuf_type.DESCRIPTOR.full_name)
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

    def __iter__(self):
        return ProtobufChannelReader.Iterator(self)

    class Iterator:  # pylint: disable=too-few-public-methods
        """Iterator over messages from a ProtobufChannelReader"""

        def __init__(self, channel_reader):
            self._channel_reader = channel_reader
            self._index = 0

        def __next__(self):
            """Returns the next vlue."""
            if self._index >= self._channel_reader.num_messages:
                raise StopIteration
            msg = self._channel_reader.get_message(self._index)
            self._index += 1
            return msg
