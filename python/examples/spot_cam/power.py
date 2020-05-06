# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os
import shutil
import tempfile

from bosdyn.client.command_line import (Command, Subcommands)

from bosdyn.client.spot_cam.power import PowerClient

from bosdyn.api.spot_cam import power_pb2

from utils import add_bool_arg

class PowerCommands(Subcommands):
    """Commands related to the Spot CAM's Power service"""

    NAME = 'power'

    def __init__(self, subparsers, command_dict):
        super(PowerCommands, self).__init__(subparsers, command_dict, [
            PowerGetPowerStatusCommand, PowerSetPowerStatusCommand
        ])

class PowerGetPowerStatusCommand(Command):
    """On/off state of specified device"""

    NAME = 'get'

    def __init__(self, subparsers, command_dict):
        super(PowerGetPowerStatusCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        ps = robot.ensure_client(PowerClient.default_service_name).get_power_status()

        return ps


class PowerSetPowerStatusCommand(Command):
    """Turns on/off the specified device"""

    NAME = 'set'

    def __init__(self, subparsers, command_dict):
        super(PowerSetPowerStatusCommand, self).__init__(subparsers, command_dict)
        add_bool_arg(self._parser, 'ptz', default=True)
        add_bool_arg(self._parser, 'aux1')
        add_bool_arg(self._parser, 'aux2')

    def _run(self, robot, options):
        ps = robot.ensure_client(PowerClient.default_service_name).set_power_status(ptz=options.ptz,
                                                                                    aux1=options.aux1,
                                                                                    aux2=options.aux2)

        return ps
