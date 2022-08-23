# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os
import threading
from unittest import mock

import cv2
import numpy as np
import pytest
from google.protobuf import timestamp_pb2
from PIL import Image

from bosdyn.api import header_pb2, image_pb2, service_fault_pb2
from bosdyn.client.fault import FaultClient, ServiceFaultDoesNotExistError
from bosdyn.client.image_service_helpers import (CameraBaseImageServicer, CameraInterface,
                                                 ImageCaptureThread, VisualImageSource,
                                                 convert_RGB_to_grayscale)


class MockFaultClient:

    def __init__(self):
        self.service_fault_counts = dict()  # key=fault id name, value = count
        self.clear_service_fault_called_count = 0

    def trigger_service_fault(self, service_fault, **kwargs):
        fault = service_fault.fault_id.fault_name
        if fault in self.service_fault_counts:
            self.service_fault_counts[fault] += 1
        else:
            self.service_fault_counts[fault] = 1
        return service_fault_pb2.TriggerServiceFaultResponse()

    def clear_service_fault(self, service_fault_id, clear_all_service_faults=False,
                            clear_all_payload_faults=False, **kwargs):
        # This function makes the assumption that every fault in this mock fault client's dictionary
        # has the same service_name in the fault id.
        if clear_all_service_faults:
            self.service_fault_counts = dict()
        elif service_fault_id.fault_name is not None:
            self.service_fault_counts[service_fault_id.fault_name] = 0
        self.clear_service_fault_called_count += 1
        return service_fault_pb2.ClearServiceFaultResponse()

    def get_total_fault_count(self):
        fault_amount = 0
        for fault_count in self.service_fault_counts.values():
            fault_amount += fault_count
        return fault_amount


class MockTimeSync:

    def wait_for_sync(self):
        return 1

    def robot_timestamp_from_local_secs(self, seconds):
        return timestamp_pb2.Timestamp(seconds=10, nanos=20)


class MockRobot:

    def __init__(self, token=None):
        self.user_token = token
        self.address = 'mock-address'

    def ensure_client(self, name):
        if name == FaultClient.default_service_name:
            return MockFaultClient()

    @property
    def time_sync(self):
        return MockTimeSync()


##### Helper functions to mimic the function signatures of the capture function
# and the decode image function for the VisualImageSource.
class FakeCamera(CameraInterface):

    def __init__(self, capture_func, decode_func):
        self.capture_func = capture_func
        self.decode_func = decode_func

    def blocking_capture(self):
        return self.capture_func()

    def image_decode(self, image_data, image_proto, image_req):
        return self.decode_func(image_data, image_proto, image_req)


# Old definition, pre 3.1.0
class OldFakeCamera(CameraInterface):

    def __init__(self, capture_func, decode_func):
        self.capture_func = capture_func
        self.decode_func = decode_func

    def blocking_capture(self):
        return self.capture_func()

    def image_decode(self, image_data, image_proto, image_format, quality_percent):
        return self.decode_func(image_data, image_proto, image_format, quality_percent)


def capture_fake():
    return "image", 1


def decode_fake(img_data, img_proto, img_req):
    img_proto.rows = 15


def decode_fake_no_resize(img_data, img_proto, img_format, quality):
    img_proto.rows = 16


def capture_return_onething():
    return 1


def decode_less_args(arg1, arg2):
    return 2


def capture_with_error():
    raise Exception("Failed Capture.")


def decode_with_error(img_data, img_proto, img_req):
    img_proto.rows = 15
    raise Exception("Failed Decode.")


class Increment():

    def __init__(self, barrier, t=1.1):
        self.timestamp = t
        self.barrier = barrier

    def capture_increment_count(self):
        self.barrier.wait(timeout=1)
        return "image", self.timestamp


