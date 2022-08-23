# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from __future__ import print_function

import itertools
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from unittest import mock

import pytest

from bosdyn.api import data_acquisition_pb2, data_acquisition_store_pb2, image_pb2
from bosdyn.client.common import FutureWrapper
#from .util import make_async
from bosdyn.client.data_acquisition_plugin_service import (Capability, DataAcquisitionPluginService,
                                                           DataAcquisitionStoreHelper,
                                                           RequestCancelledError, RequestManager,
                                                           RequestState, make_error)
from bosdyn.client.data_acquisition_store import DataAcquisitionStoreClient

from .helpers import make_async


@pytest.fixture
def daq_store_client():
    client = mock.Mock()
    response = data_acquisition_store_pb2.StoreImageResponse()
    client.store_image.return_value = response
    client.store_image_async.side_effect = make_async(client.store_image)
    response = data_acquisition_store_pb2.StoreMetadataResponse()
    client.store_metadata.return_value = response
    #client.store_metadata_async.side_effect = make_async(client.store_metadata)
    return client


@pytest.fixture
def daq_store_failure_client():
    client = mock.Mock()
    future = Future()
    future.set_exception(Exception("Test"))
    client.store_image_async.return_value = future
    return client


@pytest.fixture
def daq_robot(daq_store_client):
    robot = mock.Mock()
    robot.sync_with_directory.return_value = {}
    robot.ensure_client = lambda name: {
        DataAcquisitionStoreClient.default_service_name: daq_store_client,
    }.get(name, mock.Mock())
    return robot


def success_plugin_impl(request, store_helper: DataAcquisitionStoreHelper):
    store_helper.wait_for_stores_complete()


single_capability = [Capability(name='test', channel_name='test_channel')]


def make_single_request(action_name):
    request = data_acquisition_pb2.AcquirePluginDataRequest()
    request.action_id.group_name = 'test_group'
    request.action_id.action_name = action_name
    request.acquisition_requests.data_captures.add().name = 'test'
    return request


def test_wait_for_stores_complete_success(daq_store_client):
    """Make sure the wait_for_stores_complete function can succeed correctly"""
    state = RequestState()
    store_helper = DataAcquisitionStoreHelper(daq_store_client, state)
    assert state._status_proto.status != state._status_proto.STATUS_COMPLETE
    store_helper.wait_for_stores_complete()
    store_helper.state.set_complete_if_no_error()
    assert state._status_proto.status == state._status_proto.STATUS_COMPLETE

    state = RequestState()
    store_helper = DataAcquisitionStoreHelper(daq_store_client, state)
    pool = ThreadPoolExecutor(max_workers=1)

    data_id = data_acquisition_pb2.DataIdentifier()
    data_id.action_id.group_name = 'A'
    data_id.action_id.action_name = 'B'
    data_id.channel = 'test_channel'
    image_capture = image_pb2.ImageCapture()
    store_helper.store_image(image_capture, data_id)

    assert state._status_proto.status != state._status_proto.STATUS_COMPLETE
    store_helper.wait_for_stores_complete()
    store_helper.state.set_complete_if_no_error()
    assert state._status_proto.status == state._status_proto.STATUS_COMPLETE


def test_wait_for_stores_complete_failure(daq_store_failure_client):
    """Make sure the wait_for_stores_complete function can fail correctly"""
    state = RequestState()
    store_helper = DataAcquisitionStoreHelper(daq_store_failure_client, state)

    data_id = data_acquisition_pb2.DataIdentifier()
    data_id.action_id.group_name = 'A'
    data_id.action_id.action_name = 'B'
    data_id.channel = 'test_channel'
    image_capture = image_pb2.ImageCapture()
    store_helper.store_image(image_capture, data_id)

    store_helper.wait_for_stores_complete()
    assert state._status_proto.status == state._status_proto.STATUS_DATA_ERROR
    assert state._status_proto.data_errors[0].data_id == data_id


