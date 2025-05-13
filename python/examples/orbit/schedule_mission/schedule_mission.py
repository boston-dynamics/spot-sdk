# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
An example to show how to create, edit, and delete a mission calendar event using Orbit web API.
"""

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from typing import Iterable

import pytz

from bosdyn.orbit.client import create_client
from bosdyn.orbit.utils import add_base_arguments

# Set up logging
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
log_format = "%(levelname)s - %(message)s\n"
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
    try:
        selected_index = int(input("Enter the index of the nickname you want to choose: "))
    except ValueError:
        print("Invalid selection.")
        return None

    # Convert the user input to an integer
    selected_index = int(selected_index) - 1  # Adjust to 0-based index

    # Check if the entered index is within the valid range
    if 0 <= selected_index < len(nickname_list):
        selected_nickname = nickname_list[selected_index]
        print(f"You've selected the nickname: {selected_nickname}")
    else:
        print("Invalid index. Please enter a valid index.")
    return selected_nickname


def get_mission_name_from_mission_id(client: 'bosdyn.orbit.client.Client', mission_id: str) -> str:
    """ Fetches mission name from the provided mission ID.

        Args:
            client: Orbit client object.
            mission_id: unique ID for the mission.
        Returns:
            mission_name: mission name that matches the provided mission ID.
    """
    data = json.loads(client.get_site_walk_by_id(mission_id).content)
    mission_name = data.get("name", "Unknown")
    return mission_name


def select_site_walks_uuid(client: 'bosdyn.orbit.client.Client') -> str:
    """ Asks for user input to select a site walk from a numbered list

        Args:
            client: the client for Orbit web API
        Returns:
            A string corresponding to the Site Walk UUID
    """
    # Get site walks names and make the user choose
    site_walks_response = client.get_site_walks().json()

    # Extracting names from the list of dictionaries
    site_walks_names = [entry.get("name", "") for entry in site_walks_response]

    # Displaying available names to the user
    print("Available site walk names:")
    for idx, name in enumerate(site_walks_names, start=1):
        print(f"{idx}. {name}")

    # Asking the user to choose a name by input
    try:
        selected_site_walks_name_index = (
            int(input("Enter the number corresponding to the name: ")) - 1)
    except ValueError:
        print("Invalid selection.")
        return None
    # Retrieving the selected name and associated uuid
    selected_site_walks_name = site_walks_names[selected_site_walks_name_index]
    for entry in site_walks_response:
        if entry["name"] == selected_site_walks_name:
            selected_site_walks_uuid = entry["uuid"]
            break

    # Displaying the selected name and associated uuid
    print(f"Selected site walks_name: {selected_site_walks_name}")
    print(f"Associated site walks UUID: {selected_site_walks_uuid}")
    return selected_site_walks_uuid


def select_calendar_event_id(client: 'bosdyn.orbit.client.Client') -> str:
    """ Given a Client object, asks for user input to select a schedule calendar event from a numbered list.
        Additionally, provides robot name to user since the schedule names may not be unique.

        Args:
            client: the client for Orbit web API
        Returns:
            selected_event_id: a string corresponding to the calendar event ID.
                               Returns None if an invalid input is entered.
    """

    # Get calendar events and make the user choose
    calendar_response = client.get_calendar().json()

    calendar_events = []

    # Iterate through each event and extract information as needed
    for event in calendar_response["activeEvents"]:
        event_name = event["eventMetadata"]["name"]
        event_id = event["eventMetadata"]["eventId"]
        agent_nickname = event["agent"]["nickname"]
        mission_name = get_mission_name_from_mission_id(client, event["task"]["missionId"])

        calendar_events.append((event_name, event_id, agent_nickname, mission_name))

    # Displaying available names to the user
    print("Available calendar event names:")
    for idx, (name, _, nickname, mission_id) in enumerate(calendar_events, start=1):
        print(
            f"{idx}. Schedule event named {name} deploys robot {nickname} on mission {mission_id}")

    try:
        # Asking the user to choose a name by input
        selected_event_index = (int(input("Enter the number corresponding to the name: ")) - 1)

        # Validating the selected index
        if 0 <= selected_event_index < len(calendar_events):
            selected_event_name, selected_event_id, _, _ = calendar_events[selected_event_index]

            # Displaying the selected name and associated uuid
            print(f"Selected event name: {selected_event_name}")
            print(f"Associated event id: {selected_event_id}")
            return selected_event_id
        else:
            print("Invalid selection. Please enter a number within the correct range.")
    except ValueError:
        print("Invalid selection.")
        return None


def select_repeat_ms() -> int:
    """ Asks for user input to select a repeat cadence.

        Returns:
            selected_repeat_ms: selected repeat cadence in milliseconds.
    """
    # List of options
    repeat_ms_options = ["On a set interval", "Once"]

    # Displaying options to the user
    print("Choose an option:")
    for idx, option in enumerate(repeat_ms_options, start=1):
        print(f"{idx}. {option}")

    # Asking the user to choose an option by input
    try:
        chosen_option_index = (int(input("Enter the number corresponding to the option: ")) - 1)
    except ValueError:
        print("Invalid selection.")
        return None
    # Validating the chosen index
    if 0 <= chosen_option_index < len(repeat_ms_options):
        chosen_option = repeat_ms_options[chosen_option_index]

        if chosen_option == "Once":
            selected_repeat_ms = (
                0  # 0 millisecond repeat interval is interpreted as "does not repeat"
            )
        elif chosen_option == "On a set interval":
            selected_repeat_ms = 0
            while selected_repeat_ms < 59000:  #
                selected_repeat_ms = int(
                    input("Enter the number of milliseconds for the interval: "))
                if selected_repeat_ms < 59000:
                    print("Lowest recommended repeat interval is 59000 (59 seconds)")

        print(f"Chosen option: {chosen_option}")
        print(f"Repeat interval: {selected_repeat_ms} milliseconds")
    else:
        print("Invalid option index entered.")
    return selected_repeat_ms


def select_first_start_time() -> int:
    """ Asks for user input to select a first start time for the mission.

        Returns:
            time_since_epoch_ms: first start time since epoch in milliseconds.
    """
    start_time_input = input("Enter the desired start time in HH:MM format (24-hour): ")

    # Parse the input time string to a datetime object
    time_obj = datetime.strptime(start_time_input, "%H:%M")

    # Get the datetime object for today's date in local timezone
    local_timezone = pytz.timezone("US/Eastern")
    local_now = datetime.now(local_timezone)
    today_date_local = local_now.date()

    # Combine today's date with the provided time in local timezone
    combined_datetime_local = datetime.combine(today_date_local, time_obj.time())

    # Convert local time to UTC
    utc_timezone = pytz.timezone("UTC")
    combined_datetime_utc = local_timezone.localize(combined_datetime_local).astimezone(
        utc_timezone)

    # Calculate the difference between the combined UTC datetime and epoch
    time_since_epoch_ms = int(
        (combined_datetime_utc - datetime(1970, 1, 1, tzinfo=utc_timezone)).total_seconds() * 1000)

    return time_since_epoch_ms


def ask_for_blackout(selected_repeat_cycle: str) -> Iterable[dict[str:int]]:
    """ Asks if the user wants to apply the blackout time.

        Returns:
            selected_blackout_times: a specification for a time period over the course of a week when a schedule should not run
                                  specified as list of a dictionary defined as {"startMs": <int>, "endMs" : <int>}
                                  with startMs being the millisecond offset from the beginning of the week(Sunday) when this blackout period starts
                                  and endMs being the millisecond offset from beginning of the week(Sunday) when this blackout period ends
    """
    if selected_repeat_cycle == "Once":
        print("No repeat cycle - Blackout time cannot be applied")
        return None
    while True:
        answer = input("Do you want to set blackout times? (yes/no): ").lower()
        if answer == "yes":
            selected_blackout_times = select_blackout_times()
            break
        elif answer == "no":
            selected_blackout_times = None
            print("No blackout times set.")
            break
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")
    return selected_blackout_times


def select_blackout_times() -> Iterable[dict[str:int]]:
    """ Asks the user for blackout times during each day of the week.

        Returns:
            selected_blackout_times: a specification for a time period over the course of a week when a schedule should not run
                                  specified as list of a dictionary defined as {"startMs": <int>, "endMs" : <int>}
                                  with startMs being the millisecond offset from the beginning of the week(Sunday) when this blackout period starts
                                  and endMs being the millisecond offset from beginning of the week(Sunday) when this blackout period ends
    """
    # Initialize variables
    start_of_week = datetime.strptime("00:00:00", "%H:%M:%S")
    days_of_week = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]
    all_blackout_slots = []

    # Function to convert time to milliseconds since Sunday midnight
    def time_to_milliseconds(time):
        return int((time - start_of_week).total_seconds() * 1000)

    # Function to merge overlapping slots
    def merge_overlapping_slots(slots):
        if not slots:
            return []

        slots.sort(key=lambda x: x["startMs"])
        merged = [slots[0]]

        for slot in slots[1:]:
            if slot["startMs"] <= merged[-1]["endMs"]:
                merged[-1]["endMs"] = max(merged[-1]["endMs"], slot["endMs"])
            else:
                merged.append(slot)

        return merged

    # Iterate through each day of the week
    for day in days_of_week:
        while True:
            try:
                while True:
                    start_time_input = input(
                        f"Enter start time for blackout on {day} (HH:MM format - type 'f' to finish): "
                    )
                    if start_time_input.lower() == "f":
                        break

                    start_time = datetime.strptime(start_time_input, "%H:%M")

                    duration_input = input(f"Enter blackout duration for {day} (HH:MM format): ")
                    duration_time = datetime.strptime(duration_input, "%H:%M")

                    blackout_start = (start_of_week + timedelta(days=days_of_week.index(day)) +
                                      timedelta(hours=start_time.hour, minutes=start_time.minute))
                    blackout_end = blackout_start + timedelta(hours=duration_time.hour,
                                                              minutes=duration_time.minute)

                    start_time_ms = time_to_milliseconds(blackout_start)
                    end_time_ms = time_to_milliseconds(blackout_end)

                    all_blackout_slots.append({"startMs": start_time_ms, "endMs": end_time_ms})
                break
            except ValueError:
                print("Invalid input. Please enter a valid time in HH:MM format.")

    # Merge overlapping slots for the entire week
    all_blackout_slots_merged = merge_overlapping_slots(all_blackout_slots)

    # Displaying merged blackout slots
    print("\nUnified Merged Blackout Time Slots:")
    for slot in all_blackout_slots_merged:
        print(f"Start Time - {slot['startMs']} ms, End Time - {slot['endMs']} ms")
    # Merge overlapping slots for the entire week
    all_blackout_slots = merge_overlapping_slots(all_blackout_slots)

    # Displaying merged blackout slots
    print("\nUnified Merged Blackout Time Slots:")
    for slot in all_blackout_slots:
        print(f"Start Time - {slot['startMs']} ms, End Time - {slot['endMs']} ms")

    return all_blackout_slots


def delete_calendar_event(client: 'bosdyn.orbit.client.Client') -> None:
    """ Given a Client object, deletes a calendar event.

        Args:
            client: the client for Orbit web API
    """
    selected_event_id = select_calendar_event_id(client)
    if selected_event_id is None:
        return

    delete_calendar_response = client.delete_calendar_event(selected_event_id)
    # Check the delete_calendar_response
    if not delete_calendar_response.ok:
        LOGGER.error('delete_calendar_response failed: {}'.format(delete_calendar_response.text))
    else:
        LOGGER.info('Successfully deleted the calendar event!')


def edit_calendar_event(client: 'bosdyn.orbit.client.Client') -> None:
    """ Given a Client object, edits a calendar event.

        Args:
            client: the client for Orbit web API
    """
    selected_event_id = select_calendar_event_id(client)
    if selected_event_id is None:
        return

    calendar_response = client.get_calendar().json()

    selected_event = None

    for event in calendar_response["activeEvents"]:
        if selected_event_id == event["eventMetadata"]["eventId"]:
            selected_event = event

    # Displaying options to the user
    print("Choose an option:")
    edit_options = [
        "Edit robot",
        "Edit mission",
        "Edit repeat interval",
        "Edit schedule name",
        "Edit blackout times",
    ]
    for idx, option in enumerate(edit_options, start=1):
        print(f"{idx}. {option}")

    # Asking the user to choose an option by input
    try:
        chosen_option_index = (int(input("Enter the number corresponding to the option: ")) - 1)
    except ValueError:
        print("Invalid selection.")
        return
    # Check if the entered index is within the valid range
    if 0 <= chosen_option_index < len(edit_options):
        chosen_option = edit_options[chosen_option_index]
        print(f"You've chosen to -{chosen_option}-")
    else:
        print("Invalid selection")

    # User input values
    if chosen_option == "Edit robot":
        selected_nickname = select_robot_nickname(client)
    else:
        selected_nickname = selected_event["agent"]["nickname"]

    if chosen_option == "Edit mission":
        selected_site_walks_uuid = select_site_walks_uuid(client)
    else:
        selected_site_walks_uuid = selected_event["task"]["missionId"]

    if chosen_option == "Edit repeat interval":
        selected_repeat_ms = select_repeat_ms()
    else:
        selected_repeat_ms = selected_event["schedule"]["repeatMs"]

    if chosen_option == "Edit schedule name":
        selected_schedule_name = input("Enter the new schedule name: ")
    else:
        selected_schedule_name = selected_event["eventMetadata"]["name"]

    if chosen_option == "Edit blackout times":
        selected_blackout_times = select_blackout_times()
    else:
        if ("blackouts" in selected_event["schedule"]
           ):  # A calendar event may not have this key if no blackouts are defined
            selected_blackout_times = selected_event["schedule"]["blackouts"]
        else:
            selected_blackout_times = None

    # Also record any other data the calendar event may contain such as disableReason
    print(selected_event)
    if "disableReason" in selected_event["schedule"]:
        disable_reason = selected_event["schedule"]["disableReason"]
    else:
        disable_reason = None

    # Retain the old calendar event by including the eventId in the calendar request
    event_id = selected_event["eventMetadata"]["eventId"]

    # Mission starting time
    time_ms = client.get_system_time().json()["msSinceEpoch"]  # Set to "now"
    time_ms += 10000  # add a time buffer to avoid missing the first run event if there is a repeat interval
    # Post a calendar event to schedule the mission
    post_calendar_response = client.post_calendar_event(
        nickname=selected_nickname, time_ms=time_ms, repeat_ms=selected_repeat_ms,
        mission_id=selected_site_walks_uuid, force_acquire_estop=True, require_docked=True,
        schedule_name=selected_schedule_name, blackout_times=selected_blackout_times,
        disable_reason=disable_reason, event_id=event_id)
    # Check the post_calendar_response
    if not post_calendar_response.ok:
        LOGGER.error('post_calendar_event failed: {}'.format(post_calendar_response.text))
    else:
        LOGGER.info('Successfully edited the calendar event!')


def create_calendar_event(client: 'bosdyn.orbit.client.Client') -> None:
    """ Given a Client object, creates a calendar event.

        Args:
            client: the client for Orbit web API
    """
    # User input values
    selected_nickname = select_robot_nickname(client)
    selected_site_walks_uuid = select_site_walks_uuid(client)
    selected_repeat_ms = select_repeat_ms()
    selected_schedule_name = input("Enter the new schedule name: ")
    selected_blackout_times = ask_for_blackout(selected_repeat_ms)

    # Mission starting time
    time_ms = client.get_system_time().json()[
        "msSinceEpoch"]  # Set to "now" plus a short amount of time needed to finish this request
    time_ms += 10000  # add a time buffer to avoid missing the first run event if there is a repeat interval
    # Post a calendar event to schedule the mission
    post_calendar_response = client.post_calendar_event(
        nickname=selected_nickname,
        time_ms=time_ms,
        repeat_ms=selected_repeat_ms,
        mission_id=selected_site_walks_uuid,
        force_acquire_estop=True,
        require_docked=True,
        schedule_name=selected_schedule_name,
        blackout_times=selected_blackout_times,
    )
    # Check the post_calendar_response
    if not post_calendar_response.ok:
        LOGGER.error('post_calendar_event failed: {}'.format(post_calendar_response.text))
    else:
        LOGGER.info('Successfully posted the calendar event!')


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    add_base_arguments(parser)
    options = parser.parse_args()

    command_dictionary = {
        '1': create_calendar_event,
        '2': edit_calendar_event,
        '3': delete_calendar_event
    }
    while True:
        print("""
            Pick a function:
            (1): create_calendar_event
            (2): edit_calendar_event
            (3): delete_calendar_event
            """)
        try:
            req_type = input('>')
        except NameError:
            print('Invalid Input')
            pass
        # Check if req_type is in command_dictionary
        if req_type not in command_dictionary:
            print("Request not in the known command dictionary.")
            break
        try:
            selected_command = command_dictionary[req_type]
            selected_command(client=create_client(options))
        except Exception as e:
            print(e)


if __name__ == "__main__":
    if not main():
        sys.exit(1)
