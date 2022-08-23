# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from __future__ import absolute_import, print_function

import io
import json
import logging
import sys
import time
from datetime import datetime

import numpy as np
from PIL import Image
# Ricoh Theta
from ricoh_theta import Theta

# Payload Registration
import bosdyn.api.payload_pb2 as payload_protos
import bosdyn.client
import bosdyn.client.util
from bosdyn.api import image_pb2, image_service_pb2_grpc, service_fault_pb2
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.fault import FaultClient
from bosdyn.client.image_service_helpers import (CameraBaseImageServicer, CameraInterface,
                                                 VisualImageSource, convert_RGB_to_grayscale)
from bosdyn.client.server_util import GrpcServiceRunner
from bosdyn.client.util import setup_logging

# Create a virtual payload.
PLACEHOLDER_PAYLOAD = payload_protos.Payload()
PLACEHOLDER_PAYLOAD.name = 'Ricoh Theta Image Service'
PLACEHOLDER_PAYLOAD.description = 'This is currently a virtual/weightless payload defined for the software service only. \
                                   Please define weight and dimensions if the Ricoh Theta is mounted to Spot.'

# See https://dev.bostondynamics.com/docs/payload/configuring_payload_software#registering-payloads for more information.

DIRECTORY_NAME = 'ricoh-theta-image-service'
AUTHORITY = 'robot-ricoh-theta'
SERVICE_TYPE = 'bosdyn.api.ImageService'

_LOGGER = logging.getLogger(__name__)

# Define ServiceFaultIds for possible faults that will be thrown by the Ricoh Theta image service.
CAMERA_SETUP_FAULT = service_fault_pb2.ServiceFault(
    fault_id=service_fault_pb2.ServiceFaultId(fault_name='Ricoh Theta Initialization Failure',
                                              service_name=DIRECTORY_NAME),
    severity=service_fault_pb2.ServiceFault.SEVERITY_CRITICAL)


