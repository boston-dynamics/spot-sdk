# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os
import shutil
import tempfile

from bosdyn.api.spot_cam import health_pb2
from bosdyn.client.command_line import Command, Subcommands
from bosdyn.client.spot_cam.health import HealthClient


class HealthCommands(Subcommands):
    """Commands related to the Spot CAM's Health service"""

    NAME = 'health'

    def __init__(self, subparsers, command_dict):
        super(HealthCommands, self).__init__(subparsers, command_dict, [
            HealthClearBITEventsCommand,
            HealthGetBITStatusCommand,
            HealthGetTemperatureCommand,
            HealthGetSystemLogCommand,
        ])


class HealthClearBITEventsCommand(Command):
    """Clear out recorded BIT events"""

    NAME = 'clear'

    def __init__(self, subparsers, command_dict):
        super(HealthClearBITEventsCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        robot.ensure_client(HealthClient.default_service_name).clear_bit_events()


class HealthGetBITStatusCommand(Command):
    """List system events and degradations"""

    NAME = 'bit'

    def __init__(self, subparsers, command_dict):
        super(HealthGetBITStatusCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        events, degradations = robot.ensure_client(
            HealthClient.default_service_name).get_bit_status()

        return events, degradations


class HealthGetTemperatureCommand(Command):
    """List thermometer readings"""

    NAME = 'temperature'

    def __init__(self, subparsers, command_dict):
        super(HealthGetTemperatureCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        temp = robot.ensure_client(HealthClient.default_service_name).get_temperature()

        return temp


class HealthGetSystemLogCommand(Command):
    """Get encrypted system log"""

    NAME = 'system_log'

    def __init__(self, subparsers, command_dict):
        super(HealthGetSystemLogCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        logs = robot.ensure_client(HealthClient.default_service_name).get_system_log()

        return logs
