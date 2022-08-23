# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from bosdyn.client.command_line import Command, Subcommands
from bosdyn.client.spot_cam.version import VersionClient


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
        response = robot.ensure_client(
            VersionClient.default_service_name).get_software_version_full()
        version = response.version
        return 'Version {}.{}.{}\n{}'.format(version.major_version, version.minor_version,
                                             version.patch_level, response.detail)