def test_faults_in_visual_source():
    # Create the fault client
    fault_client = MockFaultClient()

    # Populate fault client with at least one "old" fault.
    fault_client.trigger_service_fault(
        service_fault_pb2.ServiceFault(fault_id=service_fault_pb2.ServiceFaultId(
            fault_name="fault1")))
    init_fault_amount = fault_client.get_total_fault_count()

    visual_src = VisualImageSource("source1", FakeCamera(capture_with_error, decode_with_error))

    # Attempt to get an image with no fault client enabled. Make sure no error is raised, and
    # values are returned as none.
    image, timestamp = visual_src.get_image_and_timestamp()
    assert image is None
    assert timestamp is None

    # attempt to decode an image with no fault client enabled. Make sure no error is raised.
    im_proto = image_pb2.Image(rows=10)
    status = visual_src.image_decode_with_error_checking(None, im_proto, None)
    assert im_proto.rows == 15
    assert status == image_pb2.ImageResponse.STATUS_UNSUPPORTED_IMAGE_FORMAT_REQUESTED

    # Setup faults
    visual_src.initialize_faults(fault_client, "service1")
    assert fault_client.get_total_fault_count() == 0
    assert visual_src.camera_capture_fault is not None
    assert visual_src.camera_capture_fault.fault_id.service_name == "service1"
    assert visual_src.decode_data_fault is not None
    assert visual_src.decode_data_fault.fault_id.service_name == "service1"

    # With fault client setup, check that faults are thrown when the bad functions get called.
    image, timestamp = visual_src.get_image_and_timestamp()
    assert image is None
    assert timestamp is None
    assert fault_client.service_fault_counts[
        visual_src.camera_capture_fault.fault_id.fault_name] == 1
    im_proto = image_pb2.Image(rows=21)
    status = visual_src.image_decode_with_error_checking(None, im_proto, None)
    assert im_proto.rows == 15
    assert fault_client.service_fault_counts[visual_src.decode_data_fault.fault_id.fault_name] == 1
    assert status == image_pb2.ImageResponse.STATUS_UNSUPPORTED_IMAGE_FORMAT_REQUESTED


def test_clear_not_active_faults():
    # Check that clearing faults works with non active faults.

    class MockFaultClientFaultNotActive:

        def clear_service_fault(self, service_fault_id, clear_all_service_faults=False,
                                clear_all_payload_faults=False, **kwargs):
            raise ServiceFaultDoesNotExistError(None, "error")

    visual_src = VisualImageSource("source1", FakeCamera(capture_with_error, decode_with_error))
    fault_client = MockFaultClientFaultNotActive()
    visual_src.initialize_faults(fault_client, "service1")
    assert len(visual_src.active_fault_id_names) == 0


def test_active_faults():
    # Check that active faults are managed correctly.

    visual_src = VisualImageSource("source1", FakeCamera(capture_with_error, decode_with_error))
    fault_client = MockFaultClient()
    visual_src.initialize_faults(fault_client, "service1")
    # Initialize function calls the clear_service_fault RPC.
    assert fault_client.clear_service_fault_called_count == 1
    assert len(visual_src.active_fault_id_names) == 0

    fake_fault_id = service_fault_pb2.ServiceFaultId(fault_name="Fake Capture Failure")
    fake_fault = service_fault_pb2.ServiceFault(
        fault_id=fake_fault_id, severity=service_fault_pb2.ServiceFault.SEVERITY_WARN)

    # Make sure we don't call clear_service_fault RPC because the fake fault is not active yet.
    visual_src.clear_fault(fake_fault)
    assert len(visual_src.active_fault_id_names) == 0
    assert fault_client.clear_service_fault_called_count == 1

    # Make the fake fault active.
    visual_src.trigger_fault("error", fake_fault)
    assert len(visual_src.active_fault_id_names) == 1
    assert fault_client.service_fault_counts[fake_fault.fault_id.fault_name] == 1

    # Clear the fake fault, but make sure RPC is only called once.
    visual_src.clear_fault(fake_fault)
    assert fault_client.clear_service_fault_called_count == 2
    visual_src.clear_fault(fake_fault)
    # Make sure clear_service_fault is not called for a cleared fault.
    assert fault_client.clear_service_fault_called_count == 2
    assert len(visual_src.active_fault_id_names) == 0


