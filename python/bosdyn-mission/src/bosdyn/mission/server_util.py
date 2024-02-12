# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from deprecated.sphinx import deprecated

import bosdyn.util
from bosdyn.api import header_pb2
from bosdyn.deprecated import moved_to



@deprecated(reason='The ResponseContext helper class has moved to a common location. Please use '
            'bosdyn.client.server_util.ResponseContext.', version='2.3.5', action="always")
class ResponseContext(object):

    def __init__(self, response, request, rpc_logger=None):
        self.response = response
        self.response.header.request_header.CopyFrom(request.header)
        self.request = request
        self.rpc_logger = rpc_logger

    def __enter__(self):
        self.response.header.request_received_timestamp.CopyFrom(bosdyn.util.now_timestamp())
        if self.rpc_logger:
            self.rpc_logger.add_protobuf_async(self.request)
        return self.response

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.response.header.error.code == self.response.header.error.CODE_UNSPECIFIED:
            self.response.header.error.code = self.response.header.error.CODE_OK
        if self.rpc_logger:
            self.rpc_logger.add_protobuf_async(self.response)


set_response_header = moved_to(bosdyn.client.server_util.populate_response_header, version='3.0.0')
