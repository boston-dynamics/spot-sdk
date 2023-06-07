# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
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
    feature_parser.add_argument(f'--{prefix[1]}-{name}', dest=stripped_name, action='store_true')
    feature_parser.add_argument(f'--{prefix[0]}-{name}', dest=stripped_name, action='store_false')
    feature_parser.set_defaults(**{stripped_name: default})


def ip2int(addr):
    return struct.unpack('!I', socket.inet_aton(addr))[0]


def int2ip(addr):
    return socket.inet_ntoa(struct.pack('!I', addr))


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
                out_file.write(f'cam{ring_index}\n')
                camera = cameras[ring_index]

                out_file.write(f'fx= {camera.pinhole.focal_length.x:.8f}\n')
                out_file.write(f'fy= {camera.pinhole.focal_length.y:.8f}\n')
                out_file.write(f'cx= {camera.pinhole.center_point.x:.8f}\n')
                out_file.write(f'cy= {camera.pinhole.center_point.y:.8f}\n')
                out_file.write(f'k1= {camera.pinhole.k1:.8f}\n')
                out_file.write(f'k2= {camera.pinhole.k2:.8f}\n')
                out_file.write(f'k3= {camera.pinhole.k3:.8f}\n')
                out_file.write(f'k4= {camera.pinhole.k4:.8f}\n')
                q = Quat(camera.base_tform_sensor.rotation.w, camera.base_tform_sensor.rotation.x,
                         camera.base_tform_sensor.rotation.y, camera.base_tform_sensor.rotation.z)
                R = q.to_matrix()
                T = [
                    camera.base_tform_sensor.position.x, camera.base_tform_sensor.position.y,
                    camera.base_tform_sensor.position.z
                ]

                for i in range(3):
                    for j in range(3):
                        out_file.write(f't{i}{j}= {R[i][j]:.8f}\n')
                    out_file.write(f't{i}3= {T[i]:.8f}\n')

                out_file.write('\n')

        return cameras
