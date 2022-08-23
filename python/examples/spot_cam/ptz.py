# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os
import shutil
import tempfile
from bisect import bisect_left

from bosdyn.api.spot_cam import ptz_pb2
from bosdyn.client.command_line import Command, Subcommands
from bosdyn.client.spot_cam.ptz import PtzClient


class PtzCommands(Subcommands):
    """Commands related to the Spot CAM's Ptz service"""

    NAME = 'ptz'

    def __init__(self, subparsers, command_dict):
        super(PtzCommands, self).__init__(
            subparsers,
            command_dict,
            [
                PtzListPtzCommand,
                PtzGetPtzPositionCommand,
                PtzGetPtzVelocityCommand,
                PtzSetPtzPositionCommand,
                PtzSetPtzVelocityCommand,
                PtzInitializeLensCommand,
            ])


class PtzListPtzCommand(Command):
    """Info about each ptz"""

    NAME = 'list'

    def __init__(self, subparsers, command_dict):
        super(PtzListPtzCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        ptzs = robot.ensure_client(PtzClient.default_service_name).list_ptz()

        return ptzs


class PtzGetPtzPositionCommand(Command):
    """Position of the specified ptz"""

    NAME = 'get_position'

    def __init__(self, subparsers, command_dict):
        super(PtzGetPtzPositionCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument(
            'ptz_name', default='digi', const='digi', nargs='?',
            choices=['digi', 'full_digi', 'mech', 'overlay_digi', 'full_pano', 'overlay_pano'])

    def _run(self, robot, options):
        ptz_desc = ptz_pb2.PtzDescription(name=options.ptz_name)
        position = robot.ensure_client(PtzClient.default_service_name).get_ptz_position(ptz_desc)

        return position


class PtzGetPtzVelocityCommand(Command):
    """Velocity of the specified ptz"""

    NAME = 'get_velocity'

    def __init__(self, subparsers, command_dict):
        super(PtzGetPtzVelocityCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument(
            'ptz_name', default='digi', const='digi', nargs='?',
            choices=['digi', 'full_digi', 'mech', 'overlay_digi', 'full_pano', 'overlay_pano'])

    def _run(self, robot, options):
        ptz_desc = ptz_pb2.PtzDescription(name=options.ptz_name)
        velocity = robot.ensure_client(PtzClient.default_service_name).get_ptz_velocity(ptz_desc)

        return velocity


class PtzSetPtzPositionCommand(Command):
    """Set position of the specified ptz"""

    NAME = 'set_position'

    def __init__(self, subparsers, command_dict):
        super(PtzSetPtzPositionCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument(
            'ptz_name', default='digi', const='digi', nargs='?',
            choices=['digi', 'full_digi', 'mech', 'overlay_digi', 'full_pano', 'overlay_pano'])
        self._parser.add_argument('pan', help='[0, 360] Degrees', default=0.0, type=float)
        self._parser.add_argument('tilt', help='[-30, 100] Degrees', default=0.0, type=float)
        self._parser.add_argument('zoom', help='[1, 30]', default=1.0, type=float)

    def _run(self, robot, options):
        ptz_desc = ptz_pb2.PtzDescription(name=options.ptz_name)
        ptz_position = robot.ensure_client(PtzClient.default_service_name).set_ptz_position(
            ptz_desc, options.pan, options.tilt, options.zoom)

        return ptz_position


class PtzSetPtzVelocityCommand(Command):
    """Set velocity of the specified ptz"""

    NAME = 'set_velocity'

    def __init__(self, subparsers, command_dict):
        super(PtzSetPtzVelocityCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument(
            'ptz_name', default='digi', const='digi', nargs='?',
            choices=['digi', 'full_digi', 'mech', 'overlay_digi', 'full_pano', 'overlay_pano'])
        self._parser.add_argument('pan', help='[0, 360] Degrees', default=0.0, type=float)
        self._parser.add_argument('tilt', help='[-90, 90] Degrees', default=0.0, type=float)
        self._parser.add_argument('zoom', help='[0, 0x4000]', default=0.0, type=float)

    def _run(self, robot, options):
        ptz_desc = ptz_pb2.PtzDescription(name=options.ptz_name)
        ptz_velocity = robot.ensure_client(PtzClient.default_service_name).set_ptz_velocity(
            ptz_desc, options.pan, options.tilt, options.zoom)

        return ptz_velocity


class PtzInitializeLensCommand(Command):
    """Initializes the PTZ autofocus or resets it if already initialized"""

    NAME = 'initialize_lens'

    def __init__(self, subparsers, command_dict):
        super(PtzInitializeLensCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument(
            'ptz_name', default='digi', const='digi', nargs='?',
            choices=['digi', 'full_digi', 'mech', 'overlay_digi', 'full_pano', 'overlay_pano'])

    def _run(self, robot, options):
        resp = robot.ensure_client(PtzClient.default_service_name).initialize_lens()

        return resp


