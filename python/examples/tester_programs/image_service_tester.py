# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from __future__ import print_function

import argparse
import datetime
import logging
import os
import sys
import time

# Logger for all the debug information from the tests.
_LOGGER = logging.getLogger("ImageService Tester")

from plugin_tester import acquire_get_status_and_save
from testing_helpers import (log_debug_information, run_test, test_directory_registration,
                             test_if_service_has_active_service_faults,
                             test_if_service_is_reachable)

import bosdyn.client
import bosdyn.client.util
import bosdyn.util
from bosdyn.api import data_acquisition_pb2, image_pb2
from bosdyn.client.data_acquisition import DataAcquisitionClient
from bosdyn.client.data_acquisition_store import DataAcquisitionStoreClient
from bosdyn.client.exceptions import InvalidRequestError, ResponseError, ResponseTooLargeError
from bosdyn.client.image import (ImageClient, ImageDataError, SourceDataError,
                                 UnknownImageSourceError, UnsupportedImageFormatRequestedError,
                                 UnsupportedPixelFormatRequestedError,
                                 UnsupportedResizeRatioRequestedError, build_image_request,
                                 save_images_as_files)
from bosdyn.client.util import get_logger, setup_logging, strip_image_response

TABLET_REQUIRED_IMAGE_FORMATS = {image_pb2.Image.FORMAT_JPEG}
VISUAL_FORMATS = {image_pb2.Image.FORMAT_JPEG, image_pb2.Image.FORMAT_RAW}
DEPTH_FORMATS = {image_pb2.Image.FORMAT_RAW}
ALL_FORMATS = VISUAL_FORMATS.union(DEPTH_FORMATS)


class SummaryLog(logging.Handler):
    """Accumulate all warnings and errors so that they can be printed out together in a summary."""

    def __init__(self):
        super(SummaryLog, self).__init__()
        self.warnings = []
        self.errors = []

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.ERROR:
            self.errors.append(self.format(record))
        elif record.levelno >= logging.WARNING:
            self.warnings.append(self.format(record))

    def print_summary(self):
        print('\nTesting Summary')
        if not self.warnings and not self.errors:
            print('\n\tAll tests succeeded!')
            return

        def print_items(name, items):
            if items:
                print('\n' + '\n*  '.join([name] + items))

        print_items('Errors', self.errors)
        print_items('Warnings', self.warnings)


def test_list_images(image_client, service_name, verbose):
    """Check that the image service can respond successfully to the ListImageSources RPC.

    Args:
        image_client (ImageClient): The client for the image service being tested.
        service_name (string): The unique service name of the image service.
        verbose (boolean): Print additional logging information on failure.

    Returns:
        Boolean indicating if the image service responds to the ListImageSources RPC, and each
        returned image source contains the necessary information in the proto.
    """
    image_response = None
    try:
        image_responses = image_client.list_image_sources()
    except Exception as err:
        _LOGGER.error("Exception raised when making the ListImageSources RPC: %s %s", type(err),
                      err)
        return False, []

    if len(image_responses) == 0:
        # The ListImageSources request responded with no image sources.
        _LOGGER.error("No image sources found for the image service %s" % service_name)
        return False, []

    _LOGGER.info("The following image sources are advertised by the image service: ")
    image_sources = []
    # Check all the image responses and make sure the returned ImageSource proto is filled out.
    for source in image_responses:
        _LOGGER.info("Image source name: %s", source.name)
        if verbose:
            _LOGGER.info("Full image source: %s", source)
        if len(source.name) == 0:
            # Missing a source name --> This is invalid and will cause issues throughout the image pipeline.
            _LOGGER.error("Image source is invalid: missing 'name' field.")
            return False, []
        # Track the image source names so we can use them later to make image requests.
        image_sources.append(source)
        # Rows/cols are not required, but are useful information and should be valid.
        if not (source.rows > 0 and source.cols > 0):
            _LOGGER.warning("Rows [%d] and cols [%s] are invalid or not filled out for %s.",
                            source.rows, source.cols, source.name)

        if len(source.pixel_formats) == 0:
            _LOGGER.warning("Supported pixel formats not specified for source %s", source.name)

        if len(source.image_formats) == 0:
            _LOGGER.warning("Supported image formats not specified for source %s", source.name)

    return True, image_sources


