# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import socket
import struct

from bosdyn.api.spot_cam import camera_pb2, logging_pb2
from bosdyn.client.command_line import Command, Subcommands
from bosdyn.client.math_helpers import Quat
from bosdyn.client.spot_cam.media_log import MediaLogClient


def add_bool_arg(parser, name, default=False, prefix=('disable', 'enable')):
    feature_parser = parser.add_mutually_exclusive_group(required=False)
    stripped_name = name.replace('-', '_')
    feature_parser.add_argument('--{}-{}'.format(prefix[1], name), dest=stripped_name,
                                action='store_true')
    feature_parser.add_argument('--{}-{}'.format(prefix[0], name), dest=stripped_name,
                                action='store_false')
    feature_parser.set_defaults(**{stripped_name: default})


def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]


def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))


class UtilityCommands(Subcommands):
    """Utility commands related to Spot CAM's services"""

    NAME = 'utils'

    def __init__(self, subparsers, command_dict):
        super(UtilityCommands, self).__init__(subparsers, command_dict, [
            UtilitySaveCalibrationCommand,
        ])


class UtilitySaveCalibrationCommand(Command):
    """Get calibration data from file or robot"""

    NAME = 'save_calibration'

    def __init__(self, subparsers, command_dict):
        super(UtilitySaveCalibrationCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('calibration_file', help='Filename to save result to')

    def _run(self, robot, options):
        cameras = robot.ensure_client(MediaLogClient.default_service_name).list_cameras()
        cameras = [c for c in cameras if not (c.name == 'pano' or c.name == 'ptz')]

        # Format is dictated by Spot CAM
        with open(options.calibration_file, 'w') as out_file:
            for ring_index in range(5):
                out_file.write('cam{}\n'.format(ring_index))
                camera = cameras[ring_index]

                out_file.write('fx= {:.8f}\n'.format(camera.pinhole.focal_length.x))
                out_file.write('fy= {:.8f}\n'.format(camera.pinhole.focal_length.y))
                out_file.write('cx= {:.8f}\n'.format(camera.pinhole.center_point.x))
                out_file.write('cy= {:.8f}\n'.format(camera.pinhole.center_point.y))
                out_file.write('k1= {:.8f}\n'.format(camera.pinhole.k1))
                out_file.write('k2= {:.8f}\n'.format(camera.pinhole.k2))
                out_file.write('k3= {:.8f}\n'.format(camera.pinhole.k3))
                out_file.write('k4= {:.8f}\n'.format(camera.pinhole.k4))
                q = Quat(camera.base_tform_sensor.rotation.w, camera.base_tform_sensor.rotation.x,
                         camera.base_tform_sensor.rotation.y, camera.base_tform_sensor.rotation.z)
                R = q.to_matrix()
                T = [
                    camera.base_tform_sensor.position.x, camera.base_tform_sensor.position.y,
                    camera.base_tform_sensor.position.z
                ]

                for i in range(3):
                    for j in range(3):
                        out_file.write('t{}{}= {:.8f}\n'.format(i, j, R[i][j]))
                    out_file.write('t{}{}= {:.8f}\n'.format(i, 3, T[i]))

                out_file.write('\n')

        return cameras
