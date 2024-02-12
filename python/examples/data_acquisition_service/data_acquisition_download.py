# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the data acquisition client"""

import argparse
import json
import os
import sys

from google.protobuf.timestamp_pb2 import Timestamp

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import data_acquisition_pb2, data_acquisition_store_pb2
from bosdyn.client.data_acquisition_helpers import download_data_REST
from bosdyn.client.data_acquisition_store import DataAcquisitionStoreClient
from bosdyn.client.exceptions import ResponseError


def data_acquisition_download(config):
    """Download data for a specific query configuration and write it to files.

    Args:
        config: argparse arguments passed by the user.

    Returns:
        None.
    """

    bosdyn.client.util.setup_logging(config.verbose)
    sdk = bosdyn.client.create_standard_sdk('DataAcquisitionDownloadExample')
    robot = sdk.create_robot(config.hostname)
    bosdyn.client.util.authenticate(robot)

    query_params = None
    try:
        from_timestamp = Timestamp()
        from_timestamp.FromJsonString(config.query_from_timestamp)
        to_timestamp = Timestamp()
        to_timestamp.FromJsonString(config.query_to_timestamp)
        query_params = data_acquisition_store_pb2.DataQueryParams(
            time_range=data_acquisition_store_pb2.TimeRangeQuery(from_timestamp=from_timestamp,
                                                                 to_timestamp=to_timestamp))
    except ValueError as val_err:
        print(f'Value Exception:\n{val_err}')

    download_data_REST(query_params, config.hostname, robot.user_token, config.destination_folder,
                       config.additional_REST_params)


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('--destination-folder',
                        help=('The folder where the data should be downloaded to.'), required=False,
                        default='.')
    parser.add_argument(
        '--query-from-timestamp', help=('The beginning timestamp to query from in RFC 3339 date'
                                        ' string format (YYYY-MM-DDTHH:MM::SSZ).'), required=True)
    parser.add_argument(
        '--query-to-timestamp', help=('The end timestamp to query to in RFC 3339 date'
                                      ' string format (YYYY-MM-DDTHH:MM::SSZ).'), required=True)
    parser.add_argument(
        '--additional-REST-params', type=json.loads,
        help=('JSON dictionary with additional REST '
              'parameters to append to the GET request when downloading the data. Parameters with '
              'multiple values need to be set to lists in the format (param: [value1, value2])'),
        required=False)
    options = parser.parse_args()

    try:
        if not os.path.exists(options.destination_folder):
            os.mkdir(options.destination_folder)
    except IOError as err:
        print(err)

    data_acquisition_download(options)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
