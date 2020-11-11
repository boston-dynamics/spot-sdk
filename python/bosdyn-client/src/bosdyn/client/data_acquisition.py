# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""General client implementation for the main, on-robot data-acquisition service."""

from __future__ import print_function

import functools
import collections
import json
import time

from google.protobuf import json_format

from bosdyn.client.exceptions import Error, ResponseError
from bosdyn.client.common import (common_header_errors, error_factory,
                                  handle_common_header_errors, handle_unset_status_error,
                                  error_pair, BaseClient)
from bosdyn.api import data_acquisition_pb2 as data_acquisition
from bosdyn.api import data_acquisition_service_pb2_grpc as data_acquisition_service

from bosdyn.util import now_timestamp


class DataAcquisitionResponseError(ResponseError):
    """Error in Data Acquisition RPC"""


class RequestIdDoesNotExistError(DataAcquisitionResponseError):
    """The provided request id does not exist or is invalid."""


class UnknownCaptureTypeError(DataAcquisitionResponseError):
    """The provided request contains unknown capture requests."""


class CancellationFailedError(DataAcquisitionResponseError):
    """The data acquisition request was unable to be cancelled."""


class DataAcquisitionClient(BaseClient):
    """A client for triggering data acquision and logging."""

    default_service_name = 'data-acquisition'
    service_type = 'bosdyn.api.DataAcquisitionService'

    def __init__(self):
        super(DataAcquisitionClient,
              self).__init__(data_acquisition_service.DataAcquisitionServiceStub)
        self._timesync_endpoint = None

    def update_from(self, other):
        super(DataAcquisitionClient, self).update_from(other)

        # Grab a timesync endpoint if it is available.
        try:
            self._timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    def acquire_data(self, acquisition_requests, action_name, group_name, data_timestamp=None,
                     metadata=None, **kwargs):
        """Trigger a data acquisition to save data and metadata to the data buffer.

        Args:
          acquisition_requests (bosdyn.api.AcquisitionRequestList): The different image sources and
                data sources to capture from and save to the data buffer with the same timestamp.
          action_name(string): The unique action name that all data will be saved with.
          group_name(string): The unique group name that all data will be saved with.
          data_timestamp (google.protobuf.Timestamp): The unique timestamp that all data will be
                saved with.
          metadata (bosdyn.api.Metadata | dict): The JSON structured metadata to be associated with
                the data returned by the DataAcquisitionService when logged in the data buffer
                service.

        Raises:
          RpcError: Problem communicating with the robot.

        Returns:
            If the RPC is successful, then it will return the acquire data request id, which can be
            used to check the status of the acquisition and get feedback.
        """

        if data_timestamp is None:
            if not self._timesync_endpoint:
                data_timestamp = now_timestamp()
            else:
                data_timestamp = self._timesync_endpoint.robot_timestamp_from_local_secs(
                    time.time())
        action_id = data_acquisition.CaptureActionId(action_name=action_name,
            group_name=group_name, timestamp=data_timestamp)

        metadata_proto = metadata_to_proto(metadata)
        request = data_acquisition.AcquireDataRequest(metadata=metadata_proto,
                                                      acquisition_requests=acquisition_requests,
                                                      action_id=action_id)
        return self.call(self._stub.AcquireData, request, value_from_response=get_request_id,
                         error_from_response=acquire_data_error, **kwargs)

    def acquire_data_async(self, acquisition_requests, action_name, group_name,
                           data_timestamp=None, metadata=None, **kwargs):
        """Async version of the acquire_data() RPC."""
        if data_timestamp is None:
            if not self._timesync_endpoint:
                data_timestamp = now_timestamp()
            else:
                data_timestamp = self._timesync_endpoint.robot_timestamp_from_local_secs(
                    time.time())
        action_id = data_acquisition.CaptureActionId(action_name=action_name,
            group_name=group_name, timestamp=data_timestamp)

        metadata_proto = metadata_to_proto(metadata)
        request = data_acquisition.AcquireDataRequest(metadata=metadata_proto,
                                                      acquisition_requests=acquisition_requests,
                                                      action_id=action_id)
        return self.call_async(self._stub.AcquireData, request,
                               value_from_response=get_request_id,
                               error_from_response=acquire_data_error, **kwargs)

    def get_status(self, request_id, **kwargs):
        """Check the status of a data acquisition based on the request id.

        Args:
          request_id (int): The request id associated with an AcquireData request.

        Raises:
          RpcError: Problem communicating with the robot.
          RequestIdDoesNotExistError: The request id provided is incorrect.

        Returns:
            If the RPC is successful, then it will return the full status response, which includes the
            status as well as other information about any possible errors.
        """
        request = data_acquisition.GetStatusRequest(request_id=request_id)
        return self.call(self._stub.GetStatus, request, error_from_response=_get_status_error,
                         **kwargs)

    def get_status_async(self, request_id, **kwargs):
        """Async version of the get_status() RPC."""
        request = data_acquisition.GetStatusRequest(request_id=request_id)
        return self.call_async(self._stub.GetStatus, request,
                               error_from_response=_get_status_error, **kwargs)

    def get_service_info(self, **kwargs):
        """Get information from a DAQ service to list it's capabilities - which data, metadata,
        or processing the DAQ service will perform.

        Raises:
          RpcError: Problem communicating with the robot.

        Returns:
            The GetServiceInfoResponse message, which contains all the different capabilites.
        """
        request = data_acquisition.GetServiceInfoRequest()
        return self.call(self._stub.GetServiceInfo, request,
                         value_from_response=_get_service_info_capabilities,
                         error_from_response=common_header_errors, **kwargs)

    def get_service_info_async(self, **kwargs):
        """Async version of the get_service_info() RPC."""
        request = data_acquisition.GetServiceInfoRequest()
        return self.call_async(self._stub.GetServiceInfo, request,
                               value_from_response=_get_service_info_capabilities,
                               error_from_response=common_header_errors, **kwargs)

    def cancel_acquisition(self, request_id, **kwargs):
        """Cancel a data acquisition based on the request id.
        Args:
          request_id (int): The request id associated with an AcquireData request.
        Raises:
          RpcError: Problem communicating with the robot.
          CancellationFailedError: The data acquisitions associated with the request id were unable
                                   to be cancelled.
          RequestIdDoesNotExistError: The request id provided is incorrect.
        Returns:
            If the RPC is successful, then it will return the full status response, which includes the
            status as well as other information about any possible errors.
        """
        request = data_acquisition.CancelAcquisitionRequest(request_id=request_id)
        return self.call(self._stub.CancelAcquisition, request, error_from_response=_cancel_acquisition_error,
                         **kwargs)

    def cancel_acquisition_async(self, request_id, **kwargs):
        """Async version of the cancel_acquisition() RPC."""
        request = data_acquisition.CancelAcquisitionRequest(request_id=request_id)
        return self.call_async(self._stub.CancelAcquisition, request,
                               error_from_response=_cancel_acquisition_error, **kwargs)


