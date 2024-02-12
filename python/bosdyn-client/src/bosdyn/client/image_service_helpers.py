# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import inspect
import logging
import sys
import threading
import time
from abc import ABC, abstractmethod

import numpy as np

from bosdyn.api import (header_pb2, image_pb2, image_service_pb2, image_service_pb2_grpc,
                        service_customization_pb2, service_fault_pb2)
from bosdyn.client.exceptions import RpcError
from bosdyn.client.fault import (FaultClient, ServiceFaultAlreadyExistsError,
                                 ServiceFaultDoesNotExistError)
from bosdyn.client.image import UnsupportedPixelFormatRequestedError
from bosdyn.client.server_util import populate_response_header
from bosdyn.client.service_customization_helpers import create_value_validator, validate_dict_spec
from bosdyn.client.util import setup_logging
from bosdyn.util import sec_to_nsec, seconds_to_duration

_LOGGER = logging.getLogger(__name__)

CLEAR_FAULT_RPC_TIMEOUT_SECS = 0.1


def convert_RGB_to_grayscale(image_data_RGB_np):
    """Convert numpy image from RGB to grayscale using Pillow's formula.

    Args:
        image_data_RGB_np (numpy array): The RGB image data output from a capture as a 3D numpy
        array with R, G, B channels in that order in the array.
    Returns:
        Converted image_data_np as another 2D numpy array.
    """

    # gray = 0.299 * red + 0.587 * green + 0.114 * blue
    # This code performs the above math using integer math and bit shifts for speed.
    # The constants below are the same as the ones in the above equation multiplied by 2^16
    # The final addition makes it round the correct direction when it gets truncated by the bit shift.
    rgb = image_data_RGB_np.astype(np.uint32)
    return (
        (rgb[:, :, 0] * 19595 + rgb[:, :, 1] * 38470 + rgb[:, :, 2] * 7471 + 0x8000) >> 16).astype(
            np.uint8)


class CameraInterface(ABC):
    """Abstract class interface for capturing and decoding images from a camera.

    This interface is used by the VisualImageSource to ensure that each image source
    has the expected capture and decoding methods with the right specification.
    """

    def __init__(self):
        self.capture_lock = threading.Lock()

    @abstractmethod
    def blocking_capture(self, *, custom_params=None, **kwargs):
        """Communicates with the camera payload to collect the image data. Ensure this is threadsafe as multiple
        threads/requests may try to call blocking_capture at the same time. A Lock (self.capture_lock) is provided
        as a convenience to help with this.

        Args:
            custom_params (service_customization_pb2.DictParam): Custom parameters defined by the image source
                                                                 affecting the resulting capture
            **kwargs: Other keyword arguments including future additions to the request that affect the capture.
                      If an implementer is looking to use kwargs, it is expected that they update their
                      blocking_capture function signature to accept named keyword arguments such as custom_params

        Returns:
            A tuple with image data (in any format), and the capture timestamp in seconds (float) in the
            service computer's clock.
        """
        pass

    @abstractmethod
    def image_decode(self, image_data, image_proto, image_req):
        """Decode the image data into an Image proto based on the requested format and quality.

        Args:
            image_data (Same format as the output of blocking_capture): The image data output from a capture.
            image_proto (image_pb2.Image): The proto message to populate with decoded image data.
            image_req (image_pb2.ImageRequest): The image request associated with the image_data.

        Returns:
            None.  Mutates the image_proto message with the decoded data. This function should set the image data,
            pixel format, image format, and potentially the transform snapshot fields within the image_proto
            protobuf message.
        """
        pass


