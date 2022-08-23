# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os
import shutil
import tempfile

import cv2
import numpy as np
from PIL import Image
from utils import add_bool_arg

from bosdyn.api import image_pb2
from bosdyn.api.spot_cam import camera_pb2, logging_pb2
from bosdyn.client.command_line import Command, Subcommands
from bosdyn.client.spot_cam.media_log import MediaLogClient


def write_pgm(filename, width, height, max_val, data):
    """ Helper function to supplement PIL with writing a 16-bit PGM from the IR camera
    """
    with open(filename, 'wb') as f:
        f.write('P5\n'.encode('utf-8'))
        f.write(f'{width} {height}\n'.encode('utf-8'))
        f.write(f'{max_val}\n'.encode('utf-8'))
        f.write(data)


class MediaLogCommands(Subcommands):
    """Commands related to the Spot CAM's Media Log service"""

    NAME = 'media_log'

    def __init__(self, subparsers, command_dict):
        super(MediaLogCommands, self).__init__(subparsers, command_dict, [
            MediaLogDeleteCommand,
            MediaLogDeleteAllCommand,
            MediaLogEnableDebugCommand,
            MediaLogGetStatusCommand,
            MediaLogListCamerasCommand,
            MediaLogListLogpointsCommand,
            MediaLogRetrieveCommand,
            MediaLogRetrieveAllCommand,
            MediaLogStoreCommand,
            MediaLogStoreRetrieveCommand,
            MediaLogTagCommand,
        ])


