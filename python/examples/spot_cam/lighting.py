# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os
import shutil
import tempfile

from bosdyn.api.spot_cam import LED_pb2
from bosdyn.client.command_line import Command, Subcommands
from bosdyn.client.spot_cam.lighting import LightingClient


class LightingCommands(Subcommands):
    """Commands related to the Spot CAM's Lighting service"""

    NAME = 'lighting'

    def __init__(self, subparsers, command_dict):
        super(LightingCommands,
              self).__init__(subparsers, command_dict,
                             [LightingGetLEDBrightnessCommand, LightingSetLEDBrightnessCommand])


class LightingGetLEDBrightnessCommand(Command):
    """Brightness levels of each LED"""

    NAME = 'get'

    def __init__(self, subparsers, command_dict):
        super(LightingGetLEDBrightnessCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        brightnesses = robot.ensure_client(LightingClient.default_service_name).get_led_brightness()

        return brightnesses


class LightingSetLEDBrightnessCommand(Command):
    """Sets the brightness levels of each LED at indices [0, 4)"""

    NAME = 'set'

    def __init__(self, subparsers, command_dict):
        super(LightingSetLEDBrightnessCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('brightnesses', nargs='+', help='brightness of each LED')

    def _run(self, robot, options):
        robot.ensure_client(LightingClient.default_service_name).set_led_brightness(
            float(i) for i in options.brightnesses)
