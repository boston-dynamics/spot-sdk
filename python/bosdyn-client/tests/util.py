# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from unittest import mock

import bosdyn.api.header_pb2
import bosdyn.util


def set_common_response_header(header, code=bosdyn.api.header_pb2.CommonError.CODE_OK):
    now_nsec = bosdyn.util.now_nsec()
    bosdyn.util.set_timestamp_from_nsec(header.response_timestamp, now_nsec)
    header.error.code = code


def mock_stub_response(rpc, response):
    """Build a Mock for a gRPC stub's response."""

    # Blocking RPC is straightforward:
    rpc.return_value = response

    # Async RPC needs a future-like object.
    # Mock as if the RPC completed immediately with the given response.
    future_mock = mock.Mock()
    future_mock.done.return_value = True
    future_mock.exception.return_value = None
    future_mock.result.return_value = response
    rpc.future.return_value = future_mock
