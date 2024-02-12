# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import datetime
import logging
import threading
from pathlib import Path
from time import sleep

from metric_file_group import MetricFileGroup
from uploader import Uploader

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn.client.metrics_logging import MetricsLoggingClient
from bosdyn.client.robot_id import RobotIdClient
from bosdyn.client.util import setup_logging

DIRECTORY_NAME = 'metrics-over-core'
AUTHORITY = 'metrics-over-core'
UPLOAD_URL = "https://census.bostondynamics.com/snapshot"

COREIO_DIR = "/performance_logs"

SLEEP_TIME = 1800  #Seconds passed in to method

_LOGGER = logging.getLogger('metrics_over_core_plugin')


class MetricManager:
    """ Single class to manage metric uploading and downloading
        """

    def __init__(self, robot: bosdyn.client.robot.Robot, dir_metrics: str):
        """ Initializer for the Metric Manager Class

            Args:
                robot(bosdyn.client.robot.Robot):  SDK  Robot object
                dir_metrics(str): String of the path to the metric directory
        """
        # Create the thread runner class
        self.update_thread = threading.Thread(target=self.continual_process)

        # set the metric managers robot to the one passed in
        self.robot = robot
        self.sequenceRange = []

        # Ensure we connect to the robot based on it's serial
        self.serial = self.robot.ensure_client(
            RobotIdClient.default_service_name).get_id().serial_number
        # Set our managers directory to the one passed in
        self.dir_metrics = dir_metrics

        # Create an uploader object based on the directory and robot
        self.uploader = Uploader(self.serial, dir_metrics)

    def continual_process(self):
        """ Thread runner that handles calling save and upload metrics with some dedicated sleep time after each run
        """
        while True:
            # Log the time and save our metrics to the coreio as a backup
            _LOGGER.info(f"Last metric save was: {datetime.datetime.now()}")
            self.saveMetrics()

            # Now upload them
            _LOGGER.info('Transitioning to uploading Metrics')
            if (not self.uploader.uploadMetrics(True)):
                _LOGGER.info('Unable to connect to the internet... Did not attempt upload.')

            sleep(SLEEP_TIME)

    def start(self):
        """ A helper function to start the thread
        """
        self.update_thread.start()

    def create_range(self, start: int, end: int):
        """ A helper function to create a range from starting and ending values

            Args:
                start(int): Start of the range to create
                end(int): End of the range to create
        """
        # Plus one to include latest metric
        return list(range(start, end + 1))

    def saveMetrics(self):
        """ A helper method that create a metrics client with the robot.  It then pulls the snapshots, calculates the range delta and saves new logs to the core using the Metric File Group class.
        """
        # Create different clients
        metrics_client = self.robot.ensure_client(MetricsLoggingClient.default_service_name)

        # Get the range of metrics stored on the robot
        robot_sequence_range = metrics_client.get_store_sequence_range()

        _LOGGER.info('Getting files system latest sequence:' + str(robot_sequence_range))

        # Ensure we have a working directory on the Core to save the files to its serial
        robot_dir = self.dir_metrics.joinpath(self.serial)

        #Create our class for managing a files on the core related to that serial
        metricFileGroup = MetricFileGroup(robot_dir)

        # get the range of files on the Core and their delta from what's on the robot
        sequenceRange = metricFileGroup.getSequenceRangeToDownload(robot_sequence_range)

        # Check if we are in range, update ([first, last] arrangment)
        if sequenceRange[1] - sequenceRange[0] > 0:

            _LOGGER.info("Metric range to download: {}".format(sequenceRange))

            # If not create range of files we should download
            metricSequenceToDownload = self.create_range(sequenceRange[0], sequenceRange[1])

            self.robot.logger.info('Writing range to file system')

            # Set our counter to 0
            metrics_uploaded = 0

            # Iterate through the list of metric sequences to download from the robot
            for sequenceNumber in metricSequenceToDownload:

                # Get the metric snapshot for each sequenceNumber from the robot using the metrics_client
                signedProtoList = metrics_client.get_absolute_metric_snapshot([sequenceNumber])

                # Only one should correspond
                if len(signedProtoList) > 1:
                    _LOGGER.info("ERROR: Protolist is too large.")


                # Write that that data to the core using the Metric File Group class

                metricFileGroup.write_metric_to_core(sequenceNumber, signedProtoList[0])

                # Increment our counter
                metrics_uploaded += 1

            self.robot.logger.info(str(metrics_uploaded) + ' metrics written to the Cores database')
        elif sequenceRange[1] - sequenceRange[0] == 0:
            self.robot.logger.info('No logs to download. File system is up to date.')

        elif sequenceRange[1] - sequenceRange[0] < 0:
            self.robot.logger.error('Core has a higher sequence of snapshots than the robot')
        else:
            self.robot.logger.error(
                'Error: Check connection to the robot.  Invalid value given for robot sequence range.'
            )


if __name__ == '__main__':
    # Define all arguments used by this service.
    import argparse
    parser = argparse.ArgumentParser()

    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    parser.add_argument('-d', '--dir-metrics',
                        help='The absolute path to the directory with metrics data', required=False,
                        type=Path, default=COREIO_DIR)
    options = parser.parse_args()

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.  Create an sdk object with access to the MetricsLoggingClient
    sdk = bosdyn.client.create_standard_sdk('metrics_over_core', [MetricsLoggingClient])
    robot = sdk.create_robot(options.hostname)

    #Using the credentials mounted in our DockerFile and should be passed in on start
    robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(options))

    #Establish time sync
    _LOGGER.info('Establishing time sync')
    robot.time_sync.wait_for_sync()

    # Register the MetricsLoggingClient service with the sdk
    sdk.register_service_client(MetricsLoggingClient)

    # Create our metric manager
    metricManager = MetricManager(robot, options.dir_metrics)

    _LOGGER.info('Starting Process')
    metricManager.start()
