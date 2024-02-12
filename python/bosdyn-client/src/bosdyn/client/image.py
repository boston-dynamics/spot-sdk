# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to use the image service."""
import collections
import os
import warnings

import numpy as np

from bosdyn.api import image_pb2, image_service_pb2_grpc
from bosdyn.client.common import (BaseClient, common_header_errors, custom_params_error,
                                  error_factory, error_pair, handle_common_header_errors)
from bosdyn.client.exceptions import ResponseError, UnsetStatusError


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


class UnsupportedPixelFormatRequestedError(ImageResponseError):
    """The image service cannot return data in the requested pixel format."""


class UnsupportedResizeRatioRequestedError(ImageResponseError):
    """The image service cannot return data with the requested resize ratio."""


_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_STATUS_TO_ERROR.update({
    image_pb2.ImageResponse.STATUS_OK: (None, None),
    image_pb2.ImageResponse.STATUS_UNKNOWN_CAMERA:
        error_pair(UnknownImageSourceError),
    image_pb2.ImageResponse.STATUS_SOURCE_DATA_ERROR:
        error_pair(SourceDataError),
    image_pb2.ImageResponse.STATUS_IMAGE_DATA_ERROR:
        error_pair(ImageDataError),
    image_pb2.ImageResponse.STATUS_UNSUPPORTED_IMAGE_FORMAT_REQUESTED:
        error_pair(UnsupportedImageFormatRequestedError),
    image_pb2.ImageResponse.STATUS_UNSUPPORTED_PIXEL_FORMAT_REQUESTED:
        error_pair(UnsupportedPixelFormatRequestedError),
    image_pb2.ImageResponse.STATUS_UNSUPPORTED_RESIZE_RATIO_REQUESTED:
        error_pair(UnsupportedResizeRatioRequestedError),
    image_pb2.ImageResponse.STATUS_UNKNOWN:
        error_pair(UnsetStatusError),
})


@handle_common_header_errors
def _error_from_response(response):
    """Return a custom exception based on the first invalid image response, None if no error."""
    for image_response in response.image_responses:
        result = custom_params_error(image_response, total_response=response)
        if result is not None:
            return result

        result = error_factory(response, image_response.status,
                               status_to_string=image_pb2.ImageResponse.Status.Name,
                               status_to_error=_STATUS_TO_ERROR)
        if result is not None:
            # The exception is using the image_response.  Replace it with the full response.
            result.response = response
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
                         common_header_errors, copy_request=False, **kwargs)

    def list_image_sources_async(self, **kwargs):
        """Async version of list_image_sources()"""
        req = self._get_list_image_source_request()
        return self.call_async(self._stub.ListImageSources, req, _list_image_sources_value,
                               common_header_errors, copy_request=False, **kwargs)

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
        return self.call(self._stub.GetImage, req, _get_image_value, _error_from_response,
                         copy_request=False, **kwargs)

    def get_image_async(self, image_requests, **kwargs):
        """Async version of get_image()"""
        req = self._get_image_request(image_requests)
        return self.call_async(self._stub.GetImage, req, _get_image_value, _error_from_response,
                               copy_request=False, **kwargs)

    @staticmethod
    def _get_image_request(image_requests):
        return image_pb2.GetImageRequest(image_requests=image_requests)

    @staticmethod
    def _get_list_image_source_request():
        return image_pb2.ListImageSourcesRequest()


def build_image_request(image_source_name, quality_percent=75, image_format=None, pixel_format=None,
                        resize_ratio=None):
    """Helper function which builds an ImageRequest from an image source name.

    By default the robot will choose an appropriate format when no image format
    is provided. For example, it will choose JPEG for visual images, or RAW for
    depth images. Clients can provide an image_format for other cases.

    Args:
        image_source_name (string): The image source to query.
        quality_percent (int): The image quality from [0,100] (percent-value).
        image_format (image_pb2.Image.Format): The type of format for the image
                                               data, such as JPEG, RAW, or RLE.
        pixel_format (image_pb2.Image.PixelFormat) The pixel format of the image.
        resize_ratio (double): Resize ratio for image dimensions.

    Returns:
        The ImageRequest protobuf message for the given parameters.
    """
    return image_pb2.ImageRequest(image_source_name=image_source_name,
                                  quality_percent=quality_percent, image_format=image_format,
                                  pixel_format=pixel_format, resize_ratio=resize_ratio)


def _list_image_sources_value(response):
    return response.image_sources


def _get_image_value(response):
    return response.image_responses


