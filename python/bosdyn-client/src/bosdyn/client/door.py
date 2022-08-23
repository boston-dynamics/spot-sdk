# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the door service."""

from bosdyn.api.spot import door_service_pb2_grpc
from bosdyn.client.common import (BaseClient, handle_common_header_errors,
                                  handle_lease_use_result_errors)

from .lease import add_lease_wallet_processors


class DoorClient(BaseClient):
    """Client for the door service."""
    default_service_name = 'door'

    service_type = 'bosdyn.api.spot.DoorService'

    def __init__(self):
        super(DoorClient, self).__init__(door_service_pb2_grpc.DoorServiceStub)

    def open_door(self, request, **kwargs):
        """Issue an open door command to the robot.

        Args:
            request (door_pb2.OpenDoorCommandRequest): The door command.

        Returns:
            The full OpenDoorCommandResponse message, which includes a command id for feedback.

        Raises:
            RpcError: Problem communicating with the robot.
            LeaseUseError: The lease for the request failed.
        """
        return self.call(self._stub.OpenDoor, request, None, _open_door_error_handler, **kwargs)

    def open_door_async(self, request, **kwargs):
        """Async version of open_door()."""
        return self.call_async(self._stub.OpenDoor, request, None, _open_door_error_handler,
                               **kwargs)

    def open_door_feedback(self, request, **kwargs):
        """Get feedback from the robot on a specific door command.

        Args:
            request (door_pb2.OpenDoorFeedbackRequest): The request for feedback of
                the door command.

        Returns:
            The full OpenDoorFeedbackResponse message.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        return self.call(self._stub.OpenDoorFeedback, request, None,
                         _open_door_feedback_error_handler, **kwargs)

    def open_door_feedback_async(self, request, **kwargs):
        """Async version of open_door_feedback()."""
        return self.call_async(self._stub.OpenDoorFeedback, request, None,
                               _open_door_feedback_error_handler, **kwargs)

    def update_from(self, other):
        """Update instance from another object.

        Args:
            other: The object where to copy from.
        """
        # The door service requires a lease.
        super(DoorClient, self).update_from(other)
        if self.lease_wallet:
            add_lease_wallet_processors(self, self.lease_wallet)


@handle_common_header_errors
@handle_lease_use_result_errors
def _open_door_error_handler(response):
    """Return a custom exception based on response, None if no error."""
    return None


@handle_common_header_errors
def _open_door_feedback_error_handler(response):
    """Return a custom exception based on response, None if no error."""
    return None