class MediaLogDeleteCommand(Command):
    """Delete the specified logpoint"""

    NAME = 'delete'

    def __init__(self, subparsers, command_dict):
        super(MediaLogDeleteCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('name', help='"name" of a logpoint')

    def _run(self, robot, options):
        lp = logging_pb2.Logpoint(name=options.name)
        robot.ensure_client(MediaLogClient.default_service_name).delete(lp)


class MediaLogDeleteAllCommand(Command):
    """Delete all logpoints"""

    NAME = 'delete-all'

    def __init__(self, subparsers, command_dict):
        super(MediaLogDeleteAllCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        client = robot.ensure_client(MediaLogClient.default_service_name)
        for logpoint in client.list_logpoints():
            print('Deleting {}...'.format(logpoint.name))
            client.delete(logpoint)
        print('All logpoints deleted.')


class MediaLogEnableDebugCommand(Command):
    """Enable logging of device sensors"""

    NAME = 'enable_debug'

    def __init__(self, subparsers, command_dict):
        super(MediaLogEnableDebugCommand, self).__init__(subparsers, command_dict)
        add_bool_arg(self._parser, 'temperature')
        add_bool_arg(self._parser, 'humidity')
        add_bool_arg(self._parser, 'BIT')
        add_bool_arg(self._parser, 'shock', default=True)
        add_bool_arg(self._parser, 'system-stats')

    def _run(self, robot, options):
        robot.ensure_client(MediaLogClient.default_service_name).enable_debug(
            temp=options.temperature, humidity=options.humidity, bit=options.BIT,
            shock=options.shock, system_stats=options.system_stats)


class MediaLogGetStatusCommand(Command):
    """Status of the specified logpoint"""

    NAME = 'status'

    def __init__(self, subparsers, command_dict):
        super(MediaLogGetStatusCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('name', help='"name" of a logpoint')

    def _run(self, robot, options):
        lp = logging_pb2.Logpoint(name=options.name)
        point = robot.ensure_client(MediaLogClient.default_service_name).get_status(lp)

        return point


class MediaLogListCamerasCommand(Command):
    """List all the available cameras"""

    NAME = 'list_cameras'

    def __init__(self, subparsers, command_dict):
        super(MediaLogListCamerasCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        cameras = robot.ensure_client(MediaLogClient.default_service_name).list_cameras()

        return cameras


class MediaLogListLogpointsCommand(Command):
    """List all the stored logpoints"""

    NAME = 'list_logpoints'

    def __init__(self, subparsers, command_dict):
        super(MediaLogListLogpointsCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        logpoints = robot.ensure_client(MediaLogClient.default_service_name).list_logpoints()

        return logpoints


class MediaLogRetrieveCommand(Command):
    """Retrieve the specified logpoint"""

    NAME = 'retrieve'

    def __init__(self, subparsers, command_dict):
        super(MediaLogRetrieveCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('name', help='"name" of a logpoint')
        self._parser.add_argument('--dst', default=None, help='Filename of saved image')
        add_bool_arg(self._parser, 'save-as-rgb24', default=False)
        add_bool_arg(self._parser, 'stitching', default=True)
        add_bool_arg(self._parser, "raw-ir", default=False)

    def _run(self, robot, options):
        lp = logging_pb2.Logpoint(name=options.name)
        lp = self.save_logpoint_as_image(robot, lp, options, dst_filename=options.dst)

        return lp

    @staticmethod
    def save_logpoint_as_image(robot, lp, options, dst_filename=None):
        """'options' need to have boolean arguments save-as-rgb24 and stitching."""
        if options.stitching and not options.raw_ir:
            lp, img = robot.ensure_client(MediaLogClient.default_service_name).retrieve(lp)
        else:
            lp, img = robot.ensure_client(MediaLogClient.default_service_name).retrieve_raw_data(lp)

        # case for 16 bit raw thermal image
        if lp.image_params.format == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U16:
            np_img = np.frombuffer(img, dtype=np.uint16).byteswap()
            np_img = np_img.reshape((lp.image_params.height, lp.image_params.width, 1))
            cv2.imwrite(f'{dst_filename}.pgm', np_img)
            return lp

        with tempfile.NamedTemporaryFile(delete=False) as img_file:
            img_file.write(img)
            src_filename = img_file.name

        if dst_filename is None:
            dst_filename = os.path.basename(src_filename)

        # Pano and IR both come in as JPEG from retrieve command
        if lp.image_params.height == 4800 or lp.image_params.height == 2400 or (
                lp.image_params.width == 640 and lp.image_params.height == 512):
            shutil.move(src_filename, '{}.jpg'.format(dst_filename))
        else:
            target_filename = '{}-{}x{}.rgb24'.format(dst_filename, lp.image_params.width,
                                                      lp.image_params.height)
            shutil.move(src_filename, target_filename)

            if not options.save_as_rgb24:
                with open(target_filename, mode='rb') as fd:
                    data = fd.read()

                mode = 'RGB'
                image = Image.frombuffer(mode, (lp.image_params.width, lp.image_params.height),
                                         data, 'raw', mode, 0, 1)
                image.save('{}.jpg'.format(dst_filename))

                os.remove(target_filename)

        return lp


class MediaLogRetrieveAllCommand(Command):
    """retrieve the image corresponding to each logpoint in list_logpoints"""

    NAME = 'retrieve_all'

    def __init__(self, subparsers, command_dict):
        super(MediaLogRetrieveAllCommand, self).__init__(subparsers, command_dict)
        add_bool_arg(self._parser, 'save-as-rgb24', default=False)
        add_bool_arg(self._parser, 'stitching', default=False)

    def _run(self, robot, options):
        logpoints = robot.ensure_client(MediaLogClient.default_service_name).list_logpoints()

        detailed_lps = []
        for logpoint in logpoints:
            lp = MediaLogRetrieveCommand.save_logpoint_as_image(robot, logpoint, options,
                                                                dst_filename=logpoint.name)
            detailed_lps.append(lp)

        return detailed_lps


class MediaLogStoreCommand(Command):
    """Trigger snapshot"""

    NAME = 'store'

    def __init__(self, subparsers, command_dict):
        super(MediaLogStoreCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('camera_name', default='pano', const='pano', nargs='?',
                                  choices=['pano', 'c0', 'c1', 'c2', 'c3', 'c4', 'ptz', 'ir'])

    def _run(self, robot, options):
        args = (camera_pb2.Camera(name=options.camera_name), logging_pb2.Logpoint.STILLIMAGE)
        logpoint = robot.ensure_client(MediaLogClient.default_service_name).store(*args)

        return logpoint


class MediaLogStoreRetrieveCommand(Command):
    """store followed by retrieve"""

    NAME = 'store_retrieve'

    def __init__(self, subparsers, command_dict):
        super(MediaLogStoreRetrieveCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('camera_name', default='pano', const='pano', nargs='?',
                                  choices=['pano', 'c0', 'c1', 'c2', 'c3', 'c4', 'ptz', 'ir'])
        self._parser.add_argument('--dst', default=None, help='Filename of saved image')
        add_bool_arg(self._parser, 'save-as-rgb24', default=False)
        add_bool_arg(self._parser, 'stitching', default=True)
        add_bool_arg(self._parser, 'raw-ir', default=False)

    def _run(self, robot, options):
        client = robot.ensure_client(MediaLogClient.default_service_name)

        args = (camera_pb2.Camera(name=options.camera_name), logging_pb2.Logpoint.STILLIMAGE)
        lp = client.store(*args)

        while lp.status != logging_pb2.Logpoint.COMPLETE:
            lp = client.get_status(lp)

        lp = MediaLogRetrieveCommand.save_logpoint_as_image(robot, lp, options,
                                                            dst_filename=options.dst)

        return lp


class MediaLogTagCommand(Command):
    """Update the tag of an existing logpoint"""

    NAME = 'tag'

    def __init__(self, subparsers, command_dict):
        super(MediaLogTagCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('name', help='"name" of a logpoint')
        self._parser.add_argument('tag', help='encapsulate the desired text between double quotes')

    def _run(self, robot, options):
        lp = logging_pb2.Logpoint(name=options.name, tag=options.tag)
        robot.ensure_client(MediaLogClient.default_service_name).tag(lp)
