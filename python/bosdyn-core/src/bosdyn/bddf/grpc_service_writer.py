# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""GrpcSeriesWriter is a class for registering a series which stores GRPC request/response pairs."""

from bosdyn.util import timestamp_to_nsec

from .bosdyn import GrpcRequests, GrpcResponses
from .common import PROTOBUF_CONTENT_TYPE


class GrpcServiceWriter:  # pylint: disable=too-many-instance-attributes
    """A class for logging GRPC request and response messages."""

    def __init__(self, data_writer, service_name):
        self._data_writer = data_writer
        self._service_name = service_name
        self._request_types = {}
        self._response_types = {}

    def log_request(self, protobuf):
        """Store request protobuf in the file.

        Args
         protobuf:            a protobuf request message, not serialized.
        """
        series_index = self._get_series_index(protobuf, is_request=True)
        self._data_writer.write_data(
            series_index,
            # clock correction??? -- what does C++ do?
            timestamp_to_nsec(protobuf.header.request_timestamp),
            protobuf.SerializeToString())

    def log_response(self, protobuf):
        """Store response protobuf in the file.

        Args
         protobuf:            a protobuf response message, not serialized.
        """
        series_index = self._get_series_index(protobuf, is_request=False)
        self._data_writer.write_data(series_index,
                                     timestamp_to_nsec(protobuf.header.response_timestamp),
                                     protobuf.SerializeToString())

    def _get_series_index(self, protobuf, is_request):
        message_name = protobuf.DESCRIPTOR.full_name  # pylint: disable=no-member
        if is_request:
            name_to_index = self._request_types
            series_type = GrpcRequests
        else:
            name_to_index = self._response_types
            series_type = GrpcResponses
        try:
            return name_to_index[message_name]
        except KeyError:
            pass

        series_spec = {
            series_type.SERVICE_NAME: self._service_name,
            series_type.MESSAGE_TYPE: message_name
        }
        series_index = self._data_writer.add_message_series(series_type.SERIES_TYPE, series_spec,
                                                            content_type=PROTOBUF_CONTENT_TYPE,
                                                            type_name=message_name)
        name_to_index[message_name] = series_index
        return series_index
