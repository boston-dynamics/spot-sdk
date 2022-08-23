# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the Spot CAM's MediaLogClient."""
import time

import grpc
import pytest

import bosdyn.client.spot_cam.version
from bosdyn.api.spot_cam import service_pb2_grpc, version_pb2

from . import helpers


class MockVersionService(service_pb2_grpc.VersionServiceServicer):

    def __init__(self, rpc_delay=0):
        """Create mock that returns fake software version."""
        super(MockVersionService, self).__init__()
        self._rpc_delay = rpc_delay

    def GetSoftwareVersion(self, request, context):
        time.sleep(self._rpc_delay)

        response = version_pb2.GetSoftwareVersionResponse()
        response.version.major_version = 1
        response.version.minor_version = 1
        response.version.patch_level = 4
        helpers.add_common_header(response, request)
        return response


def _setup(rpc_delay=0):
    client = bosdyn.client.spot_cam.version.VersionClient()
    service = MockVersionService(rpc_delay=rpc_delay)
    server = helpers.setup_client_and_service(client, service,
                                              service_pb2_grpc.add_VersionServiceServicer_to_server)
    return client, service, server


def test_get_software_version():
    client, service, server = _setup()
    version = client.get_software_version()
    assert version.major_version == 1
    assert version.minor_version == 1
    assert version.patch_level == 4


def test_get_software_version_async():
    client, service, server = _setup()
    version = client.get_software_version_async().result()
    assert version.major_version == 1
    assert version.minor_version == 1
    assert version.patch_level == 4
