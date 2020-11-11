# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the data acquisition client"""
from __future__ import print_function
import argparse
import os
import shutil
import sys
import time
from datetime import datetime

import bosdyn.client
import bosdyn.client.util

from bosdyn.api import estop_pb2
from bosdyn.api import data_acquisition_pb2
from bosdyn.api import data_acquisition_store_pb2
from bosdyn.api import image_pb2
from bosdyn.client.data_acquisition import (DataAcquisitionClient, RequestIdDoesNotExistError)
from bosdyn.client.data_acquisition_store import DataAcquisitionStoreClient
from bosdyn.client.exceptions import ResponseError
from data_acquisition_helpers import download_data_REST

from google.protobuf.struct_pb2 import Struct
from google.protobuf import json_format


def issue_acquire_data_request(data_acq_client, acquisition_requests, group_name,
	                           action_name, metadata=None):
    """Sends the data acquisition request.

    Args:
        data_acq_client: DataAcquisition client for send the acquisition requests.
        acquisition_requests: Acquisition requests to include in request message.
        group_name: Group name for the acquitions.
        action_name: Action name for the acquitions.
        metadata: Metadata to include in the request message.

    Returns:
        The request id (int) and the action id (CaptureActionId). A request id set as None
        indicates the AcquireData rpc failed.
    """
    # Create action id for the query for this request.
    action_id = data_acquisition_pb2.CaptureActionId(action_name=action_name,
                                                     group_name=group_name)

    # Send an AquireData request
    request_id = None
    try:
        request_id = data_acq_client.acquire_data(acquisition_requests=acquisition_requests,
            action_name=action_name, group_name=action_id.group_name, metadata=metadata)
    except ResponseError as err:
        print("Exception raised by issue_acquire_data_request: " + str(err))

    return request_id, action_id

def process_request(data_acq_client, hostname, robot, acquisition_requests, group_name,
                    action_name, metadata=None):
    """Send acquisition request, retrieve the acquired data and write it to files.

    Args:
        data_acq_client: DataAcquisition client for send the acquisition requests.
        hostname(string): Hostname of the robot.
        robot(bosdyn.client.robot): Robot instance.
        acquisition_requests: Acquisition requests to include in request message.
        group_name: Group name for the acquitions.
        action_name: Action name for the acquitions.
        metadata: Metadata to include in the request message.

    Returns:
        None.
    """
    print("\n-----------------------------------")
    from_timestamp = robot.time_sync.robot_timestamp_from_local_secs(time.time() - 300)

    # Make the acquire data request. This will return our current request id.
    request_id, action_id = issue_acquire_data_request(data_acq_client, acquisition_requests,
        group_name, action_name, metadata)

    if not request_id:
        # The AcquireData request failed for some reason. No need to attempt to
        # monitor the status.
        return

    # Monitor the status of the data acquisition
    while True:
        get_status_response = None
        try:
            get_status_response = data_acq_client.get_status(request_id)
        except ResponseError as err:
            print("Exception: " + str(err))
            break
        print("Request " + str(request_id) + " status: " +
            data_acquisition_pb2.GetStatusResponse.Status.Name(get_status_response.status))
        if get_status_response.status == data_acquisition_pb2.GetStatusResponse.STATUS_COMPLETE:
            to_timestamp = robot.time_sync.robot_timestamp_from_local_secs(time.time() + 300)
            print(from_timestamp.ToJsonString(), to_timestamp.ToJsonString())
            query_params = data_acquisition_store_pb2.DataQueryParams(
                time_range=data_acquisition_store_pb2.TimeRangeQuery(from_timestamp=from_timestamp,
                    to_timestamp=to_timestamp))
            download_data_REST(query_params, hostname, robot.user_token)
            break
        if get_status_response.status == data_acquisition_pb2.GetStatusResponse.STATUS_TIMEDOUT:
            print("Unrecoverable request timeout: {}".format(get_status_response))
            exit(1)
        time.sleep(0.2)


def cancel_acquisition_request(data_acq_client, request_id):
    """Cancels an acquisition request based on the request id

    Args:
        data_acq_client: DataAcquisition client for send the acquisition requests.
        request_id: The id number for the AcquireData request to cancel.

    Returns:
        None.
    """
    if not request_id:
        # The incoming request id is invalid. No need to attempt to cancel the request or
        # monitor the status.
        return

    try:
        is_cancelled_response = data_acq_client.cancel_acquisition(request_id)
        print("Status of the request to cancel the data-acquisition in progress: " +
            data_acquisition_pb2.CancelAcquisitionResponse.Status.Name(is_cancelled_response.status))
    except ResponseError as err:
        print("ResponseError raised when cancelling: "+str(err))
        # Don't attempt to wait for the cancellation success status.
        return

    # Monitor the status of the cancellation to confirm it was successfully cancelled.
    while True:
        get_status_response = None
        try:
            get_status_response = data_acq_client.get_status(request_id)
        except ResponseError as err:
            print("Exception: " + str(err))
            break

        print("Request " + str(request_id) + " status: " +
            data_acquisition_pb2.GetStatusResponse.Status.Name(get_status_response.status))
        if get_status_response.status == data_acquisition_pb2.GetStatusResponse.STATUS_ACQUISITION_CANCELLED:
            print("The request is fully cancelled.")
            break

