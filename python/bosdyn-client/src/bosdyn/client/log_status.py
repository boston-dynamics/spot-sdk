# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

# Boston Dynamics, Inc. Confidential Information.
# Copyright 2025. All Rights Reserved.
"""Client for the log-status service.

This allows client code to start, extend or terminate experiment logs and start retro logs.
"""

import collections

import bosdyn.util
from bosdyn.api.log_status import log_status_pb2 as log_status
from bosdyn.api.log_status import log_status_service_pb2_grpc as log_status_service
from bosdyn.client.common import (BaseClient, common_header_errors, error_factory, error_pair,
                                  handle_common_header_errors, handle_unset_status_error)
from bosdyn.client.exceptions import ResponseError


class LogStatusResponseError(ResponseError):
    """Error in Log Status RPC"""


class ExperimentAlreadyRunningError(LogStatusResponseError):
    """The log status request could not be started, an experiment is already running."""


class RequestIdDoesNotExistError(LogStatusResponseError):
    """The provided request id does not exist or is invalid."""


class InactiveLogError(LogStatusResponseError):
    """The log has already terminated and cannot be updated."""


class ConcurrencyLimitReachedError(LogStatusResponseError):
    """The limit of concurrent retro logs has be reached, a new log cannot be started."""


class LogStatusClient(BaseClient):
    """A client for interacting with robot logs."""
    # Typical name of the service in the robot's directory listing.
    default_service_name = 'log-status'
    # gRPC service proto definition implemented by this service
    service_type = 'bosdyn.api.log_status.LogStatusService'

    def __init__(self):
        super(LogStatusClient, self) \
            .__init__(log_status_service.LogStatusServiceStub)

    def get_log_status(self, id, **kwargs):
        """Synchronously get status of a log.

        Args:
            id (string): Id of log to retrieve

        Raises:
            RequestIdDoesNotExistError: Id was not found on robot
        """
        req = log_status.GetLogStatusRequest()
        req.id = id
        return self.call(self._stub.GetLogStatus, req, error_from_response=get_log_status_error,
                         copy_request=False, **kwargs)

    def get_log_status_async(self, id, **kwargs):
        """Asynchronously get status of a log."""
        req = log_status.GetLogStatusRequest()
        req.id = id
        return self.call_async(self._stub.GetLogStatus, req,
                               error_from_response=get_log_status_error, copy_request=False,
                               **kwargs)

    def get_active_log_statuses(self, **kwargs):
        """Synchronously retrieve status of active logs."""
        req = log_status.GetActiveLogStatusesRequest()
        return self.call(self._stub.GetActiveLogStatuses, req,
                         error_from_response=get_active_log_statuses_error, copy_request=False,
                         **kwargs)

    def get_active_log_statuses_async(self, **kwargs):
        """Asynchronously retrieve status of active logs."""
        req = log_status.GetActiveLogStatusesRequest()
        return self.call_async(self._stub.GetActiveLogStatuses, req,
                               error_from_response=get_active_log_statuses_error,
                               copy_request=False, **kwargs)

    def start_experiment_log(self, seconds, **kwargs):
        """Start an experiment log, to run for a specified duration.

        Args:
            seconds: Number of seconds to gather data for the experiment log

        Raises:
            ExperimentAlreadyRunningError: Only 1 experiment log can be run at a time
        """
        req = log_status.StartExperimentLogRequest()
        req.keep_alive.CopyFrom(bosdyn.util.seconds_to_duration(seconds))
        return self.call(self._stub.StartExperimentLog, req,
                         error_from_response=start_experiment_log_error, copy_request=False,
                         **kwargs)

    def start_experiment_log_async(self, seconds, **kwargs):
        """Start an experiment log, to run for a specified duration."""
        req = log_status.StartExperimentLogRequest()
        req.keep_alive.CopyFrom(bosdyn.util.seconds_to_duration(seconds))
        return self.call_async(self._stub.StartExperimentLog, req,
                               error_from_response=start_experiment_log_error, copy_request=False,
                               **kwargs)

    def start_retro_log(self, seconds, **kwargs):
        """Start a retro log, to run for a specified duration.

        Args:
            seconds: Number of seconds to gather data for the retro log

        Raises:
            ExperimentAlreadyRunningError: Retro logs cannot be run while an experiment log is running

            ConcurrencyLimitReachedError: Maximum number of retro logs are already running, another cannot be started
        """
        req = log_status.StartRetroLogRequest()
        req.past_duration.CopyFrom(bosdyn.util.seconds_to_duration(-seconds))
        return self.call(self._stub.StartRetroLog, req, error_from_response=start_retro_log_error,
                         copy_request=False, **kwargs)

    def start_retro_log_async(self, seconds, **kwargs):
        """Start a retro log, to run for a specified duration."""
        req = log_status.StartRetroLogRequest()
        req.past_duration.CopyFrom(bosdyn.util.seconds_to_duration(-seconds))
        return self.call_async(self._stub.StartRetroLog, req,
                               error_from_response=start_retro_log_error, copy_request=False,
                               **kwargs)

    def update_experiment(self, id, seconds, **kwargs):
        """Update an experiment log to run for a specified duration.

        Args:
            id (string): Id of log to retrieve
            seconds (float): Number of seconds to gather data for the experiment log

        Raises:
            RequestIdDoesNotExistError: Id was not found on robot
            InactiveLogError: Cannot update log, it is already terminated
        """
        req = log_status.UpdateExperimentLogRequest()
        req.id = id
        req.keep_alive.CopyFrom(bosdyn.util.seconds_to_duration(seconds))
        return self.call(self._stub.UpdateExperimentLog, req,
                         error_from_response=update_experiment_log_error, copy_request=False,
                         **kwargs)

    def update_experiment_async(self, id, seconds, **kwargs):
        """Update an experiment log to run for a specified duration."""
        req = log_status.UpdateExperimentLogRequest()
        req.id = id
        req.keep_alive.CopyFrom(bosdyn.util.seconds_to_duration(seconds))
        return self.call_async(self._stub.UpdateExperimentLog, req,
                               error_from_response=update_experiment_log_error, copy_request=False,
                               **kwargs)

    def terminate_log(self, id, **kwargs):
        """Terminate an experiment log.

        Args:
            id (string): Id of log to terminate

        Raises:
            RequestIdDoesNotExistError: Id was not found on robot
        """
        req = log_status.TerminateLogRequest()
        req.id = id
        return self.call(self._stub.TerminateLog, req, error_from_response=terminate_log_error,
                         copy_request=False, **kwargs)

    def terminate_log_async(self, id, **kwargs):
        """Terminate an experiment log."""
        req = log_status.TerminateLogRequest()
        req.id = id
        return self.call_async(self._stub.TerminateLog, req,
                               error_from_response=terminate_log_error, copy_request=False,
                               **kwargs)



