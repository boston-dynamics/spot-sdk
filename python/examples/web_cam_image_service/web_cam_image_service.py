# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Register and run the Web Cam Service."""

import logging
import os
import signal
import six
import time
import threading
import cv2
import numpy as np

import bosdyn.util
from bosdyn.util import sec_to_nsec
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.fault import FaultClient, ServiceFaultDoesNotExistError
from bosdyn.client.util import populate_response_header, GrpcServiceRunner, setup_logging

from bosdyn.api import service_fault_pb2
from bosdyn.api import header_pb2
from bosdyn.api import image_pb2
from bosdyn.api import image_service_pb2
from bosdyn.api import image_service_pb2_grpc

DIRECTORY_NAME = 'web-cam-service'
AUTHORITY = 'robot-web-cam'
SERVICE_TYPE = 'bosdyn.api.ImageService'

_LOGGER = logging.getLogger(__name__)

class ImageCaptureThread():
    """Continuously query and store the last successfully captured image and it's
    associated timestamp for a single camera device."""

    def __init__(self, device_name, capture, fps=30, fault_client=None, service_name=''):
        # OpenCV VideoCapture instance.
        self.capture = capture

        # Name of the image source that is being requested from.
        self.device_name = device_name

        # Frame rate (per seconds).
        self.fps = fps
        capture.set(cv2.CAP_PROP_FPS, self.fps)

        # Indicate if the image capture thread is alive.
        self.is_alive = False

        # Track the last image and timestamp for this image source.
        self.last_captured_image = None
        self.last_captured_time = None

        # Service name this thread's servicer is associated with in the robot directory.
        self.service_name = service_name

        # Fault client to report errors.
        self.fault_client = fault_client

        # Attempt to get capture parameters (gain, exposure time).
        try:
            self.camera_gain = self.capture.get(cv2.CAP_PROP_GAIN)
        except cv2.error as e:
            print("Unable to determine camera gain: " + str(e))
            self.camera_gain = None
        try:
            self.camera_exposure = self.capture.get(cv2.CAP_PROP_EXPOSURE)
        except cv2.error as e:
            print("Unable to determine camera exposure time: " + str(e))
            self.camera_exposure = None

        self._thread_lock = threading.Lock()

    def get_capture_parameters(self):
        """Creates an instance of the image_pb2.CaptureParameters protobuf message
        populated with values found from the OpenCV image source."""
        params = image_pb2.CaptureParameters()
        if self.camera_gain:
            params.gain = self.camera_gain
        if self.camera_exposure:
            # Note, here we are making the assumption that the exposure is defined in seconds.
            params.exposure_duration.seconds = int(self.camera_exposure)
        return params

    def start_thread(self):
        """Start the background thread for the image """
        print("Starting the thread for " + str(self.device_name))
        self.is_alive = True
        thread = threading.Thread(target=self._do_image_capture)
        thread.daemon = True
        thread.start()
        return thread

    def set_last_frame(self, image_frame, capture_time):
        """Update the last image capture and timestamp."""
        with self._thread_lock:
            self.last_captured_image = image_frame
            self.last_captured_time = capture_time

    def get_last_frame(self):
        """Returns the last found image and the timestamp it was acquired at."""
        frame_and_time = None
        with self._thread_lock:
            frame_and_time = (self.last_captured_image, self.last_captured_time)
        return frame_and_time

    def _do_image_capture(self):
        """Main loop for the image capture thread, which requests and saves images."""
        # The service fault to report when this thread fails to capture an image from a source
        capture_fault_id = service_fault_pb2.ServiceFaultId(fault_name='Image Capture Failure',
                                                            service_name=self.service_name)
        capture_fault = service_fault_pb2.ServiceFault(
            fault_id=capture_fault_id,
            error_message='Failed to capture an image from ' + self.device_name,
            severity=service_fault_pb2.ServiceFault.SEVERITY_WARN)
        try:
            self.fault_client.clear_service_fault(capture_fault_id)
        except ServiceFaultDoesNotExistError:
            pass
        fault_active = False
        while self.is_alive:
            # Get the image from the video capture.
            capture_time = time.time()
            success, image = self.capture.read()
            if success:
                self.set_last_frame(image, capture_time)
                if fault_active:
                    self.fault_client.clear_service_fault(capture_fault_id)
                    fault_active = False
            elif not fault_active:
                self.fault_client.trigger_service_fault(capture_fault)
                fault_active = True

        # Cleanup the video capture when the thread is done.
        self.capture.release()

    def stop_thread(self):
        """Stop the image capture thread."""
        self.is_alive = False

