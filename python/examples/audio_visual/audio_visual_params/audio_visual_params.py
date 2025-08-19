# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Simple example of getting and setting parameters in the AudioVisual Service."""

import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.audio_visual import AudioVisualClient


def main():
    import argparse

    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('-mb', '--max-brightness', type=float, required=False, default=None,
                        help='Maximum brightness for the LEDs.')
    parser.add_argument('-mbv', '--max-buzzer-volume', type=float, required=False, default=None,
                        help='Maximum volume for the buzzer.')
    options = parser.parse_args()

    # Audio-visual parameters
    params = {}
    if options.max_brightness is not None:
        params['max_brightness'] = options.max_brightness
    if options.max_buzzer_volume is not None:
        params['buzzer_max_volume'] = options.max_buzzer_volume

    # Create robot object with an image client
    sdk = bosdyn.client.create_standard_sdk('AudioVisualBehaviorsClient')
    sdk.register_service_client(AudioVisualClient)
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    av_client = robot.ensure_client(AudioVisualClient.default_service_name)

    if params:
        # Set system params (enabled, max brightness, max volume)
        print("Setting A/V system parameters...")
        resp = av_client.set_system_params(enabled=True, **params)
        print("Result:", resp)

    print("Getting A/V system parameters...")
    resp = av_client.get_system_params()
    print("Result:", resp)
    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