def test_faults_are_cleared_on_success():
    # Check that captures/decodes that fail and then later succeed will cause the faults to get cleared.
    class FailsThenSucceeds(CameraInterface):

        def __init__(self):
            self.capture_count = 0
            self.decode_count = 0

        def blocking_capture(self):
            self.capture_count += 1
            if self.capture_count == 1:
                raise Exception("Fake bad capture.")
            return "image", 1

        def image_decode(self, image_data, image_proto, image_req):
            self.decode_count += 1
            if self.decode_count == 1:
                raise Exception("Fake bad decode.")

    visual_src = VisualImageSource("source1", FailsThenSucceeds())
    fault_client = MockFaultClient()
    visual_src.initialize_faults(fault_client, "service1")
    # The first call to the capture and decode functions cause a fault to be thrown.
    image, timestamp = visual_src.get_image_and_timestamp()
    assert fault_client.service_fault_counts[
        visual_src.camera_capture_fault.fault_id.fault_name] == 1
    success = visual_src.image_decode_with_error_checking(None, image_pb2.Image(rows=21), None)
    assert fault_client.service_fault_counts[visual_src.decode_data_fault.fault_id.fault_name] == 1

    # The second calls will succeed, and now cause the faults to be cleared.
    image, timestamp = visual_src.get_image_and_timestamp()
    assert fault_client.service_fault_counts[
        visual_src.camera_capture_fault.fault_id.fault_name] == 0
    success = visual_src.image_decode_with_error_checking(None, image_pb2.Image(rows=21), None)
    assert fault_client.service_fault_counts[visual_src.decode_data_fault.fault_id.fault_name] == 0


def test_make_image_source():
    # Create a visual source with no rows/cols/image type provided.
    src_name = "source1"
    visual_src = VisualImageSource(src_name, FakeCamera(capture_fake, decode_fake))
    assert visual_src.image_source_proto.name == src_name
    assert visual_src.image_source_proto.image_type == image_pb2.ImageSource.IMAGE_TYPE_VISUAL
    assert visual_src.image_source_proto.rows == 0
    assert visual_src.image_source_proto.cols == 0

    # Create a visual source with rows and cols provided.
    src_name2 = "source2"
    src_rows2 = 60
    src_cols2 = 100
    visual_src2 = VisualImageSource(src_name2, FakeCamera(capture_fake, decode_fake), src_rows2,
                                    src_cols2)
    assert visual_src2.image_source_proto.name == src_name2
    assert visual_src2.image_source_proto.image_type == image_pb2.ImageSource.IMAGE_TYPE_VISUAL
    assert visual_src2.image_source_proto.rows == src_rows2
    assert visual_src2.image_source_proto.cols == src_cols2

    # Test the static method to create an ImageSourceProto
    src_name3 = "source3"
    src_rows3 = 10
    src_cols3 = 15
    src_type3 = image_pb2.ImageSource.IMAGE_TYPE_DEPTH
    img_proto = VisualImageSource.make_image_source(src_name3, src_rows3, src_cols3, [], src_type3)
    assert img_proto.name == src_name3
    assert img_proto.image_type == src_type3
    assert img_proto.rows == src_rows3
    assert img_proto.cols == src_cols3


