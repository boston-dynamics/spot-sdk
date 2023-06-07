# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Test the client to the auto_return service."""
import concurrent

import grpc
import pytest

import bosdyn.client.auto_return
from bosdyn.api.auto_return import auto_return_pb2, auto_return_service_pb2_grpc

from . import helpers


class MockAutoReturnServicer(auto_return_service_pb2_grpc.AutoReturnServiceServicer):

    def __init__(self):
        super(MockAutoReturnServicer, self).__init__()
        self.active_configuration_request = None
        self.leases = None

    def GetConfiguration(self, request, context):
        response = auto_return_pb2.GetConfigurationResponse()
        helpers.add_common_header(response, request)
        if self.active_configuration_request:
            response.request.CopyFrom(self.active_configuration_request)
            response.enabled = True
        return response

    def Configure(self, request, context):
        response = auto_return_pb2.ConfigureResponse()
        helpers.add_common_header(response, request)
        if request.params.max_displacement <= 0:
            response.invalid_params.max_displacement = request.params.max_displacement
            response.status = auto_return_pb2.ConfigureResponse.STATUS_INVALID_PARAMS
        else:
            response.status = auto_return_pb2.ConfigureResponse.STATUS_OK
            self.active_configuration_request = request
            self.leases = request.leases
        return response


@pytest.fixture(scope='function')
def client():
    return bosdyn.client.auto_return.AutoReturnClient()


@pytest.fixture(scope='function')
def service():
    return MockAutoReturnServicer()


@pytest.fixture(scope='function')
def server(client, service):
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=1))
    auto_return_service_pb2_grpc.add_AutoReturnServiceServicer_to_server(service, server)
    port = server.add_insecure_port('localhost:0')
    channel = grpc.insecure_channel('localhost:{}'.format(port))
    client.channel = channel
    server.start()
    return server


def test_simple(client, server, service):
    """Test basic usage of the client."""
    client.get_configuration()
    resp = client.get_configuration_async().result()
    assert not resp.enabled
    assert not resp.HasField('request')

    params = auto_return_pb2.Params()
    params.max_displacement = -1
    with pytest.raises(bosdyn.client.auto_return.InvalidParameterError):
        client.configure(params, leases=[])
    with pytest.raises(bosdyn.client.auto_return.InvalidParameterError):
        client.configure_async(params, leases=[])

    params.max_displacement = 12
    client.configure(params, leases=[])
    assert service.active_configuration_request.params.SerializeToString(
    ) == params.SerializeToString()
    # Test that the NoneType was overwritten with an iterable.
    assert len(service.leases) == 0

    resp = client.get_configuration()
    assert resp.request.params.SerializeToString() == params.SerializeToString()
