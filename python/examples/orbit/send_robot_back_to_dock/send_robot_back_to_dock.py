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


def select_robot_nickname(client: 'bosdyn.orbit.client.Client') -> str:
    """ Asks for user input to select a robot from a numbered list.
        Args:
            client: Orbit client object.
        Returns:
            selected_nickname: selected robot nickname.
    """
    # Get robot name and make the user choose
    robot_response = client.get_robots().json()
    # Extract 'nickname' field from each dictionary in the list
    nickname_list = [item.get("nickname") for item in robot_response if "nickname" in item]

    # Display the available nicknames to the user
    print("Available robot nicknames:")
    for index, nickname in enumerate(nickname_list, start=1):
        print(f"{index}. {nickname}")

    # Get user input for selecting a nickname
    while True:
        user_input = input("Enter the index of the nickname: ")
        if user_input.isdigit():  # Check if input can be converted to an integer
            selected_index = int(user_input) - 1  # Adjust to 0-based index

            # Check if the entered index is within the valid range
            if 0 <= selected_index < len(nickname_list):
                selected_nickname = nickname_list[selected_index]
                print(f"You've selected the nickname: {selected_nickname}")
                break
            else:
                print("Invalid index. Please enter a valid index.")
        else:
            print("Invalid input. Please enter a valid integer.")
    return selected_nickname


def select_site_dock(client: 'bosdyn.orbit.client.Client') -> str:
    """ Asks for user input to select a robot from a numbered list.
        Args:
            client: Orbit client object.
        Returns:
            selected_uuid: selected uuid associated with site dock.
    """
    # Get site docks and make the user choose
    site_docks_response = client.get_site_docks().json()
    # Extract 'uuid' and 'dockId' field from each dictionary in the list
    uuid_list = [item.get("uuid") for item in site_docks_response if "uuid" in item]
    dockId_list = [item.get("dockId") for item in site_docks_response if "dockId" in item]

    # Display the available site docks to the user
    print("Available site docks:")
    for index, site_dock in enumerate(dockId_list, start=1):
        print(f"{index}. {site_dock}")

    # Get user input for selecting a site dock
    while True:
        user_input = input("Enter the index of the site dock: ")
        if user_input.isdigit():  # Check if input can be converted to an integer
            selected_index = int(user_input) - 1  # Adjust to 0-based index

            # Check if the entered index is within the valid range
            if 0 <= selected_index < len(uuid_list):
                selected_site_dockId = dockId_list[selected_index]
                selected_uuid = uuid_list[selected_index]
                print(
                    f"You've selected the site dock (uuid): {selected_site_dockId} ({selected_uuid})"
                )
                break
            else:
                print("Invalid index. Please enter a valid index.")
        else:
            print("Invalid input. Please enter a valid integer.")
    return selected_uuid


def send_robot_back_to_dock(options: argparse.Namespace):
    """ A simple example to use the Orbit client to send robot back to the dock during a mission.

        Args:
            options(Namespace) : parsed args used for configuration options
        Returns
            Boolean to indicate whether the function succeeded or not
    """
    # Create Orbit client object
    client = create_client(options)

    # Assign robot nickname and site dock uuid
    if options.robot_nickname:
        selected_nickname = options.robot_nickname
    else:
        selected_nickname = select_robot_nickname(client)

    if options.site_dock_uuid:
        seleted_site_dock_uuid = options.site_dock_uuid
    else:
        seleted_site_dock_uuid = select_site_dock(client)

    # First, check if the mission is running, then obtain the current driver ID
    robot_info_response = client.get_robot_info(selected_nickname)
    if robot_info_response.json()["missionRunning"]:
        current_driver_id = robot_info_response.json()["currentDriverId"]
    else:
        LOGGER.error("Robot is not running a mission!")
        return False
    # Then, generate the mission to return to the dock from current location
    mission_response = client.post_return_to_dock_mission(selected_nickname, seleted_site_dock_uuid)
    if 'error' in mission_response.json():
        LOGGER.error(
            f"Mission failed to generate with following error: {mission_response.json()['error']}")
        return False
    else:
        mission_uuid = mission_response.json()["missionUuid"]
    # Finally, dispatch the mission back to the dock
    delete_mission = True  # whether to delete the mission after playback
    force_acquire_estop = False  # whether to force acquire the E-stop from the previous client
    skip_initialization = True  # whether to skip initialization when starting the return to dock mission
    dispatch_response = client.post_dispatch_mission_to_robot(selected_nickname, current_driver_id,
                                                              mission_uuid, delete_mission,
                                                              force_acquire_estop)
    return dispatch_response.ok


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--hostname', help='IP address associated with the Orbit instance',
                        required=True, type=str)
    parser.add_argument('--robot_nickname', help="Nickname associated with the robot",
                        required=False, type=str)
    parser.add_argument('--site_dock_uuid', help="uuid associated with the dock", required=False,
                        type=str)
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
