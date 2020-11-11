# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to use the image service."""

import collections
from bosdyn.client.common import BaseClient
from bosdyn.client.common import (error_factory, error_pair, common_header_errors, handle_common_header_errors)
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

class UnsupportedImageFormatRequestedError(ImageResponseError):
    """The image service cannot return data in this format."""

_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_STATUS_TO_ERROR.update({
    image_pb2.ImageResponse.STATUS_OK: (None, None),
    image_pb2.ImageResponse.STATUS_UNKNOWN_CAMERA: error_pair(UnknownImageSourceError),
    image_pb2.ImageResponse.STATUS_SOURCE_DATA_ERROR: error_pair(SourceDataError),
    image_pb2.ImageResponse.STATUS_IMAGE_DATA_ERROR: error_pair(ImageDataError),
    image_pb2.ImageResponse.STATUS_UNSUPPORTED_IMAGE_FORMAT_REQUESTED: error_pair(UnsupportedImageFormatRequestedError),
    image_pb2.ImageResponse.STATUS_UNKNOWN: error_pair(UnsetStatusError),
})


@handle_common_header_errors
def _error_from_response(response):
    """Return a custom exception based on the first invalid image response, None if no error."""
    for image_response in response.image_responses:
        result = error_factory(response, image_response.status,
                               status_to_string=image_pb2.ImageResponse.Status.Name,
                               status_to_error=_STATUS_TO_ERROR)
        if result is not None:
            return result
    return None


class ImageClient(BaseClient):
    """Client for the image service."""
    default_service_name = 'image'
    service_type = 'bosdyn.api.ImageService'

    def __init__(self):
        super(ImageClient, self).__init__(image_service_pb2_grpc.ImageServiceStub)

    def list_image_sources(self, **kwargs):
        """ Obtain the list of ImageSources.

        Returns:
            A list of the different image sources as strings.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_list_image_source_request()
        return self.call(self._stub.ListImageSources, req, _list_image_sources_value,
                         common_header_errors, **kwargs)

    def list_image_sources_async(self, **kwargs):
        """Async version of list_image_sources()"""
        req = self._get_list_image_source_request()
        return self.call_async(self._stub.ListImageSources, req, _list_image_sources_value,
                               common_header_errors, **kwargs)

    def get_image_from_sources(self, image_sources, **kwargs):
        """Obtain images from sources using default parameters.

        Args:
            image_sources (list of strings): The different image sources to request images from.

        Returns:
            A list of image responses for each of the requested sources.

        Raises:
            RpcError: Problem communicating with the robot.
            UnknownImageSourceError: Provided image source was invalid or not found
            image.SourceDataError: Failed to fill out ImageSource. All other fields are not filled
            UnsetStatusError: An internal ImageService issue has happened
            ImageDataError: Problem with the image data. Only ImageSource is filled
        """
        return self.get_image([build_image_request(source) for source in image_sources], **kwargs)

    def get_image_from_sources_async(self, image_sources, **kwargs):
        """Obtain images from sources using default parameters."""
        return self.get_image_async([build_image_request(source) for source in image_sources],
                                    **kwargs)

    def get_image(self, image_requests, **kwargs):
        """Obtain the set of images from the robot.

        Args:
            image_requests (list of ImageRequest): A list of the ImageRequest protobuf messages which
                                                   specify which images to collect.

        Returns:
            A list of image responses for each of the requested sources.

        Raises:
            RpcError: Problem communicating with the robot.
            UnknownImageSourceError: Provided image source was invalid or not found
            image.SourceDataError: Failed to fill out ImageSource. All other fields are not filled
            UnsetStatusError: An internal ImageService issue has happened
            ImageDataError: Problem with the image data. Only ImageSource is filled
        """
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

    Args:
        image_source_name (string): The image source to query.
        quality_percent (int): The image quality from [0,100] (percent-value).
        image_format (image_pb2.Image.Format): The type of format for the image
                                               data, such as JPEG, RAW, or RLE.

    Returns:
        The ImageRequest protobuf message for the given parameters.
    """
    return image_pb2.ImageRequest(image_source_name=image_source_name,
                                  quality_percent=quality_percent, image_format=image_format)


def _list_image_sources_value(response):
    return response.image_sources


def _get_image_value(response):
    return response.image_responses
