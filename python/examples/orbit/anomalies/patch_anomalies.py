# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""An example script to edit inspection anomaly data using the Boston Dynamics Orbit API"""

import argparse
import json
import logging
import sys

from bosdyn.orbit.client import create_client
from bosdyn.orbit.utils import add_base_arguments

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
log_format = "Patch Anomalies in Orbit: %(levelname)s - %(message)s"
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter(log_format))
LOGGER.addHandler(ch)


def bulk_close_anomalies(options: argparse.Namespace) -> bool:
    """ A simple example to show how to use the Orbit client to close multiple anomalies at once

        Args:
            options(Namespace) : parsed args used for configuration options
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedClientError: indicates that the orbit client is not authenticated properly
        Returns:
            False if the request fails and True if the request completes successfully
    """
    # Create Orbit client object
    orbit_client = create_client(options)
    anomaly_element_ids = options.bulk_close_element_ids

    # Make a patch request to close the anomalies on the specified Orbit instance
    bulk_close_anomalies_response = orbit_client.patch_bulk_close_anomalies(anomaly_element_ids)

    if not bulk_close_anomalies_response.ok:
        LOGGER.error('patch_bulk_close_anomalies() failed: {}'.format(
            bulk_close_anomalies_response.text))
        return False

    LOGGER.info(bulk_close_anomalies_response.text)

    return True


def update_anomaly(options: argparse.Namespace) -> bool:
    """ A simple example to show how to use the Orbit client to edit existing anomalies to close or open them by setting the status

        Args:
            options(Namespace) : parsed args used for configuration options
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedClientError: indicates that the orbit client is not authenticated properly
        Returns:
            False if the request fails and True if the request completes successfully
    """
    # Create Orbit client object
    orbit_client = create_client(options)
    anomaly_id = options.anomaly_uuid

    # Creating dictionary to update the status field based on parsed argument 'status' set in the command line
    updated_anomaly_data = {"status": options.status}

    # Make a patch request to patch the specified status field in updated_anomaly_data
    update_anomaly_response = orbit_client.patch_anomaly_by_id(anomaly_id, updated_anomaly_data)

    if not update_anomaly_response.ok:
        LOGGER.error('bulk_close_anomalies() failed: {}'.format(update_anomaly_response.text))
        return False

    LOGGER.info("Patched Anomaly: " + str(json.dumps(update_anomaly_response.json(), indent=4)))

    return True


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    add_base_arguments(parser)

    # For bulk closing multiple anomalies
    parser.add_argument('--bulk-close-element-ids',
                        help='Element ids of the anomalies to be closed in bulk', required=False,
                        type=str, nargs="*", default=[])

    # Patching a single anomaly with new status
    parser.add_argument('--anomaly-uuid', help='uuid of the anomaly to change fields in',
                        required=False, type=str, default='')

    # For setting the status of the anomaly specified with anomaly-uuid
    parser.add_argument(
        '--status',
        help='Value to set the specified anomaly "status" field to. Either "open" or "closed"',
        required=False, type=str, default='')

    options = parser.parse_args()

    # Ensure the required fields for each request are available in the parsed arguments to run each function
    if options.bulk_close_element_ids != [] and (options.anomaly_uuid == '' and
                                                 options.status == ''):
        bulk_close_anomalies(options)
    elif options.anomaly_uuid != '' and options.status != '' and options.bulk_close_element_ids == []:
        update_anomaly(options)
    elif options.anomaly_uuid == '' and options.status != '' and options.bulk_close_element_ids == []:
        LOGGER.error(
            "Make sure to include an --anomaly-uuid argument in the terminal command for the anomaly that you would like to update."
        )
    elif options.anomaly_uuid != '' and options.status == '' and options.bulk_close_element_ids == []:
        LOGGER.error(
            "Make sure to include a --status argument of open or closed in the terminal command.")
    else:
        LOGGER.error(
            "Please only use arguments for the bulk close command or the update an individual anomaly command."
        )


if __name__ == '__main__':
    if not main():
        sys.exit(1)