def test_wait_for_stores_complete_cancel(daq_store_client):
    """Make sure the wait_for_stores_complete function can cancel correctly"""
    state = RequestState()
    store_helper = DataAcquisitionStoreHelper(daq_store_client, state)

    data_id = data_acquisition_pb2.DataIdentifier()
    data_id.action_id.group_name = 'A'
    data_id.action_id.action_name = 'B'
    data_id.channel = 'test_channel'
    image_capture = image_pb2.ImageCapture()
    store_helper.store_image(image_capture, data_id)

    with state._lock:
        state._cancelled = True
    with pytest.raises(RequestCancelledError):
        store_helper.wait_for_stores_complete()


def test_simple_plugin(daq_robot):
    """Test that a basic plugin that completes right away works."""
    service = DataAcquisitionPluginService(daq_robot, single_capability, success_plugin_impl)
    context = None
    response = service.AcquirePluginData(make_single_request('action 1'), context)
    assert response.request_id > 0
    # Wait until the thread has run to completion
    service.executor.shutdown()
    feedback = service.GetStatus(
        data_acquisition_pb2.GetStatusRequest(request_id=response.request_id), context)
    assert feedback.status == feedback.STATUS_COMPLETE


def test_data_error(daq_robot):
    """Test that a data collection can report a data error."""

    def error_impl(request, store_helper: DataAcquisitionStoreHelper):
        data_id = data_acquisition_pb2.DataIdentifier(action_id=request.action_id,
                                                      channel=single_capability[0].channel_name)
        store_helper.state.add_errors([make_error(data_id, 'Failed to acquire data.')])
        store_helper.wait_for_stores_complete()

    service = DataAcquisitionPluginService(daq_robot, single_capability, error_impl)
    context = None
    request = make_single_request('action 1')
    response = service.AcquirePluginData(request, context)
    assert response.request_id > 0
    # Wait until the thread has run to completion
    service.executor.shutdown()
    feedback = service.GetStatus(
        data_acquisition_pb2.GetStatusRequest(request_id=response.request_id), context)
    print(feedback)
    assert feedback.status == feedback.STATUS_DATA_ERROR
    assert feedback.data_errors[0].data_id.action_id == request.action_id
    assert feedback.data_errors[0].data_id.channel == single_capability[0].channel_name


def test_buggy_plugin(daq_robot):
    """Test that a data collection function that throws an exception returns a DATA_ERROR"""

    def buggy(*args):
        raise Exception("I'm broken, yo.")

    service = DataAcquisitionPluginService(daq_robot, single_capability, buggy)
    context = None
    response = service.AcquirePluginData(make_single_request('action 1'), context)
    assert response.request_id > 0
    # Wait until the thread has run to completion
    service.executor.shutdown()
    feedback = service.GetStatus(
        data_acquisition_pb2.GetStatusRequest(request_id=response.request_id), context)
    print(feedback)
    assert feedback.status == feedback.STATUS_INTERNAL_ERROR


def test_cancel_plugin(daq_robot):
    """Test that cancelling a request actually stops it."""

    def run_forever(request, store_helper: DataAcquisitionStoreHelper):
        while True:
            store_helper.cancel_check()
            time.sleep(0.01)

    service = DataAcquisitionPluginService(daq_robot, single_capability, run_forever)
    context = None
    response = service.AcquirePluginData(make_single_request('action 1'), context)
    assert response.request_id > 0
    feedback_request = data_acquisition_pb2.GetStatusRequest(request_id=response.request_id)
    feedback = service.GetStatus(feedback_request, context)
    assert feedback.status == feedback.STATUS_ACQUIRING

    cancel_response = service.CancelAcquisition(
        data_acquisition_pb2.CancelAcquisitionRequest(request_id=response.request_id), context)
    assert cancel_response.status == cancel_response.STATUS_OK
    feedback = service.GetStatus(feedback_request, context)
    assert feedback.status in (feedback.STATUS_CANCEL_IN_PROGRESS,
                               feedback.STATUS_ACQUISITION_CANCELLED)
    service.executor.shutdown()
    feedback = service.GetStatus(feedback_request, context)
    assert feedback.status == feedback.STATUS_ACQUISITION_CANCELLED