def copy_image_response_and_strip_bytes(proto):
    """Makes a copy of the protobuf message and strip the bytes data.

    This is such that bytes fields can be stripped for logging, without
    modifying the main proto.

    Args:
        proto (image_pb2.ImageResponse): The proto to copy and remove the image data from.

    Returns:
        The copied, stripped image response proto.
    """
    copied_image_data = image_pb2.ImageResponse()
    copied_image_data.CopyFrom(proto)
    strip_image_response(copied_image_data)
    return copied_image_data


def validate_image_response(img_data: image_pb2.ImageResponse, img_req: image_pb2.ImageRequest,
                            verbose=False):
    """Check that an image response has complete and accurate information in the proto fields.

    Args:
        img_data (image_pb2.ImageResponse): The image response proto to be checked for completeness.
        img_req (image_pb2.ImageRequest): The GetImage RPC request, used for debug logging.
        verbose (boolean): Print additional logging information on failure.

    Returns:
        Boolean indicating if the image response proto has the necessary fields: image data, source name,
        and an acquisition timestamp.
    """
    validated = True
    warned = False

    # Check the critical fields of the image response (data, source name, and timestamp).
    if len(img_data.source.name) == 0:
        _LOGGER.error("The image response is missing the source name.")
        if verbose:
            _LOGGER.info("Proto field: image_responses.source.name.")
        validated = False
    if not (len(img_data.shot.image.data) > 0):  # check that it has data.
        _LOGGER.error("The image response for %s is missing image data.", img_data.source.name)
        if verbose:
            _LOGGER.info("Proto field: image_responses.shot.image.data.")
        validated = False
    if not img_data.shot.acquisition_time.seconds > 0:
        _LOGGER.error("The image response for %s is missing a valid acquisition timestamp.",
                      img_data.source.name)
        if verbose:
            _LOGGER.info("Proto field: image_responses.shot.acquisition_time.")
        validated = False

    # Check that the rows/cols match.
    if img_data.shot.image.rows != img_data.source.rows:
        _LOGGER.warning("The image response for %s contains mismatched rows information.",
                        img_data.source.name)
        if verbose:
            _LOGGER.info(
                "Proto fields: image_responses.shot.image.rows=%d and "
                "image_responses.source.rows= %d.", img_data.shot.image.rows, img_data.source.rows)
        warned = True
    if img_data.shot.image.cols != img_data.source.cols:
        _LOGGER.warning("The image response for %s contains mismatched cols information.",
                        img_data.source.name)
        if verbose:
            _LOGGER.info(
                "Proto fields: image_responses.shot.image.cols=%d and "
                "image_responses.source.cols= %d.", img_data.shot.image.cols, img_data.source.cols)
        warned = True

    # Check that the formats are filled out.
    if img_data.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_UNKNOWN:
        _LOGGER.warning("The image response for %s does not have the pixel format filled out.",
                        img_data.source.name)
        if verbose:
            _LOGGER.info("Proto field: image_responses.shot.image.pixel_format.")
        warned = True
    if img_data.shot.image.format == image_pb2.Image.FORMAT_UNKNOWN:
        _LOGGER.warning("The image response %s does not have the image format filled out.",
                        img_data.source.name)
        if verbose:
            _LOGGER.info("Proto field: image_responses.shot.image.format.")
        warned = True

    # Check that the returned image format matches the requested image format.
    if img_req.image_format not in (image_pb2.Image.FORMAT_UNKNOWN, img_data.shot.image.format):
        _LOGGER.warning(
            "The image response for %s has capture format %s which not match the "
            "requested image format %s", img_data.source.name,
            image_pb2.Image.Format.Name(img_data.shot.image.format),
            image_pb2.Image.Format.Name(img_req.image_format))
        if verbose:
            _LOGGER.info("Proto field: image_responses.shot.image.format.")
        warned = True

    if img_req.pixel_format not in (image_pb2.Image.PIXEL_FORMAT_UNKNOWN,
                                    img_data.shot.image.pixel_format):
        _LOGGER.warning(
            "The image response for %s has pixel format %s which not match the "
            "requested pixel format %s", img_data.source.name,
            image_pb2.Image.PixelFormat.Name(img_data.shot.image.pixel_format),
            image_pb2.Image.PixelFormat.Name(img_req.pixel_format))
        if verbose:
            _LOGGER.info("Proto field: image_responses.shot.image.pixel_format.")
        warned = True

    if not validated or warned:
        # If a validation check failed, also print out the complete image request and response.
        if verbose or not validated:
            _LOGGER.info("GetImage request: %s", img_req)
            _LOGGER.info(
                "Image response (to the GetImage RPC) being evaluated [data field removed]: %s",
                copy_image_response_and_strip_bytes(img_data))
    return validated


