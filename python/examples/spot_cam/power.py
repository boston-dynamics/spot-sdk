# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os
import shutil
import tempfile

from utils import add_bool_arg

from bosdyn.api.spot_cam import power_pb2
from bosdyn.client.command_line import Command, Subcommands
from bosdyn.client.spot_cam.compositor import CompositorClient
from bosdyn.client.spot_cam.power import PowerClient


class PowerCommands(Subcommands):
    """Commands related to the Spot CAM's Power service"""

    NAME = 'power'

    def __init__(self, subparsers, command_dict):
        super(PowerCommands, self).__init__(
            subparsers, command_dict,
            [PowerGetPowerStatusCommand, PowerSetPowerStatusCommand, PowerCyclePowerCommand])


class PowerGetPowerStatusCommand(Command):
    """On/off state of specified devices"""

    NAME = 'get'

    def __init__(self, subparsers, command_dict):
        super(PowerGetPowerStatusCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        ps = robot.ensure_client(PowerClient.default_service_name).get_power_status()

        return ps


class PowerSetPowerStatusCommand(Command):
    """Turns on/off the specified devices
    
    This RPC should not be used to turn off power on non-IR PTZs as it may crash the stream
    """

    NAME = 'set'

    def __init__(self, subparsers, command_dict):
        super(PowerSetPowerStatusCommand, self).__init__(subparsers, command_dict)
        add_bool_arg(self._parser, 'ptz', default=True)
        add_bool_arg(self._parser, 'aux1')
        add_bool_arg(self._parser, 'aux2')
        add_bool_arg(self._parser, 'external_mic')

    def _run(self, robot, options):
        if not options.ptz:
            screens = robot.ensure_client(CompositorClient.default_service_name).list_screens()
            screen_names = [s.name for s in screens]
            if 'mech_ir' not in screen_names and 'mech' in screen_names:
                print(
                    'Warning: Toggling off PTZ power for a non-IR Spot CAM can cause the stream to crash'
                )
        ps = robot.ensure_client(PowerClient.default_service_name).set_power_status(
            ptz=options.ptz, aux1=options.aux1, aux2=options.aux2,
            external_mic=options.external_mic)

        return ps


class PowerCyclePowerCommand(Command):
    """Turns power off then back on for the specified devices
    
    This RPC should not be used on non-IR PTZ Spot CAMs as it may crash the stream
    """

    NAME = 'cycle'

    def __init__(self, subparsers, command_dict):
        super(PowerCyclePowerCommand, self).__init__(subparsers, command_dict)
        add_bool_arg(self._parser, 'ptz', default=True)
        add_bool_arg(self._parser, 'aux1')
        add_bool_arg(self._parser, 'aux2')
        add_bool_arg(self._parser, 'external_mic')

    def _run(self, robot, options):
        if options.ptz:
            screens = robot.ensure_client(CompositorClient.default_service_name).list_screens()
            screen_names = [s.name for s in screens]
            if 'mech_ir' not in screen_names and 'mech' in screen_names:
                print(
                    'Warning: Toggling off PTZ power for a non-IR Spot CAM can cause the stream to crash'
                )

        ps = robot.ensure_client(PowerClient.default_service_name).cycle_power(
            ptz=options.ptz, aux1=options.aux1, aux2=options.aux2,
            external_mic=options.external_mic)

        return ps
