# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from __future__ import print_function
from __future__ import absolute_import

import logging
import grpc
import signal
import six
import time
from datetime import datetime
import io
import sys
import json
from PIL import Image

import bosdyn.util
from bosdyn.util import set_timestamp_from_nsec, sec_to_nsec
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.util import populate_response_header, GrpcServiceRunner, setup_logging
from bosdyn.client.fault import FaultClient, ServiceFaultDoesNotExistError

from bosdyn.api import header_pb2
from bosdyn.api import image_pb2
from bosdyn.api import image_service_pb2
from bosdyn.api import image_service_pb2_grpc
from bosdyn.api import service_fault_pb2

from ricoh_theta import Theta

DIRECTORY_NAME = 'ricoh-theta-image-service'
AUTHORITY = 'robot-ricoh-theta'
SERVICE_TYPE = 'bosdyn.api.ImageService'

_LOGGER = logging.getLogger(__name__)

# Define ServiceFaultIds for possible faults that will be thrown by the Ricoh Theta image service.
CAMERA_SETUP_FAULT = service_fault_pb2.ServiceFault(
    fault_id=service_fault_pb2.ServiceFaultId(fault_name='Ricoh Theta Initialization Failure',
                                              service_name=DIRECTORY_NAME),
    severity=service_fault_pb2.ServiceFault.SEVERITY_CRITICAL)

CAPTURE_PARAMETERS_FAULT = service_fault_pb2.ServiceFault(
    fault_id=service_fault_pb2.ServiceFaultId(fault_name='Get CaptureParameters Failure',
                                              service_name=DIRECTORY_NAME),
    error_message="Failed to get exposure/gain parameters.",
    severity=service_fault_pb2.ServiceFault.SEVERITY_WARN)

CAPTURE_FAILURE_FAULT = service_fault_pb2.ServiceFault(
    fault_id=service_fault_pb2.ServiceFaultId(fault_name='RicohTheta Image Capture Failure',
                                              service_name=DIRECTORY_NAME),
    severity=service_fault_pb2.ServiceFault.SEVERITY_WARN)