def test_make_capture_params():
    # Create a visual source with no gain/exposure provided.
    visual_src = VisualImageSource("source1", FakeCamera(capture_fake, decode_fake))
    params = visual_src.get_image_capture_params()
    assert params.gain == 0
    assert params.exposure_duration.seconds == 0
    assert params.exposure_duration.nanos == 0

    # Create a visual source with gain and exposure provided.
    gain = 1.5
    exposure = 101.005
    visual_src = VisualImageSource("source1", FakeCamera(capture_fake, decode_fake), gain=gain,
                                   exposure=exposure)
    params = visual_src.get_image_capture_params()
    assert abs(params.gain - gain) < 1e-3
    assert abs(params.exposure_duration.seconds - 101) < 1e-3
    assert abs(params.exposure_duration.nanos - int(.005 * 1e9)) <= 1

    # Test the static method to create a CaptureParameters proto
    cap_proto = VisualImageSource.make_capture_parameters(gain, exposure)
    assert abs(cap_proto.gain - gain) < 1e-3
    assert abs(cap_proto.exposure_duration.seconds - 101) < 1e-3
    assert abs(cap_proto.exposure_duration.nanos - int(.005 * 1e9)) <= 1

    # Test the static method while passing functions for gain and exposure
    cap_proto = VisualImageSource.make_capture_parameters(lambda: gain, lambda: exposure)
    assert abs(cap_proto.gain - gain) < 1e-3
    assert abs(cap_proto.exposure_duration.seconds - 101) < 1e-3
    assert abs(cap_proto.exposure_duration.nanos - int(.005 * 1e9)) <= 1


def test_visual_source_with_thread():
    barrier = threading.Barrier(2)
    inc = Increment(barrier)

    visual_src = VisualImageSource("source1", FakeCamera(inc.capture_increment_count, decode_fake))
    visual_src.create_capture_thread()
    # The Increment class has a barrier looking for "2" wait calls. If the blocking capture function gets
    # called as expected, and we call wait in the main thread of the test, then it will release.
    try:
        barrier.wait(timeout=1)
    except threading.BrokenBarrierError:
        pytest.fail("Barrier reached the timeout, therefore blocking_capture is not called.")
    finally:
        visual_src.stop_capturing()


def test_not_camera_interface():

    class WrongFakeCamera():

        def blocking_capture(self):
            return 1

    # Check that the camera_interface argument ensures that it is a class which subclasses
    # the provided CameraInterface class.
    with pytest.raises(AssertionError):
        visual_src = VisualImageSource("source1", WrongFakeCamera())

    # Check that instantiating a class with camera interface without the methods expected
    # will fail on creation.
    class BadFakeCamera(CameraInterface):

        def missing_everything(self):
            pass

    with pytest.raises(TypeError):
        visual_src = VisualImageSource("source2", BadFakeCamera())

    # # Check that instantiating a class which subclasses the camera interface but implements
    # # the methods incorrectly will throw errors.
    # with pytest.raises(Exception):
    #     visual_src = VisualImageSource("source3", FakeCamera(capture_return_onething, decode_less_args))


def test_image_capture_thread():
    default_time = 1.1
    barrier = threading.Barrier(2)
    inc = Increment(barrier, t=default_time)
    cap_thread = ImageCaptureThread("source1", inc.capture_increment_count)

    # Test the setter/getter for the image and timestamp.
    override_time = 2.8
    cap_thread.set_last_captured_image("my image", override_time)
    image, timestamp = cap_thread.get_latest_captured_image()
    assert image == "my image"
    assert abs(timestamp - override_time) < 1e-3

    # Test that starting will start the thread.
    cap_thread.start_capturing()
    # The Increment class has a barrier looking for "2" wait calls. If the blocking capture function gets
    # called as expected, and we call wait in the main thread of the test, then it will release.
    for i in range(0, 3):
        try:
            barrier.wait(timeout=1)
        except threading.BrokenBarrierError:
            pytest.fail("Barrier reached the timeout, therefore blocking_capture is not called.")
    image, t = cap_thread.get_latest_captured_image()
    assert abs(t - default_time) < 1e-3
    assert image is not None

    # Test stopping the thread.
    cap_thread.stop_capturing()
    # The capture function will no longer set the barrier on another thread, so this should reach the timeout
    # such that we know the thread has stopped.
    with pytest.raises(threading.BrokenBarrierError):
        barrier.wait(0.5)


