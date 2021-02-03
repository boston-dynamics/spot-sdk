# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A client for the docking service."""

import collections
import time

from bosdyn.api.docking import docking_pb2, docking_service_pb2_grpc
from bosdyn.client import lease
from bosdyn.client.common import (BaseClient, error_factory, handle_common_header_errors,
                                  handle_lease_use_result_errors, handle_unset_status_error)
from bosdyn.client.exceptions import ResponseError
from bosdyn.client.robot_command import CommandFailedError


class DockingClient(BaseClient):
    """A client for the docking service to help issue DockingCommand and get state.
    Clients are expected to issue a single DockingCommand and then periodically
    check the status of its execution.
    This service requires ownership over the robot, in the form of a lease and timesync.
    """
    default_service_name = 'docking'
    service_type = 'bosdyn.api.docking.DockingService'

    def __init__(self):
        super(DockingClient, self).__init__(docking_service_pb2_grpc.DockingServiceStub)

    def update_from(self, other):
        super(DockingClient, self).update_from(other)
        if self.lease_wallet:
            lease.add_lease_wallet_processors(self, self.lease_wallet)

    def docking_command(self, station_id, clock_identifier, end_time, prep_pose_behavior=None,
                        lease=None, **kwargs):
        """Issue a DockingCommandRequest to the robot.

        Args:
            station_id: The ID of the docking station to dock at.
            clock_identifier: Identifier provided by the time sync service.
            end_time: Expiry time of the command in robot time.
            prep_pose_behavior: [optional] How and if to use the pre-dock pose.
            lease: [optional] Leave empty to have the lease filled in by the LeaseWallet

        Returns:
            DockingCommand ID

        Raises:
            ResponseError: The command was unable to be completed. See error for details.
        """
        req = self._docking_command_request(lease, station_id, clock_identifier, end_time,
                                            prep_pose_behavior)
        return self.call(self._stub.DockingCommand, req, self._docking_id_from_response,
                         _docking_command_error_from_response, **kwargs)

    def docking_command_async(self, station_id, clock_identifier, end_time, prep_pose_behavior=None,
                              lease=None, **kwargs):
        """Async version of docking_command(). """
        req = self._docking_command_request(lease, station_id, clock_identifier, end_time,
                                            prep_pose_behavior)
        return self.call_async(self._stub.DockingCommand, req, self._docking_id_from_response,
                               _docking_command_error_from_response, **kwargs)


    def docking_command_feedback(self, command_id, **kwargs):
        """Check the status of a previously issued docking command.

        Args:
            command_id: The ID returned from a previous docking_command call.

        Returns:
            Status of type DockingCommandResponse.Status
        """
        req = self._docking_command_feedback_request(command_id)
        return self.call(self._stub.DockingCommandFeedback, req, self._docking_status_from_response,
                         _docking_feedback_error_from_response, **kwargs)

    def docking_command_feedback_async(self, command_id, **kwargs):
        """Async version of docking_command_feedback()."""
        req = self._docking_command_feedback_request(command_id)
        return self.call_async(self._stub.DockingCommandFeedback, req,
                               self._docking_status_from_response,
                               _docking_feedback_error_from_response, **kwargs)

    def get_docking_config(self, **kwargs):
        """Get the docking config stored on the robot.

        Returns:
            List of docking configs of type ConfigRange
        """
        req = docking_pb2.GetDockingConfigRequest()
        return self.call(self._stub.GetDockingConfig, req, self._docking_config_from_response,
                         _docking_get_config_error_from_response, **kwargs)

    def get_docking_config_async(self, **kwargs):
        """Async version of get_docking_config()."""
        req = docking_pb2.GetDockingConfigRequest()
        return self.call_async(self._stub.GetDockingConfig, req, self._docking_config_from_response,
                               _docking_get_config_error_from_response, **kwargs)

    def get_docking_state(self, **kwargs):
        """Get docking state from the robot.

        Returns:
            Robot dock state of type DockState
        """
        req = docking_pb2.GetDockingStateRequest()
        return self.call(self._stub.GetDockingState, req, self._docking_state_from_response,
                         _docking_get_state_error_from_response, **kwargs)

    def get_docking_state_async(self, **kwargs):
        """Async version of get_docking_state()."""
        req = docking_pb2.GetDockingStateRequest()
        return self.call_async(self._stub.GetDockingState, req, self._docking_state_from_response,
                               _docking_get_state_error_from_response, **kwargs)

    @staticmethod
    def _docking_command_request(lease, station_id, clock_identifier, end_time, prep_pose_behavior):
        return docking_pb2.DockingCommandRequest(lease=lease, docking_station_id=station_id,
                                                 clock_identifier=clock_identifier,
                                                 end_time=end_time,
                                                 prep_pose_behavior=prep_pose_behavior)

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


