# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""An example script to retrieve inspection anomaly data using the Boston Dynamics Orbit API."""

import argparse
import json
import logging
import sys

from bosdyn.orbit.client import create_client
from bosdyn.orbit.utils import add_base_arguments

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
log_format = "Get Anomalies in Orbit: %(levelname)s - %(message)s"
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter(log_format))
LOGGER.addHandler(ch)


def get_anomalies(options: argparse.Namespace) -> bool:
    """ A simple example to show how to use the Orbit client to get existing anomaly data

        Args:
            options(Namespace) : parsed args used for configuration options
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedClientError: indicates that the orbit client is not authenticated properly
        Returns:
            List of dictionaries representing anomalies stored in the Orbit instance based on the request parameters
    """

    # Create Orbit client object
    orbit_client = create_client(options)

    # Get the anomalies stored in the specified Orbit instance with the maximum number of returned anomalies set by the limit parameter
    get_anomalies_response = orbit_client.get_anomalies(params={"limit": options.limit})

    if not get_anomalies_response.ok:
        LOGGER.error('get_anomalies() failed: {}'.format(get_anomalies_response.text))
        return False

    # Get the json form of the get_anomalies_response
    anomalies_in_orbit = get_anomalies_response.json().get("resources")

    # Log the anomalies in the terminal
    LOGGER.info("Here are the existing anomalies stored on the Orbit instance:")

    for anomaly in anomalies_in_orbit:
        LOGGER.info('\tAnomaly title: ' + str(anomaly.get('title')))
        LOGGER.info('\t\tactionName: ' + anomaly.get('actionName'))
        LOGGER.info('\t\tstatus: ' + anomaly.get('status'))
        if anomaly.get('elementId') != None:
            LOGGER.info('\t\telementId: ' + anomaly.get('elementId'))
        LOGGER.info('\t\tuuid: ' + anomaly.get('uuid') + '\n')

    return anomalies_in_orbit


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    add_base_arguments(parser)

    # Field to limit the number of anomalies returned in the response
    parser.add_argument(
        '--limit',
        help='Maximum number of anomalies to report in the response to the get anomalies request.',
        required=False, type=str, default=20)

    options = parser.parse_args()

    get_anomalies(options)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