def get_image_formats(image_source):
    """Get the list of image formats that we believe we can request for this source."""
    if image_source.image_formats:
        return image_source.image_formats

    if image_source.image_type == image_pb2.ImageSource.IMAGE_TYPE_VISUAL:
        return VISUAL_FORMATS
    elif image_source.image_type == image_pb2.ImageSource.IMAGE_TYPE_DEPTH:
        return DEPTH_FORMATS
    return (image_pb2.Image.FORMAT_UNKNOWN,)


def get_pixel_formats(image_source):
    """Get the list of pixel formats that we believe we can request for this source."""
    if image_source.pixel_formats:
        return image_source.pixel_formats

    return (image_pb2.Image.PIXEL_FORMAT_UNKNOWN,)


def test_request(img_req, image_client, source_names, img_format, pixel_format, verbose=False):
    """Test a single request and make sure that it completes successfully.

    Args:
        img_req(list(ImageRequest)): The request to send to the robot.
        image_client(ImageClient): The client to use.
        source_names(list(str)): List of all sources names in the request.
        img_format(ImageFormat): The image format being requested.
        pixel_format(PixelFormat): The pixel format being requested.
        verbose(bool): log extra information.

    Returns:
        The list of responses if everything was successful.
        None if there was an error.
        ResponseTooLargeError if the response was too large and we should skip further testing.
        """
    try:
        img_resps = image_client.get_image(img_req)
    except UnsupportedImageFormatRequestedError as err:
        _LOGGER.error("The image format %s is unsupported for image sources %s.",
                      image_pb2.Image.Format.Name(img_format), source_names)
        if verbose:
            log_debug_information(err, img_req, strip_response=True)
        return None
    except UnsupportedPixelFormatRequestedError as err:
        _LOGGER.error("The pixel format %s is unsupported for images sources %s",
                      image_pb2.Image.PixelFormat.Name(pixel_format), source_names)
        if verbose:
            log_debug_information(err, img_req, strip_response=True)
        return None
    except ImageDataError as err:
        _LOGGER.error("The image sources (%s) were unable to be captured and decoded in format %s.",
                      source_names, image_pb2.Image.Format.Name(img_format))
        if verbose:
            log_debug_information(err, img_req, strip_response=True)
        return None
    except UnknownImageSourceError as err:
        unknown_sources = []
        for img_resp in err.response.image_responses:
            if img_resp.status == image_pb2.ImageResponse.STATUS_UNKNOWN_CAMERA:
                unknown_sources.append(img_resp.source.name)
        _LOGGER.error("The image sources %s are unknown by the image service.", unknown_sources)
        if verbose:
            log_debug_information(err, img_req, strip_response=True)
        return None
    except SourceDataError as err:
        _LOGGER.error("The image sources (%s) do not have image source information.", source_names)
        if verbose:
            log_debug_information(err, img_req, strip_response=True)
        return None
    except ResponseTooLargeError as err:
        _LOGGER.warning(
            "Note: the response for requesting image sources %s in format %s is too large and they cannot "
            "all be requested at once unless the ImageClient's grpc message limit is increased.",
            source_names, image_pb2.Image.Format.Name(img_format))
        if verbose:
            log_debug_information(err, img_req, strip_response=True)
        # Exit out when the request is too large.
        return err

    # Check that the bare minimum required fields of the image response are populated.
    if len(img_resps) != len(img_req):
        # Found too many or too few image responses in a request for only one image.
        _LOGGER.warning(
            "The GetImageResponse RPC contains %d image responses, when %d images were requested.",
            len(img_resps), len(img_req))
        if verbose:
            _LOGGER.info("GetImage requests: %s", img_req)
            _LOGGER.info("GetImage response: %s",
                         [copy_image_response_and_strip_bytes(img) for img in img_resps])
        return None

    _LOGGER.info("Successfully saved image sources %s in format %s", source_names,
                 image_pb2.Image.Format.Name(img_format))

    for request, response in zip(img_req, img_resps):
        if not validate_image_response(response, request, verbose):
            # The image response did not succeed in the validation checks, therefore the format
            # requested does not completely work. Continue to the next potential image format
            # and attempt to request it.
            return None

    return img_resps


