# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""General client implementation for the main, on-robot data-acquisition service."""

import collections
import functools
import json
import time

from google.protobuf import json_format

from bosdyn.api import data_acquisition_pb2 as data_acquisition
from bosdyn.api import data_acquisition_service_pb2_grpc as data_acquisition_service
from bosdyn.client.common import (BaseClient, common_header_errors, custom_params_error,
                                  error_factory, error_pair, handle_common_header_errors,
                                  handle_custom_params_errors, handle_unset_status_error)
from bosdyn.client.exceptions import Error, InternalServerError, ResponseError
from bosdyn.util import now_nsec, now_sec, now_timestamp, seconds_to_duration


class DataAcquisitionResponseError(ResponseError):
    """Error in Data Acquisition RPC"""


class RequestIdDoesNotExistError(DataAcquisitionResponseError):
    """The provided request id does not exist or is invalid."""


class UnknownCaptureTypeError(DataAcquisitionResponseError):
    """The provided request contains unknown capture requests."""


class CancellationFailedError(DataAcquisitionResponseError):
    """The data acquisition request was unable to be cancelled."""


class DataAcquisitionClient(BaseClient):
    """A client for triggering data acquisition and logging."""

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

    def make_acquire_data_request(self, acquisition_requests, action_name, group_name,
                                  data_timestamp=None, metadata=None, min_timeout=None):
        """Helper utility to generate an AcquireDataRequest."""
        if data_timestamp is None:
            if not self._timesync_endpoint:
                data_timestamp = now_timestamp()
            else:
                data_timestamp = self._timesync_endpoint.robot_timestamp_from_local_secs(now_sec())
        action_id = data_acquisition.CaptureActionId(action_name=action_name, group_name=group_name,
                                                     timestamp=data_timestamp)
        req = data_acquisition.AcquireDataRequest(acquisition_requests=acquisition_requests,
                                                  action_id=action_id,
                                                  metadata=metadata_to_proto(metadata))
        if min_timeout:
            req.min_timeout.CopyFrom(seconds_to_duration(min_timeout))
        return req

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
          ValueError: Metadata is not in the right format.

        Returns:
            If the RPC is successful, then it will return the acquire data request id, which can be
            used to check the status of the acquisition and get feedback.
        """
        request = self.make_acquire_data_request(acquisition_requests, action_name, group_name,
                                                 data_timestamp, metadata)
        return self.call(self._stub.AcquireData, request, value_from_response=get_request_id,
                         error_from_response=acquire_data_error, copy_request=False, **kwargs)

    def acquire_data_async(self, acquisition_requests, action_name, group_name, data_timestamp=None,
                           metadata=None, **kwargs):
        """Async version of the acquire_data() RPC."""
        request = self.make_acquire_data_request(acquisition_requests, action_name, group_name,
                                                 data_timestamp, metadata)
        return self.call_async(self._stub.AcquireData, request, value_from_response=get_request_id,
                               error_from_response=acquire_data_error, copy_request=False, **kwargs)

    def acquire_data_from_request(self, request, **kwargs):
        """Alternate version of acquire_data() that takes an AcquireDataRequest directly.

        Returns:
            If the RPC is successful, then it will return the AcquireDataResponse.
        """
        return self.call(self._stub.AcquireData, request, error_from_response=acquire_data_error,
                         **kwargs)

    def acquire_data_from_request_async(self, request, **kwargs):
        """Async version of acquire_data_from_request()."""
        return self.call_async(self._stub.AcquireData, request,
                               error_from_response=acquire_data_error, **kwargs)

    def get_status(self, request_id, **kwargs):
        """Check the status of a data acquisition based on the request id.

        Args:
          request_id (int): The request id associated with an AcquireData request.

        Raises:
          RpcError: Problem communicating with the robot.
          bosdyn.client.data_acquisition.RequestIdDoesNotExistError: The request id provided is incorrect.

        Returns:
            If the RPC is successful, then it will return the full status response, which includes the
            status as well as other information about any possible errors.
        """
        request = data_acquisition.GetStatusRequest(request_id=request_id)
        return self.call(self._stub.GetStatus, request, error_from_response=_get_status_error,
                         copy_request=False, **kwargs)

    def get_status_async(self, request_id, **kwargs):
        """Async version of the get_status() RPC."""
        request = data_acquisition.GetStatusRequest(request_id=request_id)
        return self.call_async(self._stub.GetStatus, request, error_from_response=_get_status_error,
                               copy_request=False, **kwargs)

    def get_service_info(self, **kwargs):
        """Get information from a Data Acquisition service to list its capabilities - which data,
        metadata,or processing the Data Acquisition service will perform.

        Raises:
          RpcError: Problem communicating with the robot.

        Returns:
            The GetServiceInfoResponse message, which contains all the different capabilities.
        """
        request = data_acquisition.GetServiceInfoRequest()
        return self.call(self._stub.GetServiceInfo, request,
                         value_from_response=_get_service_info_capabilities,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def get_service_info_async(self, **kwargs):
        """Async version of the get_service_info() RPC."""
        request = data_acquisition.GetServiceInfoRequest()
        return self.call_async(self._stub.GetServiceInfo, request,
                               value_from_response=_get_service_info_capabilities,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def cancel_acquisition(self, request_id, **kwargs):
        """Cancel a data acquisition based on the request id.

        Args:
          request_id (int): The request id associated with an AcquireData request.
        Raises:
          RpcError: Problem communicating with the robot.
          CancellationFailedError: The data acquisitions associated with the request id were unable
                                   to be cancelled.
          bosdyn.client.data_acquisition.RequestIdDoesNotExistError: The request id provided is incorrect.
        Returns:
            If the RPC is successful, then it will return the full status response, which includes the
            status as well as other information about any possible errors.
        """
        request = data_acquisition.CancelAcquisitionRequest(request_id=request_id)
        return self.call(self._stub.CancelAcquisition, request,
                         error_from_response=_cancel_acquisition_error, copy_request=False,
                         **kwargs)

    def cancel_acquisition_async(self, request_id, **kwargs):
        """Async version of the cancel_acquisition() RPC."""
        request = data_acquisition.CancelAcquisitionRequest(request_id=request_id)
        return self.call_async(self._stub.CancelAcquisition, request,
                               error_from_response=_cancel_acquisition_error, copy_request=False,
                               **kwargs)

    def get_live_data(self, request):
        """Call the GetLiveData RPC of the plugin service."""
        return self.call(self._stub.GetLiveData, request, error_from_response=_get_live_data_error,
                         copy_request=True)

    def get_live_data_async(self, request):
        """Async version of the get_live_data() RPC."""
        return self.call_async(self._stub.GetLiveData, request,
                               error_from_response=_get_live_data_error, copy_request=True)


_ACQUIRE_DATA_STATUS_TO_ERROR = collections.defaultdict(lambda:
                                                        (DataAcquisitionResponseError, None))

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

_CAPABILITY_LIVE_DATA_STATUS_TO_ERROR = collections.defaultdict(lambda: (None, None))
_CAPABILITY_LIVE_DATA_STATUS_TO_ERROR.update({
    # STATUS_UNKNOWN is not handled directly.
    data_acquisition.LiveDataResponse.CapabilityLiveData.STATUS_OK: (None, None),
    data_acquisition.LiveDataResponse.CapabilityLiveData.STATUS_UNKNOWN_CAPTURE_TYPE:
        error_pair(UnknownCaptureTypeError),
    # STATUS_CUSTOM_PARAMS_ERROR is handled separately.
    data_acquisition.LiveDataResponse.CapabilityLiveData.STATUS_INTERNAL_ERROR:
        error_pair(InternalServerError),
})


def metadata_to_proto(metadata):
    """Checks the type to determine if a conversion is required to create a
    bosdyn.api.Metadata proto message.

    Args:
        metadata (bosdyn.api.Metadata or dict): The JSON structured metadata to be associated
            with the data returned by the DataAcquisitionService when logged in the data buffer
            service.

    Raises:
        ValueError: Metadata is not in the right format.

    Returns:
        If metadata is provided, this will return a protobuf Metadata message. Otherwise it will
        return None.
    """
    if metadata is None:
        return None
    metadata_proto = None
    if isinstance(metadata, data_acquisition.Metadata):
        metadata_proto = metadata
    elif isinstance(metadata, dict):
        metadata_proto = data_acquisition.Metadata()
        metadata_proto.data.update(metadata)
    else:
        raise ValueError('Invalid metadata, not a dict or data_acquisition.Metadata')
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


@handle_common_header_errors
def _get_live_data_error(response):
    """Return a custom exception based on the first invalid CapabilityLiveData, None if no error."""
    for capability_live_data in response.live_data:
        result = custom_params_error(capability_live_data, total_response=response)
        if result is not None:
            return result

        result = error_factory(
            response, capability_live_data.status,
            status_to_string=data_acquisition.LiveDataResponse.CapabilityLiveData.Status.Name,
            status_to_error=_CAPABILITY_LIVE_DATA_STATUS_TO_ERROR)
        if result is not None:
            # The exception is using the capability_live_data. Replace it with the full response.
            result.response = response
            return result
    return None


def _get_service_info_capabilities(response):
    return response.capabilities


def get_request_id(response):
    return response.request_id