def write_pgm_or_ppm(image_response, filename="", filepath=".", include_pixel_format=False):
    """Write raw data from image_response to a PGM file.

    Args:
        image_response (image_pb2.ImageResponse): The ImageResponse proto to parse.
        filename (string): Name of the output file, if None is passed, then "image-{SOURCENAME}.pgm" is used.
        filepath(string): The directory to save the image.
        include_pixel_format(bool): append the pixel format to the image name when generating
                            a filename ("image-{SOURCENAME}-{PIXELFORMAT}.pgm").
    """
    # Determine the data type to decode the image.
    if image_response.shot.image.pixel_format in (image_pb2.Image.PIXEL_FORMAT_DEPTH_U16,
                                                  image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U16):
        dtype = np.uint16
        max_val = np.iinfo(np.uint16).max
    else:
        dtype = np.uint8
        max_val = np.iinfo(np.uint8).max

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
        print(
            "Cannot convert raw image into expected shape (rows %d, cols %d, color channels %d)." %
            (height, width, num_channels))
        print(err)
        return
    if not filename:
        if include_pixel_format:
            filename = "image-{}-{}{}".format(
                image_response.source.name,
                image_pb2.Image.PixelFormat.Name(image_response.shot.image.pixel_format),
                file_extension)
        else:
            filename = "image-{}{}".format(image_response.source.name, file_extension)
    filename = os.path.join(filepath, filename)
    try:
        fd_out = open(filename, 'w')
    except IOError as err:
        print("Cannot open file %s. Exception thrown: %s" % (filename, err))
        return

    pgm_header = pgm_header_number + ' ' + str(width) + ' ' + str(height) + ' ' + str(
        max_val) + '\n'
    fd_out.write(pgm_header)
    img.tofile(fd_out)
    print('Saved matrix with pixel values from camera "%s" to file "%s".' %
          (image_response.source.name, filename))


def write_image_data(image_response, filename="", filepath=".", include_pixel_format=False):
    """Write image data from image_response to a file.

    Args:
        image_response (image_pb2.ImageResponse): The ImageResponse proto to parse.
        filename (string): Name of the output file (including the file extension), if None is
                           passed, then "image-{SOURCENAME}.jpg" is used.
        filepath(string): The directory to save the image.
        include_pixel_format(bool): append the pixel format to the image name when generating
                                    a filename ("image-{SOURCENAME}-{PIXELFORMAT}.jpg").
    """
    if not filename:
        if include_pixel_format:
            filename = 'image-{}-{}.jpg'.format(
                image_response.source.name,
                image_pb2.Image.PixelFormat.Name(image_response.shot.image.pixel_format))
        else:
            filename = 'image-{}.jpg'.format(image_response.source.name)
    filename = os.path.join(filepath, filename)
    try:
        with open(filename, 'wb') as outfile:
            outfile.write(image_response.shot.image.data)
        print('Saved "{}" to "{}".'.format(image_response.source.name, filename))
    except IOError as err:
        print('Failed to save "{}".'.format(image_response.source.name))
        print(err)


