# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the Orbit client to interact with Orbit through the Boston Dynamics Orbit API."""

import argparse
import logging
import sys

from bosdyn.orbit.client import create_client
from bosdyn.orbit.utils import add_base_arguments

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
log_format = "Hello, Orbit!: %(levelname)s - %(message)s"
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter(log_format))
LOGGER.addHandler(ch)


def hello_orbit(options: argparse.Namespace) -> bool:
    """ A simple example to show how to use the Orbit client to get information on the connected robots.

        Args:
            options(Namespace) : parsed args used for configuration options
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedClientError: indicates that the orbit client is not authenticated properly
        Returns:
            Boolean to indicate whether the function succeeded or not
    """
    # Create Orbit client object
    orbit_client = create_client(options)
    # Get all the robots currently configured on the specified Orbit instance
    get_robots_response = orbit_client.get_robots()
    if not get_robots_response.ok:
        LOGGER.error('get_robots() failed: {}'.format(get_robots_response.text))
        return False
    # Get the json form of the get_robots_response
    all_robots_on_orbit = get_robots_response.json()
    # Query for the nicknames of the robots on Orbit
    robot_nicknames = []
    for robot in all_robots_on_orbit:
        robot_nickname = robot.get('nickname')
        if robot_nickname is not None:
            robot_nicknames.append(robot_nickname)
    LOGGER.info("Here are the robots connected to the Orbit instance {}: {}".format(
        options.hostname, robot_nicknames))
    return True


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    add_base_arguments(parser)
    options = parser.parse_args()
    hello_orbit(options)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
