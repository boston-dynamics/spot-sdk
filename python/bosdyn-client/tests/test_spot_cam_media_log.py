# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the Spot CAM's MediaLogClient."""
import time

import grpc
import pytest

import bosdyn.client.spot_cam.media_log
from bosdyn.api.spot_cam import camera_pb2, logging_pb2, service_pb2_grpc
from bosdyn.client.exceptions import TimedOutError

from . import helpers


class MockMediaLogService(service_pb2_grpc.MediaLogServiceServicer):

    def __init__(self, rpc_delay=0):
        """Create mock that returns fake media."""
        super(MockMediaLogService, self).__init__()
        self._rpc_delay = rpc_delay

    def Delete(self, request, context):
        time.sleep(self._rpc_delay)

        response = logging_pb2.DeleteResponse()
        helpers.add_common_header(response, request)
        return response

    def EnableDebug(self, request, context):
        time.sleep(self._rpc_delay)

        response = logging_pb2.DebugResponse()
        helpers.add_common_header(response, request)
        return response

    def GetStatus(self, request, context):
        time.sleep(self._rpc_delay)

        response = logging_pb2.GetStatusResponse()
        helpers.add_common_header(response, request)
        response.point.CopyFrom(request.point)
        return response

    def ListCameras(self, request, context):
        time.sleep(self._rpc_delay)

        response = logging_pb2.ListCamerasResponse()
        helpers.add_common_header(response, request)
        return response

    def ListLogpoints(self, request, context):
        time.sleep(self._rpc_delay)

        response = logging_pb2.ListLogpointsResponse()
        helpers.add_common_header(response, request)
        yield response

    def Retrieve(self, request, context):
        time.sleep(self._rpc_delay)

        response = logging_pb2.RetrieveResponse()
        helpers.add_common_header(response, request)
        response.logpoint.CopyFrom(request.point)
        yield response

    def RetrieveRawData(self, request, context):
        time.sleep(self._rpc_delay)

        response = logging_pb2.RetrieveRawDataResponse()
        helpers.add_common_header(response, request)
        response.logpoint.CopyFrom(request.point)
        yield response

    def SetPassphrase(self, request, context):
        time.sleep(self._rpc_delay)

        response = logging_pb2.SetPassphraseResponse()
        helpers.add_common_header(response, request)
        return response

    def Store(self, request, context):
        time.sleep(self._rpc_delay)

        response = logging_pb2.StoreResponse()
        helpers.add_common_header(response, request)
        response.point.name = request.camera.name
        response.point.type = request.type
        response.point.tag = request.tag
        return response

    def Tag(self, request, context):
        time.sleep(self._rpc_delay)

        response = logging_pb2.TagResponse()
        helpers.add_common_header(response, request)
        return response


def _setup(rpc_delay=0):
    client = bosdyn.client.spot_cam.media_log.MediaLogClient()
    service = MockMediaLogService(rpc_delay=rpc_delay)
    server = helpers.setup_client_and_service(
        client, service, service_pb2_grpc.add_MediaLogServiceServicer_to_server)
    return client, service, server


def _create_fake_logpoint(name='fake-logpoint', record_type=logging_pb2.Logpoint.STILLIMAGE,
                          status=logging_pb2.Logpoint.COMPLETE, tag='fake-logpoint-tag'):
    logpoint = logging_pb2.Logpoint()
    logpoint.name = name
    logpoint.type = record_type
    logpoint.status = status
    logpoint.tag = tag
    return logpoint


def test_delete():
    client, service, server = _setup()
    completed_lp = _create_fake_logpoint()
    client.delete(completed_lp)


def test_delete_async():
    client, service, server = _setup()
    completed_lp = _create_fake_logpoint()
    client.delete_async(completed_lp).result()


def test_enable_debug():
    client, service, server = _setup()
    client.enable_debug()


def test_enable_debug_async():
    client, service, server = _setup()
    client.enable_debug_async().result()


def test_get_status():
    client, service, server = _setup()
    completed_lp = _create_fake_logpoint()
    lp = client.get_status(completed_lp)
    assert lp.status == logging_pb2.Logpoint.COMPLETE


def test_get_status_async():
    client, service, server = _setup()
    completed_lp = _create_fake_logpoint()
    lp = client.get_status_async(completed_lp).result()
    assert lp.status == logging_pb2.Logpoint.COMPLETE


def test_get_status_timeout():
    timeout = 0.1
    client, service, server = _setup(rpc_delay=(2.0 * timeout))
    completed_lp = _create_fake_logpoint()

    with pytest.raises(TimedOutError):
        lp = client.get_status(completed_lp, timeout=timeout)


def test_get_status_async_timeout():
    timeout = 0.1
    client, service, server = _setup(rpc_delay=(2.0 * timeout))
    completed_lp = _create_fake_logpoint()

    with pytest.raises(TimedOutError):
        lp = client.get_status_async(completed_lp, timeout=timeout).result()


def test_list_cameras():
    client, service, server = _setup()
    cameras = client.list_cameras()
    assert len(cameras) == 0


def test_list_cameras_async():
    client, service, server = _setup()
    cameras = client.list_cameras_async().result()
    assert len(cameras) == 0


def test_list_logpoints():
    client, service, server = _setup()
    lps = client.list_logpoints()
    assert len(lps) == 0


def test_retrieve():
    client, service, server = _setup()
    completed_lp = _create_fake_logpoint()
    lp, image_binary = client.retrieve(completed_lp)
    assert lp.SerializeToString() == completed_lp.SerializeToString()
    assert len(image_binary) == 0


def test_retrieve_raw_data():
    client, service, server = _setup()
    completed_lp = _create_fake_logpoint()
    lp, image_binary = client.retrieve_raw_data(completed_lp)
    assert lp.SerializeToString() == completed_lp.SerializeToString()
    assert len(image_binary) == 0


def test_set_passphrase():
    client, service, server = _setup()
    client.set_passphrase('good')


def test_set_passphrase_async():
    client, service, server = _setup()
    client.set_passphrase_async('good').result()


def test_store():
    client, service, server = _setup()
    camera = camera_pb2.Camera()
    camera.name = 'pano'
    camera_tag = '{}-tag'.format(camera.name)
    lp = client.store(camera, logging_pb2.Logpoint.STILLIMAGE, camera_tag)
    assert lp.name == camera.name
    assert lp.type == logging_pb2.Logpoint.STILLIMAGE
    assert lp.tag == camera_tag


def test_store_async():
    client, service, server = _setup()
    camera = camera_pb2.Camera()
    camera.name = 'pano'
    camera_tag = '{}-tag'.format(camera.name)
    lp = client.store_async(camera, logging_pb2.Logpoint.STILLIMAGE, camera_tag).result()
    assert lp.name == camera.name
    assert lp.type == logging_pb2.Logpoint.STILLIMAGE
    assert lp.tag == camera_tag


def test_tag():
    client, service, server = _setup()
    completed_lp = _create_fake_logpoint()
    client.tag(completed_lp)


def test_tag_async():
    client, service, server = _setup()
    completed_lp = _create_fake_logpoint()
    client.tag_async(completed_lp).result()