def save_images_as_files(image_responses, filename="", filepath=".", include_pixel_format=False):
    """Write image responses to files.

    Args:
        image_responses (List[image_pb2.ImageResponse]): The list of image responses to save.
        filename (string): Name prefix of the output files (made unique by an integer suffix), if None
                           is passed the image source name is used.
        filepath(string): The directory to save the image files.
        include_pixel_format(bool): append the pixel format to the image name when generating
                                    a filename ("image-{SOURCENAME}-{PIXELFORMAT}.jpg").
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
            write_pgm_or_ppm(image, save_file_name, filepath,
                             include_pixel_format=include_pixel_format)
        else:
            # Save jpeg format as a jpeg image.
            write_image_data(image, save_file_name, filepath,
                             include_pixel_format=include_pixel_format)


def pixel_to_camera_space(image_proto, pixel_x, pixel_y, depth=1.0):
    """Using the camera intrinsics, determine the (x,y,z) point in the camera frame for
    the (u,v) pixel coordinates.

    Args:
        image_proto (image_pb2.ImageSource): The image source proto which the pixel coordinates are from.
            Use of image_pb2.ImageCaptureAndSource or image_pb2.ImageResponse types here have been deprecated.
        pixel_x (int): x-coordinate.
        pixel_y (int): y-coordinate.
        depth (double): The depth from the camera to the point of interest.

    Returns:
        An (x,y,z) tuple representing the pixel point of interest now described as a point
        in the camera frame.
    """
    if 'source' in image_proto.ListFields() or isinstance(
            image_proto, image_pb2.ImageResponse) or isinstance(image_proto,
                                                                image_pb2.ImageCaptureAndSource):
        warnings.warn(
            "Use of image_pb2.ImageCaptureAndSource or image_pb2.ImageResponse types for image_proto"
            " argument have been deprecated, use image_pb2.ImageSource instead. version=4.0.0",
            DeprecationWarning, stacklevel=2)
        image_source = image_proto.source
    else:
        image_source = image_proto

    if not image_source.HasField('pinhole'):
        raise ValueError('Requires a pinhole camera_model.')

    focal_x = image_source.pinhole.intrinsics.focal_length.x
    principal_x = image_source.pinhole.intrinsics.principal_point.x

    focal_y = image_source.pinhole.intrinsics.focal_length.y
    principal_y = image_source.pinhole.intrinsics.principal_point.y

    x_rt_camera = depth * (pixel_x - principal_x) / focal_x
    y_rt_camera = depth * (pixel_y - principal_y) / focal_y
    return (x_rt_camera, y_rt_camera, depth)


# Depth images use PIXEL_FORMAT_DEPTH_U16.  A value of 0 or MAX_DEPTH_IMAGE_RANGE
# represents invalid data.
MAX_DEPTH_IMAGE_RANGE = np.iinfo(np.uint16).max


def _depth_image_get_valid_indices(depth_array, min_dist=1, max_dist=MAX_DEPTH_IMAGE_RANGE - 1):
    """Returns an array of indices containing valid depth data.

    Args:
        depth_array: A numpy array representation of the depth data.
        min_dist (uint16): All points in the returned point cloud will be greater than min_dist from the image plane.
        max_dist (uint16): All points in the returned point cloud will be less than max_dist from the image plane.

    Returns:
        A numpy of indices containing valid depth data.
    """
    # Saturate the input to valid values.
    min_dist = np.clip(min_dist, 1, MAX_DEPTH_IMAGE_RANGE - 1)
    max_dist = np.clip(max_dist, 1, MAX_DEPTH_IMAGE_RANGE - 1)

    valid_range_idx = np.logical_and(depth_array >= min_dist, depth_array <= max_dist)
    return valid_range_idx


def _depth_image_data_to_numpy(image_response):
    """Interprets the image data as a numpy array.

    Args:
        image_response (image_pb2.ImageResponse): An ImageResponse containing a depth image.

    Returns:
        A numpy array representation of the depth data.
    """
    depth_array = np.frombuffer(image_response.shot.image.data, dtype=np.uint16)
    depth_array.shape = (image_response.shot.image.rows, image_response.shot.image.cols, -1)
    if depth_array.shape[2] == 1:
        depth_array.shape = depth_array.shape[:2]
    return depth_array


def depth_image_to_pointcloud(image_response, min_dist=0, max_dist=1000):
    """Converts a depth image into a point cloud using the camera intrinsics. The point
    cloud is represented as a numpy array of (x,y,z) values.  Requests can optionally filter
    the results based on the points distance to the image plane. A depth image is represented
    with an unsigned 16-bit integer and a scale factor to convert that distance to meters. In
    addition, values of zero and 2^16 (uint 16 maximum) are used to represent invalid indices.
    A (min_dist * depth_scale) value that casts to an integer value <=0 will be assigned a
    value of 1 (the minimum representational distance). Similarly, a (max_dist * depth_scale)
    value that casts to >= 2^16 will be assigned a value of 2^16 - 1 (the maximum
    representational distance).

    Args:
        image_response (image_pb2.ImageResponse): An ImageResponse containing a depth image.
        min_dist (double): All points in the returned point cloud will be greater than min_dist from the image plane [meters].
        max_dist (double): All points in the returned point cloud will be less than max_dist from the image plane [meters].

    Returns:
        A numpy stack of (x,y,z) values representing depth image as a point cloud expressed in the sensor frame.
    """

    if image_response.source.image_type != image_pb2.ImageSource.IMAGE_TYPE_DEPTH:
        raise ValueError('requires an image_type of IMAGE_TYPE_DEPTH.')

    if image_response.shot.image.pixel_format != image_pb2.Image.PIXEL_FORMAT_DEPTH_U16:
        raise ValueError(
            'IMAGE_TYPE_DEPTH with an unsupported format, requires PIXEL_FORMAT_DEPTH_U16.')

    if not image_response.source.HasField('pinhole'):
        raise ValueError('Requires a pinhole camera_model.')

    source_rows = image_response.source.rows
    source_cols = image_response.source.cols
    fx = image_response.source.pinhole.intrinsics.focal_length.x
    fy = image_response.source.pinhole.intrinsics.focal_length.y
    cx = image_response.source.pinhole.intrinsics.principal_point.x
    cy = image_response.source.pinhole.intrinsics.principal_point.y
    depth_scale = image_response.source.depth_scale

    # Convert the proto representation into a numpy array.
    depth_array = _depth_image_data_to_numpy(image_response)

    # Determine which indices have valid data in the user requested range.
    valid_inds = _depth_image_get_valid_indices(depth_array, np.rint(min_dist * depth_scale),
                                                np.rint(max_dist * depth_scale))

    # Compute the valid data.
    rows, cols = np.mgrid[0:source_rows, 0:source_cols]
    depth_array = depth_array[valid_inds]
    rows = rows[valid_inds]
    cols = cols[valid_inds]

    # Convert the valid distance data to (x,y,z) values expressed in the sensor frame.
    z = depth_array / depth_scale
    x = np.multiply(z, (cols - cx)) / fx
    y = np.multiply(z, (rows - cy)) / fy
    return np.vstack((x, y, z)).T
