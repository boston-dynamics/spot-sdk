# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client implementation for data acquisition store service.
"""

import collections
import functools
import json

from google.protobuf import json_format

from bosdyn.api import data_acquisition_store_pb2 as data_acquisition_store
from bosdyn.api import data_acquisition_store_service_pb2_grpc as data_acquisition_store_service
from bosdyn.api import image_pb2
from bosdyn.client import data_chunk
from bosdyn.client.common import (BaseClient, common_header_errors, error_factory, error_pair,
                                  handle_common_header_errors, handle_unset_status_error)
from bosdyn.client.exceptions import Error, ResponseError
from bosdyn.util import now_timestamp


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

    def query_stored_captures(self, query=None, **kwargs):
        """Query stored captures from the robot.

        Args:
            query (bosdyn.api.DataQueryParams) : Query parameters.
        Raises:
            RpcError: Problem communicating with the robot.
        """
        request = data_acquisition_store.QueryStoredCapturesRequest(query=query)
        self._apply_request_processors(request, copy_request=False)
        return self.call(self._stub.QueryStoredCaptures, request,
                         error_from_response=common_header_errors,
                         assemble_type=data_acquisition_store.QueryStoredCapturesResponse,
                         copy_request=False, **kwargs)

    def query_max_capture_id(self, **kwargs):
        """Query max capture id from the robot.
        Returns:
            QueryMaxCaptureIdResult, which has a max_capture_id uint64, corresponding to the 
            greatest capture id on the robot.  Used for skiping DAQ synchronization
            on connect.
        """
        request = data_acquisition_store.QueryMaxCaptureIdRequest()
        return self.call(self._stub.QueryMaxCaptureId, request,
                         value_from_response=_get_max_capture_id,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def query_max_capture_id_async(self, **kwargs):
        """Async version of the query_max_capture_id() RPC."""
        request = data_acquisition_store.QueryMaxCaptureIdRequest(query=query)
        return self.call_async(self._stub.QueryMaxCaptureId, request,
                               value_from_response=_get_max_capture_id,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)


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