class VisualImageSource():
    """Helper class to represent a single image source.

    This helper class can be used to track state associated with an image source. It can capture
    images and decode image data for an image service.
    It can be configured to:
    - throw faults for capture or decode failures
    - request images continuously on a background thread to allow image services to respond more
    rapidly to GetImage requests.

    Args:
        image_name (string): The name of the image source.
        camera_interface (subclass of CameraInterface): A camera class which inherits from and implements
                                                        the abstract methods of the CameraInterface class.
        rows (int): The number of rows of pixels in the image.
        cols (int): The number of cols of pixels in the image.
        gain (float | function): The sensor's gain in dB. This can be a fixed value or a function
                                 which returns the gain as a float.
        exposure (float | function): The exposure time for an image in seconds. This can be a fixed
                                     value or a function which returns the exposure time as a float.
        pixel_formats (image_pb2.Image.PixelFormat[]): Supported pixel formats.
        param_spec (service_customization_pb2.DictParam.Spec): A set of custom parameters passed into this
                                                               image source
        logger (logging.Logger): Logger for debug and warning messages.
    """

    def __init__(self, image_name, camera_interface, rows=None, cols=None, gain=None, exposure=None,
                 pixel_formats=[], logger=None, param_spec=None):
        self.image_source_name = image_name
        self.supported_pixel_formats = pixel_formats
        self.image_source_proto = self.make_image_source(image_name, rows, cols,
                                                         self.supported_pixel_formats,
                                                         param_spec=param_spec)
        self.get_image_capture_params = lambda request_custom_params=None: self.make_capture_parameters(
            gain=gain, exposure=exposure, request_custom_params=request_custom_params)

        self.param_spec = param_spec
        if param_spec:
            #Fail fast if the spec being used is invalid, and otherwise get a function to easily validate values
            self.value_validator = create_value_validator(param_spec)
        else:
            #Validate against empty parameter set
            self.value_validator = create_value_validator(
                service_customization_pb2.DictParam.Spec())
        # Ensure the camera_interface is a subclass of CameraInterface and has the defined capture and
        # decode methods.
        assert isinstance(camera_interface, CameraInterface)
        self.camera_interface = camera_interface

        self.capture_function = lambda custom_params=None, **kwargs: self._do_capture_with_error_checking(
            self.camera_interface.blocking_capture, custom_params=custom_params, **kwargs)

        # Optional background thread to continuously capture image data. This will help an image
        # service to respond quickly to a GetImage request, since it can use the last captured image.
        self.capture_thread = None

        # Fault client to report errors. Requires the image service name to
        # properly create the fault id.
        self.fault_client = None

        # Create fault to throw if a failure occurs when calling the blocking_capture function.
        camera_capture_fault_id = service_fault_pb2.ServiceFaultId(
            fault_name="Image Capture Failure for %s" % self.image_source_name)
        self.camera_capture_fault = service_fault_pb2.ServiceFault(
            fault_id=camera_capture_fault_id, severity=service_fault_pb2.ServiceFault.SEVERITY_WARN)
        # Create a fault to throw if a failure occurs when calling the image_decode function.
        decode_data_fault_id = service_fault_pb2.ServiceFaultId(
            fault_name="Decoding Image %s Failure" % self.image_source_name)
        self.decode_data_fault = service_fault_pb2.ServiceFault(
            fault_id=decode_data_fault_id, severity=service_fault_pb2.ServiceFault.SEVERITY_WARN)

        # This is the set of active fault id names that can potentially get cleared.
        self.active_fault_id_names = set()

        # Logger for warning messages and the last error message (used only when the background thread
        # is capturing such that error messages from the last capture can be shown still).
        self.logger = logger or _LOGGER
        self.last_error_message = None

    def set_logger(self, logger):
        """Override the existing logger for the VisualImageSource class."""
        if logger is not None:
            self.logger = logger

    def create_capture_thread(self, custom_params=None):
        """Initialize a background thread to continuously capture images.

        """
        self.capture_thread = ImageCaptureThread(self.image_source_name, self.capture_function,
                                                 custom_params=custom_params)
        self.capture_thread.start_capturing()

    def initialize_faults(self, fault_client, image_service):
        """Initialize a fault client and faults for the image source (linked to the image service).

        The fault client can be used to throw faults for capture and decode errors. All faults
        associated with the image service name provided will be cleared.

        Args:
            fault_client (FaultClient): The fault client to communicate with the robot.
            image_service (string): The image service name to associate faults with.
        """
        self.fault_client = fault_client

        # Update the fault ids to include the correct image service name.
        self.camera_capture_fault.fault_id.service_name = image_service
        self.decode_data_fault.fault_id.service_name = image_service

        # Attempt to clear any previous faults for the image service.
        if self.fault_client is not None:
            try:
                self.fault_client.clear_service_fault(
                    service_fault_pb2.ServiceFaultId(service_name=image_service),
                    clear_all_service_faults=True)
            except ServiceFaultDoesNotExistError:
                self.active_fault_id_names.clear()
            except RpcError as exc:
                self.logger.error("RPC error in initialize_faults: %s.", exc)

    def trigger_fault(self, error_message, fault):
        """Trigger a service fault for a failure to the fault service.

        Args:
            error_message (string): The error message to provide in the camera capture fault.
            fault (service_fault_pb2.ServiceFault): The complete service fault to be issued.
        """
        if self.fault_client is not None and fault is not None:
            fault.error_message = error_message
            try:
                self.fault_client.trigger_service_fault(fault)
                self.active_fault_id_names.add(fault.fault_id.fault_name)
            except ServiceFaultAlreadyExistsError:
                pass
            except RpcError as exc:
                self.logger.error("RPC error in trigger_fault: %s.", exc)

    def clear_fault(self, fault):
        """Attempts to clear the camera capture fault from the fault service.

        Args:
            fault (service_fault_pb2.ServiceFault): The fault (which contains an ID) to be cleared.
        """
        if self.fault_client is not None and fault is not None:
            try:
                if fault.fault_id.fault_name in self.active_fault_id_names:
                    self.fault_client.clear_service_fault(fault.fault_id,
                                                          timeout=CLEAR_FAULT_RPC_TIMEOUT_SECS)
                    self.active_fault_id_names.remove(fault.fault_id.fault_name)
            except ServiceFaultDoesNotExistError:
                self.logger.warning("No service fault found to clear.")
            except RpcError as exc:
                self.logger.error("RPC error in clear_fault: %s.", exc)

    def _maybe_log_error(self, error_message=None, show_last_error=False):
        """Logs the error message if it is new (to prevent spam).

        Args:
            error_message (string): The new error message.
            show_last_error (Boolean): If true, the error message will be logged even if it is not new.

        Returns:
            None. Logs messages to the logger.
        """
        if error_message is not None:
            self.last_error_message = error_message
        if show_last_error:
            # force the printout of the last error message by sending the log message at a logger level
            # high enough to not be filtered out.
            self.logger.error(self.last_error_message)
        else:
            self.logger.warning(error_message)

    def _do_capture_with_error_checking(self, capture_func, custom_params=None,
                                        **capture_func_kwargs):
        """Calls the blocking capture function and checks for any exceptions.

        This function will print warning messages and trigger a camera capture fault if an
        exception is thrown by the camera interface's blocking capture function.

        Args:
            capture_func (CameraInterface.blocking_capture): The function capturing the image
                                                              data and timestamp.
            custom_params (service_customization_pb2.DictParam): Custom parameters passed to the blocking
                                                                 capture affecting the resulting capture
            **capture_func_kwargs: Other keyword arguments for the capture_func
        """
        try:
            if custom_params or capture_func_kwargs:
                # If supplying custom_params, try a blocking capture function that can handle them
                try:
                    img, timestamp = capture_func(custom_params=custom_params,
                                                  **capture_func_kwargs)
                except TypeError:
                    img, timestamp = capture_func()
            else:
                # Supports pre-3.3 blocking_capture if no custom_params or kwargs (both introduced in 3.3) are passed
                img, timestamp = capture_func()
            # Clear out any old error messages if the capture succeeds.
            self.last_error_message = None
            # Clear any previous camera capture faults after a successful image capture for
            # this image source.
            self.clear_fault(self.camera_capture_fault)
            return img, timestamp
        except Exception as err:
            error_message = "Failed to capture an image from %s: %s %s" % (self.image_source_name,
                                                                           type(err), err)
            self._maybe_log_error(error_message)
            self.trigger_fault(error_message, self.camera_capture_fault)
            return None, None

    def get_image_and_timestamp(self, custom_params=None, **capture_func_kwargs):
        """Retrieve the latest captured image and timestamp.

        Args:
            custom_params (service_customization_pb2.DictParam): Custom parameters passed to the object's
                                                                 capture_function affecting the resulting capture
            **capture_func_kwargs: Other keyword arguments for the capture_function

        Returns:
            The latest captured image and the time (in seconds) associated with that image capture.
            Throws a camera capture fault and returns None if the image cannot be retrieved.
        """
        if self.capture_thread is not None:
            thread_capture_output = self.capture_thread.get_latest_captured_image(
                custom_params=custom_params, **capture_func_kwargs)
            valid_thread_capture, image, timestamp = thread_capture_output.is_valid, thread_capture_output.image, thread_capture_output.timestamp
            if valid_thread_capture:
                if image is None or timestamp is None:
                    # Force the printout of the last error message since the capture failed.
                    self._maybe_log_error(show_last_error=True)
                return image, timestamp
            else:
                return self.capture_function(custom_params=custom_params, **capture_func_kwargs)
        else:
            # Call the capture function (which is wrapped with an error checker) to block and get the data.
            # capture_function already handles pre-3.3 blocking capture compatibility
            return self.capture_function(custom_params=custom_params, **capture_func_kwargs)

    def image_decode_with_error_checking(self, image_data, image_proto, image_req):
        """Decode the image data into an Image proto based on the requested format and quality.

        Args:
            image_data(any format): The image data returned by the camera interface's
                                    blocking_capture function.
            image_proto (image_pb2.Image): The image proto to be mutated with the decoded data.
            image_req (image_pb2.ImageRequest): The image request associated with the image_data.

        Returns:
            image_pb2.ImageResponse.Status indicating if the decoding succeeds, or image format conversion or
            pixel conversion failed. Throws a decode data fault if the image or
            pixels cannot be decoded to the desired format. Mutates the image_proto Image proto
            with the decoded data if successful.
        """
        decode_format = None
        quality_percent = None
        pixel_format = None
        if image_req:
            decode_format = image_req.image_format
            quality_percent = image_req.quality_percent
            pixel_format = image_req.pixel_format
            if pixel_format and (pixel_format not in self.supported_pixel_formats):
                return image_pb2.ImageResponse.STATUS_UNSUPPORTED_PIXEL_FORMAT_REQUESTED
        try:
            # Older function definition did not have image_req
            # Try/except for backwards compatibility
            try:
                self.camera_interface.image_decode(image_data, image_proto, image_req)
            except TypeError:
                self.camera_interface.image_decode(image_data, image_proto, decode_format,
                                                   quality_percent)
            # Clear any previous decode data faults after a successful decoding by this image source.
            self.clear_fault(self.decode_data_fault)
            return image_pb2.ImageResponse.STATUS_OK
        except Exception as err:
            decode_format_str = None
            if decode_format is None:
                decode_format_str = "unknown format"
            else:
                decode_format_str = image_pb2.Image.Format.Name(decode_format)
            error_message = "Failed to decode image %s to format %s: %s %s" % (
                self.image_source_name, decode_format_str, type(err), err)
            self._maybe_log_error(error_message)
            self.trigger_fault(error_message, self.decode_data_fault)
            return image_pb2.ImageResponse.STATUS_UNSUPPORTED_IMAGE_FORMAT_REQUESTED

    def stop_capturing(self, timeout_secs=10):
        """Stop the image capture thread if one exists.

        Args:
            timeout_secs(int): The timeout [seconds] for attempting to join and destroy the capture thread.
        """
        if self.capture_thread is not None:
            self.capture_thread.stop_capturing(timeout_secs)

    @staticmethod
    def make_image_source(source_name, rows=None, cols=None, pixel_formats=[],
                          image_type=image_pb2.ImageSource.IMAGE_TYPE_VISUAL,
                          image_formats=[image_pb2.Image.FORMAT_JPEG], param_spec=None):
        """Create an instance of the image_pb2.ImageSource for a given source name.

        Args:
            source_name (string): The name for the camera source.
            rows (int): The number of rows of pixels in the image.
            cols (int): The number of cols of pixels in the image.
            image_type (image_pb2.ImageType): The type of image (e.g. visual, depth).
            image_formats (image_pb2.Image.Format): The image formats supported (jpeg, raw)
            pixel_formats (image_pb2.Image.PixelFormat): The pixel formats supported
            param_spec (service_customization_pb2.DictParam.Spec): A set of custom parameters
                                                                   passed into this image source
        Returns:
            An ImageSource with the cols, rows, and image type populated.
        """
        source = image_pb2.ImageSource()
        source.name = source_name

        if rows is not None and cols is not None:
            source.rows = rows
            source.cols = cols

        # Image from the ricoh theta is a JPEG, which is considered a visual image source (no depth data).
        source.image_type = image_type
        source.image_formats.extend(image_formats)
        source.pixel_formats.extend(pixel_formats)
        if param_spec:
            source.custom_params.CopyFrom(param_spec)
        return source

    @staticmethod
    def make_capture_parameters(gain=None, exposure=None, request_custom_params=None):
        """Creates an instance of the image_pb2.CaptureParameters protobuf message.

        Args:
            gain (float | function): The sensor's gain in dB. This can be a fixed value or a function
                                     which returns the gain as a float.
            exposure (float | function): The exposure time for an image in seconds. This can be a fixed
                              value or a function which returns the exposure time as a float.
            request_custom_params (service_customization_pb2.DictParam): Custom Params associated with the image
                            request. Should not be 'None', but left as an option to accomodate old callers
        Returns:
            An instance of the protobuf CaptureParameters message.
        """
        params = image_pb2.CaptureParameters()
        if gain:
            if callable(gain):
                params.gain = gain()
            else:
                params.gain = gain
        if exposure:
            if callable(exposure):
                params.exposure_duration.CopyFrom(seconds_to_duration(exposure()))
            elif exposure == float('inf'):
                params.exposure_duration.CopyFrom(seconds_to_duration(sys.maxsize))
            else:
                params.exposure_duration.CopyFrom(seconds_to_duration(exposure))
        if request_custom_params:
            params.custom_params.CopyFrom(request_custom_params)
        return params


