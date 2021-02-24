# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to use the image service."""
import os
import numpy as np
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
    """System cannot generate image data for the ImageCapture at this time."""

class UnsupportedImageFormatRequestedError(ImageResponseError):
    """The image service cannot return data in the requested format."""

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
                        image_format=None):
    """Helper function which builds an ImageRequest from an image source name.

    By default the robot will choose an appropriate format when no image format
    is provided. For example, it will choose JPEG for visual images, or RAW for
    depth images. Clients can provide an image_format for other cases.

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


def write_pgm_or_ppm(image_response, filename="", filepath="."):
    """Write raw data from image_response to a PGM file.

    Args:
        image_response (image_pb2.ImageResponse): The ImageResponse proto to parse.
        filename (string): Name of the output file, if None is passed, then "image-{SOURCENAME}.pgm" is used.
        filepath(string): The directory to save the image.
    """
    # Determine the data type to decode the image.
    if image_response.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_DEPTH_U16:
        dtype = np.uint16
    else:
        dtype = np.uint8

    num_channels = 1
    pgm_header_number = 'P5'
    file_extension = ".pgm"
    # Determine the pixel format to get the number of channels the data comes in.
    if image_response.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_RGB_U8:
        num_channels = 3
        pgm_header_number = 'P6'
        file_extension = ".ppm"
    elif image_response.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_RGBA_U8:
        print("PGM/PPM format does not support RGBA encodings.")
        return
    elif image_response.shot.image.pixel_format in (image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8,
                                                    image_pb2.Image.PIXEL_FORMAT_DEPTH_U16,
                                                    image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U16):
        num_channels = 1
    else:
        print("Unsupported pixel format for PGM/PPM: %s." %
            image_pb2.Image.PixelFormat.Name(image_response.shot.image.pixel_format))
        return

    img = np.frombuffer(image_response.shot.image.data, dtype=dtype)
    height = image_response.shot.image.rows
    width = image_response.shot.image.cols
    try:
        img = img.reshape((height, width, num_channels))
    except ValueError as err:
        print("Cannot convert raw image into expected shape (rows %d, cols %d, color channels %d)." % (height, width, num_channels))
        print(err)
        return
    if not filename:
        image_source_filename = "image-%s%s" % (image_response.source.name, file_extension)
        filename = image_source_filename
    filename = os.path.join(filepath, filename)
    try:
        fd_out = open(filename, 'w')
    except IOError as err:
        print("Cannot open file %s. Exception thrown: %s" % (filename, err))
        return

    max_val = np.amax(img)
    pgm_header = pgm_header_number + ' ' + str(width) + ' ' + str(height) + ' ' + str(max_val) + '\n'
    fd_out.write(pgm_header)
    img.tofile(fd_out)
    print('Saved matrix with pixel values from camera "%s" to file "%s".' % (
        image_response.source.name, filename))

def write_image_data(image_response, filename="", filepath="."):
    """Write image data from image_response to a file.

    Args:
        image_response (image_pb2.ImageResponse): The ImageResponse proto to parse.
        filename (string): Name of the output file (including the file extension), if None is
                           passed, then "image-{SOURCENAME}.jpg" is used.
        filepath(string): The directory to save the image.
    """
    if not filename:
        image_source_filename = 'image-{}.jpg'.format(image_response.source.name)
        filename = image_source_filename
    filename = os.path.join(filepath, filename)
    try:
        with open(filename, 'wb') as outfile:
            outfile.write(image_response.shot.image.data)
        print('Saved "{}" to "{}".'.format(image_response.source.name, filename))
    except IOError as err:
        print('Failed to save "{}".'.format(image_response.source.name))
        print(err)

def save_images_as_files(image_responses, filename="", filepath="."):
    """Write image responses to files.

    Args:
        image_responses (List[image_pb2.ImageResponse]): The list of image responses to save.
        filename (string): Name prefix of the output files (made unique by an integer suffix), if None
                           is passed the image source name is used.
        filepath(string): The directory to save the image files.
    """
    for index, image in enumerate(image_responses):
        save_file_name = ""
        if filename:
            # Add a suffix of the index of the image to ensure the filename is unique.
            save_file_name = filename + str(index)
        if image.shot.image.format == image_pb2.Image.FORMAT_UNKNOWN:
            # Don't save an image with no format.
            continue
        elif not image.shot.image.format == image_pb2.Image.FORMAT_JPEG:
            # Save raw and rle sources as text files with the full matrix saved as text values. The matrix will
            # be of size: rows X cols X color channels. Color channels is determined through the pixel format.
            write_pgm_or_ppm(image, save_file_name, filepath)
        else:
            # Save jpeg format as a jpeg image.
            write_image_data(image, save_file_name, filepath)