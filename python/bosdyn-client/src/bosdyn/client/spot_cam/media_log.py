# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Spot CAM MediaLog service."""

import logging

_LOGGER = logging.getLogger(__name__)

from bosdyn.client.common import (BaseClient, common_header_errors, handle_common_header_errors)
from bosdyn.api.spot_cam import service_pb2_grpc
from bosdyn.api.spot_cam import logging_pb2


class MediaLogClient(BaseClient):
    """A client calling Spot CAM MediaLog service.
    """
    default_service_name = 'spot-cam-media-log'
    service_type = 'bosdyn.api.spot_cam.MediaLogService'

    def __init__(self):
        super(MediaLogClient, self).__init__(service_pb2_grpc.MediaLogServiceStub)

    def delete(self, logpoint, **kwargs):
        """Removes the Logpoint from the Spot CAM system.

        Args:
          logpoint: spot_cam.Logpoint.name must be filled out."""
        request = logging_pb2.DeleteRequest(point=logpoint)
        return self.call(self._stub.Delete, request, self._delete_from_response,
                         self._media_log_error_from_response, **kwargs)

    def delete_async(self, logpoint, **kwargs):
        """Async version of delete()"""
        request = logging_pb2.DeleteRequest(point=logpoint)
        return self.call_async(self._stub.Delete, request, self._delete_from_response,
                               self._media_log_error_from_response, **kwargs)

    def enable_debug(self, temp=False, humidity=False, bit=False, shock=True, system_stats=False, **kwargs):
        """Start periodic logging of health data to the database, queryable via Health service.

        Args:
          temp: Enable logging of temperature data.
          humidity: Enable logging of humidity data.
          bit: Enable logging of BIT events coming from the Health service.
          shock: Enable logging of Shock data.
          system_stats: Enable logging of cpu, gpu, memory, and network utilization."""
        request = logging_pb2.DebugRequest(enable_temperature=temp,
                                           enable_humidity=humidity,
                                           enable_BIT=bit,
                                           enable_shock=shock,
                                           enable_system_stat=system_stats)
        return self.call(self._stub.EnableDebug, request, self._enable_debug_from_response,
                         self._media_log_error_from_response, **kwargs)

    def enable_debug_async(self, temp=False, humidity=False, bit=False, shock=True, system_stats=False, **kwargs):
        """Async version of enable_debug()"""
        request = logging_pb2.DebugRequest(enable_temperature=temp,
                                                 enable_humidity=humidity,
                                                 enable_BIT=bit,
                                                 enable_shock=shock,
                                                 enable_system_stat=system_stats)
        return self.call_async(self._stub.EnableDebug, request, self._enable_debug_from_response,
                               self._media_log_error_from_response, **kwargs)

    def get_status(self, logpoint, **kwargs):
        """Gets the state of the specified logpoint.

        Args:
          logpoint: spot_cam.Logpoint.name must be filled out.
        Returns:
          A spot_cam.Logpoint with the status filled out."""
        request = logging_pb2.GetStatusRequest(point=logpoint)
        return self.call(self._stub.GetStatus, request, self._get_status_from_response,
                         self._media_log_error_from_response, **kwargs)

    def get_status_async(self, logpoint, **kwargs):
        """Async version of get_status()"""
        request = logging_pb2.GetStatusRequest(point=logpoint)
        return self.call_async(self._stub.GetStatus, request, self._get_status_from_response,
                               self._media_log_error_from_response, **kwargs)

    def list_cameras(self, **kwargs):
        """List cameras on Spot CAM"""
        request = logging_pb2.ListCamerasRequest()
        return self.call(self._stub.ListCameras, request, self._list_cameras_from_response,
                         self._media_log_error_from_response, **kwargs)

    def list_cameras_async(self, **kwargs):
        """Async version of list_cameras()"""
        request = logging_pb2.ListCamerasRequest()
        return self.call_async(self._stub.ListCameras, request, self._list_cameras_from_response,
                               self._media_log_error_from_response, **kwargs)

    def list_logpoints(self, **kwargs):
        """List Logpoints on Spot CAM"""
        request = logging_pb2.ListLogpointsRequest()
        return self.call(self._stub.ListLogpoints, request, self._list_logpoints_from_response,
                         self._media_log_error_from_response, **kwargs)

    def retrieve(self, logpoint, **kwargs):
        """Retrieves the image associated with the Logpoint.

        Args:
          logpoint: spot_cam.Logpoint.name must be filled out."""
        request = logging_pb2.RetrieveRequest(point=logpoint)
        return self.call(self._stub.Retrieve, request, self._retrieve_from_response,
                         self._media_log_error_from_response, **kwargs)

    def retrieve_raw_data(self, logpoint, **kwargs):
        """Retrieves the image associated with the Logpoint.

        Args:
          logpoint: spot_cam.Logpoint.name must be filled out."""
        request = logging_pb2.RetrieveRawDataRequest(point=logpoint)
        return self.call(self._stub.RetrieveRawData, request, self._retrieve_from_response,
                         self._media_log_error_from_response, **kwargs)

    def set_passphrase(self, passphrase, **kwargs):
        """Set password for Spot CAM filesystem."""
        request = logging_pb2.SetPassphraseRequest(passphrase=passphrase)
        return self.call(self._stub.SetPassphrase, request, self._set_passphrase_from_response,
                         self._media_log_error_from_response, **kwargs)

    def set_passphrase_async(self, passphrase, **kwargs):
        """Async version of set_passphrase()"""
        request = logging_pb2.SetPassphraseRequest(passphrase=passphrase)
        return self.call_async(self._stub.SetPassphrase, request, self._set_passphrase_from_response,
                               self._media_log_error_from_response, **kwargs)

    def store(self, camera, record_type, tag=None, **kwargs):
        """Store media on the Spot CAM.

        Args:
          camera: spot_cam.Camera protobuf describing the camera to store media on.
          record_type: spot_cam.Logpoint.RecordType indicating the type of recording.
          tag: Optional string to associate with the stored media.
        Returns:
          An spot_cam.Logpoint describing the stored data.
        """
        request = logging_pb2.StoreRequest(camera=camera, type=record_type, tag=tag)
        return self.call(self._stub.Store, request, self._store_from_response,
                         self._media_log_error_from_response, **kwargs)

    def store_async(self, camera, record_type, tag=None, **kwargs):
        """Async version of store()"""
        request = logging_pb2.StoreRequest(camera=camera, type=record_type, tag=tag)
        return self.call_async(self._stub.Store, request, self._store_from_response,
                               self._media_log_error_from_response, **kwargs)

    def tag(self, logpoint, **kwargs):
        """Update the 'tag' field of an existing Logpoint.

        Args:
          logpoint: 'tag' and 'name' in spot_cam.Logpoint must be filled out."""
        request = logging_pb2.TagRequest(point=logpoint)
        return self.call(self._stub.Tag, request, self._tag_from_response,
                         self._media_log_error_from_response, **kwargs)

    def tag_async(self, logpoint, **kwargs):
        """Async version of tag()"""
        request = logging_pb2.TagRequest(point=logpoint)
        return self.call_async(self._stub.Tag, request, self._tag_from_response,
                               self._media_log_error_from_response, **kwargs)

    @staticmethod
    def _delete_from_response(response):
        pass

    @staticmethod
    def _enable_debug_from_response(response):
        pass

    @staticmethod
    def _get_status_from_response(response):
        return response.point

    @staticmethod
    def _list_cameras_from_response(response):
        return response.cameras

    @staticmethod
    def _list_logpoints_from_response(responses):
        logpoints = []
        for response in responses:
            logpoints.extend(response.logpoints)

        return logpoints

    @staticmethod
    def _retrieve_from_response(responses):
        total = 0

        local_chunks = []
        logpoint = None
        for response in responses:
            if logpoint is None:
                logpoint = response.logpoint
            chunk = response.data
            total += len(chunk.data)
            _LOGGER.debug('Retrieved {} bytes ({}/{})'.format(
                len(chunk.data), total, chunk.total_size))
            local_chunks.append(chunk)
        return logpoint, b''.join(chunk.data for chunk in local_chunks)

    @staticmethod
    def _set_passphrase_from_response(response):
        pass

    @staticmethod
    def _store_from_response(response):
        return response.point

    @staticmethod
    def _tag_from_response(response):
        pass

    @staticmethod
    @handle_common_header_errors
    def _media_log_error_from_response(response):  # pylint: disable=unused-argument
        return None
