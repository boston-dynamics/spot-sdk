# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os
import shutil
import tempfile

from google.protobuf.duration_pb2 import Duration
from utils import add_bool_arg

from bosdyn.api.spot_cam import streamquality_pb2
from bosdyn.client.command_line import Command, Subcommands
from bosdyn.client.spot_cam.streamquality import StreamQualityClient


class StreamQualityCommands(Subcommands):
    """Commands related to the Spot CAM's StreamQuality service"""

    NAME = 'stream_quality'

    def __init__(self, subparsers, command_dict):
        super(StreamQualityCommands, self).__init__(subparsers, command_dict, [
            StreamQualityGetStreamParamsCommand, StreamQualitySetStreamParamsCommand,
            StreamQualityCongestionControlCommand
        ])


class StreamQualityGetStreamParamsCommand(Command):
    """Get image quality and postprocessing settings"""

    NAME = 'get'

    def __init__(self, subparsers, command_dict):
        super(StreamQualityGetStreamParamsCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        result = robot.ensure_client(StreamQualityClient.default_service_name).get_stream_params()

        return result


class StreamQualitySetStreamParamsCommand(Command):
    """Set image quality and postprocessing settings"""

    NAME = 'set'
    AWB_MODE = [
        'off', 'auto', 'incandescent', 'fluorescent', 'warm_fluorescent', 'daylight', 'cloudy',
        'twilight', 'shade', 'dark'
    ]
    EXPOSURE_MODE = ['auto', 'sync', 'manual']

    def __init__(self, subparsers, command_dict):
        super(StreamQualitySetStreamParamsCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('--target-bitrate', type=int,
                                  help='video compression (bits per second)')
        self._parser.add_argument('--refresh-interval', type=int,
                                  help='how often to update feed (in frames)')
        self._parser.add_argument('--idr-interval', type=int,
                                  help='how often to send IDR message (in frames)')
        self._parser.add_argument('--awb-mode', default='auto', const='auto', nargs='?',
                                  choices=StreamQualitySetStreamParamsCommand.AWB_MODE)
        self._parser.add_argument('--exposure-mode', default='auto', const='auto', nargs='?',
                                  choices=StreamQualitySetStreamParamsCommand.EXPOSURE_MODE)
        self._parser.add_argument(
            '--exposure-duration', type=float, default=0.5,
            help='Exposure duration to use with manual exposure mode (in seconds)')

    def _run(self, robot, options):

        if options.exposure_mode == 'auto':
            auto_exposure = streamquality_pb2.StreamParams.AutoExposure()
        else:
            auto_exposure = None

        if options.exposure_mode == 'sync':
            sync_auto_exposure = streamquality_pb2.StreamParams.SyncAutoExposure()
        else:
            sync_auto_exposure = None

        if options.exposure_mode == 'manual':
            duration_nanos = int(options.exposure_duration * 1e9)
            exposure_duration = Duration()
            exposure_duration.FromNanoseconds(duration_nanos)
            manual_exposure = streamquality_pb2.StreamParams.ManualExposure(
                exposure=exposure_duration)
        else:
            manual_exposure = None

        result = robot.ensure_client(StreamQualityClient.default_service_name).set_stream_params(
            options.target_bitrate, options.refresh_interval, options.idr_interval,
            StreamQualitySetStreamParamsCommand.AWB_MODE.index(options.awb_mode), auto_exposure,
            sync_auto_exposure, manual_exposure)

        return result


class StreamQualityCongestionControlCommand(Command):
    """Get image quality and postprocessing settings"""

    NAME = 'congestion_control'

    def __init__(self, subparsers, command_dict):
        super(StreamQualityCongestionControlCommand, self).__init__(subparsers, command_dict)
        add_bool_arg(self._parser, 'congestion_control')

    def _run(self, robot, options):
        result = robot.ensure_client(
            StreamQualityClient.default_service_name).enable_congestion_control(
                options.congestion_control)

        return result