_ACQUIRE_DATA_STATUS_TO_ERROR = collections.defaultdict(
    lambda: (DataAcquisitionResponseError, None))

_ACQUIRE_DATA_STATUS_TO_ERROR.update({
    data_acquisition.AcquireDataResponse.STATUS_OK: (None, None),
    data_acquisition.AcquireDataResponse.STATUS_UNKNOWN_CAPTURE_TYPE:
        error_pair(UnknownCaptureTypeError)
})

_GET_STATUS_STATUS_TO_ERROR = collections.defaultdict(lambda: (None, None))
_GET_STATUS_STATUS_TO_ERROR.update({
    data_acquisition.GetStatusResponse.STATUS_REQUEST_ID_DOES_NOT_EXIST:
        error_pair(RequestIdDoesNotExistError)
})

_CANCEL_ACQUISITION_STATUS_TO_ERROR = collections.defaultdict(lambda: (None, None))
_CANCEL_ACQUISITION_STATUS_TO_ERROR.update({
    data_acquisition.CancelAcquisitionResponse.STATUS_REQUEST_ID_DOES_NOT_EXIST:
        error_pair(RequestIdDoesNotExistError),
    data_acquisition.CancelAcquisitionResponse.STATUS_FAILED_TO_CANCEL:
        error_pair(CancellationFailedError)
})

def metadata_to_proto(metadata):
    """Checks the type to determine if a conversion is required to create a
    bosdyn.api.Metadata proto message.

    Args:
        metadata (bosdyn.api.Metadata or dict): The JSON structured metadata to be associated
            with the data returned by the DataAcquisitionService when logged in the data buffer
            service.

    Returns:
        If metadata is provided, this will return a protobuf Metadata message. Otherwise it will
        return None.
    """
    metadata_proto = None
    if isinstance(metadata, data_acquisition.Metadata):
        metadata_proto = metadata
    elif isinstance(metadata, dict):
        metadata_proto = data_acquisition.Metadata()
        metadata_proto.data.update(metadata)
    return metadata_proto


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def acquire_data_error(response):
    """Return a custom exception based on the AcquireData response, None if no error."""
    return error_factory(response, response.status,
                        status_to_string=data_acquisition.AcquireDataResponse.Status.Name,
                        status_to_error=_ACQUIRE_DATA_STATUS_TO_ERROR)


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _get_status_error(response):
    """Return a custom exception based on the GetStatus response, None if no error."""
    return error_factory(response, response.status,
                        status_to_string=data_acquisition.GetStatusResponse.Status.Name,
                        status_to_error=_GET_STATUS_STATUS_TO_ERROR)

@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _cancel_acquisition_error(response):
    """Return a custom exception based on the CancelAcquisition response, None if no error."""
    return error_factory(response, response.status,
                        status_to_string=data_acquisition.CancelAcquisitionResponse.Status.Name,
                        status_to_error=_CANCEL_ACQUISITION_STATUS_TO_ERROR)

def _get_service_info_capabilities(response):
    return response.capabilities

def get_request_id(response):
    return response.request_id