class ThreadCaptureOutput:
    """Small struct to represent the output of an ImageCaptureThread's get_latest_captured_image
    in a future-compatible way

    Args:
        is_valid (Boolean): Whether the latest capture uses the custom parameters and other arguments
                            supplied in the latest request, and is therefore returned
        image (Any | None): If the latest capture is valid, the image data in any format
                            (e.g. numpy, bytes, array)
        timestamp (float): The timestamp that the latest valid capture was taken
    """

    def __init__(self, is_valid, image, timestamp):
        self.is_valid = is_valid
        self.image = image
        self.timestamp = timestamp


class ImageCaptureThread():
    """Continuously query and store the last successfully captured image and its
    associated timestamp for a single camera device.

    Args:
        image_source_name(string): The image source name.
        capture_func (CameraInterface.blocking_capture): The function capturing the image
                                                         data and timestamp.
        capture_period_secs (int): Amount of time (in seconds) between captures to wait
                                   before triggering the next capture. Defaults to
                                   0.05s between captures.
        custom_params (service_customization_pb2.DictParam): Custom parameters passed to capture_func
                                                             affecting the resulting capture
        **capture_func_kwargs: Other keyword arguments for the capture_func
    """

    def __init__(self, image_source_name, capture_func, capture_period_secs=0.05,
                 custom_params=None, **capture_func_kwargs):
        # Name of the image source that is being requested from.
        self.image_source_name = image_source_name

        # Indicate if the image capture thread is alive.
        self.stop_capturing_event = threading.Event()

        # Track the last image and timestamp for this image source.
        self.last_captured_image = None
        self.last_captured_time = None

        # Has a capture with the latest parameters completed (not necessarily successfully)
        self.has_updated_capture = False

        # Lock for the thread.
        self._thread_lock = threading.Lock()
        self._thread = None

        # The wait time between captures.
        self.capture_period_secs = capture_period_secs

        # Custom parameters the thread is currently running with
        self.custom_params = custom_params

        #Other keyword arguments the thread is currently running with
        self.capture_func_kwargs = capture_func_kwargs

        # Original user-passed capture_func
        self.init_capture_function = capture_func

        # Function that completes the capture
        # Expected function signature: blocking_capture_function(custom_params=None): returns (image data[numpy bytes array], time[float])
        self.capture_function = self._make_capture_func(capture_func, custom_params=None,
                                                        **capture_func_kwargs)

    def start_capturing(self):
        """Start the background thread for the image captures."""
        print("Starting the thread for %s" % self.image_source_name)
        self._thread = threading.Thread(target=self._do_image_capture)
        self._thread.daemon = True
        self._thread.start()

    def maybe_update_thread(self, custom_params=None, **capture_func_kwargs):
        if custom_params != self.custom_params or capture_func_kwargs != self.capture_func_kwargs:
            self.capture_function = self._make_capture_func(self.init_capture_function,
                                                            custom_params, **capture_func_kwargs)
            self.custom_params = custom_params
            self.capture_func_kwargs = capture_func_kwargs
            self.has_updated_capture = False

    def set_last_captured_image(self, image_frame, capture_time):
        """Update the last image capture and timestamp."""
        with self._thread_lock:
            self.last_captured_image = image_frame
            self.last_captured_time = capture_time
            self.has_updated_capture = True

    def get_latest_captured_image(self, custom_params=None, **capture_func_kwargs):
        """Returns the last found image and timestamp in a ThreadCaptureOutput object if that
            image uses the latest params. Otherwise returns a ThreadCaptureOutput object with
            is_valid = False and capture/timestamp as None.
        """

        with self._thread_lock:
            if (custom_params == self.custom_params and
                    capture_func_kwargs == self.capture_func_kwargs and self.has_updated_capture):
                return ThreadCaptureOutput(True, self.last_captured_image, self.last_captured_time)
            else:
                self.maybe_update_thread(custom_params=custom_params, **capture_func_kwargs)
                return ThreadCaptureOutput(False, None, None)

    def _make_capture_func(self, capture_func, custom_params=None, **capture_func_kwargs):
        """Update the capture function to use custom_params and capture_func_kwargs if it can"""

        # capture_func is likely provided through create_capture_thread, which already does handling for pre-3.3 blocking_capture
        # Still, check for the custom_params argument to ensure we accomodate pre-3.3 direct implementations of ImageCaptureThreads
        if "custom_params" in inspect.signature(capture_func).parameters.keys():
            #If using a blocking capture function that takes in custom params or kwargs, one should supply those
            def output_capture_function():
                return capture_func(custom_params=custom_params, **capture_func_kwargs)
        else:
            output_capture_function = capture_func
        return output_capture_function

    def _do_image_capture(self):
        """Main loop for the image capture thread, which requests and saves images."""
        while not self.stop_capturing_event.isSet():
            # Get the image by calling the blocking capture function.
            start_time = time.time()
            capture, capture_time = self.capture_function()
            self.set_last_captured_image(capture, capture_time)

            # Wait for the total capture period (where the wait time is adjusted based on how
            # long the capture took).
            wait_time = self.capture_period_secs - (time.time() - start_time)
            if self.stop_capturing_event.wait(wait_time):
                # If stop_capturing_event is set, then break from the capture loop now.
                break

    def stop_capturing(self, timeout_secs=10):
        """Stop the image capture thread."""
        self.stop_capturing_event.set()
        self._thread.join(timeout=timeout_secs)