class RicohThetaServiceHelper(CameraInterface):

    def __init__(self, theta_ssid, theta_instance, logger=None, live_stream=False,
                 capture_continuously=False):
        # Setup the logger.
        self.logger = logger or _LOGGER

        # Save whether or not we are capturing continuously. If we are not, but live stream is
        # enabled, then we should wipe the generator and start a new stream at the latest.
        self.capture_continuously = capture_continuously

        # Boolean indicating which capture method: True = fast mjpeg captures with lower quality stitching, and
        # False = slower jpeg captures with high quality stitching
        self.live_stream = live_stream

        # Name of the image source that is being requested from.
        self.theta_ssid = theta_ssid
        self.image_source_name = "RicohTheta_" + theta_ssid

        # Default value for JPEG image quality, in case one is not provided in the GetImage request.
        self.default_jpeg_quality = 95

        self.camera = theta_instance
        self.rows = None
        self.cols = None
        self.camera_gain = None
        self.camera_exposure = None

        try:
            self.camera_gain, self.camera_exposure = self.camera.getCaptureParameters(
                print_to_screen=False)
        except Exception as err:
            # An issue occurred getting the file format for the camera images. This is likely due
            # to upstream failures creating the Theta instance, which already have triggered service
            # faults.
            _LOGGER.info("Unable to set the image width/height dimensions. Error message: %s %s",
                         str(type(err)), str(err))
            pass

        self.mjpeg_generator = None
        self._maybe_reset_mjpeg_generator()

        # Request the image format (height, width) from the camera.
        if not self.live_stream:
            format_json = None
            try:
                format_json = self.camera.getFileFormat(print_to_screen=False)
            except Exception as err:
                # An issue occurred getting the file format for the camera images. This is likely due
                # to upstream failures creating the Theta instance, which already have triggered service
                # faults.
                _LOGGER.info(
                    "Unable to set the image width/height dimensions. Error message: %s %s",
                    str(type(err)), str(err))
                pass
            if format_json is not None:
                print(format_json)
                self.cols = format_json["width"]
                self.rows = format_json["height"]
        else:
            # The live stream has different dimensions then the full ricoh theta image because it
            # is lower resolution and doesn't have the full image processing as the regular ricoh
            # theta still captures. There is no easy way with the API requests to get the dimensions of
            # the mjpeg, so we will just take the first image and decode it to get the size.
            if self.mjpeg_generator is not None:
                image_data = next(self.mjpeg_generator)
                pil_image = Image.open(io.BytesIO(image_data))
                self.cols = pil_image.size[0]
                self.rows = pil_image.size[1]
            else:
                _LOGGER.info("Unable to set the image dimensions because no mjpeg generator.")
                pass

    def _maybe_reset_mjpeg_generator(self):
        """Reset the generator which reads from the mjpeg stream.

        This is used to help catch up the live stream generator to the latest/most recent
        images being viewed from the camera.
        """
        if self.live_stream:
            try:
                self.mjpeg_generator = self.camera.yieldLivePreview(print_to_screen=False)
            except Exception as err:
                _LOGGER.info("Error in creating the live preview: %s %s", str(type(err)), str(err))
                # Default to original capture method.
                self.live_stream = False

    def blocking_capture(self):
        """Take an image and download the processed image to local memory from the Ricoh Theta camera.

        Returns:
            The complete image's json data and a buffer of the image bytes.
        """
        if self.camera is None:
            raise Exception("The Ricoh Theta camera instance is not initialized.")

        if not self.capture_continuously and self.live_stream:
            self._maybe_reset_mjpeg_generator()

        # Send the request to take a picture
        capture_time_secs = time.time()

        # If we are in "live_stream" mode, then just return the next result of the generator that reads from
        # the motion jpeg live preview. .
        if self.live_stream and self.mjpeg_generator is not None:
            buffer_bytes = next(self.mjpeg_generator)
            return buffer_bytes, capture_time_secs

        # Otherwise, request to take a picture (blocking) and download the image.
        self.camera.takePicture(print_to_screen=False)
        img_json, img_raw = self.camera.getLastImage(wait_for_latest=True, print_to_screen=False)
        if not (img_json and img_raw):
            # The getLastImage request failed, return None.
            _LOGGER.warning("The getLastImage request to the Ricoh Theta returned no data.")
            raise Exception("The takePicture Request for the Ricoh Theta returned no data.")

        buffer_bytes = img_raw.raw
        buffer_bytes.decode_content = True

        # Attempt to determine the capture timestamp for the image using the date time zone string returned
        # from the ricoh theta camera. If this fails, we will fall back to the timestamp saved right when
        # the capture was triggered.
        try:
            # Split on the "+" and "-" to remove the timezone information from the string. Note, on python 3.6
            # the time zone parsing in strptime does not correctly parse a timezone with a semicolon, and the
            # ricoh theta's output includes this. So for now, we use this string splitting to just remove the
            # timezone entirely.
            date_time = img_json["dateTimeZone"].split("+")[0].split("-")[0]
            # Convert from string to an actual datetime object
            date_time_obj = time.strptime(date_time, "%Y:%m:%d %H:%M:%S")
            # Convert from a datetime object to a time object (seconds) in the local clock's time.
            capture_time_secs = time.mktime(date_time_obj)
        except Exception as err:
            # Part of the datetime string parsing failed. Therefore just use the saved capture_time_secs.
            pass

        # Return the result of reading the image into local memory. Apparently, the action of reading the buffer can
        # only be performed one time unless it is converted to a stream or copied.
        return buffer_bytes.read(), capture_time_secs

    def image_decode(self, image_data, image_proto, image_req):
        pixel_format = image_req.pixel_format
        image_format = image_req.image_format

        converted_image_data = Image.open(io.BytesIO(image_data))
        if pixel_format == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8:
            converted_image_data_np = convert_RGB_to_grayscale(np.asarray(converted_image_data))
            # Convert back to Pillow.
            converted_image_data = Image.fromarray(np.uint8(converted_image_data_np))
            image_proto.pixel_format = pixel_format
        else:
            image_proto.pixel_format = image_pb2.Image.PIXEL_FORMAT_RGB_U8

        # Note, we are currently not setting any information for the transform snapshot or the frame
        # name for an image sensor since this information can't be determined with HTTP calls to ricoh
        # theta's api.

        resize_ratio = image_req.resize_ratio
        quality_percent = image_req.quality_percent

        compressed_byte_buffer = io.BytesIO()
        if resize_ratio < 0 or resize_ratio > 1:
            raise ValueError("Resize ratio %s is out of bounds." % resize_ratio)
        if resize_ratio != 1.0 and resize_ratio != 0:
            new_width = int(converted_image_data.size[0])
            new_height = int(converted_image_data.size[1])
            converted_image_data = converted_image_data.resize((new_width, new_height),
                                                               Image.ANTIALIAS)
            image_proto.cols = new_width
            image_proto.rows = new_height

        # Set the image data.
        if image_format == image_pb2.Image.FORMAT_RAW:
            # Note, the returned raw bytes array from the Ricoh Theta camera is often around 8MB, so the GRPC server
            # must be setup to have an increased message size limit. The run_ricoh_image_service script does increase
            # the size to allow for the larger raw images.
            # PIL will not do any JPEG compression if the quality is specified as 100. It effectively treats
            # requests with quality > 95 as a request for a raw image.
            converted_image_data.save(compressed_byte_buffer, format=converted_image_data.format,
                                      quality=100)
            image_proto.data = compressed_byte_buffer.getvalue()
            image_proto.format = image_pb2.Image.FORMAT_RAW
        elif image_format == image_pb2.Image.FORMAT_JPEG or image_format == image_pb2.Image.FORMAT_UNKNOWN or image_format is None:
            # Choose the best image format if the request does not specify the image format, which is JPEG since
            # it matches the output of the ricoh theta camera and is compact enough to transmit.
            # Decode the bytes into a PIL jpeg image. This allows for the formatting to be compressed. This is then
            # converted back into a bytes array.
            checked_quality = self.default_jpeg_quality
            if quality_percent > 0 and quality_percent <= 100:
                # A valid image quality percentage was passed with the image request,
                # so use this value instead of the service's default.
                if quality_percent > 95:
                    # PIL will not do any JPEG compression if the quality is specified as 100. It effectively treats
                    # requests with quality > 95 as a request for a raw image.
                    checked_quality = 95
                else:
                    checked_quality = quality_percent
            converted_image_data.save(compressed_byte_buffer, "JPEG", quality=int(checked_quality))
            image_proto.data = compressed_byte_buffer.getvalue()
            # Set the format as JPEG because the incoming requested format could've initially been None/unknown
            # in this case.
            image_proto.format = image_pb2.Image.FORMAT_JPEG
        else:
            # Don't support RLE for ricoh theta cameras.
            _LOGGER.info("GetImage request for unsupported format %s",
                         str(image_pb2.Image.Format.Name(image_format)))


