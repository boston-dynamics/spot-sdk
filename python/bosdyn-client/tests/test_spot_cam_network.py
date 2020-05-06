# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the Spot CAM's NetworkClient."""
import time

import grpc
import pytest

import bosdyn.client.spot_cam.network

from bosdyn.api.spot_cam import network_pb2, service_pb2_grpc

from . import helpers

import socket
import struct

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

    def GetNetworkSettings(self, request, context):
        time.sleep(self._rpc_delay)

        response = network_pb2.GetNetworkSettingsResponse()
        _fill_network_tuple(response.settings)
        helpers.add_common_header(response, request)
        return response

    def SetICEConfiguration(self, request, context):
        time.sleep(self._rpc_delay)

        response = network_pb2.SetICEConfigurationResponse()
        helpers.add_common_header(response, request)
        return response

    def SetNetworkSettings(self, request, context):
        time.sleep(self._rpc_delay)

        response = network_pb2.GetNetworkSettingsResponse()
        response.settings.CopyFrom(request.settings)
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

def _fill_network_tuple(nt, src=None):
    if not src:
        src = _mock_network_tuple()

    nt.CopyFrom(src)
    return nt

def _mock_ice_server(server_type=network_pb2.ICEServer.TURN, address='127.0.0.1', port=22):
    server = network_pb2.ICEServer()
    server.type = server_type
    server.address = address
    server.port = port
    return server

def _mock_network_tuple(address='127.0.0.1', netmask='255.255.255.0', gateway='8.8.8.8', mtu=1500):
    nt = network_pb2.NetworkTuple()
    nt.address.value = ip2int(address)
    nt.netmask.value = ip2int(netmask)
    nt.gateway.value = ip2int(gateway)
    nt.mtu.value = mtu
    return nt

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

def test_get_network_settings():
    client, service, server = _setup()
    ns = client.get_network_settings()
    mock = _mock_network_tuple()
    assert ns.address == mock.address
    assert ns.netmask == mock.netmask
    assert ns.gateway == mock.gateway
    assert ns.mtu == mock.mtu

def test_get_network_settings_async():
    client, service, server = _setup()
    ns = client.get_network_settings_async().result()
    mock = _mock_network_tuple()
    assert ns.address == mock.address
    assert ns.netmask == mock.netmask
    assert ns.gateway == mock.gateway
    assert ns.mtu == mock.mtu

def test_set_ice_configuration():
    client, service, server = _setup()
    ice = client.set_ice_configuration([_mock_ice_server()])

def test_set_ice_configuration_async():
    client, service, server = _setup()
    ice = client.set_ice_configuration_async([_mock_ice_server()]).result()

def test_set_network_settings():
    client, service, server = _setup()
    ns = client.set_network_settings('127.0.0.1', '255.255.255.0', '8.8.8.8', 1500)
    mock = _mock_network_tuple()
    assert ns.address == mock.address
    assert ns.netmask == mock.netmask
    assert ns.gateway == mock.gateway
    assert ns.mtu == mock.mtu

def test_set_network_settings_async():
    client, service, server = _setup()
    ns = client.set_network_settings_async('127.0.0.1', '255.255.255.0', '8.8.8.8', 1500).result()
    mock = _mock_network_tuple()
    assert ns.address == mock.address
    assert ns.netmask == mock.netmask
    assert ns.gateway == mock.gateway
    assert ns.mtu == mock.mtu