def test_plugin_stages(daq_robot):
    """Test that we can transition through the stages acquiring->saving->complete"""

    # Used to coordinate between the service and client rather than relying on sleeps.
    go = threading.Event()
    done = threading.Event()

    def collect_data(request, store_helper: DataAcquisitionStoreHelper):
        while not go.wait(timeout=1):
            print('Waiting on go 1')
            store_helper.cancel_check()
        print('Go 1 Finished.')
        go.clear()
        store_helper.state.set_status(data_acquisition_pb2.GetStatusResponse.STATUS_SAVING)
        done.set()
        while not go.wait(timeout=1):
            print('Waiting on go 2')
            store_helper.cancel_check()
        print('Go 2 Finished.')
        store_helper.wait_for_stores_complete()

    service = DataAcquisitionPluginService(daq_robot, single_capability, collect_data)
    context = None
    response = service.AcquirePluginData(make_single_request('action 1'), context)
    assert response.request_id > 0
    try:
        feedback_request = data_acquisition_pb2.GetStatusRequest(request_id=response.request_id)
        feedback = service.GetStatus(feedback_request, context)
        assert feedback.status == feedback.STATUS_ACQUIRING
        go.set()
        assert done.wait(timeout=1)
        done.clear()
        feedback = service.GetStatus(feedback_request, context)
        assert feedback.status == feedback.STATUS_SAVING
        go.set()
        service.executor.shutdown(wait=True)
        feedback = service.GetStatus(feedback_request, context)
        assert feedback.status == feedback.STATUS_COMPLETE
    finally:
        # If anything fails, make sure that we kill the background thread.
        service.CancelAcquisition(
            data_acquisition_pb2.CancelAcquisitionRequest(request_id=response.request_id), context)
        service.executor.shutdown(wait=False)


def test_removal():
    """Make sure that old requests get removed correctly from the request manager"""

    m = RequestManager()
    requests = [m.add_request() for i in range(10)]
    request_ids = {request_id for request_id, state in requests}
    assert len(request_ids) == 10  # Verify that all requests are unique

    for request_id, state in requests[0:5]:
        m.mark_request_finished(request_id)

    # Cleanup the finished requests
    m.cleanup_requests(time.time() + 1e-6)

    # Make sure the old requests are in fact removed
    for request_id, state in requests[0:5]:
        with pytest.raises(KeyError):
            m.get_request_state(request_id)

    # Make sure the newer requests are still around
    for request_id, state in requests[5:]:
        assert state is m.get_request_state(request_id)


def test_request_removal(daq_robot):
    """Make some requests, and then verify that old ones get removed."""
    context = None
    with mock.patch('time.time') as mock_time:
        service = DataAcquisitionPluginService(daq_robot, single_capability, success_plugin_impl)
        mock_time.return_value = 0
        response1 = service.AcquirePluginData(make_single_request('action 1'), context)
        assert response1.request_id > 0

        while True:
            feedback_response = service.GetStatus(
                data_acquisition_pb2.GetStatusRequest(request_id=response1.request_id), context)
            if feedback_response.status == feedback_response.STATUS_COMPLETE:
                break
        mock_time.return_value = 100

        # The current cleanup triggering happens when a request arrives.
        response2 = service.AcquirePluginData(make_single_request('action 1'), context)
        assert response2.request_id != response1.request_id

        feedback_response = service.GetStatus(
            data_acquisition_pb2.GetStatusRequest(request_id=response1.request_id), context)
        print(feedback_response)
        assert feedback_response.status == feedback_response.STATUS_REQUEST_ID_DOES_NOT_EXIST