def request_image_and_save(image_sources, image_client, filepath, image_formats=ALL_FORMATS,
                           pixel_formats=(image_pb2.Image.PIXEL_FORMAT_UNKNOWN,), verbose=False):
    """Request the image sources in all possible formats and save the data.

    This makes GetImage RPCs for the image sources for each type of image format. The requests which
    respond without errors are then checked for completeness in the proto response, and saved.

    A warning message is printed if an image source cannot respond in a format that the tablet will
    be able to understand.

    Args:
        image_sources (List[ImageSource]): The image source names from the image service.
        image_client (ImageClient): The client for the image service being tested.
        filepath (string): A destination folder to save the images at.
        image_formats (Iterable(image_pb2.Image.ImageFormat)): image formats to capture.
        pixel_formats (Iterable(image_pb2.Image.PixelFormat)): pixel formats to capture.
        verbose (boolean): Print additional logging information on failure.

    Returns:
        Boolean indicating if the image sources could be successfully requested in one of the possible image
        formats and the image response is validated.
    """
    successful_request_found = False
    successful_tablet_request_found = False
    source_names = [source.name for source in image_sources]
    contains_visual = any(
        source.image_type == image_pb2.ImageSource.IMAGE_TYPE_VISUAL for source in image_sources)
    # Check that one of the formats requested by the tablet will work.
    for img_format in image_formats:
        for pixel_format in pixel_formats:
            img_req = [
                build_image_request(source.name, image_format=img_format, pixel_format=pixel_format)
                for source in image_sources
                if img_format in get_image_formats(source)
            ]
            if not img_req:
                continue
            responses = test_request(img_req, image_client, source_names, img_format, pixel_format,
                                     verbose)
            if not responses:
                continue
            if isinstance(responses, ResponseTooLargeError):
                return True

            # All checks for the image response have succeeded for this image format!
            successful_request_found = True
            if img_format in TABLET_REQUIRED_IMAGE_FORMATS:
                successful_tablet_request_found = True

            # Save all the collect images.
            save_images_as_files(responses, filepath=filepath, include_pixel_format=True)

    if contains_visual and not successful_tablet_request_found:
        _LOGGER.warning(
            "The image sources %s did not respond successfully to a GetImage RPC with one of the "
            "known image formats (%s) used by the tablet. This means the images will NOT appear successfully "
            "on the tablet.", source_names,
            [image_pb2.Image.Format.Name(f) for f in TABLET_REQUIRED_IMAGE_FORMATS])

    return successful_request_found


