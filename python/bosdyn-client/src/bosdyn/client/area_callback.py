# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import collections

from bosdyn.api.graph_nav import area_callback_pb2, area_callback_service_pb2_grpc
from bosdyn.client.common import (BaseClient, common_header_errors, error_factory, error_pair,
                                  handle_common_header_errors, handle_lease_use_result_errors,
                                  handle_unset_status_error)
from bosdyn.client.exceptions import LeaseUseError, ResponseError


class AreaCallbackClient(BaseClient):
    service_type = 'bosdyn.api.graph_nav.AreaCallbackService'
    default_service_name = None

    def __init__(self):
        super(AreaCallbackClient,
              self).__init__(area_callback_service_pb2_grpc.AreaCallbackServiceStub)

    def area_callback_information(self, request=None, **kwargs):
        request = request or area_callback_pb2.AreaCallbackInformationRequest()
        return self.call(self._stub.AreaCallbackInformation, request, value_from_response=None,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def begin_callback(self, request, **kwargs):
        return self.call(self._stub.BeginCallback, request, value_from_response=None,
                         error_from_response=_begin_callback_error, copy_request=False, **kwargs)

    def begin_control(self, request, **kwargs):
        return self.call(self._stub.BeginControl, request, value_from_response=None,
                         error_from_response=_begin_control_error, copy_request=False, **kwargs)

    def update_callback(self, request, **kwargs):
        return self.call(self._stub.UpdateCallback, request, value_from_response=None,
                         error_from_response=_update_callback_error, copy_request=False, **kwargs)

    def end_callback(self, request, **kwargs):
        return self.call(self._stub.EndCallback, request, value_from_response=None,
                         error_from_response=_end_callback_error, copy_request=False, **kwargs)


class AreaCallbackResponseError(ResponseError):
    """General class of errors for AreaCallback service."""


class InvalidCommandIdError(AreaCallbackResponseError):
    """Provided command id does not match the current command id."""


class InvalidConfigError(AreaCallbackResponseError):
    """The provided configuration does not provide the necessary data."""


class ExpiredEndTimeError(AreaCallbackResponseError):
    """The provided end time has already expired."""


class MissingLeaseResourcesError(AreaCallbackResponseError):
    """A required lease resource was not provided."""


class ShutdownCallbackFailedError(AreaCallbackResponseError):
    """The callback failed to shut down properly."""


# yapf: disable
_BEGIN_CALLBACK_TO_ERROR = collections.defaultdict(
    lambda: (AreaCallbackResponseError, None))
_BEGIN_CALLBACK_TO_ERROR.update({
    area_callback_pb2.BeginCallbackResponse.STATUS_OK: (None, None),
    area_callback_pb2.BeginCallbackResponse.STATUS_INVALID_CONFIGURATION: error_pair(InvalidConfigError),
    area_callback_pb2.BeginCallbackResponse.STATUS_EXPIRED_END_TIME: error_pair(ExpiredEndTimeError),
})

@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _begin_callback_error(response):
    return error_factory(response, response.status,
                         status_to_string=area_callback_pb2.BeginCallbackResponse.Status.Name,
                         status_to_error=_BEGIN_CALLBACK_TO_ERROR)

_BEGIN_CONTROL_TO_ERROR = collections.defaultdict(
    lambda: (AreaCallbackResponseError, None))
_BEGIN_CONTROL_TO_ERROR.update({
    area_callback_pb2.BeginControlResponse.STATUS_OK: (None, None),
    area_callback_pb2.BeginControlResponse.STATUS_INVALID_COMMAND_ID: error_pair(InvalidCommandIdError),
    area_callback_pb2.BeginControlResponse.STATUS_MISSING_LEASE_RESOURCES: error_pair(MissingLeaseResourcesError),
    # This one generally shouldn't happen because it should get first caught
    # by @handle_lease_use_result_errors
    area_callback_pb2.BeginControlResponse.STATUS_LEASE_ERROR: error_pair(LeaseUseError),
})

@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _begin_control_error(response):
    return error_factory(response, response.status,
                         status_to_string=area_callback_pb2.BeginControlResponse.Status.Name,
                         status_to_error=_BEGIN_CONTROL_TO_ERROR)

_UPDATE_CALLBACK_TO_ERROR = collections.defaultdict(
    lambda: (AreaCallbackResponseError, None))
_UPDATE_CALLBACK_TO_ERROR.update({
    area_callback_pb2.UpdateCallbackResponse.STATUS_OK: (None, None),
    area_callback_pb2.UpdateCallbackResponse.STATUS_INVALID_COMMAND_ID: error_pair(InvalidCommandIdError),
    area_callback_pb2.UpdateCallbackResponse.STATUS_EXPIRED_END_TIME: error_pair(ExpiredEndTimeError),
})

@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _update_callback_error(response):
    return error_factory(response, response.status,
                         status_to_string=area_callback_pb2.UpdateCallbackResponse.Status.Name,
                         status_to_error=_UPDATE_CALLBACK_TO_ERROR)


_END_CALLBACK_TO_ERROR = collections.defaultdict(
    lambda: (AreaCallbackResponseError, None))
_END_CALLBACK_TO_ERROR.update({
    area_callback_pb2.EndCallbackResponse.STATUS_OK: (None, None),
    area_callback_pb2.EndCallbackResponse.STATUS_INVALID_COMMAND_ID: error_pair(InvalidCommandIdError),
    area_callback_pb2.EndCallbackResponse.STATUS_SHUTDOWN_CALLBACK_FAILED: error_pair(ShutdownCallbackFailedError),
})

@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _end_callback_error(response):
    return error_factory(response, response.status,
                         status_to_string=area_callback_pb2.EndCallbackResponse.Status.Name,
                         status_to_error=_END_CALLBACK_TO_ERROR)
# yapf: enable
