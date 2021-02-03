# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A class for reading Protobuf data from a DataFile."""

from .common import PROTOBUF_CONTENT_TYPE


class ProtobufReader:
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
         channel_name: name of the channel of messages.
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