def make_ricoh_theta_image_service(theta_ssid, theta_password, theta_client, robot, logger=None,
                                   use_background_capture_thread=False, live_stream=False):
    # Create an theta instance, which will perform the HTTP requests to the ricoh theta
    # camera (using the Ricoh Theta API: https://api.ricoh/docs/#ricoh-theta-api).
    theta_instance = Theta(theta_ssid=theta_ssid, theta_pw=theta_password, client_mode=theta_client,
                           show_state_at_init=False)
    try:
        # Test that communication to the camera works before creating the complete image service.
        theta_instance.showState()
    except json.decoder.JSONDecodeError as err:
        _LOGGER.warning("Ricoh Theta faulted on initialization.")
        # The JSONDecodeError signifies that the response from the ricoh theta HTTP post requests are
        # coming back empty, meaning the camera is not setup correctly to communicate with the theta instance.
        fault_client = robot.ensure_client(FaultClient.default_service_name)
        fault = CAMERA_SETUP_FAULT
        fault.error_message = "Failed to communicate with the camera at %s: server is " % theta_instance.baseip + \
                                "responding with empty json messages."
        resp = fault_client.trigger_service_fault_async(fault)
        return False, None
    except Exception as err:
        error = "Exception raised when attempting to communicate with the ricoh theta: %s" % str(
            err)
        _LOGGER.warning(error)
        fault_client = robot.ensure_client(FaultClient.default_service_name)
        fault = CAMERA_SETUP_FAULT
        fault.error_message = error
        resp = fault_client.trigger_service_fault_async(fault)
        return False, None

    ricoh_helper = RicohThetaServiceHelper(theta_ssid, theta_instance, logger, live_stream,
                                           use_background_capture_thread)
    img_src = VisualImageSource(
        ricoh_helper.image_source_name, ricoh_helper, ricoh_helper.rows, ricoh_helper.cols,
        ricoh_helper.camera_gain, ricoh_helper.camera_exposure,
        [image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8, image_pb2.Image.PIXEL_FORMAT_RGB_U8], logger)
    return True, CameraBaseImageServicer(robot, DIRECTORY_NAME, [img_src], logger,
                                         use_background_capture_thread)