def device_name_to_source_name(device_name):
    return os.path.basename(device_name)

class WebCamImageServicer(image_service_pb2_grpc.ImageServiceServicer):
    """GRPC service to provide access to multiple different image sources. The service can list the
    available image (device) sources and query each source for image data."""

    def __init__(self, bosdyn_sdk_robot, service_name, image_source_device_names=[], logger=None):
        super(WebCamImageServicer, self).__init__()

        self.logger = logger or _LOGGER

        # Create a robot instance.
        self.bosdyn_sdk_robot = bosdyn_sdk_robot

        # Service name this servicer is associated with in the robot directory.
        self.service_name = service_name

        # Fault client to report service faults
        self.fault_client = self.bosdyn_sdk_robot.ensure_client(FaultClient.default_service_name)

        # Get a timesync endpoint from the robot instance such that the image timestamps can be
        # reported in the robot's time.
        self.bosdyn_sdk_robot.time_sync.wait_for_sync()

        # Map tracking the image source name to the protobuf message representing that source.
        # key: device_name (str), value: image_pb2.ImageSource
        self.image_sources = {}

        # Map tracking the image source name to the ImageCaptureThread running in the background.
        # key: device_name (str), value: VideoCapture thread
        self.image_name_to_video = {}

        # Set the different ImageSource protos and ImageCaptureThread for each image source name
        # provided on initialization.
        for device_name in image_source_device_names:
            image_source_proto, video_capture = self.make_image_source(str(device_name))
            source_name = image_source_proto.name
            self.image_name_to_video[source_name] = ImageCaptureThread(
                device_name, video_capture, fault_client=self.fault_client,
                service_name=self.service_name)
            self.image_name_to_video[source_name].start_thread()
            self.image_sources[source_name] = image_source_proto

        # Default value for JPEG image quality, in case one is not provided in the GetImage request.
        self.default_jpeg_quality = 100

    def ListImageSources(self, request, context):
        """Obtain the list of ImageSources for this given service.

        Args:
            request (image_pb2.ListImageSourcesRequest): The list images request.
            context (GRPC ClientContext): tracks internal grpc statuses and information.

        Returns:
            A list of all image sources known to this image service. Note, there could be multiple image
            services registered with the robot's directory service that can have different image sources.
        """
        response = image_pb2.ListImageSourcesResponse()
        for source in self.image_sources.values():
            response.image_sources.add().CopyFrom(source)
        populate_response_header(response, request)
        return response

    def GetImage(self, request, context):
        """The image service's GetImage implementation that gets the latest image capture from
        all the image sources specified in the request.

        Args:
            request (image_pb2.GetImageRequest): The image request, which specifies the image sources to
                                                 query, and other format parameters.
            context (GRPC ClientContext): tracks internal grpc statuses and information.

        Returns:
            The ImageSource and Image data for the last captured image from each image source name
            specified in the request.
        """
        response = image_pb2.GetImageResponse()
        for img_req in request.image_requests:
            img_resp = response.image_responses.add()
            src_name = img_req.image_source_name
            if src_name not in self.image_sources and src_name not in self.image_name_to_video:
                # This camera is not known, therefore set a failure status in the response message.
                img_resp.status = image_pb2.ImageResponse.STATUS_UNKNOWN_CAMERA
                continue

            if src_name in self.image_sources:
                img_resp.source.CopyFrom(self.image_sources[src_name])
            else:
                # Couldn't find the image source information for the device name.
                img_resp.status = image_pb2.ImageResponse.STATUS_SOURCE_DATA_ERROR

            if src_name not in self.image_name_to_video:
                # Couldn't find the image capture information for the device name.
                img_resp.status = image_pb2.ImageResponse.STATUS_IMAGE_DATA_ERROR
                continue

            capture_instance = self.image_name_to_video[src_name]
            img_resp.shot.capture_params.CopyFrom(capture_instance.get_capture_parameters())
            frame, img_time = capture_instance.get_last_frame()
            if frame is None or img_time is None:
                response.header.error.code = header_pb2.CommonError.CODE_INTERNAL_SERVER_ERROR
                response.header.error.message = 'Failed to capture an image from {} on the server.'.format(
                    src_name)
                return response

            # Convert the image capture time from the local clock time into the robot's time. Then set it as
            # the acquisition timestamp for the image data.
            img_resp.shot.acquisition_time.CopyFrom(
                self.bosdyn_sdk_robot.time_sync.robot_timestamp_from_local_secs(
                    sec_to_nsec(img_time)))
            img_resp.shot.image.rows = int(frame.shape[0])
            img_resp.shot.image.cols = int(frame.shape[1])

            # Determine the pixel format for the data.
            if frame.shape[2] == 3:
                # RGB image.
                img_resp.shot.image.pixel_format = image_pb2.Image.PIXEL_FORMAT_RGB_U8
            elif frame.shape[2] == 1:
                # Greyscale image.
                img_resp.shot.image.pixel_format = image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8
            elif frame.shape[2] == 4:
                # RGBA image.
                img_resp.shot.image.pixel_format = image_pb2.Image.PIXEL_FORMAT_RGBA_U8
            else:
                # The number of pixel channels did not match any of the known formats.
                img_resp.shot.image.pixel_format = image_pb2.Image.PIXEL_FORMAT_UNKNOWN

            # Note, we are currently not setting any information for the transform snapshot or the frame
            # name for an image sensor since this information can't be determined with openCV.

            # Set the image data.
            if img_req.image_format == image_pb2.Image.FORMAT_RAW:
                img_resp.shot.image.data = np.ndarray.tobytes(frame)
                img_resp.shot.image.format = image_pb2.Image.FORMAT_RAW
            elif img_req.image_format == image_pb2.Image.FORMAT_JPEG:
                # If the image format is requested as UNKNOWN or JPEG, return a JPEG. Since this service
                # is for a webcam, we choose a sane default for the return if the request format is unpopulated.
                quality = self.default_jpeg_quality
                if img_req.quality_percent > 0 and img_req.quality_percent <= 100:
                    # A valid image quality percentage was passed with the image request,
                    # so use this value instead of the service's default.
                    quality = img_req.quality_percent
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                img_resp.shot.image.data = cv2.imencode('.jpg', frame, encode_param)[1].tostring()
                img_resp.shot.image.format = image_pb2.Image.FORMAT_JPEG
            else:
                # If the image format is requested as UNKNOWN, return a JPEG. Since this service
                # is for a webcam, we choose a sane default for the return if the request "image_format"
                # field is unpopulated.
                quality = self.default_jpeg_quality
                if img_req.quality_percent > 0 and img_req.quality_percent <= 100:
                    # A valid image quality percentage was passed with the image request,
                    # so use this value instead of the service's default.
                    quality = img_req.quality_percent
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                img_resp.shot.image.data = cv2.imencode('.jpg', frame, encode_param)[1].tostring()
                img_resp.shot.image.format = image_pb2.Image.FORMAT_JPEG

            # Set that we successfully got the image.
            if img_resp.status == image_pb2.ImageResponse.STATUS_UNKNOWN:
                img_resp.status = image_pb2.ImageResponse.STATUS_OK

        # No header error codes, so set the response header as CODE_OK.
        populate_response_header(response, request)
        return response

    @staticmethod
    def make_image_source(device_name="/dev/video0"):
        """Create an instance of the image_pb2.ImageSource and a VideoCapture for that image source.
        Args:
            device_name(str): The image source name that should be described.

        Returns:
            An ImageSource with the cols, rows, and image type populated, in addition to an OpenCV VideoCapture
            instance which can be used to query the image source for images.
        """
        # Defaults to "/dev/video0" for the device name, which will take the first (or only) connected camera.
        source = image_pb2.ImageSource()
        source.name = device_name_to_source_name(device_name)
        capture = cv2.VideoCapture(device_name)
        source.cols = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        source.rows = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        source.image_type = image_pb2.ImageSource.IMAGE_TYPE_VISUAL
        return source, capture


def run_service(bosdyn_sdk_robot, port, service_name, device_names, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = image_service_pb2_grpc.add_ImageServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = WebCamImageServicer(bosdyn_sdk_robot, service_name, device_names, logger=logger)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


def add_web_cam_arguments(parser):
    parser.add_argument(
        '--device-name',
        help=('Image source to query. If none are passed, it will default to the first available '
              'source.'), action='append', required=False, default=["/dev/video0"])


if __name__ == '__main__':
    # Define all arguments used by this service.
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    add_web_cam_arguments(parser)
    options = parser.parse_args()

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk("ImageServiceSDK")
    robot = sdk.create_robot(options.hostname)
    robot.authenticate_from_payload_credentials(options.guid, options.secret)

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options.port, DIRECTORY_NAME, options.device_name,
                                 logger=_LOGGER)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, SERVICE_TYPE, AUTHORITY, options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()