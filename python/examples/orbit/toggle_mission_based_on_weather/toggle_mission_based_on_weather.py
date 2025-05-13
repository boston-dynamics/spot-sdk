# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
An example to show how to enable or disable calendar events based on weather using Orbit web API.
"""

import argparse
import logging
import sys
import time

import pyowm

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


def toggle_mission_based_on_weather(options: argparse.Namespace) -> None:
    """A simple example to use the Orbit client to enable or disable group of missions depending on the weather forecast.
        
        Args:
            options(Namespace) : parsed args used for configuration options
    """
    # Create Orbit client object
    client = create_client(options)
    # Continuously monitor for rain condition
    while True:
        try:
            # Fetch the list of existing calendar events
            calendar_response = client.get_calendar()
            if not calendar_response.ok:
                LOGGER.error('get_calendar() failed: {}'.format(calendar_response.text))

            LOGGER.info("Current list of scheduled mission instances: {}".format(
                calendar_response.json()))

            # Fetch the weather
            open_weather_map = pyowm.OWM(options.owmapikey)
            # Search for a location by name
            location = f"{options.city}, {options.country}"  # Replace with your desired location
            # Get the current weather data
            rain_forecast = open_weather_map.weather_manager().weather_at_place(
                location).weather.rain

            if rain_forecast:
                disable_reason = "Rain"
                client.post_calendar_events_disable_all(disable_reason)
                for hr, volume in rain_forecast.items():
                    LOGGER.warning(f"At {hr}: Expected rain volume is {volume} mm")
            else:
                client.post_calendar_events_enable_all()
                LOGGER.info("Not raining! All missions enabled.")

            # Sleep for given period
            time.sleep(options.period * 60)
        except Exception:
            LOGGER.exception('An exception occurred')


def main():
    parser = argparse.ArgumentParser()
    add_base_arguments(parser)
    parser.add_argument('--owmapikey', help='API key for Open Weather Map', required=True, type=str)
    parser.add_argument('--period', required=False, default=0.1,
                        help='desired period (min) to check for the weather', type=int)
    parser.add_argument('--city', required=True, type=str)
    parser.add_argument('--country', required=True, type=str)
    options = parser.parse_args()
    toggle_mission_based_on_weather(options)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