def test_request_each_image(image_client, image_sources, filepath, verbose):
    """Check that each image source can be successfully requested from the image service.

    This makes the GetImage RPC for every image source individually, and then a request containing all
    sources at once. It validates that the response is a complete proto (i.e. includes source name,
    timestamp, and data), and will save the images acquired when complete.

    Args:
        image_client (ImageClient): The client for the image service being tested.
        image_sources (List[ImageSource]): The image source names from the image service.
        filepath (string): A destination folder to save the images at.
        verbose (boolean): Print additional logging information on failure.

    Returns:
        Boolean indicating if every image source (and a request containing all sources at once) can
        be returned with the GetImage RPC, and the response contains enough image information (source
        name, data).
    """
    success = True
    # Test each image source individually.
    for source in image_sources:
        img_req_succeeded = request_image_and_save([source], image_client, filepath,
                                                   image_formats=get_image_formats(source),
                                                   pixel_formats=get_pixel_formats(source),
                                                   verbose=verbose)
        success = success and img_req_succeeded

    # Test a request for all the image sources (if more than one). Only do this if things have
    # been successful up until now.
    if success and len(image_sources) > 1:
        mega_img_req_succeeded = request_image_and_save(image_sources, image_client, filepath,
                                                        verbose=False)
        success = success and mega_img_req_succeeded
    return success


def test_images_respond_in_order(image_client, image_sources, verbose):
    """Check that each image source returns multiple images with in-order acquisition timestamps.

    Args:
        image_client (ImageClient): The client for the image service being tested.
        image_sources (List[ImageSource]): The image source names from the image service.
        verbose (boolean): Print additional logging information on failure.

    Returns:
        Boolean indicating if every image source responds to multiple image requests with images that
        have in-order acquisition timestamps.
    """
    # Request an image source 3 times and ensure each acquisition timestamp is later.
    for source in image_sources:
        for format in ALL_FORMATS:
            if format not in get_image_formats(source):
                continue
            responses = []
            for i in range(0, 3):
                try:
                    img_resp = image_client.get_image(
                        [build_image_request(source.name, image_format=format)])
                    assert len(img_resp) == 1
                    responses.append(img_resp[0])
                except Exception as err:
                    _LOGGER.error('Error capturing from source %s: %s', source.name, err)
                    break

            # Check that the timestamps are increasing.
            for curr_image, next_image in zip(responses[:-1], responses[1:]):
                curr_img_time = bosdyn.util.timestamp_to_sec(curr_image.shot.acquisition_time)
                next_img_time = bosdyn.util.timestamp_to_sec(next_image.shot.acquisition_time)
                if curr_img_time > next_img_time:
                    _LOGGER.error(
                        "Image source %s (requested as format %s) has out-of-order timestamps. Ensure only one image "
                        "service is running and the timestamps are being set properly.",
                        source.name, image_pb2.Image.Format.Name(format))
                    if verbose:
                        _LOGGER.info(
                            "First image responds with time: %s (%s seconds). The next image responds "
                            "with time: %s (%s seconds).", curr_image.shot.acquisition_time,
                            curr_img_time, next_image.shot.acquisition_time, next_img_time)
                    return False

    # All images respond with consecutive (potentially new) images.
    return True


def test_full_data_acquisition_integration(robot, image_sources, service_name, verbose):
    """Check that the image service is properly integrated with the data-acquisition service.

    Ensures that all image sources are listed as data acquisition image capabilities, and that each
    image capability for the service can be acquired and saved successfully.

    Args:
        robot (Robot): The robot to make client connections to.
        image_sources (List[ImageSource]): The image source names from the image service.
        service_name (string): The unique service name of the image service.
        verbose (boolean): Print additional logging information on failure.

    Returns:
        Boolean indicating that all of the service's image sources are listed in the on-robot
        data acquisition service and can be acquired successfully.
    """
    data_acquisition_client = robot.ensure_client(DataAcquisitionClient.default_service_name)
    data_store_client = robot.ensure_client(DataAcquisitionStoreClient.default_service_name)

    # Check that all the image sources from the image service are listed in the image capabilities of
    # the on-robot data acquisition service.
    capabilities = data_acquisition_client.get_service_info()
    found_service_name = False
    for capability in capabilities.image_sources:
        if capability.service_name == service_name:
            found_service_name = True
            # Check that each source is present.
            sources_not_found = []
            for src in image_sources:
                if src.name not in capability.image_source_names:
                    sources_not_found.append(src)
            if len(sources_not_found) > 0:
                _LOGGER.error(
                    "Image sources listed by the image service are not present in the data "
                    "acquisition service's set of image capabilities: %s", sources_not_found)
                if verbose:
                    _LOGGER.info("GetServiceInfo response: %s", capabilities)
                return False

    if not found_service_name:
        _LOGGER.error(
            "The image service %s is not listed as an image source in the data acquisition "
            "service's set of image capabilities.", service_name)
        if verbose:
            _LOGGER.info("GetServiceInfo response: %s", capabilities)
        return False

    # Check that each image source can be acquired and saved successfully.
    success = True
    group_name = "Image Service [%s] Test %s" % (
        service_name, datetime.datetime.today().strftime("%b %d %Y %H:%M:%S"))
    for src in image_sources:
        action_name = "acquire and status check: " + src.name
        acquisition_request = data_acquisition_pb2.AcquisitionRequestList()
        acquisition_request.image_captures.extend([
            data_acquisition_pb2.ImageSourceCapture(image_service=service_name,
                                                    image_source=src.name)
        ])
        capability_success = acquire_get_status_and_save(acquisition_request, src, action_name,
                                                         group_name, data_acquisition_client,
                                                         data_store_client, verbose)
        success = capability_success and success

    return success


