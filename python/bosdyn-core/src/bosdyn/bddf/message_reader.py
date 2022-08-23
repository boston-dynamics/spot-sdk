# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A class for reading message data from a DataFile."""

from deprecated import deprecated

from .common import PROTOBUF_CONTENT_TYPE


class MessageReader:
    """A class for reading message data from a DataFile.

    Methods raise ParseError if there is a problem with the format of the file.
    """

    def __init__(self, data_reader, require_protobuf=False):
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
            if require_protobuf and message_type.content_type != PROTOBUF_CONTENT_TYPE:
                continue  # Not a protobuf series
            self._channel_name_to_series_descriptor[channel_name] = series_descriptor
            self._channel_name_to_series_index[channel_name] = series_descriptor.series_index

    @property
    def data_reader(self):
        """Return underlying DataReader this object is using."""
        return self._data_reader

    @property
    def channel_name_to_series_descriptor(self):
        """Return a mapping of {channel name -> series descriptor} for message series."""
        return self._channel_name_to_series_descriptor

    @property
    @deprecated(reason='Use channel_name_to_series_descriptor instead', version='3.1.0')
    def channel_name_to_series_decriptor(self):
        """Return a mapping of {channel name -> series descriptor} for message series."""
        return self._channel_name_to_series_descriptor

    def series_index(self, channel_name, message_type=None):
        """Return series index (int) to access SeriesDescriptors and messages.

        Args:
         channel_name: name of the channel of messages.
         message_type: specify message type, if channel may have multiple
                        kinds of messages (optional)
        """
        if message_type is None:
            return self._channel_name_to_series_index[channel_name]

        for series_index, series_identifier in enumerate(
                self._data_reader.file_index.series_identifiers):
            try:
                series_channel = series_identifier.spec["bosdyn:channel"]
            except KeyError:
                continue  # Not a protobuf series
            if series_channel != channel_name:
                continue
            series_descriptor = self._data_reader.series_descriptor(series_index)
            if series_descriptor.WhichOneof("DataType") != "message_type":
                continue  # Not a protobuf series
            if message_type == series_descriptor.message_type.type_name:
                return series_index

        raise KeyError("No series with channel_name={} and message_type={}".format(
            channel_name, message_type))

    def series_index_to_descriptor(self, series_index):
        """Given a series index, return the associated SeriesDescriptor

        Args:
         series_index:  index (int) from the series_index() call
        """
        return self._data_reader.file_index.series_descriptor(series_index)

    def get_blob(self, series_index, index_in_series):
        """Return binary data from message stored in the file.

        Args:
         series_index:     index (int) from the series_index() call
         index_in_series:  the index of the message within the series

        Returns: DataTypeDescriptor for channel, timestamp_nsec (int), binary data
        """
        return self._data_reader.read(series_index, index_in_series)