def _test_camera_service(use_background_capture_thread, logger=None):
    robot = MockRobot()

    src_name = "source1"
    r_amt = 10
    c_amt = 21
    gain = 25
    visual_src = VisualImageSource(src_name, FakeCamera(capture_fake, decode_fake), rows=r_amt,
                                   cols=c_amt, gain=gain)
    src_name2 = "source_cap_error"
    visual_src2 = VisualImageSource(src_name2, FakeCamera(capture_with_error, decode_fake),
                                    rows=r_amt, cols=c_amt)
    src_name3 = "source_decode_error"
    visual_src3 = VisualImageSource(src_name3, FakeCamera(capture_fake, decode_with_error),
                                    rows=r_amt, cols=c_amt)
    src_name4 = "source_capture_malformed"
    visual_src4 = VisualImageSource(src_name4, FakeCamera(capture_return_onething, decode_fake),
                                    rows=r_amt, cols=c_amt)
    src_name5 = "source_decode_malformed"
    visual_src5 = VisualImageSource(src_name5, FakeCamera(capture_fake, decode_less_args),
                                    rows=r_amt, cols=c_amt)
    src_name6 = "source2"
    visual_src6 = VisualImageSource(src_name6, FakeCamera(capture_fake, decode_fake), rows=r_amt,
                                    cols=c_amt, gain=gain)
    image_sources = [visual_src, visual_src2, visual_src3, visual_src4, visual_src5, visual_src6]
    camera_service = CameraBaseImageServicer(
        robot, "camera-service", image_sources,
        use_background_capture_thread=use_background_capture_thread, logger=logger)

    req = image_pb2.ListImageSourcesRequest()
    resp = camera_service.ListImageSources(req, None)
    assert resp.header.error.code == header_pb2.CommonError.CODE_OK
    assert len(resp.image_sources) == 6
    found_src1, found_src2, found_src3, found_src4, found_src5, found_src6 = False, False, False, False, False, False
    for src in resp.image_sources:
        if src.name == src_name:
            found_src1 = True
        if src.name == src_name2:
            found_src2 = True
        if src.name == src_name3:
            found_src3 = True
        if src.name == src_name4:
            found_src4 = True
        if src.name == src_name5:
            found_src5 = True
        if src.name == src_name6:
            found_src6 = True
    assert found_src1 and found_src2 and found_src3 and found_src4 and found_src5 and found_src6

    # Request a known image source and make sure the response is as expected.
    req = image_pb2.GetImageRequest()
    req.image_requests.extend(
        [image_pb2.ImageRequest(image_source_name=src_name, quality_percent=10)])
    resp = camera_service.GetImage(req, None)
    assert resp.header.error.code == header_pb2.CommonError.CODE_OK
    assert len(resp.image_responses) == 1
    img_resp = resp.image_responses[0]
    assert img_resp.source.name == src_name
    assert img_resp.source.rows == r_amt
    assert img_resp.source.cols == c_amt
    assert img_resp.shot.capture_params.gain == gain
    assert img_resp.shot.image.rows == 15  # Output of decode_fake
    assert img_resp.shot.image.cols == c_amt
    assert abs(img_resp.shot.acquisition_time.seconds - 10) < 1e-3  # Robot converted timestamp
    assert abs(img_resp.shot.acquisition_time.nanos - 20) < 1e-3  # Robot converted timestamp

    # Request multiple image sources and make sure the response is complete.
    req = image_pb2.GetImageRequest()
    req.image_requests.extend([
        image_pb2.ImageRequest(image_source_name=src_name, quality_percent=10),
        image_pb2.ImageRequest(image_source_name=src_name6)
    ])
    resp = camera_service.GetImage(req, None)
    assert resp.header.error.code == header_pb2.CommonError.CODE_OK
    assert len(resp.image_responses) == 2
    found_src1, found_src6 = False, False
    for src in resp.image_responses:
        if src.source.name == src_name:
            found_src1 = True
        if src.source.name == src_name6:
            found_src6 = True
    assert found_src6 and found_src1

    # Request an image source that does not exist.
    req = image_pb2.GetImageRequest()
    req.image_requests.extend(
        [image_pb2.ImageRequest(image_source_name="unknown", quality_percent=10)])
    resp = camera_service.GetImage(req, None)
    assert resp.header.error.code == header_pb2.CommonError.CODE_OK
    assert len(resp.image_responses) == 1
    img_resp = resp.image_responses[0]
    assert img_resp.status == image_pb2.ImageResponse.STATUS_UNKNOWN_CAMERA

    # Request an image from a source with a bad capture function.
    req = image_pb2.GetImageRequest()
    req.image_requests.extend(
        [image_pb2.ImageRequest(image_source_name=src_name2, quality_percent=10)])
    resp = camera_service.GetImage(req, None)
    assert resp.header.error.code == header_pb2.CommonError.CODE_OK
    assert len(resp.image_responses) == 1
    img_resp = resp.image_responses[0]
    assert img_resp.status == image_pb2.ImageResponse.STATUS_IMAGE_DATA_ERROR

    # Request an image from a source with a decode error.
    req = image_pb2.GetImageRequest()
    req.image_requests.extend(
        [image_pb2.ImageRequest(image_source_name=src_name3, quality_percent=10)])
    resp = camera_service.GetImage(req, None)
    assert resp.header.error.code == header_pb2.CommonError.CODE_OK
    assert len(resp.image_responses) == 1
    img_resp = resp.image_responses[0]
    print(img_resp)
    assert img_resp.status == image_pb2.ImageResponse.STATUS_UNSUPPORTED_IMAGE_FORMAT_REQUESTED

    # Request an image with a malformed capture function (should raise an error so developer can fix).
    req = image_pb2.GetImageRequest()
    req.image_requests.extend(
        [image_pb2.ImageRequest(image_source_name=src_name4, quality_percent=10)])
    resp = camera_service.GetImage(req, None)
    assert resp.header.error.code == header_pb2.CommonError.CODE_OK
    assert len(resp.image_responses) == 1
    img_resp = resp.image_responses[0]
    assert img_resp.status == image_pb2.ImageResponse.STATUS_IMAGE_DATA_ERROR