_GET_LOG_STATUS_STATUS_TO_ERROR = \
    collections.defaultdict(lambda: (LogStatusResponseError, None))
_GET_LOG_STATUS_STATUS_TO_ERROR.update({
    log_status.GetLogStatusResponse.STATUS_OK: (None, None),
    log_status.GetLogStatusResponse.STATUS_ID_NOT_FOUND: error_pair(RequestIdDoesNotExistError),
})

_GET_ACTIVE_LOG_STATUSES_STATUS_TO_ERROR = \
    collections.defaultdict(lambda: (LogStatusResponseError, None))
_GET_ACTIVE_LOG_STATUSES_STATUS_TO_ERROR.update({
    log_status.GetActiveLogStatusesResponse.STATUS_OK: (None, None),
})

_START_EXPERIMENT_LOG_STATUS_TO_ERROR = \
    collections.defaultdict(lambda: (LogStatusResponseError, None))
_START_EXPERIMENT_LOG_STATUS_TO_ERROR.update({
    log_status.StartExperimentLogResponse.STATUS_OK: (None, None),
    log_status.StartExperimentLogResponse.STATUS_EXPERIMENT_LOG_RUNNING:
        error_pair(ExperimentAlreadyRunningError),
})

_START_RETRO_LOG_STATUS_TO_ERROR = \
    collections.defaultdict(lambda: (LogStatusResponseError, None))
_START_RETRO_LOG_STATUS_TO_ERROR.update({
    log_status.StartRetroLogResponse.STATUS_OK: (None, None),
    log_status.StartRetroLogResponse.STATUS_EXPERIMENT_LOG_RUNNING:
        error_pair(ExperimentAlreadyRunningError),
    log_status.StartRetroLogResponse.STATUS_CONCURRENCY_LIMIT_REACHED:
        error_pair(ConcurrencyLimitReachedError),
})

_UPDATE_EXPERIMENT_LOG_STATUS_TO_ERROR = \
    collections.defaultdict(lambda: (LogStatusResponseError, None))
_UPDATE_EXPERIMENT_LOG_STATUS_TO_ERROR.update({
    log_status.UpdateExperimentLogResponse.STATUS_OK: (None, None),
    log_status.UpdateExperimentLogResponse.STATUS_ID_NOT_FOUND:
        error_pair(RequestIdDoesNotExistError),
    log_status.UpdateExperimentLogResponse.STATUS_LOG_TERMINATED:
        error_pair(InactiveLogError),
})

_TERMINATE_LOG_STATUS_TO_ERROR = \
    collections.defaultdict(lambda: (LogStatusResponseError, None))
_TERMINATE_LOG_STATUS_TO_ERROR.update({
    log_status.TerminateLogResponse.STATUS_OK: (None, None),
    log_status.TerminateLogResponse.STATUS_ID_NOT_FOUND: error_pair(RequestIdDoesNotExistError),
})



@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def get_log_status_error(response):
    """Return a custom exception based on the GetLogStatus response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=log_status.GetLogStatusResponse.Status.Name,
                         status_to_error=_GET_LOG_STATUS_STATUS_TO_ERROR)


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def get_active_log_statuses_error(response):
    """Return a custom exception based on the GetActiveLogStatuses response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=log_status.GetActiveLogStatusesResponse.Status.Name,
                         status_to_error=_GET_ACTIVE_LOG_STATUSES_STATUS_TO_ERROR)


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def start_experiment_log_error(response):
    """Return a custom exception based on the StartExperimentLog response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=log_status.StartExperimentLogResponse.Status.Name,
                         status_to_error=_START_EXPERIMENT_LOG_STATUS_TO_ERROR)


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def start_retro_log_error(response):
    """Return a custom exception based on the StartRetroLog response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=log_status.StartRetroLogResponse.Status.Name,
                         status_to_error=_START_RETRO_LOG_STATUS_TO_ERROR)


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def update_experiment_log_error(response):
    """Return a custom exception based on the UpdateExperimentLog response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=log_status.UpdateExperimentLogResponse.Status.Name,
                         status_to_error=_UPDATE_EXPERIMENT_LOG_STATUS_TO_ERROR)


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def terminate_log_error(response):
    """Return a custom exception based on the TerminateLog response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=log_status.TerminateLogResponse.Status.Name,
                         status_to_error=_TERMINATE_LOG_STATUS_TO_ERROR)


