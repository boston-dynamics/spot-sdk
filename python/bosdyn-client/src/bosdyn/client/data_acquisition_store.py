# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client implementation for data acquisition store service.
"""

from os import fstat
from pathlib import Path

from google.protobuf import json_format

from bosdyn.api import data_acquisition_store_pb2 as data_acquisition_store
from bosdyn.api import data_acquisition_store_service_pb2_grpc as data_acquisition_store_service
from bosdyn.api import data_chunk_pb2 as data_chunk
from bosdyn.api import header_pb2, image_pb2
from bosdyn.client.channel import DEFAULT_HEADER_BUFFER_LENGTH, DEFAULT_MAX_MESSAGE_LENGTH
from bosdyn.client.common import (BaseClient, common_header_errors, error_factory, error_pair,
                                  handle_common_header_errors, handle_unset_status_error)
from bosdyn.client.data_chunk import split_serialized
from bosdyn.client.exceptions import Error, ResponseError
from bosdyn.util import now_timestamp

DEFAULT_CHUNK_SIZE_BYTES = int(DEFAULT_MAX_MESSAGE_LENGTH - DEFAULT_HEADER_BUFFER_LENGTH)


class DataAcquisitionStoreClient(BaseClient):
    """A client for triggering data acquisition store methods."""

    default_service_name = 'data-acquisition-store'
    service_type = 'bosdyn.api.DataAcquisitionStoreService'

    def __init__(self):
        super(DataAcquisitionStoreClient,
              self).__init__(data_acquisition_store_service.DataAcquisitionStoreServiceStub)
        self._timesync_endpoint = None

    def update_from(self, other):
        super(DataAcquisitionStoreClient, self).update_from(other)

        # Grab a timesync endpoint if it is available.
        try:
            self._timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    def list_capture_actions(self, query, **kwargs):
        """List capture actions that satisfy the query parameters.

        Args:
             query (bosdyn.api.DataQueryParams) : Query parameters.

        Returns:
             CaptureActionIds for the actions matching the query parameters.
        """

        request = data_acquisition_store.ListCaptureActionsRequest(query=query)
        return self.call(self._stub.ListCaptureActions, request,
                         value_from_response=_get_action_ids,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def list_capture_actions_async(self, query, **kwargs):
        """Async version of the list_capture_actions() RPC."""
        request = data_acquisition_store.ListCaptureActionsRequest(query=query)
        return self.call_async(self._stub.ListCaptureActions, request,
                               value_from_response=_get_action_ids,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def list_stored_images(self, query, **kwargs):
        """List images that satisfy the query parameters.

        Args:
             query (bosdyn.api.DataQueryParams) : Query parameters.

        Returns:
             DataIdentifiers for the images matching the query parameters.
        """

        request = data_acquisition_store.ListStoredImagesRequest(query=query)
        return self.call(self._stub.ListStoredImages, request, value_from_response=_get_data_ids,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def list_stored_images_async(self, query, **kwargs):
        """Async version of the list_stored_images_actions() RPC."""
        request = data_acquisition_store.ListStoredImagesRequest(query=query)
        return self.call_async(self._stub.ListStoredImages, request,
                               value_from_response=_get_data_ids,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def list_stored_metadata(self, query, **kwargs):
        """List metadata that satisfy the query parameters.

        Args:
             query (bosdyn.api.DataQueryParams) : Query parameters.

        Returns:
             DataIdentifiers for the metadata matching the query parameters.
        """

        request = data_acquisition_store.ListStoredMetadataRequest(query=query)
        return self.call(self._stub.ListStoredMetadata, request, value_from_response=_get_data_ids,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def list_stored_metadata_async(self, query, **kwargs):
        """Async version of the list_stored_metadata() RPC."""
        request = data_acquisition_store.ListStoredMetadataRequest(query=query)
        return self.call_async(self._stub.ListStoredMetadata, request,
                               value_from_response=_get_data_ids,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def list_stored_alertdata(self, query, **kwargs):
        """List AlertData that satisfy the query parameters.

        Args:
             query (bosdyn.api.DataQueryParams) : Query parameters.

        Returns:
             DataIdentifiers for the AlertData matching the query parameters.
        """

        request = data_acquisition_store.ListStoredAlertDataRequest(query=query)
        return self.call(self._stub.ListStoredAlertData, request, value_from_response=_get_data_ids,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def list_stored_alertdata_async(self, query, **kwargs):
        """Async version of the list_stored_alertdata() RPC."""
        request = data_acquisition_store.ListStoredAlertDataRequest(query=query)
        return self.call_async(self._stub.ListStoredAlertData, request,
                               value_from_response=_get_data_ids,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def list_stored_data(self, query, **kwargs):
        """List data that satisfy the query parameters.

        Args:
             query (bosdyn.api.DataQueryParams) : Query parameters.

        Returns:
             DataIdentifiers for the data matching the query parameters.
        """

        request = data_acquisition_store.ListStoredDataRequest(query=query)
        return self.call(self._stub.ListStoredData, request, value_from_response=_get_data_ids,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def list_stored_data_async(self, query, **kwargs):
        """Async version of the list_stored_data() RPC."""
        request = data_acquisition_store.ListStoredDataRequest(query=query)
        return self.call_async(self._stub.ListStoredData, request,
                               value_from_response=_get_data_ids,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def store_image(self, image, data_id, **kwargs):
        """Store image.

        Args:
            image (bosdyn.api.ImageCapture) : Image to store.
            data_id (bosdyn.api.DataIdentifier) : Data identifier to use for storing the image.

        Returns:
             StoreImageResponse response.
        """

        request = data_acquisition_store.StoreImageRequest(image=image, data_id=data_id)
        return self.call(self._stub.StoreImage, request, error_from_response=common_header_errors,
                         copy_request=False, **kwargs)

    def store_image_async(self, image, data_id, **kwargs):
        """Async version of the store_image() RPC."""
        request = data_acquisition_store.StoreImageRequest(image=image, data_id=data_id)
        return self.call_async(self._stub.StoreImage, request,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def store_metadata(self, associated_metadata, data_id, **kwargs):
        """Store metadata.

        Args:
            associated_metadata (bosdyn.api.AssociatedMetadata) : Metadata to store. If metadata is
                not associated with a particular piece of data, the data_id field in this object
                needs to specify only the action_id part.
            data_id (bosdyn.api.DataIdentifier) : Data identifier to use for storing this
                associated metadata.

        Returns:
             StoreMetadataResponse response.
        """

        request = data_acquisition_store.StoreMetadataRequest(metadata=associated_metadata,
                                                              data_id=data_id)
        return self.call(self._stub.StoreMetadata, request,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def store_metadata_async(self, associated_metadata, data_id, **kwargs):
        """Async version of the store_metadata() RPC."""
        request = data_acquisition_store.StoreMetadataRequest(metadata=associated_metadata,
                                                              data_id=data_id)
        return self.call_async(self._stub.StoreMetadata, request,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def store_alertdata(self, associated_alert_data, data_id, **kwargs):
        """Store AlertData.

        Args:
            associated_alert_data (bosdyn.api.AssociatedAlertData) : AlertData to store. If AlertData is
                not associated with a particular piece of data, the data_id field in this object
                needs to specify only the action_id part.
            data_id (bosdyn.api.DataIdentifier) : Data identifier to use for storing this
                associated AlertData.

        Returns:
             StoreAlertDataResponse response.
        """

        request = data_acquisition_store.StoreAlertDataRequest(alert_data=associated_alert_data,
                                                               data_id=data_id)
        return self.call(self._stub.StoreAlertData, request,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def store_alertdata_async(self, associated_alert_data, data_id, **kwargs):
        """Async version of the store_alertdata() RPC."""
        request = data_acquisition_store.StoreAlertDataRequest(alert_data=associated_alert_data,
                                                               data_id=data_id)
        return self.call_async(self._stub.StoreAlertData, request,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def store_data(self, data, data_id, file_extension=None, **kwargs):
        """Store data.

        Args:
            data (bytes) : Arbitrary data to store.
            data_id (bosdyn.api.DataIdentifier) : Data identifier to use for storing this data.
            file_extension (string) : File extension to use for writing the data to a file.

        Returns:
             StoreDataResponse response.
        """

        request = data_acquisition_store.StoreDataRequest(data=data, data_id=data_id,
                                                          file_extension=file_extension)
        return self.call(self._stub.StoreData, request, error_from_response=common_header_errors,
                         copy_request=False, **kwargs)

    def store_data_async(self, data, data_id, file_extension=None, **kwargs):
        """Async version of the store_data() RPC."""
        request = data_acquisition_store.StoreDataRequest(data=data, data_id=data_id,
                                                          file_extension=file_extension)
        return self.call_async(self._stub.StoreData, request,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def store_data_as_chunks(self, data, data_id, file_extension=None, **kwargs):
        """Store data using streaming, supports storing of large data that is too large for a single store_data rpc. Note: using this rpc means that the data must be loaded into memory.

        Args:
            data (bytes) : Arbitrary data to store.
            data_id (bosdyn.api.DataIdentifier) : Data identifier to use for storing this data.
            file_extension (string) : File extension to use for writing the data to a file.

        Returns:
             StoreDataResponse final successful response or first failed response.
        """
        return self.call(self._stub.StoreDataStream,
                         _iterate_data_chunks(data, data_id, file_extension),
                         error_from_response=common_header_errors, value_from_response=None,
                         copy_request=False, **kwargs)

    def store_data_as_chunks_async(self, data, data_id, file_extension=None, **kwargs):
        """Async version of the store_data_as_chunks() RPC."""
        return self.call_async_streaming(
            self._stub.StoreDataStream, _iterate_data_chunks(data, data_id, file_extension),
            error_from_response=common_header_errors, value_from_response=None,
            assemble_type=data_acquisition_store.StoreStreamResponse, copy_request=False, **kwargs)

    def store_file(self, file_path, data_id, file_extension=None, **kwargs):
        """Store file using file path, supports storing of large files that are too large for a single store_data rpc.

        Args:
            file_path (string) : File path to arbitrary data to store.
            data_id (bosdyn.api.DataIdentifier) : Data identifier to use for storing this data.
            file_extension (string) : File extension to use for writing the data to a file.

        Returns:
             StoreDataResponse final successful response or first failed response.
        """

        file_abs = Path(file_path).absolute()
        file = open(file_abs, "rb")
        return self.call(self._stub.StoreDataStream,
                         _iterate_store_file(file, data_id, file_extension=file_extension),
                         error_from_response=common_header_errors, value_from_response=None,
                         copy_request=False, **kwargs)

    def store_file_async(self, file_path, data_id, file_extension=None, **kwargs):
        """Async version of the store_file() RPC."""

        file_abs = Path(file_path).absolute()
        file = open(file_abs, "rb")
        return self.call_async_streaming(
            self._stub.StoreDataStream,
            _iterate_store_file(file, data_id, file_extension=file_extension),
            error_from_response=common_header_errors, value_from_response=None,
            assemble_type=data_acquisition_store.StoreStreamResponse, copy_request=False, **kwargs)

    def query_stored_captures(self, query=None, **kwargs):
        """Query stored captures from the robot.

        Args:
            query (bosdyn.api.QueryParameters) : Query parameters.
        Raises:
            RpcError: Problem communicating with the robot.
        """
        request = data_acquisition_store.QueryStoredCapturesRequest(query=query)
        self._apply_request_processors(request, copy_request=False)
        return self.call(self._stub.QueryStoredCaptures, request,
                         error_from_response=common_header_errors,
                         assemble_type=data_acquisition_store.QueryStoredCapturesResponse,
                         copy_request=False, **kwargs)

    def query_stored_captures_async(self, query=None, **kwargs):
        """Async version of the query_stored_captures() RPC."""
        request = data_acquisition_store.QueryStoredCapturesRequest(query=query)
        self._apply_request_processors(request, copy_request=False)
        return self.call_async_streaming(
            self._stub.QueryStoredCaptures, request, error_from_response=common_header_errors,
            assemble_type=data_acquisition_store.QueryStoredCapturesResponse, copy_request=False,
            **kwargs)

    def query_max_capture_id(self, **kwargs):
        """Query max capture id from the robot.
        Returns:
            QueryMaxCaptureIdResult, which has a max_capture_id uint64, corresponding to the
            greatest capture id on the robot.  Used for skipping DAQ synchronization
            on connect.
        """
        request = data_acquisition_store.QueryMaxCaptureIdRequest()
        return self.call(self._stub.QueryMaxCaptureId, request,
                         value_from_response=_get_max_capture_id,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def query_max_capture_id_async(self, **kwargs):
        """Async version of the query_max_capture_id() RPC."""
        request = data_acquisition_store.QueryMaxCaptureIdRequest()
        return self.call_async(self._stub.QueryMaxCaptureId, request,
                               value_from_response=_get_max_capture_id,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)


def _iterate_store_file(file, data_id, file_extension=None):
    """Iterator over file data and create multiple StoreStreamRequest

        Args:
            file (BufferedReader) : Reader to the file for arbitrary data to store.
            data_id (bosdyn.api.DataIdentifier) : Data identifier to use for storing this data.
            file_extension (string) : File extension to use for writing the data to a file.
        Returns:
            StoreStreamRequests iterates over these requests.
        """
    total_size = fstat(file.fileno()).st_size
    while True:
        chunk = file.read(DEFAULT_CHUNK_SIZE_BYTES)
        if not chunk:
            # No more data
            break
        data = data_chunk.DataChunk(data=chunk, total_size=total_size)
        request = data_acquisition_store.StoreStreamRequest(chunk=data, data_id=data_id,
                                                            file_extension=file_extension)
        yield request


def _iterate_data_chunks(data, data_id, file_extension=None):
    """Iterator over data and create multiple StoreDataRequest

        Args:
            data (bytes) : Arbitrary data to store.
            data_id (bosdyn.api.DataIdentifier) : Data identifier to use for storing this data.
            file_extension (string) : File extension to use for writing the data to a file.
        Returns:
            StoreDataRequests iterates over these requests.
        """
    total_size = len(data)
    for chunk in split_serialized(data, DEFAULT_CHUNK_SIZE_BYTES):
        chunk_data = data_chunk.DataChunk(data=chunk, total_size=total_size)
        request = data_acquisition_store.StoreStreamRequest(chunk=chunk_data, data_id=data_id,
                                                            file_extension=file_extension)
        yield request


def _get_action_ids(response):
    return response.action_ids


def _get_data_ids(response):
    return response.data_ids


def _get_image(response):
    return response.image


def _get_metadata(response):
    return response.metadata


def _get_max_capture_id(response):
    return response.max_capture_id
