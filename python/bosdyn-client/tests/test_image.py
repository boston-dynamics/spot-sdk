# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the image client."""
import logging
import time

import grpc
import pytest

import bosdyn.api.image_pb2 as image_protos
import bosdyn.api.image_service_pb2_grpc as image_service
import bosdyn.client.image
from bosdyn.api.service_customization_pb2 import CustomParamError
from bosdyn.client.exceptions import TimedOutError

from . import helpers


class MockImageServicer(image_service.ImageServiceServicer):

    def __init__(self, rpc_delay=0, image_sources=[], image_responses=[],
                 expected_image_sources=[]):
        """Create mock that returns specific token after optional delay."""
        super(MockImageServicer, self).__init__()
        self._rpc_delay = rpc_delay
        self._image_sources = image_sources
        self._expected_image_sources = expected_image_sources
        self._image_responses = image_responses

    def ListImageSources(self, request, context):
        """Implement the ListImageSources function of the service.

        This is simply implemented as a mock version, rather than full version.
        """
        resp = image_protos.ListImageSourcesResponse()
        helpers.add_common_header(resp, request)
        if self._image_sources:
            resp.image_sources.extend(self._image_sources)
        time.sleep(self._rpc_delay)
        return resp

    def GetImage(self, request, context):
        """Implement the GetImage function of the service."""
        resp = image_protos.GetImageResponse()
        helpers.add_common_header(resp, request)
        assert len(self._expected_image_sources) == len(request.image_requests)
        for image_request in request.image_requests:
            assert image_request.image_source_name in self._expected_image_sources
        if self._image_responses:
            resp.image_responses.extend(self._image_responses)
        time.sleep(self._rpc_delay)
        return resp


def _setup(rpc_delay=0, image_sources=[], image_responses=[], expected_image_sources=[]):
    client = bosdyn.client.image.ImageClient()
    service = MockImageServicer(rpc_delay=rpc_delay, image_sources=image_sources,
                                image_responses=image_responses,
                                expected_image_sources=expected_image_sources)
    server = helpers.setup_client_and_service(client, service,
                                              image_service.add_ImageServiceServicer_to_server)
    return client, service, server


def test_list_sources_empty():
    client, service, server = _setup()
    result = client.list_image_sources()
    assert 0 == len(result)


def test_list_sources_empty_async():
    client, service, server = _setup()
    fut = client.list_image_sources_async()
    assert 0 == len(fut.result())


def test_list_sources_timeout():
    timeout = 0.1
    client, service, server = _setup(rpc_delay=(2.0 * timeout))
    with pytest.raises(TimedOutError):
        result = client.list_image_sources(timeout=timeout)


def test_list_sources_timeout_async():
    timeout = 0.1
    client, service, server = _setup(rpc_delay=(2.0 * timeout))
    fut = client.list_image_sources_async(timeout=timeout)
    with pytest.raises(TimedOutError):
        result = fut.result()


def test_list_sources_single():
    image_source = image_protos.ImageSource()
    client, service, server = _setup(image_sources=[image_source])
    assert 1 == len(client.list_image_sources())


def test_list_sources_single_async():
    image_source = image_protos.ImageSource()
    client, service, server = _setup(image_sources=[image_source])
    fut = client.list_image_sources_async()
    assert 1 == len(fut.result())


def test_list_sources_multiple():
    image_source_a = image_protos.ImageSource()
    image_source_b = image_protos.ImageSource()
    client, service, server = _setup(image_sources=[image_source_a, image_source_b])
    assert 2 == len(client.list_image_sources())


def test_list_sources_single_async():
    image_source_a = image_protos.ImageSource()
    image_source_b = image_protos.ImageSource()
    client, service, server = _setup(image_sources=[image_source_a, image_source_b])
    fut = client.list_image_sources_async()
    assert 2 == len(fut.result())


def test_get_image_sources_empty():
    client, service, server = _setup()
    res = client.get_image_from_sources(image_sources=[])