def run_service(bosdyn_sdk_robot, options, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = image_service_pb2_grpc.add_ImageServiceServicer_to_server

    # Instance of the servicer to be run.
    init_success, service_servicer = make_ricoh_theta_image_service(
        options.theta_ssid, options.theta_password, options.theta_client, bosdyn_sdk_robot, logger,
        options.capture_continuously, options.live_stream)
    if init_success and service_servicer is not None:
        service_runner = GrpcServiceRunner(service_servicer, add_servicer_to_server_fn,
                                           options.port, logger=logger)
        return True, service_runner
    else:
        return False, None


def add_ricoh_theta_arguments(parser):
    parser.add_argument("--theta-ssid", default=None, required=True, help='Ricoh Theta ssid')
    parser.add_argument(
        '--theta-password', default=None, required=False,
        help='Optional password for ricoh theta (if not provided, the default password is used).')
    parser.add_argument(
        '--theta-client', action='store_true',
        help='Run the Ricoh Theta in client mode (camera connects to specified network).')
    parser.add_argument(
        '--capture-continuously', action='store_true', dest='capture_continuously', help=
        "Use a background thread to request images continuously. Otherwise, capture images only when a "
        "GetImage RPC is received.")
    parser.add_argument(
        '--capture-when-requested', action='store_false', dest='capture_continuously', help=
        "Only request images from the Ricoh Theta when a GetImage RPC is received. Otherwise, use "
        "a background thread to request images continuously.")
    parser.add_argument(
        '--live-stream', action='store_true',
        help="Return images as a live stream but with less high quality image stitching.")
    parser.set_defaults(capture_continuously=False)


if __name__ == '__main__':
    # Define all arguments used by this service.
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    add_ricoh_theta_arguments(parser)
    options = parser.parse_args()

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose, include_dedup_filter=True)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk("RicohThetaImageServiceSDK")
    robot = sdk.create_robot(options.hostname)
    PLACEHOLDER_PAYLOAD.GUID, secret = bosdyn.client.util.get_guid_and_secret(options)
    robot.register_payload_and_authenticate(PLACEHOLDER_PAYLOAD, secret)

    # Create a service runner to start and maintain the service on background thread. This helper function
    # also returns the servicer associated with the service runner, such that the initialize_camera function
    # can be called after directory registration.
    camera_initialization_success, service_runner = run_service(robot, options, logger=_LOGGER)

    if not camera_initialization_success:
        _LOGGER.error("Ricoh Theta camera did not initialize successfully. The service will NOT be "
                      "registered with the directory.")
        sys.exit(1)

    # The initialization for the camera succeeded! The directory registration will clear any
    # existing service faults for us automatically. Use a keep alive to register the service
    # with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, SERVICE_TYPE, AUTHORITY, options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()