def data_acquisition(config):
    """A simple example of using the data acquisition client to request data and check status."""

    bosdyn.client.util.setup_logging(config.verbose)
    sdk = bosdyn.client.create_standard_sdk('DataAcquisitionClientExample')
    robot = sdk.create_robot(config.hostname)
    robot.authenticate(config.username, config.password)
    robot.time_sync.wait_for_sync()

    # Create data acquisition clients
    data_acq_client = robot.ensure_client(DataAcquisitionClient.default_service_name)

    now = robot.time_sync.robot_timestamp_from_local_secs(time.time())
    capture_name = "DataAcquisitionExample_{}".format(now.ToJsonString().replace(':', '-'))

    service_info = data_acq_client.get_service_info()
    print("Available capabilities are:\n" + str(service_info))

    # Request 1 contains only internal metadata capture requests and an image request.
    acquisition_requests = data_acquisition_pb2.AcquisitionRequestList()
    acquisition_requests.image_captures.extend([
        data_acquisition_pb2.ImageSourceCapture(image_service="image",
                                                image_source="back_fisheye_image")])
    acquisition_requests.data_captures.extend([
        data_acquisition_pb2.DataCapture(name="robot-state"),
        data_acquisition_pb2.DataCapture(name="detailed-position-data"),
        data_acquisition_pb2.DataCapture(name="detected-objects")])

    process_request(data_acq_client, config.hostname, robot, acquisition_requests, capture_name,
        "InternalAcquisitions")

    # Request 2 contains capture requests for all the capabilities and a user-generated metadata
    # struct.
    json_struct = Struct()
    json_struct.update({
        "user_comment" : "it is raining"
    })
    metadata=data_acquisition_pb2.Metadata(data=json_struct)

    acquisition_requests = data_acquisition_pb2.AcquisitionRequestList()
    acquisition_requests.image_captures.extend(
        [data_acquisition_pb2.ImageSourceCapture(image_service="image",
            image_source="left_fisheye_image"),
        data_acquisition_pb2.ImageSourceCapture(image_service="image",
            image_source="right_fisheye_image")])
    acquisition_requests.data_captures.extend([
        data_acquisition_pb2.DataCapture(name="robot-state"),
        data_acquisition_pb2.DataCapture(name="detailed-position-data"),
        data_acquisition_pb2.DataCapture(name="basic-position-data"),
        data_acquisition_pb2.DataCapture(name="detected-objects"),
        data_acquisition_pb2.DataCapture(name="GPS"),
        data_acquisition_pb2.DataCapture(name="velodyne-point-cloud")
        ])

    process_request(data_acq_client, config.hostname, robot, acquisition_requests, capture_name,
        "AllAcquisitions", metadata)


    # Request 3 contains capture requests for only one capability from main DAQ and one capability
    # from DAQ plugin.
    acquisition_requests = data_acquisition_pb2.AcquisitionRequestList()
    acquisition_requests.data_captures.extend([
        data_acquisition_pb2.DataCapture(name="robot-state"),
        data_acquisition_pb2.DataCapture(name="GPS"),
        data_acquisition_pb2.DataCapture(name="velodyne-point-cloud"),
        ])

    process_request(data_acq_client, config.hostname, robot, acquisition_requests, capture_name,
        "PartialAcquisitions")


    # Request #4 shows how to issue and then cancel different data acquistion requests (one on-robot
    # data source and one off-robot plugin data source).
    print("\n-----------------------------------")
    acquisition_requests = data_acquisition_pb2.AcquisitionRequestList()
    acquisition_requests.data_captures.extend([
        data_acquisition_pb2.DataCapture(name="robot-state"),
        data_acquisition_pb2.DataCapture(name="slow-gps"),
    ])
    request_id, action_id = issue_acquire_data_request(
        data_acq_client, acquisition_requests, capture_name, "AcquisitionsToCancel")
    time.sleep(2)
    cancel_acquisition_request(data_acq_client, request_id)


    # Request 5 contains a SpotCAM capture request.
    acquisition_requests = data_acquisition_pb2.AcquisitionRequestList()
    acquisition_requests.data_captures.extend([
        data_acquisition_pb2.DataCapture(name="spot-cam-pano"),
        data_acquisition_pb2.DataCapture(name="spot-cam-ptz"),
        data_acquisition_pb2.DataCapture(name="spot-cam-ir"),
        data_acquisition_pb2.DataCapture(name="robot-state")])

    process_request(data_acq_client, config.hostname, robot, acquisition_requests, capture_name,
        "SpotCAMAcquisitions")


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    options = parser.parse_args(argv)

    data_acquisition(options)


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
