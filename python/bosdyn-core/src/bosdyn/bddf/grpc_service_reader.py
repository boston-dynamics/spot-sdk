# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A container for the GrpcProtoReaders associated with a given service in a bddf file."""

from .grpc_proto_reader import GrpcProtoReader


class GrpcServiceReader:
    """A container for the GrpcProtoReaders associated with a given service in a bddf file."""

    def __init__(self, grpc_reader, service_name):
        self._grpc_reader = grpc_reader
        self._service_name = service_name
        self._type_name_to_reader = {}

    @property
    def data_reader(self):
        """Accessor for the DataReader used by this object."""
        return self._grpc_reader.data_reader

    def get_proto_reader(self, type_name):
        """Returns a GrpcProtoReader for messages with the specified protobuf type name."""
        return self._type_name_to_reader[type_name]

    def add_proto_reader(self, series_index, proto_type, series_type, series_descriptor):
        """Create and return a GrpcProtoReader for the given series in the bddf file."""
        reader = GrpcProtoReader(self, series_index, series_type, proto_type, series_descriptor)
        self._type_name_to_reader[proto_type.DESCRIPTOR.full_name] = reader
        return reader
