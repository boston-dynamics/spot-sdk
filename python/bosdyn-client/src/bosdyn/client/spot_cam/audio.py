# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Spot CAM Audio service."""

import logging

_LOGGER = logging.getLogger(__name__)

from bosdyn.client.common import (BaseClient, common_header_errors, handle_common_header_errors)
from bosdyn.api.spot_cam import service_pb2_grpc
from bosdyn.api.spot_cam import audio_pb2
from bosdyn.api import data_chunk_pb2

from google.protobuf.wrappers_pb2 import FloatValue


class AudioClient(BaseClient):
    """A client calling Spot CAM Audio service.
    """
    default_service_name = 'spot-cam-audio'
    service_type = 'bosdyn.api.spot_cam.AudioService'

    def __init__(self):
        super(AudioClient, self).__init__(service_pb2_grpc.AudioServiceStub)

    def list_sounds(self, **kwargs):
        """Retrieve the list of available sounds"""
        request = audio_pb2.ListSoundsRequest()
        return self.call(self._stub.ListSounds, request, self._list_sounds_from_response,
                         self._audio_error_from_response, **kwargs)

    def list_sounds_async(self, **kwargs):
        """Async version of list_sounds()"""
        request = audio_pb2.ListSoundsRequest()
        return self.call_async(self._stub.ListSounds, request, self._list_sounds_from_response,
                               self._audio_error_from_response, **kwargs)

    def set_volume(self, percentage, **kwargs):
        """Set the current volume as a percentage"""
        request = audio_pb2.SetVolumeRequest(volume=percentage)
        return self.call(self._stub.SetVolume, request, self._set_volume_from_response,
                         self._audio_error_from_response, **kwargs)

    def set_volume_async(self, percentage, **kwargs):
        """Async version of set_volume()"""
        request = audio_pb2.SetVolumeRequest(volume=percentage)
        return self.call_async(self._stub.SetVolume, request, self._set_volume_from_response,
                               self._audio_error_from_response, **kwargs)

    def get_volume(self, **kwargs):
        """Retrieve the current volume as a percentage"""
        request = audio_pb2.GetVolumeRequest()
        return self.call(self._stub.GetVolume, request, self._get_volume_from_response,
                         self._audio_error_from_response, **kwargs)

    def get_volume_async(self, **kwargs):
        """Async version of get_volume()"""
        request = audio_pb2.GetVolumeRequest()
        return self.call_async(self._stub.GetVolume, request, self._get_volume_from_response,
                               self._audio_error_from_response, **kwargs)

    def play_sound(self, sound, gain=None, **kwargs):
        """Play already uploaded sound with optional volume gain multiplier"""
        if gain:
            fv = FloatValue()
            fv.value = gain
            request = audio_pb2.PlaySoundRequest(sound=sound, gain=fv)
        else:
            request = audio_pb2.PlaySoundRequest(sound=sound)
        return self.call(self._stub.PlaySound, request, self._play_sound_from_response,
                         self._audio_error_from_response, **kwargs)

    def play_sound_async(self, sound, gain=1.0, **kwargs):
        """Async version of play_sound()"""
        fv = FloatValue()
        fv.value = gain
        request = audio_pb2.PlaySoundRequest(sound=sound, gain=fv)
        return self.call_async(self._stub.PlaySound, request, self._play_sound_from_response,
                               self._audio_error_from_response, **kwargs)

    def delete_sound(self, sound, **kwargs):
        """Delete sound found in list_sounds()"""
        request = audio_pb2.DeleteSoundRequest(sound=sound)
        return self.call(self._stub.DeleteSound, request, self._delete_sound_from_response,
                         self._audio_error_from_response, **kwargs)

    def delete_sound_async(self, sound, **kwargs):
        """Async version of delete_sound()"""
        request = audio_pb2.DeleteSoundRequest(sound=sound)
        return self.call_async(self._stub.DeleteSound, request, self._delete_sound_from_response,
                               self._audio_error_from_response, **kwargs)

    def load_sound(self, sound, data, max_chunk_size=1024 * 1024, **kwargs):
        """Uploads the WAV data tagged with the specified Sound"""

        def yield_requests(data):
            request = audio_pb2.LoadSoundRequest(sound=sound)
            request.data.total_size = len(data)

            # Break file into chunks if it's too large.
            last = 0
            for i in range(max_chunk_size, request.data.total_size, max_chunk_size):
                request.data.data = data[last:i]
                yield request
                last = i

            # Small (leftover) chunks gets sent here
            if last < request.data.total_size:
                request.data.data = data[last:]
                yield request

        return self.call(self._stub.LoadSound, yield_requests(data), self._load_sound_from_response,
                         self._audio_error_from_response, **kwargs)

    @staticmethod
    def _list_sounds_from_response(response):
        return response.sounds

    @staticmethod
    def _set_volume_from_response(response):
        pass

    @staticmethod
    def _get_volume_from_response(response):
        return response.volume

    @staticmethod
    def _play_sound_from_response(response):
        pass

    @staticmethod
    def _delete_sound_from_response(response):
        pass

    @staticmethod
    def _load_sound_from_response(response):
        pass

    @staticmethod
    @handle_common_header_errors
    def _audio_error_from_response(response):  # pylint: disable=unused-argument
        return None
