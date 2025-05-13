# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the Orbit client to get runs response and process data through the Boston Dynamics Orbit API."""

import argparse
import logging
import sys

from bosdyn.orbit.client import create_client
from bosdyn.orbit.utils import add_base_arguments

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
log_format = "Output: %(levelname)s - %(message)s\n"
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter(log_format))
LOGGER.addHandler(ch)


def get_runs_response(options: argparse.Namespace) -> bool:
    """ A simple example to show how to use the Orbit client to get runs response and process data.

        Args:
            options(Namespace) : parsed args used for configuration options
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedClientError: indicates that the orbit client is not authenticated properly
        Returns
            Boolean to indicate whether the function succeeded or not
    """
    # Create Orbit client object
    orbit_client = create_client(options)
    # From the runs response, obtain the list of the mission names and the status counts.
    runs_response = orbit_client.get_runs()
    if not runs_response.ok:
        LOGGER.error('get_runs() failed: {}'.format(runs_response.text))
        return False

    runs = runs_response.json()
    mission_names = []
    # Mission status indicates the final state of the mission recognized by Orbit
    mission_status = {
        "SUCCESS": 0,
        "FAILURE": 0,
        "ERROR": 0,
        "STOPPED": 0,
        "UNKNOWN": 0,
        "RUNNING": 0,
        "PAUSED": 0,
        "NONE": 0
    }

    for session in runs['resources']:
        if session['missionName'] not in mission_names:
            mission_names.append(session['missionName'])
            mission_status[session["missionStatus"]] += 1

    LOGGER.info(
        "Here are the missions played during the latest 20 runs on the Orbit instance {}: {}".
        format(options.hostname, mission_names))

    LOGGER.info(
        "Here are the counts for each mission status played during the latest 20 runs on the Orbit instance {}: {}"
        .format(options.hostname, mission_status))

    return True


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    add_base_arguments(parser)
    options = parser.parse_args()
    get_runs_response(options)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
