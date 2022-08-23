# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import json
import os
import shutil
import tempfile

from utils import int2ip

from bosdyn.api.spot_cam import network_pb2
from bosdyn.client.command_line import Command, Subcommands
from bosdyn.client.spot_cam.network import NetworkClient


class NetworkCommands(Subcommands):
    """Commands related to the Spot CAM's Network service"""

    NAME = 'network'

    def __init__(self, subparsers, command_dict):
        super(NetworkCommands, self).__init__(
            subparsers,
            command_dict,
            [
                NetworkGetICEConfigurationCommand,
                NetworkSetICEConfigurationCommand,
            ])




class NetworkGetICEConfigurationCommand(Command):
    """Current ICE settings"""

    NAME = 'ice_settings'

    def __init__(self, subparsers, command_dict):
        super(NetworkGetICEConfigurationCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        ic = robot.ensure_client(NetworkClient.default_service_name).get_ice_configuration()

        return ic




class NetworkSetICEConfigurationCommand(Command):
    """Set ICE settings"""

    NAME = 'set_ice'

    def __init__(self, subparsers, command_dict):
        super(NetworkSetICEConfigurationCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('ice_file', metavar='ice.json', type=argparse.FileType('r'),
                                  help='IceServer(s) in JSON format')

    def _run(self, robot, options):
        with options.ice_file as handler:
            json_ice_servers = json.load(handler)

        ice_servers = []
        for ice in json_ice_servers:
            ice_servers.append(
                network_pb2.ICEServer(type=ice['type'], address=ice['address'], port=ice['port']))

        robot.ensure_client(NetworkClient.default_service_name).set_ice_configuration(ice_servers)


