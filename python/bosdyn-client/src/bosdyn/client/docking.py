# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the docking command service."""

import collections

from bosdyn.api.docking import docking_pb2, docking_service_pb2_grpc
from bosdyn.client import lease
from bosdyn.client.common import (BaseClient, error_factory, handle_common_header_errors,
                                  handle_lease_use_result_errors, handle_unset_status_error)
from bosdyn.client.exceptions import ResponseError


class DockingClient(BaseClient):
    """A client docking the robot.
    Clients are expected to issue a docking command and then periodically
    check the status of this command.
    This service requires ownership over the robot, in the form of a lease.
    """
    default_service_name = 'docking'
    service_type = 'bosdyn.api.docking.DockingService'

    def __init__(self):
        super(DockingClient, self).__init__(docking_service_pb2_grpc.DockingServiceStub)

    def update_from(self, other):
        super(DockingClient, self).update_from(other)
        if self.lease_wallet:
            lease.add_lease_wallet_processors(self, self.lease_wallet)

    def docking_command(self, station_id, clock_identifier, end_time, lease=None, **kwargs):
        """Issue a docking request to the robot."""
        req = self._docking_command_request(lease, station_id, clock_identifier, end_time)
        return self.call(self._stub.DockingCommand, req, self._docking_id_from_response,
                         _docking_command_error_from_response, **kwargs)

    def docking_command_async(self, station_id, clock_identifier, end_time, lease=None, **kwargs):
        """Async version of docking_command()."""
        req = self._docking_command_request(lease, station_id, clock_identifier, end_time)
        return self.call_async(self._stub.DockingCommand, req, self._docking_id_from_response,
                               _docking_command_error_from_response, **kwargs)


    def docking_command_feedback(self, command_id, **kwargs):
        """Check the status of a previously issued docking command."""
        req = self._docking_command_feedback_request(command_id)
        return self.call(self._stub.DockingCommandFeedback, req, self._docking_status_from_response,
                         _docking_feedback_error_from_response, **kwargs)

    def docking_command_feedback_async(self, command_id, **kwargs):
        """Async version of docking_command_feedback()"""
        req = self._docking_command_feedback_request(command_id)
        return self.call_async(self._stub.DockingCommandFeedback, req,
                               self._docking_status_from_response,
                               _docking_feedback_error_from_response, **kwargs)

    def get_docking_config(self, **kwargs):
        """Issue a docking config request to the robot."""
        req = docking_pb2.GetDockingConfigRequest()
        return self.call(self._stub.GetDockingConfig, req, self._docking_config_from_response,
                         _docking_get_config_error_from_response, **kwargs)

    def get_docking_config_async(self, **kwargs):
        """Issue a docking config request to the robot."""
        req = docking_pb2.GetDockingConfigRequest()
        return self.call_async(self._stub.GetDockingConfig, req, self._docking_config_from_response,
                               _docking_get_config_error_from_response, **kwargs)

    def get_docking_state(self, **kwargs):
        """Get docking state from the robot."""
        req = docking_pb2.GetDockingStateRequest()
        return self.call(self._stub.GetDockingState, req, self._docking_state_from_response,
                         _docking_get_state_error_from_response, **kwargs)

    def get_docking_state_async(self, **kwargs):
        """Get docking state from the robot."""
        req = docking_pb2.GetDockingStateRequest()
        return self.call_async(self._stub.GetDockingState, req, self._docking_state_from_response,
                               _docking_get_state_error_from_response, **kwargs)

    @staticmethod
    def _docking_command_request(lease, station_id, clock_identifier, end_time):
        return docking_pb2.DockingCommandRequest(lease=lease, docking_station_id=station_id,
                                                 clock_identifier=clock_identifier,
                                                 end_time=end_time)

    @staticmethod
    def _docking_command_feedback_request(command_id):
        return docking_pb2.DockingCommandFeedbackRequest(docking_command_id=command_id)

    @staticmethod
    def _docking_id_from_response(response):
        return response.docking_command_id

    @staticmethod
    def _docking_status_from_response(response):
        return response.status

    @staticmethod
    def _docking_config_from_response(response):
        return response.dock_configs

    @staticmethod
    def _docking_state_from_response(response):
        return response.dock_state


_DOCKING_COMMAND_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_DOCKING_COMMAND_STATUS_TO_ERROR.update(
    {docking_pb2.DockingCommandResponse.STATUS_OK: (None, None)})


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _docking_command_error_from_response(response):
    """Return an exception based on response from DockingCommand RPC, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=docking_pb2.DockingCommandResponse.Status.Name,
                         status_to_error=_DOCKING_COMMAND_STATUS_TO_ERROR)


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _docking_feedback_error_from_response(response):
    """Return an exception based on response from DockingCommandFeedback RPC, None if no error."""
    return None


@handle_common_header_errors
def _docking_get_config_error_from_response(response):
    """Return an exception based on response from GetDockingConfig RPC, None if no error."""
    return None


@handle_common_header_errors
def _docking_get_state_error_from_response(response):
    """Return an exception based on response from GetDockingState RPC, None if no error."""
    return None