def test_get_image_source_unset():
    image_response = image_protos.ImageResponse()
    client, service, server = _setup(expected_image_sources=['foo'],
                                     image_responses=[image_response])
    with pytest.raises(bosdyn.client.exceptions.UnsetStatusError):
        res = client.get_image_from_sources(image_sources=['foo'])


def test_get_image_source_unset_async():
    image_response = image_protos.ImageResponse()
    client, service, server = _setup(expected_image_sources=['foo'],
                                     image_responses=[image_response])
    fut = client.get_image_from_sources_async(image_sources=['foo'])
    with pytest.raises(bosdyn.client.exceptions.UnsetStatusError):
        res = fut.result()


def test_get_image_source_ok():
    image_response = image_protos.ImageResponse(status=image_protos.ImageResponse.STATUS_OK)
    client, service, server = _setup(expected_image_sources=['foo'],
                                     image_responses=[image_response])
    res = client.get_image_from_sources(image_sources=['foo'])
    assert 1 == len(res)


def test_get_image_source_async_ok():
    image_response = image_protos.ImageResponse(status=image_protos.ImageResponse.STATUS_OK)
    client, service, server = _setup(expected_image_sources=['foo'],
                                     image_responses=[image_response])
    fut = client.get_image_from_sources_async(image_sources=['foo'])
    assert 1 == len(fut.result())


def test_get_image_source_unknown_camera():
    image_response = image_protos.ImageResponse(
        status=image_protos.ImageResponse.STATUS_UNKNOWN_CAMERA)
    client, service, server = _setup(expected_image_sources=['foo'],
                                     image_responses=[image_response])
    with pytest.raises(bosdyn.client.image.UnknownImageSourceError):
        res = client.get_image_from_sources(image_sources=['foo'])


def test_get_image_source_unknown_and_known_camera():
    image_response_unknown = image_protos.ImageResponse(
        status=image_protos.ImageResponse.STATUS_UNKNOWN_CAMERA)
    image_response_ok = image_protos.ImageResponse(status=image_protos.ImageResponse.STATUS_OK)
    client, service, server = _setup(expected_image_sources=['foo', 'bar'],
                                     image_responses=[image_response_ok, image_response_unknown])
    with pytest.raises(bosdyn.client.image.UnknownImageSourceError):
        res = client.get_image_from_sources(image_sources=['foo', 'bar'])


def test_get_image_source_data_error():
    image_response = image_protos.ImageResponse(
        status=image_protos.ImageResponse.STATUS_SOURCE_DATA_ERROR)
    client, service, server = _setup(expected_image_sources=['foo'],
                                     image_responses=[image_response])
    with pytest.raises(bosdyn.client.image.SourceDataError):
        res = client.get_image_from_sources(image_sources=['foo'])


def test_get_image_source_data_error():
    image_response = image_protos.ImageResponse(
        status=image_protos.ImageResponse.STATUS_IMAGE_DATA_ERROR)
    client, service, server = _setup(expected_image_sources=['foo'],
                                     image_responses=[image_response])
    with pytest.raises(bosdyn.client.image.ImageDataError):
        res = client.get_image_from_sources(image_sources=['foo'])


def test_get_image_custom_params_errror():
    image_response = image_protos.ImageResponse(
        status=image_protos.ImageResponse.STATUS_CUSTOM_PARAMS_ERROR)
    image_response.custom_param_error.status = CustomParamError.STATUS_UNSUPPORTED_PARAMETER
    image_response.custom_param_error.error_messages.append('Bad param added.')
    client, service, server = _setup(expected_image_sources=['foo'],
                                     image_responses=[image_response])
    with pytest.raises(bosdyn.client.CustomParamError) as excinfo:
        res = client.get_image_from_sources(image_sources=['foo'])
    assert excinfo.value.custom_param_error.status == CustomParamError.STATUS_UNSUPPORTED_PARAMETER
