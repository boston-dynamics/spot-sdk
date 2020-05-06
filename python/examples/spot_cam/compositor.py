# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os
import shutil
import tempfile

from bosdyn.client.command_line import (Command, Subcommands)

from bosdyn.client.spot_cam.compositor import CompositorClient

from bosdyn.api.spot_cam import compositor_pb2

class CompositorCommands(Subcommands):
    """Commands related to the Spot CAM's Compositor service"""

    NAME = 'compositor'

    def __init__(self, subparsers, command_dict):
        super(CompositorCommands, self).__init__(subparsers, command_dict, [
            CompositorSetScreenCommand, CompositorGetScreenCommand,
            CompositorListScreensCommand, CompositorGetVisibleCamerasCommand,
        ])


class CompositorSetScreenCommand(Command):
    """Switch camera network stream to specified view"""

    NAME = 'set'

    def __init__(self, subparsers, command_dict):
        super(CompositorSetScreenCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('name', default='digi', const='digi', nargs='?', choices=['digi', 'digi_overlay', 'digi_full', 'c0', 'c1', 'c2', 'c3', 'c4'])

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
