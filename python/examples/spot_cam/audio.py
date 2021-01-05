# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os
import shutil
import tempfile

from bosdyn.client.command_line import (Command, Subcommands)

from bosdyn.client.spot_cam.audio import AudioClient

from bosdyn.api.spot_cam import audio_pb2


class AudioCommands(Subcommands):
    """Commands related to the Spot CAM's Audio service"""

    NAME = 'audio'

    def __init__(self, subparsers, command_dict):
        super(AudioCommands, self).__init__(subparsers, command_dict, [
            AudioListSoundsCommand,
            AudioSetVolumeCommand,
            AudioGetVolumeCommand,
            AudioPlaySoundCommand,
            AudioDeleteSoundCommand,
            AudioLoadSoundCommand,
        ])


class AudioListSoundsCommand(Command):
    """List of uploaded sounds"""

    NAME = 'list'

    def __init__(self, subparsers, command_dict):
        super(AudioListSoundsCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        sounds = robot.ensure_client(AudioClient.default_service_name).list_sounds()

        return sounds


class AudioSetVolumeCommand(Command):
    """Adjust the volume in terms of percentage"""

    NAME = 'set_volume'

    def __init__(self, subparsers, command_dict):
        super(AudioSetVolumeCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('percentage', help='volume of the CAM')

    def _run(self, robot, options):
        volume = min(max(float(options.percentage), 0.0), 100.0)
        sounds = robot.ensure_client(AudioClient.default_service_name).set_volume(volume)

        return sounds


class AudioGetVolumeCommand(Command):
    """Get the current volume in terms of percentage"""

    NAME = 'get_volume'

    def __init__(self, subparsers, command_dict):
        super(AudioGetVolumeCommand, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        volume = robot.ensure_client(AudioClient.default_service_name).get_volume()

        return volume


class AudioPlaySoundCommand(Command):
    """Play a sound found in 'list'"""

    NAME = 'play'

    def __init__(self, subparsers, command_dict):
        super(AudioPlaySoundCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('name', help='name of sound')
        self._parser.add_argument('--gain', help='volume gain multiplier', default=None, type=float)

    def _run(self, robot, options):
        sound = audio_pb2.Sound(name=options.name)
        gain = options.gain
        if gain:
            gain = max(gain, 0.0)
        robot.ensure_client(AudioClient.default_service_name).play_sound(sound, gain)


class AudioDeleteSoundCommand(Command):
    """Delete a sound found in 'list'"""

    NAME = 'delete'

    def __init__(self, subparsers, command_dict):
        super(AudioDeleteSoundCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('name', help='name of sound')

    def _run(self, robot, options):
        sound = audio_pb2.Sound(name=options.name)
        robot.ensure_client(AudioClient.default_service_name).delete_sound(sound)


class AudioLoadSoundCommand(Command):
    """Uploads specified WAV file"""

    NAME = 'load'

    def __init__(self, subparsers, command_dict):
        super(AudioLoadSoundCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('name', help='name of sound')
        self._parser.add_argument('src', help='WAV file to upload')

    def _run(self, robot, options):
        sound = audio_pb2.Sound(name=options.name)
        with open(options.src, 'rb') as fh:
            data = fh.read()
        robot.ensure_client(AudioClient.default_service_name).load_sound(sound, data)
