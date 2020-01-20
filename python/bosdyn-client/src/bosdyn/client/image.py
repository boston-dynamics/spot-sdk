# Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the image service."""

import collections
from bosdyn.client.common import BaseClient
from bosdyn.client.common import (error_factory, common_header_errors, handle_common_header_errors)
from bosdyn.client.exceptions import ResponseError, UnsetStatusError

from bosdyn.api import image_pb2
from bosdyn.api import image_service_pb2_grpc


class ImageResponseError(ResponseError):
    """General class of errors for Image service."""


class UnknownImageSourceError(ImageResponseError):
    """System cannot find the requested image source name."""


class SourceDataError(ImageResponseError):
    """System cannot generate the ImageSource at this time."""


class ImageDataError(ImageResponseError):
    """System cannot generate image data at this time."""


_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_STATUS_TO_ERROR.update({
    image_pb2.ImageResponse.STATUS_OK: (None, None),
    image_pb2.ImageResponse.STATUS_UNKNOWN_CAMERA: (UnknownImageSourceError,
                                                    UnknownImageSourceError.__doc__),
    image_pb2.ImageResponse.STATUS_SOURCE_DATA_ERROR: (SourceDataError, SourceDataError.__doc__),
    image_pb2.ImageResponse.STATUS_IMAGE_DATA_ERROR: (ImageDataError, ImageDataError.__doc__),
})


@handle_common_header_errors
def _error_from_response(response):
    """Return a custom exception based on the first invalid image response, None if no error."""
    for image_response in response.image_responses:
        if image_response.status is image_pb2.ImageResponse.STATUS_UNKNOWN:
            return UnsetStatusError(response, UnsetStatusError.__doc__)

        result = error_factory(response, image_response.status,
                               status_to_string=image_pb2.ImageResponse.Status.Name,
                               status_to_error=_STATUS_TO_ERROR)
        if result is not None:
            return result
    return None


class ImageClient(BaseClient):
    """Client to the image service."""
    default_authority = 'api.spot.robot'
    default_service_name = 'robot_image_service'
    service_type = 'bosdyn.api.ImageService'

    def __init__(self):
        super(ImageClient, self).__init__(image_service_pb2_grpc.ImageServiceStub)

    def list_image_sources(self, **kwargs):
        """ Obtain the list of ImageSources."""
        req = self._get_list_image_source_request()
        return self.call(self._stub.ListImageSources, req, _list_image_sources_value,
                         common_header_errors, **kwargs)

    def list_image_sources_async(self, **kwargs):
        """Async version of list_image_sources()"""
        req = self._get_list_image_source_request()
        return self.call_async(self._stub.ListImageSources, req, _list_image_sources_value,
                               common_header_errors, **kwargs)

    def get_image_from_sources(self, image_sources, **kwargs):
        """Obtain images from sources using default parameters."""
        return self.get_image([build_image_request(source) for source in image_sources], **kwargs)

    def get_image_from_sources_async(self, image_sources, **kwargs):
        """Obtain images from sources using default parameters."""
        return self.get_image_async([build_image_request(source) for source in image_sources],
                                    **kwargs)

    def get_image(self, image_requests, **kwargs):
        """Obtain the set of images from the robot."""
        req = self._get_image_request(image_requests)
        return self.call(self._stub.GetImage, req, _get_image_value, _error_from_response, **kwargs)

    def get_image_async(self, image_requests, **kwargs):
        """Async version of get_image()"""
        req = self._get_image_request(image_requests)
        return self.call_async(self._stub.GetImage, req, _get_image_value, _error_from_response,
                               **kwargs)

    @staticmethod
    def _get_image_request(image_requests):
        return image_pb2.GetImageRequest(image_requests=image_requests)

    @staticmethod
    def _get_list_image_source_request():
        return image_pb2.ListImageSourcesRequest()


def build_image_request(image_source_name, quality_percent=75,
                        image_format=image_pb2.Image.FORMAT_UNKNOWN):
    """Helper function which builds an ImageRequest from an image source name.

    By default the robot will choose an appropriate format - such as JPEG for
    visual images, or RAW for depth images. Clients can override image_format
    in those cases.
    """
    return image_pb2.ImageRequest(image_source_name=image_source_name,
                                  quality_percent=quality_percent, image_format=image_format)


def _list_image_sources_value(response):
    return response.image_sources


def _get_image_value(response):
    return response.image_responses
