# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import json
import logging
import math
import os
from typing import List

import requests
from metric_file_group import MetricFileGroup
from requests import Response

_LOGGER = logging.getLogger('metrics_over_core_plugin')

UPLOAD_URL = "https://census.bostondynamics.com/snapshot"


class Uploader:

    def __init__(self, serial: int, data_path: str):
        """  Initializer for the Uploader class.  This method assigns two variables, serial and data_path, for later use by other methods
            
            Args:
                serial(int): Robot serial for identification and defining the data path later
                data_path(str): Path to where the data is stored on your computer or the CoreI/O
        """
        # Serial number of the robot for the metrics being pulled
        self.serialNumber = serial

        # Path to where the data is stored on the COREIO
        self.data_path = data_path

    def test_connection(self):
        """
        Check if the internet is reachable by pinging bostondynamics.com
        """
        try:
            response = requests.get("https://bostondynamics.com/", timeout=25)
            return True
        except requests.ConnectionError:
            return False

    def uploadMetrics(self, core_flag: bool):
        """  Upload metrics to the bosdyn servers.  Creates a path to the folder where logs are stored then creates a Metric File Group based on that path to interact with it. The snapshot ranges are then grabbed from the local folder and the latest sent to Bosdyn servers.  Based on the response, snapshots from the robot are uploaded.
            
            Args:
                core_flag(bool):  Expect a boolean value for the core_flag indicating the files should be read from the typical core file path or one on the desktop
        """

        # Check we have a passed in data path
        if (self.data_path == None):
            _LOGGER.info('Data path not correctly passed in')
            return False

        # If our boolean core_flag boolean value is true, retrieve that file from the OS with the assumed file path structure
        if (core_flag):
            robot_dir = os.path.join(self.data_path, str(self.serialNumber))
        else:
            # Otherwise just use the pathed in data path
            robot_dir = self.data_path

        # Create a metricFileGroup manager for managing grabbing the files from the passed in directory
        metricFileGroup = MetricFileGroup(robot_dir)
        _LOGGER.info(f'Robot dir: {robot_dir}')

        # Primarily for logging purposes, check if we can connect to the internet
        if (self.test_connection()):
            _LOGGER.info('Can successfully connect to the internet ')
        else:
            _LOGGER.info('CANNOT successfully connect to the internet ')
            return False

        # Get the oldest day / sequence number using our metric file manager.
        latestSeq = metricFileGroup.get_sequence_num(True)

        # Also get the most current sequence number / day.  This is toggled in the method based on the passed in boolean valye
        oldestSeq = metricFileGroup.get_sequence_num(False)

        # Get the data of the latest sequence number
        latestSequenceData = metricFileGroup.get_data(latestSeq)

        _LOGGER.info(f'Robot dir: {robot_dir}')

        # Upload  a snapshot of the data to the BostonDynamics servers

        response = self.uploadSnapshotFromData(latestSequenceData)

        # Check the response status code
        if response.status_code == 200 or response.status_code == 201:
            _LOGGER.info('Successfully uploaded first reponse')
        else:
            _LOGGER.info('Did not successfuly download the first reponse')
            return False

        # If we did not exit above, we had a successful response

        # Get the response data
        data = response.json()

        # Get the returned missing ranges from the Bosdyn servers
        ranges = data["hints"]["ranges"]

        # Retrieve the sequence set to upload to the servers based on what we have and what they are missing
        sequenceSetToUpload = self.get_numbers_within_ranges(ranges, latestSeq, oldestSeq)

        if (len(sequenceSetToUpload) > 0):
            _LOGGER.info('Server is behind core. Uploading snapshots for: ' +
                         str(sequenceSetToUpload))
        else:
            _LOGGER.info("Server was up to date.")

        # Create an upload counter
        total_uploaded = 0

        for cur_seq in sequenceSetToUpload:

            # Get the data of the next sequence in my sequenceSetToUpload from wherever I stored it
            sequenceData = metricFileGroup.get_data(cur_seq)

            # Send and recieve a response from the Bosdyn servers
            response = self.uploadSnapshotFromData(sequenceData)

            # If we had a successful response, we successfully uploaded those metrics
            if response.status_code == 200 or response.status_code == 201:
                total_uploaded = total_uploaded + 1
            else:
                _LOGGER.info('Did not successfully upload record')

        _LOGGER.info('Successfully uploaded: ' + str(total_uploaded))

    def uploadSnapshotFromData(self, data) -> Response:
        """  Upload a single snapshot to the bosdyn servers.
            
            Args:
                data(bytes):  expects a binary data file of snapshot data
            
            Raises:
                RequestionException: There was an ambiguous exception that occurred while handling your request.
        """

        # Try and catch a blocking send with all of that data
        try:

            # Form our URL and request
            headers = {'Content-Type': 'application/octet-stream'}
            response = requests.put(UPLOAD_URL, data=data, headers=headers)

            # If the HTTP response status code is 200 (OK), then the URL is reachable

            if response.status_code == 200:
                return response
            if response.status_code == 201:
                return response
            else:
                raise requests.RequestException
        except requests.RequestException as e:
            _LOGGER.info(e)
            return response

    def get_numbers_within_ranges(self, ranges, end_val: int, start_val: int) -> List[int]:
        """  Get the snapshot numbers that are in the ranges returned by the server and also within the range of data that we have in our local file system.
            
            Args:
                ranges(): snapshot ranges missing from bosdyn servers returned from our initial request
                end_val(int):  Most recent value on our local file system
                start_val(int):  Oldest snapshot valye on our local file system
        """

        toUpload = []
        for range_step in ranges:

            # Get this steps stop and start
            range_start = range_step.get("start")
            range_end = range_step.get("end")

            if range_start == None:
                range_start = -math.inf
            if range_end == None:
                range_end = math.inf

            # Next farthest start is the largest between the range start and the start of the range of our local file system
            adjStart = max(float(start_val), range_start)

            # Next closest end is the smallest between the range end and the end of our local file system
            adjEnd = min(float(end_val), range_end)

            # Check our bounds make sense
            if adjStart <= adjEnd:
                #add one to be inclusive of the ending val
                for i in range(adjStart, adjEnd + 1):
                    toUpload.append(i)

        return toUpload
