# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os
import shutil
import tempfile

from utils import add_bool_arg

from bosdyn.api.spot_cam import compositor_pb2
from bosdyn.client.command_line import Command, Subcommands
from bosdyn.client.spot_cam.compositor import CompositorClient


class CompositorCommands(Subcommands):
    """Commands related to the Spot CAM's Compositor service"""

    NAME = 'compositor'

    def __init__(self, subparsers, command_dict):
        super(CompositorCommands, self).__init__(subparsers, command_dict, [
            CompositorSetScreenCommand,
            CompositorGetScreenCommand,
            CompositorListScreensCommand,
            CompositorGetVisibleCamerasCommand,
            CompositorGetIrColorMapCommand,
            CompositorSetIrColorMapCommand,
            CompositorSetIrMeterOverlayCommand,
        ])


class CompositorSetScreenCommand(Command):
    """Switch camera network stream to specified view"""

    NAME = 'set'

    def __init__(self, subparsers, command_dict):
        super(CompositorSetScreenCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument(
            'name', default='digi', const='digi', nargs='?', choices=[
                'digi', 'digi_overlay', 'digi_full', 'c0', 'c1', 'c2', 'c3', 'c4', 'mech',
                'mech_full', 'mech_overlay', 'mech_overlay_ir', 'mech_ir', 'mech_full_ir',
                'pano_full'
            ])

    def _run(self, robot, options):
        result = robot.ensure_client(CompositorClient.default_service_name).set_screen(options.name)

        return result


class CompositorGetScreenCommand(Command):
    """Get currently selected screen"""

    NAME = 'get'

    def __init__(self, subparsers, command_dict):
        super(CompositorGetScreenCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        result = robot.ensure_client(CompositorClient.default_service_name).get_screen()

        return result


class CompositorListScreensCommand(Command):
    """List available screens"""

    NAME = 'list'

    def __init__(self, subparsers, command_dict):
        super(CompositorListScreensCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        result = robot.ensure_client(CompositorClient.default_service_name).list_screens()

        return result


class CompositorGetVisibleCamerasCommand(Command):
    """List currently visible windows"""

    NAME = 'visible'

    def __init__(self, subparsers, command_dict):
        super(CompositorGetVisibleCamerasCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        result = robot.ensure_client(CompositorClient.default_service_name).get_visible_cameras()

        return result


class CompositorGetIrColorMapCommand(Command):
    """Get currently selected IR colormap on Spot CAM"""

    NAME = 'get_colormap'

    def __init__(self, subparsers, command_dict):
        super(CompositorGetIrColorMapCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        result = robot.ensure_client(CompositorClient.default_service_name).get_ir_colormap()

        return result


class CompositorSetIrColorMapCommand(Command):
    """Set IR colormap to use on Spot CAM"""

    NAME = 'set_colormap'

    def __init__(self, subparsers, command_dict):
        super(CompositorSetIrColorMapCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('color', default='inferno', const='inferno', nargs='?',
                                  choices=['jet', 'inferno', 'turbo', 'greyscale', 'grayscale'])
        self._parser.add_argument('--min-temp', default=0.0, type=float,
                                  help='minimum temperature on the temperature scale')
        self._parser.add_argument('--max-temp', default=100.0, type=float,
                                  help='maximum temperature on the temperature scale')
        add_bool_arg(self._parser, 'auto_scale', default=True)

    def _run(self, robot, options):
        string_to_colormap_enum = {
            'jet': compositor_pb2.IrColorMap.COLORMAP_JET,
            'inferno': compositor_pb2.IrColorMap.COLORMAP_INFERNO,
            'turbo': compositor_pb2.IrColorMap.COLORMAP_TURBO,
            'greyscale': compositor_pb2.IrColorMap.COLORMAP_GREYSCALE,
            'grayscale': compositor_pb2.IrColorMap.COLORMAP_GREYSCALE,
        }
        color = string_to_colormap_enum[options.color]
        result = robot.ensure_client(CompositorClient.default_service_name).set_ir_colormap(
            color, options.min_temp, options.max_temp, options.auto_scale)

        return result


class CompositorSetIrMeterOverlayCommand(Command):
    """Set IR reticle to use on Spot CAM+IR"""

    NAME = 'set_reticle'

    def __init__(self, subparsers, command_dict):
        super(CompositorSetIrMeterOverlayCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('color', default='jet', const='jet', nargs='?',
                                  choices=['jet', 'greyscale', 'grayscale'])
        self._parser.add_argument(
            '-x', type=float, default=0.5,
            help='horizontal coordinate of reticle as a ratio of the display, \
                range from 0 to 1 with 0 being the leftmost edge and 1 being the rightmost')
        self._parser.add_argument(
            '-y', type=float, default=0.5,
            help='vertical coordinate of reticle as a ratio of the display, \
                range from 0 to 1 with 0 being the top and 1 being the bottom')
        add_bool_arg(self._parser, 'enable', default=True)

    def _run(self, robot, options):
        result = robot.ensure_client(CompositorClient.default_service_name).set_ir_meter_overlay(
            options.x, options.y, options.enable)

        return result
