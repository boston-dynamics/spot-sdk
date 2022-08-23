# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging
import threading

import bosdyn.client
from bosdyn.client.spot_cam.lighting import LightingClient

_LOGGER = logging.getLogger(__name__)


class LightsHelper:
    """Context manager that flashes Spot CAM LEDs for the duration of the context.

    Use as follows:

    .. code-block:: python

        with LightsHelper(robot, frequency, brightness):
            # Lights will flash here
        # Lights will stop flashing here.

    Args:
        robot: Robot object for creating clients
        frequency: Desired frequency for a complete flash cycle in Hz.
        brightness: Desired LED brightness [0, 1]
    """

    def __init__(self, robot, frequency, brightness, logger=None):
        self.logger = logger
        self.freq = frequency
        self.brightness = brightness
        self.lighting_client = robot.ensure_client(LightingClient.default_service_name)
        self.thread_lights = None
        self.stop_event = threading.Event()

    def __enter__(self):
        self.thread_lights = threading.Thread(
            target=set_lights_with_freq_and_brightness, args=(
                self.stop_event,
                self.lighting_client,
                self.freq,
                self.brightness,
            ))
        self.thread_lights.start()

    def __exit__(self, exc_type, exc_value, tb):
        self.stop_event.set()
        self.thread_lights.join()


def set_lights_with_freq_and_brightness(stop_event, lighting_client, frequency, brightness):
    """Given the threading event, lighting client, desired light frequency and brightness,
    this helper will blink the Spot CAM lights until threading event is set to stop. This
    function must be used within a thread to prevent it from running forever.

    Args:
        stop_event (threading.Event()): Threading event used for stopping and returning.
        lighting_client (LightingClient): Lighting client from bosdyn.client
        frequency (float): Desired frequency (Hz) for flashing the Spot CAM lights
        brightness (float): Desired brightness [0, 1] for the Spot CAM lights
    """
    while not stop_event.is_set():
        try:
            _set_lights_to_blink(stop_event, lighting_client, frequency, brightness)
        except bosdyn.client.TimedOutError:
            _LOGGER.error('Timed out trying to set lights. Retrying.')
        except bosdyn.client.Error:
            _LOGGER.exception('Failed to set lights. Retrying.')
            stop_event.wait(1)  # Wait up to 1 second so as to not hammer the service.


def _set_lights_brightness(lighting_client, brightness, timeout=1):
    """Helper to set LED brightnesses using default RPC settings"""
    lighting_client.set_led_brightness(brightness, timeout=timeout)


def _set_lights_on(stop_event, lighting_client, duration=1, brightness=0.5):
    # Set minimum and maximum boundaries for brightness
    if brightness < 0.1:
        brightness = 0.1
    elif brightness > 1.0:
        brightness = 1.0
    # Turn spotCAM lights on
    if duration == 0:  # leave the lights on if duration is set to 0
        setting = [brightness] * 4
        _set_lights_brightness(lighting_client, setting)
    else:
        setting = [brightness] * 4
        _set_lights_brightness(lighting_client, setting)
        stop_event.wait(duration)
        _set_lights_off(lighting_client)


def _set_lights_off(lighting_client):
    setting = [0] * 4
    _set_lights_brightness(lighting_client, setting)


def _set_lights_to_blink(stop_event, lighting_client, freq=1, brightness=0.5):
    period = 1 / freq
    _set_lights_on(stop_event, lighting_client, period / 2, brightness)
    _set_lights_off(lighting_client)
    stop_event.wait(period / 2)
