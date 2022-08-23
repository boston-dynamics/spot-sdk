# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import os
import shutil
import tempfile

from bosdyn.api.spot_cam import audio_pb2
from bosdyn.client.command_line import Command, Subcommands
from bosdyn.client.spot_cam.audio import AudioClient


class AudioCommands(Subcommands):
    """Commands related to the Spot CAM's Audio service"""

    NAME = 'audio'

    def __init__(self, subparsers, command_dict):
        super(AudioCommands, self).__init__(subparsers, command_dict, [
            AudioListSoundsCommand, AudioSetVolumeCommand, AudioGetVolumeCommand,
            AudioPlaySoundCommand, AudioDeleteSoundCommand, AudioLoadSoundCommand,
            AudioGetAudioCaptureChannel, AudioSetAudioCaptureChannel, AudioGetAudioCaptureGain,
            AudioSetAudioCaptureGain
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


#
# RPCs for Spot CAM+IR Only
#


class AudioGetAudioCaptureChannel(Command):
    """Get the current microphone channel"""

    NAME = 'get_capture_channel'

    def __init__(self, subparsers, command_dict):
        super(AudioGetAudioCaptureChannel, self).__init__(subparsers, command_dict)

    def _run(self, robot, options):
        channel = robot.ensure_client(AudioClient.default_service_name).get_audio_capture_channel()

        return channel


class AudioSetAudioCaptureChannel(Command):
    """Set the microphone channel"""

    NAME = 'set_capture_channel'

    def __init__(self, subparsers, command_dict):
        super(AudioSetAudioCaptureChannel, self).__init__(subparsers, command_dict)
        self._parser.add_argument('channel_name', default='internal_mic', const='internal_mic',
                                  nargs='?', choices=['internal_mic', 'external_mic'])

    def _run(self, robot, options):
        if options.channel_name == 'internal_mic':
            channel = audio_pb2.AudioCaptureChannel.AUDIO_CHANNEL_INTERNAL_MIC
        else:
            channel = audio_pb2.AudioCaptureChannel.AUDIO_CHANNEL_EXTERNAL_MIC
        return robot.ensure_client(
            AudioClient.default_service_name).set_audio_capture_channel(channel)


class AudioGetAudioCaptureGain(Command):
    """Get the current gain of the external microphone"""

    NAME = 'get_capture_gain'

    def __init__(self, subparsers, command_dict):
        super(AudioGetAudioCaptureGain, self).__init__(subparsers, command_dict)
        self._parser.add_argument('channel_name', default='external_mic', const='internal_mic',
                                  nargs='?', choices=['internal_mic', 'external_mic'])

    def _run(self, robot, options):
        if options.channel_name == 'internal_mic':
            channel = audio_pb2.AudioCaptureChannel.AUDIO_CHANNEL_INTERNAL_MIC
        else:
            channel = audio_pb2.AudioCaptureChannel.AUDIO_CHANNEL_EXTERNAL_MIC
        gain = robot.ensure_client(AudioClient.default_service_name).get_audio_capture_gain(channel)

        return gain


class AudioSetAudioCaptureGain(Command):
    """Adjust the gain from 0.0 to 1.0"""

    NAME = 'set_capture_gain'

    def __init__(self, subparsers, command_dict):
        super(AudioSetAudioCaptureGain, self).__init__(subparsers, command_dict)
        self._parser.add_argument('channel_name', default='external_mic', const='internal_mic',
                                  nargs='?', choices=['internal_mic', 'external_mic'])
        self._parser.add_argument('gain', help='Gain of the CAM\'s external microphone, 0.0 to 1.0')

    def _run(self, robot, options):
        gain = min(max(float(options.gain), 0.0), 1.0)
        if options.channel_name == 'internal_mic':
            channel = audio_pb2.AudioCaptureChannel.AUDIO_CHANNEL_INTERNAL_MIC
        else:
            channel = audio_pb2.AudioCaptureChannel.AUDIO_CHANNEL_EXTERNAL_MIC
        return robot.ensure_client(AudioClient.default_service_name).set_audio_capture_gain(
            channel, gain)