def test_image_service_no_thread():
    _test_camera_service(use_background_capture_thread=False)


def test_image_service_with_thread(caplog, capsys):
    # Disable the logger from printing messages because the background thread will repeatedly
    # print failure messages for all the "buggy" capture options that are being used to test
    # the service.
    _test_camera_service(use_background_capture_thread=True)


def test_gain_and_exposure_as_functions():

    class GainAndExposure():

        def __init__(self):
            self.gain = 0
            self.exposure = 0

        def get_gain(self):
            self.gain += 1
            return self.gain

        def get_exposure(self):
            self.exposure += 1
            return self.exposure

    # Check that gain/exposure functions are accepted inputs and get recalled each time you get the
    # capture parameters proto.
    ge = GainAndExposure()
    visual_src = VisualImageSource("source1", FakeCamera(capture_fake, decode_fake),
                                   gain=ge.get_gain, exposure=ge.get_exposure)
    capture_params = visual_src.get_image_capture_params()
    assert capture_params.gain == 1
    assert capture_params.exposure_duration.seconds == 1

    capture_params = visual_src.get_image_capture_params()
    assert capture_params.gain == 2
    assert capture_params.exposure_duration.seconds == 2


def test_decode_backwards_compatibility():
    # Check that new decode call signature works with older camera interface that have specific
    # arguments and no resize_ratio.
    visual_src = VisualImageSource("source1", OldFakeCamera(capture_fake, decode_fake_no_resize))
    capture_params = visual_src.get_image_capture_params()
    im_proto = image_pb2.Image(rows=15)
    success = visual_src.image_decode_with_error_checking(None, im_proto, None)
    assert im_proto.rows == 16
    assert success


