# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Class for registering a series which stores protobuf messages in a message series."""

from .bosdyn import MessageChannel
from .common import PROTOBUF_CONTENT_TYPE


class ProtobufSeriesWriter:  # pylint: disable=too-many-instance-attributes
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
        return MessageChannel.SERIES_TYPE

    @property
    def series_spec(self):
        """Return the series_spec for the series."""
        return self._series_spec
