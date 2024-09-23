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
from pathlib import Path

from google.protobuf.timestamp_pb2 import Timestamp

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import data_acquisition_store_pb2, image_pb2
from bosdyn.client.data_acquisition_helpers import clean_filename, download_data_REST
from bosdyn.client.data_acquisition_store import DataAcquisitionStoreClient


def data_acquisition_download(robot, destination_folder, query_from_timestamp, query_to_timestamp,
                              additional_REST_params=None):
    """Download data for a specific query configuration and write it to files.

    Args:
        config: argparse arguments passed by the user.

    Returns:
        None.
    """
    query_params = None
    try:
        # Create query parmas
        from_timestamp = Timestamp()
        from_timestamp.FromJsonString(query_from_timestamp)
        to_timestamp = Timestamp()
        to_timestamp.FromJsonString(query_to_timestamp)
        query_params = data_acquisition_store_pb2.DataQueryParams(
            time_range=data_acquisition_store_pb2.TimeRangeQuery(from_timestamp=from_timestamp,
                                                                 to_timestamp=to_timestamp))
    except ValueError as val_err:
        print(f'Value Exception:\n{val_err}')

    download_data_REST(query_params, robot.address, robot.user_token, destination_folder,
                       additional_REST_params)


def query_stored_captures_download(robot, destination_folder, query_from_timestamp,
                                   query_to_timestamp):

    # Create query params
    from_timestamp = Timestamp()
    from_timestamp.FromJsonString(query_from_timestamp)
    to_timestamp = Timestamp()
    to_timestamp.FromJsonString(query_to_timestamp)

    daq_store_client: DataAcquisitionStoreClient = robot.ensure_client(
        DataAcquisitionStoreClient.default_service_name)
    time_range_query_parameters = data_acquisition_store_pb2.TimeRangeQuery(
        from_timestamp=from_timestamp, to_timestamp=to_timestamp)

    absolute_path = Path(destination_folder).absolute()
    folder = Path(absolute_path.parent, clean_filename(absolute_path.name), 'DATA')
    folder.mkdir(parents=True, exist_ok=True)

    # Variables used for querying the correct captures.
    from_id = None
    current_id = None

    # Variables for validating a retrieved capture.
    current_complete = False
    filename = None
    while True:
        # To gather all captures within the time range, query_stored_captures must be called until there are no more captures returned while increasing `captures_from_id` in QueryParameters to exclude already downloaded captures.
        # Query for images, data, and large_data. Large data will be retrieved in parts so we must make as many calls as it takes to download the entire data capture.
        response = daq_store_client.query_stored_captures(
            query=data_acquisition_store_pb2.QueryParameters(
                time_range=time_range_query_parameters, include_images=True, include_data=True,
                include_large=True, captures_from_id=from_id))
        if len(response.results) <= 0:
            # No more captures to process
            print('Completed all downloads.')
            break

        for result in response.results:

            # Default capture details
            raw_data = b''
            offset = 0
            total_size = 0
            file_extension = '.bin'

            # We will check to see which type of data capture we have
            result_type = result.WhichOneof("result")
            if result_type == "image":
                raw_data = result.image.image.data
                # Raw data should complete data for images
                total_size = len(raw_data)
                if result.image.image.format == image_pb2.Image.FORMAT_JPEG:
                    file_extension = '.jpg'
                else:
                    file_extension = '.raw'
            elif result_type == "data":
                raw_data = result.data.data
                # Raw data should contain complete data
                total_size = len(raw_data)
                if len(result.data.file_extension) > 0:
                    file_extension = result.data.file_extension
            elif result_type == "large_data":
                raw_data = result.large_data.chunk.data
                # For large data the offset can be used to make sure we are writing the correct part in the correct order
                offset = result.large_data.offset
                # Raw data likely does not contain complete data here so we will use the total_size field from the data chunk
                total_size = result.large_data.chunk.total_size
                if len(result.large_data.file_extension) > 0:
                    file_extension = result.large_data.file_extension

            if current_id != result.data_id.id:
                # We have a new capture so check whether the capture is complete or not
                if current_id is not None and current_complete == False:
                    # This will likely happen when large_data offset become out of sync, additional error handling can be added here to prevent skipping but for this example we will ignore this
                    print('Error: Capture data incomplete and we have moved to the next capture.')

                # We have a new capture so create a new file
                current_complete = False
                current_id = result.data_id.id
                mission_name = result.data_id.action_id.group_name
                mission_folder = Path(folder.absolute(), clean_filename(mission_name))
                mission_folder.mkdir(parents=True, exist_ok=True)
                filename = Path(
                    mission_folder,
                    clean_filename(
                        f'{result.data_id.action_id.action_name}_{result.data_id.channel}{result.data_id.data_name if len(result.data_id.data_name) > 0 else ""}{file_extension}'
                    ))
                if filename is not None and filename.exists():
                    os.remove(filename)
                print(
                    f'Found capture {current_id} with length of {total_size} bytes, saving to {mission_name}/{filename}.'
                )

            if filename is not None and filename.exists():
                filesize = os.stat(filename).st_size
                if offset != filesize:
                    print(
                        f'Offset on large data does not align with expected: offset = {offset}, while expected = {filesize}. Trying again...'
                    )
                    continue

            if len(raw_data) > 0:
                # Write data to the current file, we use 'ab' here since we may have a large_data file that requires appending, this should not affect other capture types.
                # Since we remove this file if exists above we assume here that this file is in the correct state.
                with open(filename, "ab") as file:
                    size_written = file.write(raw_data)
                    if size_written != len(raw_data):
                        print(f'Failed to write correct amount of bytes for file `{filename}`')
                        continue
                    print(f'Wrote {size_written} to file: {filename}')

            # Check that the file written is the correct size
            if os.stat(filename).st_size == total_size:
                # We have a complete file
                print(f'File complete {filename}.')
                from_id = current_id + 1
                current_complete = True


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser(description='Download data from DAQ')
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

    subparsers = parser.add_subparsers(dest='command')
    parser_zip = subparsers.add_parser('rest')
    parser_zip.add_argument(
        '--additional-REST-params', type=json.loads,
        help=('JSON dictionary with additional REST '
              'parameters to append to the GET request when downloading the data. Parameters with '
              'multiple values need to be set to lists in the format (param: [value1, value2])'),
        required=False)

    parser_zip = subparsers.add_parser(
        'grpc', help='Query data directly, currently supports raw data downloads.')

    options = parser.parse_args()

    bosdyn.client.util.setup_logging(options.verbose)
    sdk = bosdyn.client.create_standard_sdk('DataAcquisitionDownloadExample')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    try:
        if not os.path.exists(options.destination_folder):
            os.mkdir(options.destination_folder)
    except IOError as err:
        print(err)

    if options.command == 'rest':
        data_acquisition_download(robot, options.destination_folder, options.query_from_timestamp,
                                  options.query_to_timestamp, options.additional_REST_params)
    elif options.command == 'grpc':
        query_stored_captures_download(
            robot,
            options.destination_folder,
            options.query_from_timestamp,
            options.query_to_timestamp,
        )


if __name__ == '__main__':
    if not main():
        sys.exit(1)
