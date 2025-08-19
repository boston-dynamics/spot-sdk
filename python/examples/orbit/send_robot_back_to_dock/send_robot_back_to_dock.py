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
from datetime import datetime as now

from bosdyn.orbit.client import create_client
from bosdyn.orbit.utils import add_base_arguments

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


def send_robot_back_to_dock(options: argparse.Namespace) -> bool:
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
        selected_site_dock_uuid = options.site_dock_uuid
    else:
        selected_site_dock_uuid = select_site_dock(client)

    # First, check if the mission is running, then obtain the current driver ID
    robot_info_response = client.get_robot_info(selected_nickname)
    if robot_info_response.json()["missionRunning"]:
        current_driver_id = robot_info_response.json()["currentDriverId"]
    else:
        LOGGER.error("Robot is not running a mission!")
        return False
    # Generate a walk to the dock
    send_robot_response = client.post_return_to_dock_mission(selected_nickname,
                                                             selected_site_dock_uuid)
    resp_json = send_robot_response.json()
    if 'error' in resp_json:
        LOGGER.error(f"Failed to generate walk: {resp_json['error']}")
        return False
    if 'walk' not in resp_json:
        LOGGER.error("No walk returned in response.")
        return False
    walk = resp_json['walk']

    # Dispatch the walk to the robot
    dispatch_response = client.post_dispatch_mission_to_robot(robot_nickname=selected_nickname,
                                                              walk=walk,
                                                              driver_id=current_driver_id)
    # Retry dispatch if it fails
    try_count = 1
    while dispatch_response.ok is False and try_count < options.retries:
        try_count += 1
        LOGGER.warning(f"Dispatch failed, retrying {try_count}/{options.retries}...")
        dispatch_response = client.post_dispatch_mission_to_robot(robot_nickname=selected_nickname,
                                                                  walk=walk,
                                                                  driver_id=current_driver_id)
    if not dispatch_response.ok:
        LOGGER.error(f"Failed to dispatch walk: {dispatch_response.text}")
        return False

    LOGGER.info("Successfully dispatched walk to robot.")
    return True


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    add_base_arguments(parser)
    parser.add_argument('--robot_nickname', help="Nickname associated with the robot",
                        required=False, type=str)
    parser.add_argument('--site_dock_uuid', help="uuid associated with the dock", required=False,
                        type=str)
    parser.add_argument('--retries', help="Number of retries for dispatching the walk",
                        required=False, type=int, default=3)
    options = parser.parse_args()
    send_robot_back_to_dock(options)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
