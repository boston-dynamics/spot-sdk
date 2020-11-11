# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client for the data-service.

"""

from __future__ import print_function

from bosdyn.client.exceptions import Error
from bosdyn.client.common import BaseClient, common_header_errors
import bosdyn.api.data_index_pb2 as data_index_protos
import bosdyn.api.data_service_pb2_grpc as data_service


class InvalidArgument(Error):
    """A given argument could not be used."""


class DataServiceClient(BaseClient):
    """A client for adding to robot data buffer."""

    default_service_name = 'data-service'
    service_type = 'bosdyn.api.DataService'

    def __init__(self):
        super(DataServiceClient, self).__init__(data_service.DataServiceStub)
        self.log_tick_schemas = {}
        self._timesync_endpoint = None

    def update_from(self, other):
        super(DataServiceClient, self).update_from(other)

        # Grab a timesync endpoint if it is available.
        try:
            self._timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    def get_data_index(self, query, **kwargs):
        """Query for data index

        Args:
          query:  DataQuery

        Raises:
          RpcError: Problem communicating with the robot.
        """
        return self._do_get_data_index(self.call, query, **kwargs)

    def get_data_index_async(self, query, **kwargs):
        """Async version of get_data_index."""
        return self._do_get_data_index(self.call_async, query, **kwargs)

    def _do_get_data_index(self, func, query, **kwargs):
        """Internal get_data_index RPC stub call."""
        request = data_index_protos.GetDataIndexRequest(data_query=query)

        return func(self._stub.GetDataIndex, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def get_data_pages(self, time_range, **kwargs):
        return self._do_get_data_pages(self.call, time_range, **kwargs)

    def get_data_pages_async(self, time_range, **kwargs):
        return self._do_get_data_pages(self.call_async, time_range, **kwargs)

    def _do_get_data_pages(self, func, time_range, **kwargs):
        """Internal get_data_pages RPC stub call."""
        request = data_index_protos.GetDataPagesRequest(time_range=time_range)

        return func(self._stub.GetDataPages, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def delete_data_pages(self, time_range, page_ids, **kwargs):
        return self._do_delete_data_pages(self.call, time_range, page_ids, **kwargs)

    def delete_data_pages_async(self, time_range, page_ids, **kwargs):
        return self._do_delete_data_pages(self.call_async, time_range, page_ids, **kwargs)

    def _do_delete_data_pages(self, func, time_range, page_ids, **kwargs):
        """Internal delete_data_pages RPC stub call."""
        request = data_index_protos.DeleteDataPagesRequest(time_range=time_range, page_ids=page_ids)

        return func(self._stub.DeleteDataPages, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def get_events_comments(self, query, **kwargs):
        """Query for operator comments and events

        Args:
          query: EventsCommentsSpec

        Raises:
          RpcError: Problem communicating with the robot.
        """
        return self._do_get_events_comments(self.call, query, **kwargs)

    def get_events_comments_async(self, query, **kwargs):
        """Async version of get_data_index."""
        return self._do_get_events_comments(self.call_async, query, **kwargs)

    def _do_get_events_comments(self, func, query, **kwargs):
        """Internal get_data_index RPC stub call."""
        request = data_index_protos.GetEventsCommentsRequest(event_comment_request=query)

        return func(self._stub.GetEventsComments, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def get_data_buffer_status(self, get_blob_specs=False, **kwargs):
        """Query for operator comments and events

        Args:
          get_blob_specs (bool): whether to list message series.

        Raises:
          RpcError: Problem communicating with the robot.
        """
        return self._do_get_data_buffer_status(self.call, get_blob_specs, **kwargs)

    def get_data_buffer_status_async(self, get_blob_specs=False, **kwargs):
        """Async version of get_data_index."""
        return self._do_get_data_buffer_status(self.call_async, get_blob_specs, **kwargs)

    def _do_get_data_buffer_status(self, func, get_blob_specs, **kwargs):
        """Internal get_data_buffer_status RPC stub call."""
        request = data_index_protos.GetDataBufferStatusRequest(get_blob_specs=get_blob_specs)
        return func(self._stub.GetDataBufferStatus, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)