class CameraBaseImageServicer(image_service_pb2_grpc.ImageServiceServicer):
    """GRPC service to provide access to multiple different image sources.

    The service can list the available image (device) sources and query each source for image data.

    Args:
        bosdyn_sdk_robot (Robot): The robot instance for the service to connect to.
        service_name (string): The name of the image service.
        image_sources(List[VisualImageSource]): The list of image sources (provided as a VisualImageSource).
        logger (logging.Logger): Logger for debug and warning messages.
        use_background_capture_thread (bool): If true, the image service will create a thread that continuously
            captures images so the image service can respond rapidly to the GetImage request. If false,
            the image service will call an image sources' blocking_capture_function during the GetImage request.
        background_capture_params (service_customization_pb2.DictParam): If use_background_capture_thread is true,
            custom image source parameters used for all of the background captures. Otherwise ignored
    """

    def __init__(self, bosdyn_sdk_robot, service_name, image_sources, logger=None,
                 use_background_capture_thread=True, background_capture_params=None):
        super(CameraBaseImageServicer, self).__init__()
        if logger is None:
            # Set up the logger to remove duplicated messages and use a specific logging format.
            setup_logging(include_dedup_filter=True)
            self.logger = _LOGGER
        else:
            self.logger = logger

        self.bosdyn_sdk_robot = bosdyn_sdk_robot

        # Service name this servicer is associated with in the robot directory.
        self.service_name = service_name

        # Fault client to report service faults
        self.fault_client = self.bosdyn_sdk_robot.ensure_client(FaultClient.default_service_name)

        # Get a timesync endpoint from the robot instance such that the image timestamps can be
        # reported in the robot's time.
        self.bosdyn_sdk_robot.time_sync.wait_for_sync()

        # A list of all the image sources available by this service. List[VisualImageSource]
        self.image_sources_mapped = dict()  # Key: source name (string), Value: VisualImageSource
        for source in image_sources:
            # Set the logger for each visual image source to be the logger of the camera service class.
            source.set_logger(self.logger)
            # Set up the fault client so service faults can be created.
            source.initialize_faults(self.fault_client, self.service_name)
            # Potentially start the capture threads in the background.
            if use_background_capture_thread:
                source.create_capture_thread(background_capture_params)
            # Save the visual image source class associated with the image source name.
            self.image_sources_mapped[source.image_source_name] = source

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
        for source in self.image_sources_mapped.values():
            response.image_sources.add().CopyFrom(source.image_source_proto)
        populate_response_header(response, request)
        return response

    def _set_format_and_decode(self, image_data, img_proto, img_req):
        """Calls the image_decode_with_error_checking function, which returns a (Boolean, Boolean) if the decoding succeeds."""
        # This function should set the image data, pixel format, image format, and transform snapshot fields.
        return self.image_sources_mapped[
            img_req.image_source_name].image_decode_with_error_checking(
                image_data, img_proto, img_req)

    def GetImage(self, request, context):
        """Gets the latest image capture from all the image sources specified in the request.

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
            if src_name not in self.image_sources_mapped:
                # The requested camera source does not match the name of the Ricoh Theta camera, so it cannot
                # be completed and will have a failure status in the response message.
                img_resp.status = image_pb2.ImageResponse.STATUS_UNKNOWN_CAMERA
                self.logger.warning("Camera source '%s' is unknown.", src_name)
                continue

            if img_req.resize_ratio < 0 or img_req.resize_ratio > 1:
                img_resp.status = image_pb2.ImageResponse.STATUS_UNSUPPORTED_RESIZE_RATIO_REQUESTED
                self.logger.warning("Resize ratio %f is unsupported.", img_req.resize_ratio)
                continue

            if img_req.HasField("custom_params"):
                value_validation_error = self.image_sources_mapped[src_name].value_validator(
                    img_req.custom_params)
                if value_validation_error:
                    img_resp.status = image_pb2.ImageResponse.STATUS_CUSTOM_PARAMS_ERROR
                    img_resp.custom_param_error.CopyFrom(value_validation_error)
                    continue

            # Set the image source information in the response.
            img_resp.source.CopyFrom(self.image_sources_mapped[src_name].image_source_proto)

            # Set the image capture parameters in the response.
            img_resp.shot.capture_params.CopyFrom(
                self.image_sources_mapped[src_name].get_image_capture_params(img_req.custom_params))

            if img_req.HasField("custom_params"):
                #If future keyword arguments are added here, they'll need to be added to this call
                #get_image_and_timestamp already calls a 'sanitized' capture function that handles pre-3.3 blocking_captures
                captured_image, img_time_seconds = self.image_sources_mapped[
                    src_name].get_image_and_timestamp(custom_params=img_req.custom_params)
            else:
                #get_image_and_timestamp() can accomodate pre-3.3 blocking_capture calls if no custom params are supplied
                captured_image, img_time_seconds = self.image_sources_mapped[
                    src_name].get_image_and_timestamp()

            if captured_image is None or img_time_seconds is None:
                img_resp.status = image_pb2.ImageResponse.STATUS_IMAGE_DATA_ERROR
                error_message = "Failed to capture an image from %s on the server." % src_name
                response.header.error.message = error_message
                self.logger.warning(error_message)
                continue

            # Convert the image capture time from the local clock time into the robot's time. Then set it as
            # the acquisition timestamp for the image data.
            img_resp.shot.acquisition_time.CopyFrom(
                self.bosdyn_sdk_robot.time_sync.robot_timestamp_from_local_secs(img_time_seconds))

            img_resp.shot.image.rows = img_resp.source.rows
            img_resp.shot.image.cols = img_resp.source.cols

            # Set the image data.
            img_resp.shot.image.format = img_req.image_format
            decode_status = self._set_format_and_decode(captured_image, img_resp.shot.image,
                                                        img_req)
            if decode_status != image_pb2.ImageResponse.STATUS_OK:
                img_resp.status = decode_status

            # Set that we successfully got the image.
            if img_resp.status == image_pb2.ImageResponse.STATUS_UNKNOWN:
                img_resp.status = image_pb2.ImageResponse.STATUS_OK

        # No header error codes, so set the response header as CODE_OK.
        populate_response_header(response, request)
        return response

    def __del__(self):
        for source in self.image_sources_mapped.values():
            source.stop_capturing()