class RicohThetaImageServicer(image_service_pb2_grpc.ImageServiceServicer):
    """GRPC service to provide access to multiple different image sources. The service can list the
    available image (device) sources and query each source for image data."""

    def __init__(self, bosdyn_sdk_robot, theta_ssid, logger=None):
        self.robot = bosdyn_sdk_robot
        self.robot.time_sync.wait_for_sync()

        # Create a service fault client.
        self.fault_client = self.robot.ensure_client(FaultClient.default_service_name)
        self.clear_faults_on_startup()

        # Setup the logger.
        self.logger = logger or _LOGGER

        # Name of the image source that is being requested from.
        self.theta_ssid = theta_ssid
        self.device_name = "RicohTheta_"+theta_ssid

        # Default value for JPEG image quality, in case one is not provided in the GetImage request.
        self.default_jpeg_quality = 95

        # Camera related variables. These will get initialized by calling initialize_camera(). If the
        # initialization of the camera failed, the service will never get registered with the directory.
        # This is done after because if a fault is thrown when attempting to connect to the Ricoh Theta
        # on startup, there is likely an issue with the camera connection or hardware, and the service
        # will likely to continue to fail until these issues are fixed.
        self.camera = None
        self.capture_parameters = image_pb2.CaptureParameters()
        self.ricoh_image_src_proto = image_pb2.ImageSource()

    def initialize_camera(self, theta_password, theta_client):
        """Creates the Ricoh Theta camera object and attempts to make a request to the camera.

        This function is called after the RicohTheta servicer is registered with the directory. This way, if the
        initial requests to the camera fail, the service faults will be present and remain active. Also, this
        function will initialize the ImageSource proto and the CaptureParameters proto, which only need to be set
        once at startup.

        Args:
            theta_password(string): The password for the Ricoh Theta camera.
            theta_client(boolean): A boolean indicating whether the camera is in client_mode or not.

        Returns:
            A boolean indicating whether or not the initialization of the Ricoh Theta camera succeeded.
        """
        # Initialize the Theta camera object and test the connection with the camera.show_state_at_init
        self.camera = Theta(theta_ssid=self.theta_ssid, theta_pw=theta_password, client_mode=theta_client, show_state_at_init=False)
        try:
            self.camera.showState()
        except json.decoder.JSONDecodeError as err:
            _LOGGER.warning("Ricoh Theta faulted on initialization.")
            # The JSONDecodeError signifies that the response from the ricoh theta HTTP post requests are
            # coming back empty, meaning the camera is not
            fault = CAMERA_SETUP_FAULT
            fault.error_message = "Failed to communicate with the camera at %s: server is responding with empty messages." % self.camera.baseip
            resp = self.fault_client.trigger_service_fault_async(fault)
            return False

        # One-time attempt to create a capture parameters protobuf (gain, exposure time).
        self.capture_parameters = self.create_capture_parameters()

        # Keep a local copy of the image source protobuf message so that it doesn't have to be
        # recreated repeatedly.
        self.ricoh_image_src_proto = self.make_ricoh_theta_image_source()

        return True

    def clear_faults_on_startup(self):
        """Attempts to clear any ServiceFaults from the Ricoh Theta image service when it was last run."""
        try:
            self.fault_client.clear_service_fault(service_fault_pb2.ServiceFaultId(service_name=DIRECTORY_NAME),
                                                  clear_all_service_faults=True)
        except ServiceFaultDoesNotExistError:
            pass

    def create_capture_parameters(self):
        """Creates an instance of the image_pb2.CaptureParameters protobuf message
        populated with values from the Ricoh Theta getOptions request.

        Returns:
            An instance of the protobuf CaptureParameters message.
        """
        params = image_pb2.CaptureParameters()
        gain, exposure = None, None
        try:
            gain, exposure = self.camera.getCaptureParameters(print_to_screen=False)
        except Exception as err:
            # Trigger a capture parameter fault.
            self.fault_client.trigger_service_fault_async(CAPTURE_PARAMETERS_FAULT)

        if gain:
            params.gain = gain
        if exposure:
            params.exposure_duration.seconds = int(exposure)
        return params

    def get_last_processed_image(self):
        """Take an image and download the processed image to local memory from the Ricoh Theta camera.

        Returns:
            The complete image's json data and a buffer of the image bytes.
        """
        if self.camera is None:
            return None, None
        # Send the request to take a picture
        self.camera.takePicture(print_to_screen=False)
        img_json, img_raw = self.camera.getLastImage(print_to_screen=False)
        if not (img_json and img_raw):
            # The getLastImage request failed, return None.
            _LOGGER.warning("The getLastImage request to the Ricoh Theta returned no data.")
            return None, None

        buffer_bytes = img_raw.raw
        buffer_bytes.decode_content = True
        return img_json, buffer_bytes

    def ListImageSources(self, request, context):
        """Obtain the list of ImageSources for this image source.

        Args:
            request (image_pb2.ListImageSourcesRequest): The list images request.
            context (GRPC ClientContext): tracks internal grpc statuses and information.

        Returns:
            A list of all image sources known to this image service. Note, this service is setup to run a
            single client connection to a Ricoh Theta camera, so that will be the only returned source.
        """
        response = image_pb2.ListImageSourcesResponse()
        add_source = response.image_sources.add()
        add_source.CopyFrom(self.ricoh_image_src_proto)
        populate_response_header(response, request)
        return response

    def GetImage(self, request, context):
        """The image service's GetImage implementation that gets the latest image from the ricoh theta
        camera. This will return the last "processed" image; the Ricoh Theta camera will processes the
        images internally before outputting a jpeg.
        Note, this can take upwards of 3 seconds, so the image could be slightly older.

        Args:
            request (image_pb2.GetImageRequest): The image request, which specifies the image sources to
                                                 query, and other format parameters.
            context (GRPC ClientContext): tracks internal grpc statuses and information.

        Returns:
            The ImageSource and Image data for the last captured image from the Ricoh Theta camera.
        """
        response = image_pb2.GetImageResponse()
        for img_req in request.image_requests:
            img_resp = response.image_responses.add()
            if img_req.image_source_name != self.device_name:
                # The requested camera source does not match the name of the Ricoh Theta camera, so if cannot
                # be completed and will have a failure status in the response message.
                img_resp.status = image_pb2.ImageResponse.STATUS_UNKNOWN_CAMERA
                _LOGGER.info("Camera source '%s' is unknown to the Ricoh Theta image service.", img_req.image_source_name)
                continue
            # Set the image source information for the Ricoh Theta camera.
            img_resp.source.CopyFrom(self.ricoh_image_src_proto)

            # Set the image capture parameters.
            img_resp.shot.capture_params.CopyFrom(self.capture_parameters)

            # Get the last image from the camera.
            img_info_json, img_bytes = None, None
            camera_acquisition_errored = False
            try:
                img_info_json, img_bytes = self.get_last_processed_image()
            except Exception as err:
                _LOGGER.info("GetImage request threw an error: %s %s", str(type(err)), str(err))
                camera_acquisition_errored = True

            if camera_acquisition_errored:
                # Image acquisition request failed (and the camera connection is working).
                img_resp.status = image_pb2.ImageResponse.STATUS_IMAGE_DATA_ERROR
                _LOGGER.info("Setting status DATA_ERROR for the GetImage request because the get_last_processed_image() "
                            "function threw an error.")
                # Trigger a fault for the capture failure.
                fault = CAPTURE_FAILURE_FAULT
                fault.error_message = "Failed to get an image for %s." % img_req.image_source_name
                self.fault_client.trigger_service_fault_async(fault)
                continue
            else:
                # No camera errors. Clear faults for any capture failures or initialization failures since
                # images are being captured and no weird HTTP error codes are being thrown for the post
                # requests to get the images.
                self.fault_client.clear_service_fault_async(CAPTURE_FAILURE_FAULT.fault_id)

            if img_info_json is None or img_bytes is None:
                # Could not get the image data from the Ricoh Theta camera.
                img_resp.status = image_pb2.ImageResponse.STATUS_IMAGE_DATA_ERROR
                continue

            # Read the image into local memory. Apparently, the action of reading the buffer can only be performed
            # one time unless it is converted to a stream or copied.
            img_bytes_read = img_bytes.read()

            # Split on the "-" to remove the timezone information from the string.
            date_time = img_info_json["dateTimeZone"].split("-")[0]
            # Shorten the year (the first value) from a four digit year to two digit value such that the format
            # matches the datetime expectation. (Ex. 2021 --> 21).
            date_time_str = date_time[2:]
            # Convert from string to an actual datetime object
            date_time_obj = datetime.strptime(date_time_str, "%y:%m:%d %H:%M:%S")
            # Convert from a datetime object to a time object (seconds) in the local clock's time.
            time_obj = time.mktime(date_time_obj.timetuple())
            # Convert the time object in local clock into the robot's clock, and set it as the acquisition timestamp
            # for the image.
            img_resp.shot.acquisition_time.CopyFrom(self.robot.time_sync.robot_timestamp_from_local_secs(sec_to_nsec(time_obj)))

            # Set the height and width of the image.
            if "width" in img_info_json:
                img_resp.shot.image.cols = int(img_info_json["width"])
            if "height" in img_info_json:
                img_resp.shot.image.rows = int(img_info_json["height"])

            # Ricoh Theta takes colored JPEG images, so it's pixel type is RGB.
            img_resp.shot.image.pixel_format = image_pb2.Image.PIXEL_FORMAT_RGB_U8

            # Note, we are currently not setting any information for the transform snapshot or the frame
            # name for an image sensor since this information can't be determined with HTTP calls to ricoh
            # theta's api.

            # Set the image data.
            if img_req.image_format == image_pb2.Image.FORMAT_RAW:
                # Note, the returned raw bytes array from the Ricoh Theta camera is often around 8MB, so the GRPC server
                # must be setup to have an increased message size limit. The run_ricoh_image_service script does increase
                # the size to allow for the larger raw images.
                pil_image = Image.open(io.BytesIO(img_bytes_read))
                compressed_byte_buffer = io.BytesIO()
                # PIL will not do any JPEG compression if the quality is specifed as 100. It effectively treats
                # requests with quality > 95 as a request for a raw image.
                pil_image.save(compressed_byte_buffer, format=pil_image.format, quality=100)
                img_resp.shot.image.data = compressed_byte_buffer.getvalue()
                img_resp.shot.image.format = image_pb2.Image.FORMAT_RAW
            elif img_req.image_format == image_pb2.Image.FORMAT_JPEG or img_req.image_format == image_pb2.Image.FORMAT_UNKNOWN:
                # Choose the best image format if the request does not specify the image format, which is JPEG since it matches
                # the output of the ricoh theta camera and is compact enough to transmit.
                # Decode the bytes into a PIL jpeg image. This allows for the formatting to be compressed. This is then
                # converted back into a bytes array.
                pil_image = Image.open(io.BytesIO(img_bytes_read))
                compressed_byte_buffer = io.BytesIO()
                quality = self.default_jpeg_quality
                if img_req.quality_percent > 0 and img_req.quality_percent <= 100:
                    # A valid image quality percentage was passed with the image request,
                    # so use this value instead of the service's default.
                    if img_req.quality_percent > 95:
                        # PIL will not do any JPEG compression if the quality is specifed as 100. It effectively treats
                        # requests with quality > 95 as a request for a raw image.
                        quality = 95
                    else:
                        quality = img_req.quality_percent
                pil_image.save(compressed_byte_buffer, format=pil_image.format, quality=int(quality))
                img_resp.shot.image.data = compressed_byte_buffer.getvalue()
                img_resp.shot.image.format = image_pb2.Image.FORMAT_JPEG
            else:
                # Don't support RLE for ricoh theta cameras.
                img_resp.status = image_pb2.ImageResponse.STATUS_UNSUPPORTED_REQUESTED_IMAGE_FORMAT
                _LOGGER.info("GetImage request for unsupported format %s", str(image_pb2.Image.Format.Name(img_req.image_format)))

            # Set that we successfully got the image.
            if img_resp.status == image_pb2.ImageResponse.STATUS_UNKNOWN:
                img_resp.status = image_pb2.ImageResponse.STATUS_OK

        # Set the header after all image sources requested have been processed.
        populate_response_header(response, request)
        return response

    def make_ricoh_theta_image_source(self):
        """Create an instance of the image_pb2.ImageSource for the Ricoh Theta.

        Returns:
            An ImageSource with the cols, rows, and image type populated.
        """
        source = image_pb2.ImageSource()
        source.name = self.device_name

        # Request the image format (height, width) from the camera.
        format_json = None
        try:
            format_json = self.camera.getFileFormat(print_to_screen=False)
        except Exception as err:
            # An issue occurred getting the file format for the camera images. This is likely due
            # to upstream failures creating the Theta instance, which already have triggered service
            # faults.
            _LOGGER.info("Unable to set the image width/height dimensions. Error message: %s %s", str(type(err)), str(err))
            pass
        if format_json is not None:
            source.cols = format_json["width"]
            source.rows = format_json["height"]

        # Image from the ricoh theta is a JPEG, which is considered a visual image source (no depth data).
        source.image_type = image_pb2.ImageSource.IMAGE_TYPE_VISUAL
        return source


def run_service(bosdyn_sdk_robot, port, theta_ssid, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = image_service_pb2_grpc.add_ImageServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = RicohThetaImageServicer(bosdyn_sdk_robot, theta_ssid, logger=logger)
    service_runner = GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)
    return service_runner, service_servicer


def add_ricoh_theta_arguments(parser):
    parser.add_argument("--theta-ssid", default=None, required=True, help='Ricoh Theta ssid')
    parser.add_argument('--theta-password', default=None, required=False,
        help='Optional password for ricoh theta (if not provided, the default password is used).')
    parser.add_argument('--theta-client', action='store_true',
        help='Run the Ricoh Theta in client mode (camera connects to specified network).')


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
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk("RicohThetaImageServiceSDK")
    robot = sdk.create_robot(options.hostname)
    robot.authenticate_from_payload_credentials(options.guid, options.secret)

    # Create a service runner to start and maintain the service on background thread. This helper function
    # also returns the servicer associated with the service runner, such that the initialize_camera function
    # can be called after directory registration.
    service_runner, service_servicer = run_service(robot, options.port, options.theta_ssid, logger=_LOGGER)

    camera_initialization_success = service_servicer.initialize_camera(options.theta_password,
                                                                       options.theta_client)

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