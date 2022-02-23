# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Reads a particular series of GRPC request or response messages from a bddf file."""


class GrpcProtoReader:
    """Reads a particular series of GRPC request or response messages from a bddf file."""

    def __init__(  # pylint: disable=too-many-arguments
            self, service_reader, series_index, series_type, proto_type, series_descriptor):
        self._service_reader = service_reader
        self._series_index = series_index
        self._series_type = series_type
        self._proto_type = proto_type
        self._series_descriptor = series_descriptor
        self._num_messages = None

    @property
    def num_messages(self):
        """Number of messages in of the given type."""
        if self._num_messages is None:
            self._num_messages = self._service_reader.data_reader.num_data_blocks(
                self._series_index)
        return self._num_messages

    def get_message(self, index_in_series):
        """Get a message from the series by its index number in the series."""
        _desc, timestamp_nsec, data = self._service_reader.data_reader.read(
            self._series_index, index_in_series)
        protobuf = self._proto_type()
        protobuf.ParseFromString(data)
        return timestamp_nsec, protobuf
