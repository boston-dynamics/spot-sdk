# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import os
import sys
import time

import bosdyn.client
import bosdyn.client.util
from bosdyn.choreography.client.choreography import (ChoreographyClient,
                                                     load_choreography_sequence_from_txt_file)
from bosdyn.client import ResponseError, RpcError, create_standard_sdk
from bosdyn.client.exceptions import UnauthenticatedError
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.license import LicenseClient

DEFAULT_DANCE = "default_dance.csq"


def main(argv):
    # Parse args
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('--choreography-filepath',
                        help='The filepath to load the choreographed sequence text file from.')
    parser.add_argument('--upload-only', action='store_true',
                        help='Only upload, without executing.')
    options = parser.parse_args(argv)

    # Create robot object with the ability to access the ChoreographyClient
    sdk = bosdyn.client.create_standard_sdk('UploadChoreography')
    sdk.register_service_client(ChoreographyClient)
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    license_client = robot.ensure_client(LicenseClient.default_service_name)
    if not license_client.get_feature_enabled([ChoreographyClient.license_name
                                              ])[ChoreographyClient.license_name]:
        print("This robot is not licensed for choreography.")
        sys.exit(1)

    # Check that an estop is connected with the robot so that the robot commands can be executed.
    assert not robot.is_estopped(), "Robot is estopped. Please use an external E-Stop client, " \
                                    "such as the estop SDK example, to configure E-Stop."

    # Create a lease and lease keep-alive so we can issue commands. A lease is required to execute
    # a choreographed sequence.
    lease_client = robot.ensure_client(LeaseClient.default_service_name)
    lease = lease_client.acquire()
    lk = LeaseKeepAlive(lease_client)

    # Create the client for the Choreography service.
    choreography_client = robot.ensure_client(ChoreographyClient.default_service_name)

    # Load the choreography from a text file into a local protobuf ChoreographySequence message.
    if options.choreography_filepath:
        # Use the filepath provided.
        try:
            choreography = load_choreography_sequence_from_txt_file(options.choreography_filepath)
        except Exception as execp:
            print("Failed to load choreography. Raised exception: " + str(execp))
            return True
    else:
        # Use a default dance stored in this directory.
        default_filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), DEFAULT_DANCE)
        try:
            choreography = load_choreography_sequence_from_txt_file(default_filepath)
        except Exception as execp:
            print("Failed to load choreography. Raised exception: " + str(execp))
            return True

    # Once the choreography is loaded into a protobuf message, upload the routine to the robot. We set
    # non_strict_parsing to true so that the robot will automatically correct any errors it find in the routine.
    try:
        upload_response = choreography_client.upload_choreography(choreography,
                                                                  non_strict_parsing=True)
    except UnauthenticatedError as err:
        print(
            "The robot license must contain 'choreography' permissions to upload and execute dances. "
            "Please contact Boston Dynamics Support to get the appropriate license file. ")
        return True
    except ResponseError as err:
        # Check if the ChoreographyService considers the uploaded routine as valid. If not, then the warnings must be
        # addressed before the routine can be executed on robot.
        error_msg = "Choreography sequence upload failed. The following warnings were produced: "
        for warn in err.response.warnings:
            error_msg += warn
        print(error_msg)
        return True

    sequences_on_robot = choreography_client.list_all_sequences()
    print('Sequence uploaded. All sequences on the robot:\n{}'.format('\n'.join(
        sequences_on_robot.known_sequences)))
    if options.upload_only:
        return True

    # If the routine was valid, then we can now execute the routine on robot.
    # Power on the robot. The robot can start from any position, since the Choreography Service can automatically
    # figure out and move the robot to the position necessary for the first move.
    robot.power_on()

    # First, get the name of the choreographed sequence that was uploaded to the robot to uniquely identify which
    # routine to perform.
    routine_name = choreography.name
    # Then, set a start time five seconds after the current time.
    client_start_time = time.time() + 5.0
    # Specify the starting slice of the choreography. We will set this to slice=0 so that the routine begins at
    # the very beginning.
    start_slice = 0
    # Issue the command to the robot's choreography service.
    choreography_client.execute_choreography(choreography_name=routine_name,
                                             client_start_time=client_start_time,
                                             choreography_starting_slice=start_slice)

    # Estimate how long the choreographed sequence will take, and sleep that long.
    total_choreography_slices = 0
    for move in choreography.moves:
        total_choreography_slices += move.requested_slices
    estimated_time_seconds = total_choreography_slices / choreography.slices_per_minute * 60.0
    time.sleep(estimated_time_seconds)

    # Sit the robot down and power off the robot.
    robot.power_off()
    return True


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
