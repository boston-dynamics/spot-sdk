# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Register and run the Web Cam Service."""

import logging
import os
import time
import cv2
import numpy as np

import bosdyn.util
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.util import setup_logging
from bosdyn.client.server_util import GrpcServiceRunner
from bosdyn.api import image_pb2
from bosdyn.api import image_service_pb2_grpc
from bosdyn.client.image_service_helpers import (VisualImageSource, CameraBaseImageServicer,
                                                 CameraInterface, convert_RGB_to_grayscale)

DIRECTORY_NAME = 'web-cam-service'
AUTHORITY = 'robot-web-cam'
SERVICE_TYPE = 'bosdyn.api.ImageService'

_LOGGER = logging.getLogger(__name__)


class WebCam(CameraInterface):
    """Provide access to the latest web cam data using openCV's VideoCapture."""

    def __init__(self, device_name):
        # Check if the user is passing an index to a camera port, i.e. "0" to get the first
        # camera in the operating system's enumeration of available devices. The VideoCapture
        # takes either a filepath to the device (as a string), or a index to the device (as an
        # int). Attempt to see if the device name can be cast to an integer before initializing
        # the video capture instance.
        # Someone may pass just the index because on certain operating systems (like Windows),
        # it is difficult to find the path to the device. In contrast, on linux the video
        # devices are all found at /dev/videoXXX locations and it is easier.
        try:
            device_name = int(device_name)
        except ValueError as err:
            # No action if the device cannot be converted. This likely means the device name
            # is some sort of string input -- for example, linux uses the default device ports
            # for cameras as the strings "/dev/video0"
            pass

        # Create the image source name from the device name.
        self.image_source_name = device_name_to_source_name(device_name)

        # OpenCV VideoCapture instance.
        self.capture = cv2.VideoCapture(device_name)
        if not self.capture.isOpened():
            # Unable to open a video capture connection to the specified device.
            err = "Unable to open a cv2.VideoCapture connection to %s" % device_name
            _LOGGER.warning(err)
            raise Exception(err)

        # Attempt to determine the gain and exposure for the camera.
        self.camera_exposure, self.camera_gain = None, None
        try:
            self.camera_gain = self.capture.get(cv2.CAP_PROP_GAIN)
        except cv2.error as e:
            _LOGGER.warning("Unable to determine camera gain: %s", e)
            self.camera_gain = None
        try:
            self.camera_exposure = self.capture.get(cv2.CAP_PROP_EXPOSURE)
        except cv2.error as e:
            _LOGGER.warning("Unable to determine camera exposure time: %s", e)
            self.camera_exposure = None

        # Determine the dimensions of the image.
        self.rows = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.cols = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))

        self.default_jpeg_quality = 75

    def blocking_capture(self):
        # Get the image from the video capture.
        capture_time = time.time()
        success, image = self.capture.read()
        if success:
            return image, capture_time
        else:
            raise Exception("Unsuccessful call to cv2.VideoCapture().read()")

    def image_decode(self, image_data, image_proto, image_req):
        pixel_format = image_req.pixel_format
        # Convert pixel format.
        converted_image_data = image_data
        if pixel_format == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8:
            converted_image_data = convert_RGB_to_grayscale(
                cv2.cvtColor(image_data, cv2.COLOR_BGR2RGB))

        if pixel_format == image_pb2.Image.PIXEL_FORMAT_UNKNOWN:
            # Hardcode to RGB for simplicity.
            image_proto.pixel_format = image_pb2.Image.PIXEL_FORMAT_RGB_U8
        else:
            image_proto.pixel_format = pixel_format

        # Note, we are currently not setting any information for the transform snapshot or the frame
        # name for an image sensor since this information can't be determined with openCV.

        resize_ratio = image_req.resize_ratio
        quality_percent = image_req.quality_percent

        if resize_ratio < 0 or resize_ratio > 1:
            raise ValueError("Resize ratio %s is out of bounds." % resize_ratio)

        if resize_ratio != 1.0 and resize_ratio != 0:
            image_proto.rows = int(image_proto.rows * resize_ratio)
            image_proto.cols = int(image_proto.cols * resize_ratio)
            converted_image_data = cv2.resize(converted_image_data, (image_proto.cols, image_proto.rows),
                                              interpolation = cv2.INTER_AREA)

        # Set the image data.
        image_format = image_req.image_format
        if image_format == image_pb2.Image.FORMAT_RAW:
            image_proto.data = np.ndarray.tobytes(converted_image_data)
            image_proto.format = image_pb2.Image.FORMAT_RAW
        elif image_format == image_pb2.Image.FORMAT_JPEG or image_format == image_pb2.Image.FORMAT_UNKNOWN or image_format is None:
            # If the image format is requested as JPEG or if no specific image format is requested, return
            # a JPEG. Since this service is for a webcam, we choose a sane default for the return if the
            # request format is unpopulated.
            quality = self.default_jpeg_quality
            if 0 < quality_percent <= 100:
                # A valid image quality percentage was passed with the image request,
                # so use this value instead of the service's default.
                quality = quality_percent
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
            image_proto.data = cv2.imencode('.jpg', converted_image_data, encode_param)[1].tobytes()
            image_proto.format = image_pb2.Image.FORMAT_JPEG
        else:
            # Unsupported format.
            raise Exception(
                "Image format %s is unsupported." % image_pb2.Image.Format.Name(image_format))


def device_name_to_source_name(device_name):
    if type(device_name) == int:
        return "video" + str(device_name)
    else:
        return os.path.basename(device_name)


def make_webcam_image_service(bosdyn_sdk_robot, service_name, device_names, logger=None):
    image_sources = []
    for device in device_names:
        web_cam = WebCam(device)
        # Hard-code supported pixel formats in this tutorial file. Please refer to SDK example on
        # how to determine correct list of supported pixel formats.
        img_src = VisualImageSource(web_cam.image_source_name, web_cam, rows=web_cam.rows,
                                    cols=web_cam.cols, gain=web_cam.camera_gain,
                                    exposure=web_cam.camera_exposure,
                                    pixel_formats=[image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8,
                                                   image_pb2.Image.PIXEL_FORMAT_RGB_U8])
        image_sources.append(img_src)
    return CameraBaseImageServicer(bosdyn_sdk_robot, service_name, image_sources, logger)


def run_service(bosdyn_sdk_robot, port, service_name, device_names, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = image_service_pb2_grpc.add_ImageServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = make_webcam_image_service(bosdyn_sdk_robot, service_name, device_names,
                                                 logger=logger)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


def add_web_cam_arguments(parser):
    # Set the default source as index 0 to point to the first
    # available device found by the operating system.
    parser.add_argument(
        '--device-name',
        help=('Image source to query. If none are passed, it will default to the first available '
              'source.'), nargs='*', default=['0'])


if __name__ == '__main__':
    # Define all arguments used by this service.
    import argparse
    parser = argparse.ArgumentParser(allow_abbrev=False)
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    add_web_cam_arguments(parser)
    options = parser.parse_args()

    devices = options.device_name
    if not devices:
        # No sources were provided. Set the default source as index 0 to point to the first
        # available device found by the operating system.
        devices = ["0"]

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose, include_dedup_filter=True)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk("ImageServiceSDK")
    robot = sdk.create_robot(options.hostname)
    robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(options))

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options.port, DIRECTORY_NAME, devices, logger=_LOGGER)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, SERVICE_TYPE, AUTHORITY, options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()
