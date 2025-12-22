# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Common message processors."""

from bosdyn.api.header_pb2 import RequestHeader
from bosdyn.util import now_nsec, set_timestamp_from_nsec  # bosdyn-core


class AddRequestHeader(object):
    """Sets header fields common to all bosdyn.api requests."""

    def __init__(self, client_name_func):
        """Constructor, takes function to access the client name to insert into request headers."""
        self.get_client_name = client_name_func

    def _create_header(self):
        header = RequestHeader()
        header.client_name = self.get_client_name()
        set_timestamp_from_nsec(header.request_timestamp, now_nsec())
        return header

    def mutate(self, request):
        """Mutate request such that its header contains a client name and a timestamp.

        Headers are not required for third party proto requests/responses.
        """
        header = self._create_header()
        try:
            request.header.CopyFrom(header)
        except AttributeError:
            pass


class DataBufferLoggingProcessor:
    """Processor that logs every protobuf message to the robot's data buffer."""

    def __init__(self, data_buffer_client):
        """
        Args:
            data_buffer_client: Instance of DataBufferClient.
        """
        self.data_buffer_client = data_buffer_client

    def mutate(self, proto, **kwargs):
        """Logs the protobuf message to the data buffer.
        Args:
            proto: The protobuf request or response to log.
        """
        self.data_buffer_client.add_protobuf_async(proto)


def log_all_rpcs(client, data_buffer_client):
    """Attach a DataBufferLoggingProcessor to log all RPC requests and responses for the given client."""
    processor = DataBufferLoggingProcessor(data_buffer_client)
    client.request_processors.append(processor)
    client.response_processors.append(processor)
