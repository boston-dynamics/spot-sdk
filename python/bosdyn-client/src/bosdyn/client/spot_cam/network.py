# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Spot CAM Network service."""

import socket
import struct 

from bosdyn.client.common import (BaseClient, handle_common_header_errors)
from bosdyn.api.spot_cam import service_pb2_grpc
from bosdyn.api.spot_cam import network_pb2

class NetworkClient(BaseClient):
    """A client calling Spot CAM Network services such as ICE Candidates, SSL certs / Keys etc.

    Note: Interactive Connectivity Establishment (ICE) is a protocol which lets two devices use
    an intermediary to exchange offers and answers even if the two devices are separated
    by Network Address Translation (NAT).
    """
    default_service_name = 'spot-cam-network'
    service_type = 'bosdyn.api.spot_cam.NetworkService'

    def __init__(self):
        super(NetworkClient, self).__init__(service_pb2_grpc.NetworkServiceStub)

    def get_ice_configuration(self, **kwargs):
        """Set ICE configuration on Spot CAM. This overrides all existing configured servers"""
        request = network_pb2.GetICEConfigurationRequest()
        return self.call(self._stub.GetICEConfiguration, request, self._ice_servers_from_response,
                         self._ice_network_error_from_response, **kwargs)

    def get_ice_configuration_async(self, **kwargs):
        """Async version of get_ice_configuration()"""
        request = network_pb2.GetICEConfigurationRequest()
        return self.call_async(self._stub.GetICEConfiguration, request,
                               self._ice_servers_from_response,
                               self._ice_network_error_from_response, **kwargs)


    def set_ice_configuration(self, ice_servers, **kwargs):
        """Get ICE configuration from Spot CAM"""
        request = self._set_ice_configuration_request(ice_servers)
        return self.call(self._stub.SetICEConfiguration, request, None,
                         self._ice_network_error_from_response, **kwargs)

    def set_ice_configuration_async(self, ice_servers, **kwargs):
        """Async version of set_ice_configuration()"""
        request = self._set_ice_configuration_request(ice_servers)
        return self.call_async(self._stub.SetICEConfiguration, request, None,
                               self._ice_network_error_from_response, **kwargs)


    @staticmethod
    def _set_ice_configuration_request(ice_servers):
        request = network_pb2.SetICEConfigurationRequest()
        request.servers.extend(ice_servers)
        return request

    @staticmethod
    def _ice_servers_from_response(response):
        return response.servers

    @staticmethod
    @handle_common_header_errors
    def _ice_network_error_from_response(response):  # pylint: disable=unused-argument
        return None
