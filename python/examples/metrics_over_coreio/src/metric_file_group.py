# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging
from pathlib import Path

_LOGGER = logging.getLogger('metrics_over_core_plugin')
from typing import List


class MetricFileGroup:
    """  Initializer for the MetricFileGroup
            
            Args:
                robot_dir(str): path to performance log files
        """

    def __init__(self, robot_dir):
        '''  Initializer for the MetricFileGroup
            
            Args:
                robot_dir(str): path to performance log files
        '''
        self.ensure_directory_exists(robot_dir)
        self.directory = robot_dir

    def ensure_directory_exists(self, directory: str):
        """  Create a direct at the file path if one does not yet exist
            
            Args:
                directory(str): path to performance log files
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            directory_path.mkdir(parents=True, exist_ok=True)
            _LOGGER.info('Directory created @: ' + str(directory))
        else:
            _LOGGER.info('Directory already exists @: ' + str(directory))

    def get_data(self, sequence_num: str) -> bytearray:
        """   A helper function to read a specific file from within this file group
            
            Args:
                sequence num(str): Sequence number of the file to read
            
            Raises:
                FileNotFoundError:If the file specified by current_dir does not exist, a FileNotFoundError will be thrown when attempting to open i
            
            Returns:
                A byte array of the file_content written when we first wrote the snapshot from the robot onto the coreio.  Saved in the file corresponding to that snapshot number.
        """

        # Set file name to current sequence_num
        file_name = str(sequence_num)

        # Create a directory based on that file name
        current_dir = Path(self.directory) / file_name

        # Read the binary data in that file
        with open(current_dir, 'rb') as file:
            file_content = file.read()

        # Check it is a real object and the right data type
        if (not isinstance(file_content, bytes)) or file_content == None:
            _LOGGER.error("File content is of bad type")
            return None

        return bytearray(file_content)

    def get_sequence_num(self, latest: bool) -> int:
        """  A helper function to get the sequence number in the file system
            
            Args:
                latest(bool): Indicator flag for whether the method should return the max or min sequence number from the range found within the file system
            
            Raises:
                FileNotFoundError: If the file specified by current_dir does not exist, a FileNotFoundError will be thrown when attempting to open i
            
            Returns:
                sequence(int): largest or smallest sequence number on the COREIO
        """
        # List all files in the directory
        files = [f.name for f in Path(self.directory).iterdir() if f.is_file()]

        # If there are no files, return None
        if not files:
            return None

        # Convert filenames to integers and get the file with the largest number
        if latest:
            return max(files, key=lambda f: int(f.split('.')[0]))
        else:
            return min(files, key=lambda f: int(f.split('.')[0]))

    def getSequenceRangeToDownload(self, sequence_range: List[int]) -> List[int]:
        """  A helper function to get the sequence range to download from the robot.  It checks for data on the core first and 
            
            Args:
                sequence_range(int[]): Sequence range of snapshots returned by the robot
            
            Returns:
                SequenceRange(int[]): An array of size two with the first value being on the latest on core/robot and the second the
                latest on robot
        """

        # Get the latest sequence number on the saved to the COREIO file system
        latestonCore = self.get_sequence_num(True)

        if latestonCore != None:
            _LOGGER.info('Core has historical data stored. Getting the latest sequence.')
            latestSequenceSaved = int(latestonCore)
        else:
            # Core does not have any data, take the start of the robot's sequence range
            latestSequenceSaved = sequence_range[0]

        # If the top end of the robot's sequence is greater than or equal to either the latest on the core or first value of on the robot
        if (sequence_range[1] >= latestSequenceSaved):

            # Set the sequence starting from my latest value to the top of the sequence
            sequenceRange = [latestSequenceSaved, sequence_range[1]]
            # sequence_range is of format first,Last
            # sequenceRange = [latest on core or earliest on the robot, latest on robot]
        else:
            _LOGGER.info('ERROR: Core says it has more recent metrics than the robot')
            #Set sequence range to the robots
            sequenceRange = sequence_range

        return sequenceRange

    def write_metric_to_core(self, sequence_num: int, signedProto):
        """ Write a metric snapshot to the core.  Creates / gets the directory bsdrf on the robot's serial and the snapshot sequence number.
            
            Args:
                sequence_num (int): Sequence number of the metric snapshot
                signedProto (bytes): Protobuff message return from the get_absolute_metric_snapshot method
            
            Raises:
                FileNotFoundError:If the file specified by current_dir does not exist, a FileNotFoundError will be thrown when attempting to open i

        """
        # Create/get folder for the robot serial
        self.ensure_directory_exists(self.directory)

        # Set file name to current sequence_num
        file_name = str(sequence_num)

        # Make a directory based on the file_name
        current_dir = self.directory.joinpath(file_name)

        _LOGGER.info("Current directory: {}".format(current_dir))

        try:
            with open(current_dir, 'wb') as f:

                # Write out only the data
                f.write(signedProto.data)
                _LOGGER.info(f'Successully wrote log {sequence_num} to file')
                f.close()
        except Exception as e:
            _LOGGER.error(f"Error writing to file for {self.serial} on {file_name}: {e}")
