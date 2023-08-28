# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

'''
An example to show how to export run archives(mission data) from Scout to the current directory in /temp.
'''

import argparse
import logging
import os
import sys

from bosdyn.scout.client import ScoutClient

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
log_format = "Export Run archives: %(levelname)s - %(message)s"
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter(log_format))
LOGGER.addHandler(ch)


def export_run_archives(options):
    ''' A simple example to show how to use the Scout client to export run archives(mission data) from Scout.
        - Args:
            - options(Namespace) : parsed args used for configuration options
        - Raises:
            - RequestExceptions: exceptions thrown by the Requests library 
            - UnauthenticatedScoutClientError: indicates that the scout client is not authenticated properly
        - Returns 
            - Boolean to indicate whether the function succeeded or not
    '''
    # Determine the value for the argument "verify"
    if options.verify in ["True", "False"]:
        verify = (options.verify == "True")
    else:
        LOGGER.info(
            "The provided value for the argument verify [{}] is not either 'True' or 'False'. Assuming verify is set to 'path/to/CA bundle'"
            .format(options.verify))
        verify = options.verify
    # A Scout client object represents a single Scout instance.
    scout_client = ScoutClient(hostname=options.hostname, verify=verify, cert=options.cert)
    # The Scout client needs to be authenticated before using its functions
    scout_client.authenticate_with_password()
    # Query the latest runs(missions)
    # Note that there are a lot of arguments available here we might want to use eg limit, start date etc.
    # Importantly without a 'limit' argument we only get the most recent 20 runs
    get_runs_response = scout_client.get_runs(params={"limit": options.num_of_runs})
    # Check the get_runs_response is valid
    if not get_runs_response.ok:
        LOGGER.error(
            "Access error to runs endpoint. Please make sure you are using an admin account! " +
            get_runs_response.reason)
        return False
    # Obtain the json form of the response
    runs_json = get_runs_response.json()
    # Create a temp directory
    if not (os.path.exists('temp')):
        os.makedirs('temp')
    # Iterate through all the runs resources and retrieve zip files
    LOGGER.info("Going through {} runs to grab zip files for each run!".format(
        len(runs_json['resources'])))
    for run_resource in runs_json['resources']:
        # Save the following fields
        run_uuid = run_resource['uuid']
        mission_name = run_resource['missionName']
        start_time = run_resource['startTime']
        action_count = run_resource['actionCount']
        mission_status = run_resource['missionStatus']
        # Ensure that the action count is non-zero before attempting to get a run archives
        if (action_count == 0):
            LOGGER.warning(
                "Note that " + mission_name +
                " contains 0 completed actions! We are going to skip exporting the zip file for this mission."
            )
            continue
        # Check that the run has reached a terminal state before attempting to get a run archives
        if mission_status not in ["SUCCESS", "FAILURE", "ERROR", "STOPPED", "NONE", "UNKNOWN"]:
            LOGGER.warning(
                "Note that {} has not reached a terminal state. Mission status is {} We are going to skip exporting the zip file for this mission to avoid getting a partial zip!"
                .format(mission_name, mission_status))
            continue
        # Get the run archives using the run_uuid
        get_run_archives_by_id_response = scout_client.get_run_archives_by_id(run_uuid)
        # Check that the get_run_archives_by_id_response is valid
        if not get_run_archives_by_id_response.ok:
            LOGGER.error("Get run archives response error " + get_runs_response.reason)
            return False
        # Obtain the content field containing the zip file
        run_archives_zip_file = get_run_archives_by_id_response.content
        # Set the file name schema
        file_name = f'temp/{mission_name}_{start_time}_{run_uuid}.zip'
        # Write the run_archives_zip_file to file_name
        file = open(file_name, "wb")
        file.write(run_archives_zip_file)
        file.close()
        LOGGER.info("Downloaded: " + file_name)


def main(argv):
    '''Command line interface.'''
    parser = argparse.ArgumentParser()
    parser.add_argument('-hostname', help='IP address associated with the Scout instance',
                        required=True, type=str)
    parser.add_argument('-num_of_runs',
                        help='The number of latest runs to export archives data for.',
                        required=False, type=int, default=10)
    parser.add_argument(
        '-verify',
        help=
        'verify(path to a CA bundle or Boolean): controls whether we verify the server’s TLS certificate',
        default=True,
    )
    parser.add_argument(
        '-cert', help=
        "(a .pem file or a tuple with ('cert', 'key') pair): a local cert to use as client side certificate ",
        nargs='+', default=None)
    options = parser.parse_args(argv)
    try:
        return export_run_archives(options)
    except Exception as exc:
        LOGGER.error('Export Run archives threw an exception: %r', exc)
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
