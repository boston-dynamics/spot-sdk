# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A class for reading GRPC data from a DataFile."""

from .bosdyn import GrpcRequests, GrpcResponses
from .common import LOGGER
from .grpc_service_reader import GrpcServiceReader


class GrpcReader:
    """A class for reading GRPC data from a DataFile.

    Methods raise ParseError if there is a problem with the format of the file.
    """

    def __init__(self, data_reader, protobuf_classes):
        self._data_reader = data_reader
        self._service_name_to_reader = {}
        self._series_index_to_reader = {}
        proto_name_to_class = {
            proto_class.DESCRIPTOR.full_name: proto_class for proto_class in protobuf_classes
        }
        self._proto_name_to_reader = {}
        for series_index, series_identifier in enumerate(data_reader.file_index.series_identifiers):
            print(series_index)
            if series_identifier.series_type not in (GrpcRequests.SERIES_TYPE,
                                                     GrpcResponses.SERIES_TYPE):
                print(series_identifier.series_type, GrpcRequests.SERIES_TYPE,
                      GrpcResponses.SERIES_TYPE)
                continue

            service_name = series_identifier.spec[GrpcRequests.SERVICE_NAME]
            message_type = series_identifier.spec[GrpcRequests.MESSAGE_TYPE]
            try:
                proto_class = proto_name_to_class[message_type]
            except KeyError:
                LOGGER.exception("Don't have a protobuf class for %s", message_type)
                continue
            try:
                service_reader = self._service_name_to_reader[service_name]
            except KeyError:
                service_reader = GrpcServiceReader(self, service_name)
                self._service_name_to_reader[service_name] = service_reader
            print("D")
            series_descriptor = self._data_reader.series_descriptor(series_index)
            reader = service_reader.add_proto_reader(series_index, proto_class,
                                                     series_identifier.series_type,
                                                     series_descriptor)
            if message_type not in self._proto_name_to_reader:
                self._proto_name_to_reader[message_type] = reader
            self._series_index_to_reader[series_index] = reader
        print(self._proto_name_to_reader.keys())

    @property
    def data_reader(self):
        """Return underlying DataReader this object is using."""
        return self._data_reader

    def get_proto_reader(self, proto_name):
        """Return the GrpcProtoReader for protobuf messages with the specified type name."""
        return self._proto_name_to_reader[proto_name]

    def get_message(self, series_index, index_in_series):
        """Return a deserialized protobuf from bytes stored in the file.

        Args:
         series_index:     index (int) from the series_index() call
         index_in_series:  the index of the message within the series

        Returns: timestamp_nsec (int), deserialized protobuf object
        """
        reader = self._series_index_to_reader[series_index]
        return reader.get_message(index_in_series)
