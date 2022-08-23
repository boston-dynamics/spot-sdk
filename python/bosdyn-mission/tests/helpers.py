# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Common unit test helpers for bosdyn.mission tests."""


import concurrent
import sys
import time

import grpc
import pytest

if sys.version_info[0:2] >= (3, 3):
    # Python version 3.3 added unittest.mock
    from unittest import mock
else:
    # The backport is on PyPi as just "mock"
    import mock

from google.protobuf import timestamp_pb2

import bosdyn.api.header_pb2 as HeaderProto
import bosdyn.api.mission.nodes_pb2 as nodes_pb2
import bosdyn.mission.util
import bosdyn.util
from bosdyn.api import lease_pb2
from bosdyn.client.robot_command import RobotCommandBuilder

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


def build_stand_command(deprecated, **kwargs):
    if (deprecated):
        cmd = RobotCommandBuilder.stand_command(**kwargs)
    else:
        cmd = RobotCommandBuilder.synchro_stand_command(**kwargs)
    return cmd


def build_sit_command(deprecated):
    if (deprecated):
        cmd = RobotCommandBuilder.sit_command()
    else:
        cmd = RobotCommandBuilder.synchro_sit_command()
    return cmd


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


def create_value(v):
    return bosdyn.api.mission.util_pb2.Value(constant=bosdyn.mission.util.python_var_to_value(v))


def define_blackboard(dict_values):
    node_to_return = nodes_pb2.DefineBlackboard()
    for (key, value) in dict_values.items():
        node_to_return.blackboard_variables.add().CopyFrom(
            bosdyn.api.mission.util_pb2.KeyValue(key=key, value=value))
    return node_to_return


def set_blackboard(dict_values):
    node_to_return = nodes_pb2.SetBlackboard()
    for (key, value) in dict_values.items():
        node_to_return.blackboard_variables.add().CopyFrom(
            bosdyn.api.mission.util_pb2.KeyValue(key=key, value=value))
    return node_to_return
