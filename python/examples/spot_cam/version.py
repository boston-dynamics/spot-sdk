# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os
import shutil
import tempfile

from bosdyn.client.command_line import (Command, Subcommands)

from bosdyn.client.spot_cam.version import VersionClient

from bosdyn.api.spot_cam import version_pb2


class VersionCommands(Subcommands):
    """Commands related to the Spot CAM's Version service"""

    NAME = 'version'

    def __init__(self, subparsers, command_dict):
        super(VersionCommands, self).__init__(subparsers, command_dict,
                                              [VersionGetSoftwareVersionCommand])


class VersionGetSoftwareVersionCommand(Command):
    """Spot CAM's software version"""

    NAME = 'software'

    def __init__(self, subparsers, command_dict):
        super(VersionGetSoftwareVersionCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        version = robot.ensure_client(VersionClient.default_service_name).get_software_version()

        return version