def main(argv):
    """Main testing interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument("--service-name", required=True, type=str,
                        help="Unique service name for the image service being tested.")
    parser.add_argument('--destination-folder',
                        help='The folder where the images should be saved to.', required=False,
                        default='.')
    parser.add_argument(
        '--check-data-acquisition', action='store_true', help=
        "Test that the image sources are available in the data acquisition service and can be acquired."
    )

    options = parser.parse_args(argv)

    # Setup logger specific for this test program.
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    summary = SummaryLog()
    _LOGGER.addHandler(summary)

    sdk = bosdyn.client.create_standard_sdk('TestImageService')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()
    robot.sync_with_directory()

    try:
        # Test the directory registration of the image service.
        run_test(test_directory_registration,
                 "Image Service is registered in the robot's directory.", robot,
                 options.service_name, ImageClient.service_type)

        # Now that we know the service is registered, create a client for the image service on robot.
        robot.sync_with_directory()
        image_client = robot.ensure_client(options.service_name)

        # Test that the gRPC communications go through to the image service.
        run_test(test_if_service_is_reachable,
                 ("Image service's directory registration networking "
                  "information is correct and the image can be communicated with via gRPC."),
                 image_client.list_image_sources)

        # Test if there are any active service faults thrown by the image service in the current
        # robot state proto.
        run_test(test_if_service_has_active_service_faults, "The image service has no active "
                 "service faults in the current robot state.", robot, options.service_name)

        # Test that the service has image sources listed and the source protos are filled out properly.
        _LOGGER.info(
            "TEST: Image Service contains image sources with correctly formatted source protos.")
        success, image_sources = test_list_images(image_client, options.service_name,
                                                  options.verbose)
        if success:
            _LOGGER.info("SUCCESS!\n")
        else:
            return False

        # Test that each image source can respond to a GetImage request.
        run_test(test_request_each_image, "Request each image and ensure the response is complete.",
                 image_client, image_sources, options.destination_folder, options.verbose)

        # Test that when multiple images are requested, each returned image has a new (or at least identical)
        # acquisition timestamp.
        run_test(
            test_images_respond_in_order, "Multiple requested images respond in order based on the "
            "acquisition timestamp.", image_client, image_sources, options.verbose)

        if options.check_data_acquisition:
            # Check that the image service has integrated with the data acquisition service, each image source
            # is broadcast as an image capability, and can successfully be acquired and saved.
            run_test(
                test_full_data_acquisition_integration,
                "Image service is successfully integrated with "
                "the data acquisition service.", robot, image_sources, options.service_name,
                options.verbose)

        # Test if there are any active service faults thrown by the image service in the current
        # robot state proto.
        run_test(test_if_service_has_active_service_faults,
                 "The image service has no active service faults "
                 "after all tests are complete.", robot, options.service_name)

    finally:
        summary.print_summary()
    return True


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
