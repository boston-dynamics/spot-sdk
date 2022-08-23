# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the data acquisition client"""
from __future__ import print_function

import argparse
import sys
import time

from google.protobuf.struct_pb2 import Struct

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import data_acquisition_pb2
from bosdyn.client.data_acquisition import DataAcquisitionClient
from bosdyn.client.data_acquisition_helpers import (acquire_and_process_request,
                                                    cancel_acquisition_request, download_data_REST,
                                                    issue_acquire_data_request,
                                                    make_time_query_params)
from bosdyn.client.image import build_image_request


def data_acquisition(config):
    """A simple example of using the data acquisition client to request data and check status."""

    bosdyn.client.util.setup_logging(config.verbose)
    sdk = bosdyn.client.create_standard_sdk('DataAcquisitionClientExample')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    # Create data acquisition clients
    data_acq_client = robot.ensure_client(DataAcquisitionClient.default_service_name)

    now = robot.time_sync.robot_timestamp_from_local_secs(time.time())
    group_name = "DataAcquisitionExample_{}".format(now.ToJsonString().replace(':', '-'))

    service_info = data_acq_client.get_service_info()
    print("Available capabilities are:\n" + str(service_info))

    # Get the start time so we can download all data from this example.
    start_time_secs = time.time()

    # Request 1 contains only internal metadata capture requests and an image request.
    acquisition_requests = data_acquisition_pb2.AcquisitionRequestList()
    acquisition_requests.image_captures.extend([
        data_acquisition_pb2.ImageSourceCapture(
            image_service="image", image_request=build_image_request("back_fisheye_image"))
    ])
    acquisition_requests.data_captures.extend([
        data_acquisition_pb2.DataCapture(name="robot-state"),
        data_acquisition_pb2.DataCapture(name="detailed-position-data"),
        data_acquisition_pb2.DataCapture(name="detected-objects")
    ])

    acquire_and_process_request(data_acq_client, acquisition_requests, group_name,
                                "InternalAcquisitions")

    # Request 2 contains capture requests for all the capabilities and a user-generated metadata
    # struct.
    json_struct = Struct()
    json_struct.update({"user_comment": "it is raining"})
    metadata = data_acquisition_pb2.Metadata(data=json_struct)

    acquisition_requests = data_acquisition_pb2.AcquisitionRequestList()
    acquisition_requests.image_captures.extend([
        data_acquisition_pb2.ImageSourceCapture(
            image_service="image", image_request=build_image_request("left_fisheye_image")),
        data_acquisition_pb2.ImageSourceCapture(
            image_service="image", image_request=build_image_request("right_fisheye_image"))
    ])
    acquisition_requests.data_captures.extend([
        data_acquisition_pb2.DataCapture(name="robot-state"),
        data_acquisition_pb2.DataCapture(name="detailed-position-data"),
        data_acquisition_pb2.DataCapture(name="basic-position-data"),
        data_acquisition_pb2.DataCapture(name="detected-objects"),
        data_acquisition_pb2.DataCapture(name="GPS"),
        data_acquisition_pb2.DataCapture(name="velodyne-point-cloud")
    ])

    acquire_and_process_request(data_acq_client, acquisition_requests, group_name,
                                "AllAcquisitions", metadata)

    # Request 3 contains capture requests for only one capability from main DAQ and one capability
    # from DAQ plugin.
    acquisition_requests = data_acquisition_pb2.AcquisitionRequestList()
    acquisition_requests.data_captures.extend([
        data_acquisition_pb2.DataCapture(name="robot-state"),
        data_acquisition_pb2.DataCapture(name="GPS"),
        data_acquisition_pb2.DataCapture(name="velodyne-point-cloud"),
    ])

    acquire_and_process_request(data_acq_client, acquisition_requests, group_name,
                                "PartialAcquisitions")

    # Request #4 shows how to issue and then cancel different data acquisition requests (one on-robot
    # data source and one off-robot plugin data source).
    print("\n-----------------------------------")
    acquisition_requests = data_acquisition_pb2.AcquisitionRequestList()
    acquisition_requests.data_captures.extend([
        data_acquisition_pb2.DataCapture(name="robot-state"),
        data_acquisition_pb2.DataCapture(name="slow-gps"),
    ])
    request_id, action_id = issue_acquire_data_request(data_acq_client, acquisition_requests,
                                                       group_name, "AcquisitionsToCancel")
    time.sleep(2)
    cancel_acquisition_request(data_acq_client, request_id)

    # Request 5 contains a SpotCAM capture request.
    acquisition_requests = data_acquisition_pb2.AcquisitionRequestList()
    acquisition_requests.data_captures.extend([
        data_acquisition_pb2.DataCapture(name="spot-cam-pano"),
        data_acquisition_pb2.DataCapture(name="spot-cam-ptz"),
        data_acquisition_pb2.DataCapture(name="spot-cam-ir"),
        data_acquisition_pb2.DataCapture(name="robot-state")
    ])

    acquire_and_process_request(data_acq_client, acquisition_requests, group_name,
                                "SpotCAMAcquisitions")

    # Get the end time, and download all the data from the example.
    end_time_secs = time.time()
    query_params = make_time_query_params(start_time_secs, end_time_secs, robot)
    download_data_REST(query_params, config.hostname, robot.user_token, destination_folder='.')


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args(argv)

    data_acquisition(options)


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
