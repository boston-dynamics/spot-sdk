# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client implementation for data acquisition store service.
"""

from __future__ import print_function

import functools
import collections
import json

from google.protobuf import json_format

from bosdyn.client.exceptions import Error, ResponseError
from bosdyn.client.common import (common_header_errors, error_factory,
                                  handle_common_header_errors, handle_unset_status_error,
                                  error_pair, BaseClient)
from bosdyn.api import data_acquisition_store_pb2 as data_acquisition_store
from bosdyn.api import data_acquisition_store_service_pb2_grpc as data_acquisition_store_service
from bosdyn.api import image_pb2

from bosdyn.util import now_timestamp


class DataAcquisitionStoreClient(BaseClient):
    """A client for triggering data acquision store methods."""

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
        """List capture actions that safisfy the query parameters.

        Args:
             query (bosdyn.api.DataQueryParams) : Query parameters.

        Returns:
             CaptureActionIds for the actions matching the query parameters.
        """

        request = data_acquisition_store.ListCaptureActionsRequest(query=query)
        return self.call(self._stub.ListCaptureActions, request,
                         value_from_response=_get_action_ids,
                         error_from_response=common_header_errors, **kwargs)

    def list_capture_actions_async(self, query, **kwargs):
        """Async version of the list_capture_actions() RPC."""
        request = data_acquisition_store.ListCaptureActionsRequest(query=query)
        return self.call_async(self._stub.ListCaptureActions, request,
                               value_from_response=_get_action_ids,
                               error_from_response=common_header_errors, **kwargs)


    def list_stored_images(self, query, **kwargs):
        """List images that safisfy the query parameters.

        Args:
             query (bosdyn.api.DataQueryParams) : Query parameters.

        Returns:
             DataIdentifiers for the images matching the query parameters.
        """

        request = data_acquisition_store.ListStoredImagesRequest(query=query)
        return self.call(self._stub.ListStoredImages, request, value_from_response=_get_data_ids,
                         error_from_response=common_header_errors, **kwargs)

    def list_stored_images_async(self, query, **kwargs):
        """Async version of the list_stored_images_actions() RPC."""
        request = data_acquisition_store.ListStoredImagesRequest(query=query)
        return self.call_async(self._stub.ListStoredImages, request,
                               value_from_response=_get_data_ids,
                               error_from_response=common_header_errors, **kwargs)


    def list_stored_metadata(self, query, **kwargs):
        """List metadata that safisfy the query parameters.

        Args:
             query (bosdyn.api.DataQueryParams) : Query parameters.

        Returns:
             DataIdentifiers for the metadata matching the query parameters.
        """

        request = data_acquisition_store.ListStoredMetadataRequest(query=query)
        return self.call(self._stub.ListStoredMetadata, request, value_from_response=_get_data_ids,
                         error_from_response=common_header_errors, **kwargs)

    def list_stored_metadata_async(self, query, **kwargs):
        """Async version of the list_stored_metadata() RPC."""
        request = data_acquisition_store.ListStoredMetadataRequest(query=query)
        return self.call_async(self._stub.ListStoredMetadata, request,
                               value_from_response=_get_data_ids,
                               error_from_response=common_header_errors, **kwargs)


    def list_stored_data(self, query, **kwargs):
        """List data that safisfy the query parameters.

        Args:
             query (bosdyn.api.DataQueryParams) : Query parameters.

        Returns:
             DataIdentifiers for the data matching the query parameters.
        """

        request = data_acquisition_store.ListStoredDataRequest(query=query)
        return self.call(self._stub.ListStoredData, request, value_from_response=_get_data_ids,
                         error_from_response=common_header_errors, **kwargs)

    def list_stored_data_async(self, query, **kwargs):
        """Async version of the list_stored_data() RPC."""
        request = data_acquisition_store.ListStoredDataRequest(query=query)
        return self.call_async(self._stub.ListStoredData, request,
                               value_from_response=_get_data_ids,
                               error_from_response=common_header_errors, **kwargs)


    def store_image(self, image, data_id, **kwargs):
        """Store image.

        Args:
            image (bosdyn.api.ImageCapture) : Image to store.
            data_id (bosdyn.api.DataIdentifier) : Data identifier to use for storing the image.

        Returns:
             StoreImageResponse response.
        """

        request = data_acquisition_store.StoreImageRequest(image=image, data_id=data_id)
        return self.call(self._stub.StoreImage, request,
                         error_from_response=common_header_errors, **kwargs)


    def store_image_async(self, image, data_id, **kwargs):
        """Async version of the store_image() RPC."""
        request = data_acquisition_store.StoreImageRequest(image=image, data_id=data_id)
        return self.call_async(self._stub.StoreImage, request,
                               error_from_response=common_header_errors, **kwargs)


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
                         error_from_response=common_header_errors, **kwargs)


    def store_metadata_async(self, associated_metadata, data_id, **kwargs):
        """Async version of the store_metadata() RPC."""
        request = data_acquisition_store.StoreMetadataRequest(metadata=associated_metadata,
            data_id=data_id)
        return self.call_async(self._stub.StoreMetadata, request,
                               error_from_response=common_header_errors, **kwargs)


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
        return self.call(self._stub.StoreData, request,
                         error_from_response=common_header_errors, **kwargs)


    def store_data_async(self, data, data_id, file_extension=None, **kwargs):
        """Async version of the store_data() RPC."""
        request = data_acquisition_store.StoreDataRequest(data=data, data_id=data_id,
            file_extension=file_extension)
        return self.call_async(self._stub.StoreData, request,
                               error_from_response=common_header_errors, **kwargs)


def _get_action_ids(response):
    return response.action_ids

def _get_data_ids(response):
    return response.data_ids

def _get_image(response):
    return response.image

def _get_metadata(response):
    return response.metadata
