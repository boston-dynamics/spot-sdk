# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
An example to show how to send robot back to the dock using Orbit web API.
"""

import argparse
import logging
import sys

from bosdyn.orbit.client import create_client

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
log_format = "%(levelname)s - %(message)s"
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter(log_format))
LOGGER.addHandler(ch)


def send_robot_back_to_dock(options: argparse.Namespace):
    """ A simple example to use the Orbit client to send robot back to the dock during a mission.

        Args:
            options(Namespace) : parsed args used for configuration options
        Returns
            Boolean to indicate whether the function succeeded or not
    """
    # Create Orbit client object
    client = create_client(options)
    # Fetch the robot nickname and dock uuid from input arguments
    robot_nickname = options.robot_nickname
    site_dock_uuid = options.site_dock_uuid
    # First, check if the mission is running, then obtain the current driver ID
    robot_info_response = client.get_robot_info(robot_nickname)
    if robot_info_response.json()["missionRunning"]:
        current_driver_id = robot_info_response.json()["currentDriverId"]
    else:
        LOGGER.error("Robot is not running a mission!")
        return False
    # Then, generate the mission to return to the dock from current location
    mission_response = client.post_return_to_dock_mission(robot_nickname, site_dock_uuid)
    if 'error' in mission_response.json():
        LOGGER.error(
            f"Mission failed to generate with following error: {mission_response.json()['error']}")
        return False
    else:
        mission_uuid = mission_response.json()["missionUuid"]
    # Finally, dispatch the mission back to the dock
    delete_mission = True  # whether to delete the mission after playback
    force_acquire_estop = False  # whether to force acquire the E-stop from the previous client
    dispatch_response = client.post_dispatch_mission_to_robot(robot_nickname, current_driver_id,
                                                              mission_uuid, delete_mission,
                                                              force_acquire_estop)
    return dispatch_response.ok


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', help='IP address associated with the Orbit instance',
                        required=True, type=str)
    parser.add_argument('--robot_nickname', required=True, type=str)
    parser.add_argument('--site_dock_uuid', required=True, type=str)
    parser.add_argument(
        '--verify',
        help=
        'verify(path to a CA bundle or Boolean): controls whether we verify the server’s TLS certificate',
        default=True,
    )
    parser.add_argument(
        '--cert', help=
        "(a .pem file or a tuple with ('cert', 'key') pair): a local cert to use as client side certificate ",
        nargs='+', default=None)
    options = parser.parse_args()
    send_robot_back_to_dock(options)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
