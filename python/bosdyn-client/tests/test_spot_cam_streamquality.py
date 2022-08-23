# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the Spot CAM's StreamQualityClient."""
import time

import grpc
import pytest

import bosdyn.client.spot_cam.streamquality
from bosdyn.api.spot_cam import service_pb2_grpc, streamquality_pb2

from . import helpers


class MockStreamQualityService(service_pb2_grpc.StreamQualityServiceServicer):

    def __init__(self, rpc_delay=0):
        """Create mock that returns fake stream parameters."""
        super(MockStreamQualityService, self).__init__()
        self._rpc_delay = rpc_delay

    def GetStreamParams(self, request, context):
        time.sleep(self._rpc_delay)

        response = streamquality_pb2.GetStreamParamsResponse()
        response.params.CopyFrom(_mock_stream_params())
        helpers.add_common_header(response, request)
        return response

    def SetStreamParams(self, request, context):
        time.sleep(self._rpc_delay)

        response = streamquality_pb2.SetStreamParamsResponse()
        response.params.CopyFrom(request.params)
        helpers.add_common_header(response, request)
        return response


def _setup(rpc_delay=0):
    client = bosdyn.client.spot_cam.streamquality.StreamQualityClient()
    service = MockStreamQualityService(rpc_delay=rpc_delay)
    server = helpers.setup_client_and_service(
        client, service, service_pb2_grpc.add_StreamQualityServiceServicer_to_server)
    return client, service, server


def _mock_stream_params(target_bitrate=100, refresh_interval=10, idr_interval=1,
                        awb_mode=streamquality_pb2.StreamParams.AUTO):
    sp = streamquality_pb2.StreamParams()
    sp.targetbitrate.value = target_bitrate
    sp.refreshinterval.value = refresh_interval
    sp.idrinterval.value = idr_interval
    sp.awb.CopyFrom(streamquality_pb2.StreamParams.AwbMode(awb=awb_mode))
    return sp


def test_set_stream_params():
    client, service, server = _setup()
    mock = _mock_stream_params()
    result = client.set_stream_params(mock.targetbitrate.value, mock.refreshinterval.value,
                                      mock.idrinterval.value, mock.awb.awb)
    assert result.SerializeToString() == mock.SerializeToString()


def test_set_stream_params_async():
    client, service, server = _setup()
    mock = _mock_stream_params()
    result = client.set_stream_params_async(mock.targetbitrate.value, mock.refreshinterval.value,
                                            mock.idrinterval.value, mock.awb.awb).result()
    assert result.SerializeToString() == mock.SerializeToString()


def test_get_stream_params():
    client, service, server = _setup()
    mock = _mock_stream_params()
    result = client.get_stream_params()
    assert result.SerializeToString() == mock.SerializeToString()


def test_get_stream_params():
    client, service, server = _setup()
    mock = _mock_stream_params()
    result = client.get_stream_params_async().result()
    assert result.SerializeToString() == mock.SerializeToString()