def test_convert_pixel_format():

    empty_visual_src = VisualImageSource("source1", FakeCamera(capture_fake,
                                                               decode_fake), rows=None, cols=None,
                                         gain=None, exposure=None, pixel_formats=[])
    grayscale_visual_src = VisualImageSource(
        "source1", FakeCamera(capture_fake, decode_fake), rows=None, cols=None, gain=None,
        exposure=None, pixel_formats=[image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8])
    rgb_visual_src = VisualImageSource(
        "source1", FakeCamera(capture_fake, decode_fake), rows=None, cols=None, gain=None,
        exposure=None, pixel_formats=[
            image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8, image_pb2.Image.PIXEL_FORMAT_RGB_U8
        ])

    im_proto = image_pb2.Image(rows=15)
    grayscale_im_req = image_pb2.ImageRequest(
        pixel_format=image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8)
    rgb_im_req = image_pb2.ImageRequest(pixel_format=image_pb2.Image.PIXEL_FORMAT_RGB_U8)
    unknown_im_req = image_pb2.ImageRequest(pixel_format=image_pb2.Image.PIXEL_FORMAT_UNKNOWN)

    # Test VisualImageSource with empty pixel formats.
    status = empty_visual_src.image_decode_with_error_checking(None, im_proto, None)
    assert im_proto.rows == 15
    assert status == image_pb2.ImageResponse.STATUS_OK
    status = empty_visual_src.image_decode_with_error_checking(None, im_proto, unknown_im_req)
    assert im_proto.rows == 15
    assert status == image_pb2.ImageResponse.STATUS_OK
    status = empty_visual_src.image_decode_with_error_checking(None, im_proto, grayscale_im_req)
    assert im_proto.rows == 15
    assert status == image_pb2.ImageResponse.STATUS_UNSUPPORTED_PIXEL_FORMAT_REQUESTED
    status = empty_visual_src.image_decode_with_error_checking(None, im_proto, rgb_im_req)
    assert im_proto.rows == 15
    assert status == image_pb2.ImageResponse.STATUS_UNSUPPORTED_PIXEL_FORMAT_REQUESTED

    # Test VisualImageSource with only grayscale pixel format.
    status = grayscale_visual_src.image_decode_with_error_checking(None, im_proto, None)
    assert im_proto.rows == 15
    assert status == image_pb2.ImageResponse.STATUS_OK
    status = grayscale_visual_src.image_decode_with_error_checking(None, im_proto, unknown_im_req)
    assert im_proto.rows == 15
    assert status == image_pb2.ImageResponse.STATUS_OK
    status = grayscale_visual_src.image_decode_with_error_checking(None, im_proto, grayscale_im_req)
    assert im_proto.rows == 15
    assert status == image_pb2.ImageResponse.STATUS_OK
    status = grayscale_visual_src.image_decode_with_error_checking(None, im_proto, rgb_im_req)
    assert im_proto.rows == 15
    assert status == image_pb2.ImageResponse.STATUS_UNSUPPORTED_PIXEL_FORMAT_REQUESTED

    # Test VisualImageSource with grayscale and rgb pixel format.
    status = rgb_visual_src.image_decode_with_error_checking(None, im_proto, None)
    assert im_proto.rows == 15
    assert status == image_pb2.ImageResponse.STATUS_OK
    status = rgb_visual_src.image_decode_with_error_checking(None, im_proto, unknown_im_req)
    assert im_proto.rows == 15
    assert status == image_pb2.ImageResponse.STATUS_OK
    status = rgb_visual_src.image_decode_with_error_checking(None, im_proto, grayscale_im_req)
    assert im_proto.rows == 15
    assert status == image_pb2.ImageResponse.STATUS_OK
    status = rgb_visual_src.image_decode_with_error_checking(None, im_proto, rgb_im_req)
    assert im_proto.rows == 15
    assert status == image_pb2.ImageResponse.STATUS_OK


def test_convert_pixel_format_comparisons():
    im = np.zeros((3, 3, 3), np.uint8)
    for x in range(0, 2):
        for y in range(0, 2):
            for i in range(0, 2):
                im[x, y, i] = x + y + 1
    converted_im = convert_RGB_to_grayscale(im)

    cv_converted_im = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
    assert converted_im.all() == cv_converted_im.all()

    pil_im = Image.fromarray(np.uint8(im))
    pil_converted_im = pil_im.convert('L')
    pil_converted_im = np.asarray(pil_converted_im)
    assert converted_im.all() == pil_converted_im.all()
