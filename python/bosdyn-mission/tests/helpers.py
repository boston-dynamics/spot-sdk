# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Common unit test helpers for bosdyn.mission tests."""


import concurrent
import sys
import time
from unittest import mock

import grpc
import pytest
from google.protobuf import timestamp_pb2

import bosdyn.api.header_pb2 as HeaderProto
import bosdyn.api.mission.nodes_pb2 as nodes_pb2
import bosdyn.mission.util
import bosdyn.util
from bosdyn.api import lease_pb2
from bosdyn.client.robot_command import RobotCommandBuilder
from bosdyn.mission.util import create_value, define_blackboard, set_blackboard

CONSTANT_TIMESTAMP = timestamp_pb2.Timestamp(seconds=12345, nanos=6789)


def setup_service_and_channel(service, service_adder):
    """Starts a service listening on a port and returns channel to it.

    The service should have already been instantiated. It will be
    attached to a server listening on an ephemeral port and started.

    Args:
        * service: The implementation of a gRPC service
        * service_adder: The function to add a service to a server. This is
        specified in the gRPC generated python, with a name like
        add_FooServiceServicer_to_server. Unfortunately, there's not an easy
        way to get to that method from the Service class.
    Returns:
        Channel to the server.
    """
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=1))
    service_adder(service, server)
    port = server.add_insecure_port('localhost:0')
    server.start()
    return server, grpc.insecure_channel('localhost:{}'.format(port))


def add_common_header(response, request, error_code=HeaderProto.CommonError.CODE_OK,
                      error_message=None):
    """Sets the common header on the response.

    Args:
        response: The response object to fill the header with.
        request: The request to be echoed in the response common header.
        error_code: The code to use, OK by default.
        error_message: Any error message to include, empty by default.
    """
    header = HeaderProto.ResponseHeader()
    header.request_header.CopyFrom(request.header)
    header.error.code = error_code
    if error_message:
        header.error.message = error_message
    response.header.CopyFrom(header)


def set_converted_timestamp_skew(client, skew_sec):
    """Set the timestamp returned by the client's timesync endpoint."""

    def get_ts(local_secs):
        return bosdyn.util.nsec_to_timestamp((local_secs + skew_sec) * bosdyn.util.NSEC_PER_SEC)

    if client._timesync_endpoint is None:
        client._timesync_endpoint = mock.Mock()
    client._timesync_endpoint.robot_timestamp_from_local_secs = get_ts


def start_server(servicer_to_server, client, service, robot=None):
    """Build a server, add the given service to it, hook up the client, and start it."""
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=1))
    servicer_to_server(service, server)
    port = server.add_insecure_port('localhost:0')
    channel = grpc.insecure_channel('localhost:{}'.format(port))
    client.channel = channel
    server.start()
    return server


def build_lease(sequence, epoch='foo', resource='bar'):
    lease = lease_pb2.Lease(resource=resource, epoch=epoch)
    lease.sequence.extend(sequence)
    return lease
