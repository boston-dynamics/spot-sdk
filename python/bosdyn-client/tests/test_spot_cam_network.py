# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the Spot CAM's NetworkClient."""
import socket
import struct
import time

import grpc
import pytest

import bosdyn.client.spot_cam.network
from bosdyn.api.spot_cam import network_pb2, service_pb2_grpc

from . import helpers


def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]


def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))


class MockNetworkService(service_pb2_grpc.NetworkServiceServicer):

    def __init__(self, rpc_delay=0):
        """Create mock that returns fake network statuses."""
        super(MockNetworkService, self).__init__()
        self._rpc_delay = rpc_delay

    def GetICEConfiguration(self, request, context):
        time.sleep(self._rpc_delay)

        response = network_pb2.GetICEConfigurationResponse()
        response.servers.extend([_mock_ice_server()])
        helpers.add_common_header(response, request)
        return response

    def SetICEConfiguration(self, request, context):
        time.sleep(self._rpc_delay)

        response = network_pb2.SetICEConfigurationResponse()
        helpers.add_common_header(response, request)
        return response



def _setup(rpc_delay=0):
    client = bosdyn.client.spot_cam.network.NetworkClient()
    service = MockNetworkService(rpc_delay=rpc_delay)
    server = helpers.setup_client_and_service(client, service,
                                              service_pb2_grpc.add_NetworkServiceServicer_to_server)
    return client, service, server


def _fill_ice_server(server, src=None):
    if not src:
        src = _mock_ice_server()

    server.CopyFrom(src)
    return server


def _mock_ice_server(server_type=network_pb2.ICEServer.TURN, address='127.0.0.1', port=22):
    server = network_pb2.ICEServer()
    server.type = server_type
    server.address = address
    server.port = port
    return server


def test_get_ice_configuration():
    client, service, server = _setup()
    ice = client.get_ice_configuration()
    mock = _mock_ice_server()
    assert len(ice) == 1
    assert ice[0].type == mock.type
    assert ice[0].address == mock.address
    assert ice[0].port == mock.port


def test_get_ice_configuration_async():
    client, service, server = _setup()
    ice = client.get_ice_configuration_async().result()
    mock = _mock_ice_server()
    assert len(ice) == 1
    assert ice[0].type == mock.type
    assert ice[0].address == mock.address
    assert ice[0].port == mock.port


def test_set_ice_configuration():
    client, service, server = _setup()
    ice = client.set_ice_configuration([_mock_ice_server()])


def test_set_ice_configuration_async():
    client, service, server = _setup()
    ice = client.set_ice_configuration_async([_mock_ice_server()]).result()


