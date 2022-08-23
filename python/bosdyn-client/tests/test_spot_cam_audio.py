# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the Spot CAM's AudioClient."""
import sys
import time

import grpc
import pytest

import bosdyn.client.spot_cam.audio
from bosdyn.api import header_pb2
from bosdyn.api.spot_cam import audio_pb2, service_pb2_grpc

from . import helpers


class MockAudioService(service_pb2_grpc.AudioServiceServicer):

    def __init__(self, rpc_delay=0):
        """Create mock that returns fake audio responses."""
        super(MockAudioService, self).__init__()
        self._rpc_delay = rpc_delay

    def ListSounds(self, request, context):
        time.sleep(self._rpc_delay)

        response = audio_pb2.ListSoundsResponse()
        response.sounds.add().name = 'good'
        response.sounds.add().name = 'bad'
        helpers.add_common_header(response, request)
        return response

    def SetVolume(self, request, context):
        time.sleep(self._rpc_delay)

        response = audio_pb2.SetVolumeResponse()
        helpers.add_common_header(response, request)
        return response

    def GetVolume(self, request, context):
        time.sleep(self._rpc_delay)

        response = audio_pb2.GetVolumeResponse()
        response.volume = 50
        helpers.add_common_header(response, request)
        return response

    def PlaySound(self, request, context):
        time.sleep(self._rpc_delay)

        response = audio_pb2.PlaySoundResponse()
        helpers.add_common_header(response, request)
        return response

    def DeleteSound(self, request, context):
        time.sleep(self._rpc_delay)

        response = audio_pb2.DeleteSoundResponse()
        helpers.add_common_header(response, request)
        return response

    def LoadSound(self, request_iterator, context):
        time.sleep(self._rpc_delay)

        response = audio_pb2.LoadSoundResponse()
        data = []
        first_request_header = None
        for r in request_iterator:
            first_request_header = first_request_header or r
            data.extend(r.data.data)

        original_length = len(data)
        if sys.version_info[0] < 3:
            data = ''.join(map(str, data))
        else:
            data = ''.join(map(chr, data))
        char = data[0]
        if (char == 'a' and original_length == 10) or \
                (char == 'b' and original_length == 100) or \
                (char == 'c' and original_length == 200):
            helpers.add_common_header(response, first_request_header)
        else:
            helpers.add_common_header(response, first_request_header,
                                      error_code=header_pb2.CommonError.CODE_INVALID_REQUEST,
                                      error_message='Unexpected test data {}'.format(len(data)))

        return response


def _setup(rpc_delay=0):
    client = bosdyn.client.spot_cam.audio.AudioClient()
    service = MockAudioService(rpc_delay=rpc_delay)
    server = helpers.setup_client_and_service(client, service,
                                              service_pb2_grpc.add_AudioServiceServicer_to_server)
    return client, service, server


def _create_fake_sound(name='fake-sound'):
    sound = audio_pb2.Sound()
    sound.name = name
    return sound


def test_list_sounds():
    client, service, server = _setup()
    sounds = client.list_sounds()
    assert len(sounds) == 2
    assert sounds[0].name == 'good'
    assert sounds[1].name == 'bad'


def test_list_sounds_async():
    client, service, server = _setup()
    sounds = client.list_sounds_async().result()
    assert len(sounds) == 2
    assert sounds[0].name == 'good'
    assert sounds[1].name == 'bad'


def test_set_volume():
    client, service, server = _setup()
    client.set_volume(100)


def test_set_volume_async():
    client, service, server = _setup()
    client.set_volume_async(100).result()


def test_get_volume():
    client, service, server = _setup()
    volume = client.get_volume()
    assert volume == 50


def test_set_volume_async():
    client, service, server = _setup()
    volume = client.get_volume_async().result()
    assert volume == 50


def test_play_sound():
    client, service, server = _setup()
    sound = _create_fake_sound()
    client.play_sound(sound, 100)


def test_play_sound_async():
    client, service, server = _setup()
    sound = _create_fake_sound()
    client.play_sound_async(sound, 100).result()


def test_play_sound_no_gain():
    client, service, server = _setup()
    sound = _create_fake_sound()
    client.play_sound(sound)


def test_play_sound_no_gain_async():
    client, service, server = _setup()
    sound = _create_fake_sound()
    client.play_sound_async(sound).result()


def test_delete_sound():
    client, service, server = _setup()
    sound = _create_fake_sound()
    client.delete_sound(sound)


def test_delete_sound_async():
    client, service, server = _setup()
    sound = _create_fake_sound()
    client.delete_sound_async(sound).result()


def test_load_sound_small_chunk():
    client, service, server = _setup()
    sound = _create_fake_sound()
    data = b'a' * 10
    client.load_sound(sound, data, max_chunk_size=100)


def test_load_sound_exact_large_chunk():
    client, service, server = _setup()
    sound = _create_fake_sound()
    data = b'b' * 100
    client.load_sound(sound, data, max_chunk_size=100)


def test_load_sound_large_chunk():
    client, service, server = _setup()
    sound = _create_fake_sound()
    data = b'c' * 200
    client.load_sound(sound, data, max_chunk_size=100)