def blocking_dock_robot(robot, dock_id, num_retries=4):
    """Blocking helper that takes control of the robot and docks it.

    Args:
        robot: The instance of the robot to control.
        dock_id: The ID of the dock to dock at.
        num_retries: Optional, number of attempts.

    Returns:
        The number of retries required

    Raises:
        CommandFailedError: The robot was unable to be docked. See error for details.
    """
    docking_client = robot.ensure_client(DockingClient.default_service_name)

    attempt_number = 0
    docking_success = False

    # Try to dock the robot
    while attempt_number < num_retries and not docking_success:
        attempt_number += 1
        cmd_end_time = time.time() + 30  # expect to finish in 30 seconds
        cmd_timeout = cmd_end_time + 10  # client side buffer

        prep_pose = (docking_pb2.PREP_POSE_USE_POSE if
                     (attempt_number % 2) else docking_pb2.PREP_POSE_SKIP_POSE)

        cmd_id = docking_client.docking_command(
            dock_id, robot.time_sync.endpoint.clock_identifier,
            robot.time_sync.robot_timestamp_from_local_secs(cmd_end_time), prep_pose)

        while time.time() < cmd_timeout:
            status = docking_client.docking_command_feedback(cmd_id)
            if status == docking_pb2.DockingCommandFeedbackResponse.STATUS_IN_PROGRESS:
                # keep waiting/trying
                time.sleep(1)
            elif status == docking_pb2.DockingCommandFeedbackResponse.STATUS_DOCKED:
                docking_success = True
                break
            elif (status in [
                    docking_pb2.DockingCommandFeedbackResponse.STATUS_MISALIGNED,
                    docking_pb2.DockingCommandFeedbackResponse.STATUS_ERROR_COMMAND_TIMED_OUT,
            ]):
                # Retry
                break
            else:
                raise CommandFailedError(
                    "Docking Failed, status: '%s'" %
                    docking_pb2.DockingCommandFeedbackResponse.Status.Name(status))

    if docking_success:
        return attempt_number - 1

    # Try and put the robot in a safe position
    try:
        blocking_go_to_prep_pose(robot, dock_id)
    except CommandFailedError:
        pass

    # Raise error on original failure to dock
    raise CommandFailedError("Docking Failed, too many attempts")


def blocking_go_to_prep_pose(robot, dock_id, timeout=20):
    """Blocking helper that takes control of the robot and takes it to the prep pose only.

    Args:
        robot: The instance of the robot to control.
        dock_id: The ID of the dock to use.

    Returns:
        None

    Raises:
        CommandFailedError: The robot was unable to go to the prep pose. See error for details.
    """
    docking_client = robot.ensure_client(DockingClient.default_service_name)

    # Try and put the robot in a safe position
    cmd_end_time = time.time() + timeout
    cmd_timeout = cmd_end_time + 10  # client side buffer

    cmd_id = docking_client.docking_command(
        dock_id, robot.time_sync.endpoint.clock_identifier,
        robot.time_sync.robot_timestamp_from_local_secs(cmd_end_time),
        docking_pb2.PREP_POSE_ONLY_POSE)

    while time.time() < cmd_timeout:
        status = docking_client.docking_command_feedback(cmd_id)
        if status == docking_pb2.DockingCommandFeedbackResponse.STATUS_IN_PROGRESS:
            # keep waiting/trying
            time.sleep(1)
        elif status == docking_pb2.DockingCommandFeedbackResponse.STATUS_AT_PREP_POSE:
            return
        else:
            raise CommandFailedError("Failed to go to the prep pose, status: '%s'" %
                                     docking_pb2.DockingCommandFeedbackResponse.Status.Name(status))

    raise CommandFailedError("Error going to the prep pose, timeout exceeded.")


def blocking_undock(robot, timeout=20):
    """Blocking helper that undocks the robot from the currently docked dock.

    Args:
        robot: The instance of the robot to control.

    Returns:
        None

    Raises:
        CommandFailedError: The robot was unable to undock. See error for details.
    """
    docking_client = robot.ensure_client(DockingClient.default_service_name)

    # Try and put the robot in a safe position
    cmd_end_time = time.time() + timeout
    cmd_timeout = cmd_end_time + 10  # client side buffer

    cmd_id = docking_client.docking_command(
        0, robot.time_sync.endpoint.clock_identifier,
        robot.time_sync.robot_timestamp_from_local_secs(cmd_end_time), docking_pb2.PREP_POSE_UNDOCK)

    while time.time() < cmd_timeout:
        status = docking_client.docking_command_feedback(cmd_id)
        if status == docking_pb2.DockingCommandFeedbackResponse.STATUS_IN_PROGRESS:
            # keep waiting/trying
            time.sleep(1)
        elif status == docking_pb2.DockingCommandFeedbackResponse.STATUS_AT_PREP_POSE:
            return
        else:
            raise CommandFailedError("Failed to undock the robot, status: '%s'" %
                                     docking_pb2.DockingCommandFeedbackResponse.Status.Name(status))

    raise CommandFailedError("Error undocking the robot, timeout exceeded.")
