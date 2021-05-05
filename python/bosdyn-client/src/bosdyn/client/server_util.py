# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging
from bosdyn.api import header_pb2
import bosdyn.util


_LOGGER = logging.getLogger(__name__)

class ResponseContext(object):
    """Helper to log gRPC request and response message to the data buffer for a service.

    It should be called using a "with" statement each time an RPC is received such that
    the request and response proto messages can be passed in. It will automatically log
    the request and response to the data buffer, and mutates the headers to add additional
    information before logging.

    Args:
        response (protobuf): any gRPC response message with a bosdyn.api.ResponseHeader proto.
        request (protobuf): any gRPC request message with a bosdyn.api.RequestHeader proto.
        rpc_logger (DataBufferClient): Optional data buffer client to log the messages; if not
            provided, only the headers will be mutated and nothing will be logged.
    """

    def __init__(self, response, request, rpc_logger=None):
        self.response = response
        self.response.header.request_header.CopyFrom(request.header)
        self.request = request
        self.rpc_logger = rpc_logger

    def __enter__(self):
        """Adds a start timestamp to the response header and logs the request RPC."""
        self.response.header.request_received_timestamp.CopyFrom(bosdyn.util.now_timestamp())
        if self.rpc_logger:
            self.rpc_logger.add_protobuf_async(self.request)
        return self.response

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Updates the header code if unset and logs the response RPC."""
        if self.response.header.error.code == self.response.header.error.CODE_UNSPECIFIED:
            self.response.header.error.code = self.response.header.error.CODE_OK
        if exc_type is not None:
            # An uncaught exception was raised by the service. Automatically set the header
            # to be an internal error.
            self.response.header.error.code = self.response.header.error.CODE_INTERNAL_SERVER_ERROR
            self.response.header.error.message = "[%s] %s" % (exc_type.__name__, exc_val)
        if self.rpc_logger:
            self.rpc_logger.add_protobuf_async(self.response)

