# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
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
from bosdyn.client.util import GrpcServiceRunner, setup_logging
from bosdyn.api import image_pb2
from bosdyn.api import image_service_pb2_grpc
from bosdyn.client.image_service_helpers import VisualImageSource, CameraBaseImageServicer, CameraInterface

DIRECTORY_NAME = 'web-cam-service'
AUTHORITY = 'robot-web-cam'
SERVICE_TYPE = 'bosdyn.api.ImageService'

_LOGGER = logging.getLogger(__name__)


class WebCam(CameraInterface):
    """Provide access to the latest web cam data using openCV's VideoCapture."""

    def __init__(self, device_name, fps=30, show_debug_information=False, codec=""):
        self.show_debug_images = show_debug_information

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
            _LOGGER.warn(err)
            raise Exception(err)

        self.capture.set(cv2.CAP_PROP_FPS, fps)

        # Use the codec input argument to determine the  OpenCV 'FourCC' variable is a byte code specifying
        # the video coedc (the compression/decompression software).
        if len(codec) == 4:
            # Converts the codec from a single string to a list of four capitalized characters, then
            # creates a video writer based on those characters and sets this as a property of the
            # main VideoCatpure for the camera.
            self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*codec.upper()))
        elif len(codec) > 0:
            # Non-empty codec string, but it isn't the correct four character string we expect.
            raise Exception("The codec argument provided (%s) is the incorrect format. It should be a four character string." % codec)

        # Attempt to determine the gain and exposure for the camera.
        self.camera_exposure, self.camera_gain = None, None
        try:
            self.camera_gain = self.capture.get(cv2.CAP_PROP_GAIN)
        except cv2.error as e:
            _LOGGER.warn("Unable to determine camera gain: %s", e)
            self.camera_gain = None
        try:
            self.camera_exposure = self.capture.get(cv2.CAP_PROP_EXPOSURE)
        except cv2.error as e:
            _LOGGER.warn("Unable to determine camera exposure time: %s", e)
            self.camera_exposure = None

        # Determine the dimensions of the image.
        self.rows = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.cols = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))

        self.default_jpeg_quality = 75

    def blocking_capture(self):
        # Get the image from the video capture.
        capture_time = time.time()
        success, image = self.capture.read()
        if self.show_debug_images:
            _LOGGER.info("Image Capture Result: %s", str(success))
            try:
                cv2.imshow("WebCam Image Capture", image)
                cv2.waitKey(1)
            except Exception:
                _LOGGER.warn("Unable to display the webcam image captured.")
                pass
        if success:
            return image, capture_time
        else:
            raise Exception("Unsuccessful call to cv2.VideoCapture().read()")

    def image_decode(self, image_data, image_proto, image_format, quality_percent=75):
        # Determine the pixel format for the data.
        if image_data.shape[2] == 3:
            # RGB image.
            image_proto.pixel_format = image_pb2.Image.PIXEL_FORMAT_RGB_U8
        elif image_data.shape[2] == 1:
            # Greyscale image.
            image_proto.pixel_format = image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8
        elif image_data.shape[2] == 4:
            # RGBA image.
            image_proto.pixel_format = image_pb2.Image.PIXEL_FORMAT_RGBA_U8
        else:
            # The number of pixel channels did not match any of the known formats.
            image_proto.pixel_format = image_pb2.Image.PIXEL_FORMAT_UNKNOWN

        # Note, we are currently not setting any information for the transform snapshot or the frame
        # name for an image sensor since this information can't be determined with openCV.

        # Set the image data.
        if image_format == image_pb2.Image.FORMAT_RAW:
            image_proto.data = np.ndarray.tobytes(image_data)
            image_proto.format = image_pb2.Image.FORMAT_RAW
        elif image_format == image_pb2.Image.FORMAT_JPEG or image_format is None:
            # If the image format is requested as JPEG or if no specific image format is requested, return
            # a JPEG. Since this service is for a webcam, we choose a sane default for the return if the
            # request format is unpopulated.
            quality = self.default_jpeg_quality
            if quality_percent > 0 and quality_percent <= 100:
                # A valid image quality percentage was passed with the image request,
                # so use this value instead of the service's default.
                quality = quality_percent
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            image_proto.data = cv2.imencode('.jpg', image_data, encode_param)[1].tobytes()
            image_proto.format = image_pb2.Image.FORMAT_JPEG
        else:
            # Unsupported format.
            raise Exception(
                "Image format %s is unsupported." % image_pb2.Image.Format.Name(image_format))


def device_name_to_source_name(device_name):
    if type(device_name) == int:
        return "video"+str(device_name)
    else:
        return os.path.basename(device_name)


def make_webcam_image_service(bosdyn_sdk_robot, service_name, device_names,
                              show_debug_information=False, logger=None,
                              codec=""):
    image_sources = []
    for device in device_names:
        web_cam = WebCam(device, show_debug_information=show_debug_information, codec=codec)
        img_src = VisualImageSource(web_cam.image_source_name, web_cam, rows=web_cam.rows,
                                    cols=web_cam.cols, gain=web_cam.camera_gain,
                                    exposure=web_cam.camera_exposure)
        image_sources.append(img_src)
    return CameraBaseImageServicer(bosdyn_sdk_robot, service_name, image_sources, logger)


def run_service(bosdyn_sdk_robot, port, service_name, device_names,
                show_debug_information=False, logger=None,
                codec=""):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = image_service_pb2_grpc.add_ImageServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = make_webcam_image_service(bosdyn_sdk_robot, service_name, device_names,
                                                 show_debug_information, logger=logger, codec=codec)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


def add_web_cam_arguments(parser):
    parser.add_argument(
        '--device-name',
        help=('Image source to query. If none are passed, it will default to the first available '
              'source.'), action='append', required=False, default=[])
    parser.add_argument(
        '--show-debug-info', action='store_true', required=False,
        help="If passed, openCV will try to display the captured web cam images.")
    parser.add_argument(
        '--codec', required=False, help="The four character video codec (compression format). For example, " +\
        "this is commonly 'DIVX' on windows or 'MJPG' on linux.", default="")

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
    robot.authenticate_from_payload_credentials(options.guid, options.secret)

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options.port, DIRECTORY_NAME, devices,
                                 options.show_debug_info, logger=_LOGGER,
                                 codec=options.codec)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, SERVICE_TYPE, AUTHORITY, options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()
