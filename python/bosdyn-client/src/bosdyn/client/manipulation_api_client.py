# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Manipulation API service."""

from bosdyn.api import manipulation_api_service_pb2_grpc
from bosdyn.client.common import (BaseClient, handle_common_header_errors,
                                  handle_lease_use_result_errors)

from .lease import add_lease_wallet_processors


class ManipulationApiClient(BaseClient):
    """Client for the ManipulationAPI service."""
    default_service_name = 'manipulation'
    service_type = 'bosdyn.api.ManipulationApiService'

    def __init__(self):
        super(ManipulationApiClient,
              self).__init__(manipulation_api_service_pb2_grpc.ManipulationApiServiceStub)

    def update_from(self, other):
        """Update instance from another object.

        Args:
            other: The object where to copy from.
        """
        super(ManipulationApiClient, self).update_from(other)
        if self.lease_wallet:
            add_lease_wallet_processors(self, self.lease_wallet)

    def manipulation_api_command(self, manipulation_api_request, **kwargs):
        """Issue a manipulation api command to the robot.

        Args:
            manipulation_api_request (manipulation_api_pb2.ManipulationApiRequest): The command request
                for a manipulation task.

        Returns:
            The full ManipulationApiResponse message, which includes a command id for feedback.
        """
        return self.call(self._stub.ManipulationApi, manipulation_api_request,
                         error_from_response=_manipulation_api_command_error_from_response,
                         **kwargs)

    def manipulation_api_command_async(self, manipulation_api_request, **kwargs):
        """Async version of the manipulation_api_command()."""
        return self.call_async(self._stub.ManipulationApi, manipulation_api_request, **kwargs)

    def manipulation_api_feedback_command(self, manipulation_api_feedback_request, **kwargs):
        """Issue a manipulation api feedback request to the robot.

        Args:
            manipulation_api_feedback_request (manipulation_api_pb2.ManipulationApiFeedbackRequest): The
                request for feedback for a specific manipulation command.

        Returns:
            The full ManipulationApiFeedbackResponse message.
        """
        return self.call(self._stub.ManipulationApiFeedback, manipulation_api_feedback_request,
                         error_from_response=_manipulation_api_feedback_error_from_response,
                         **kwargs)

    def manipulation_api_feedback_command_async(self, manipulation_api_feedback_request, **kwargs):
        """Async version of the manipulation_api_feedback_command()."""
        return self.call_async(self._stub.ManipulationApiFeedback,
                               manipulation_api_feedback_request, **kwargs)

    def grasp_override_command(self, grasp_override_request, **kwargs):
        """Issue a grasp override command to the robot.

        Args:
            grasp_override_request (manipulation_api_pb2.ApiGraspOverrideRequest): The command request
                for a grasp override.

        Returns:
            An ApiGraspOverrideResponse message.
        """
        return self.call(self._stub.OverrideGrasp, grasp_override_request,
                         error_from_response=_grasp_override_command_error_from_response, **kwargs)

    def grasp_override_command_async(self, grasp_override_request, **kwargs):
        """Async version of the grasp_override_command()."""
        return self.call_async(self._stub.OverrideGrasp, grasp_override_request, **kwargs)


@handle_common_header_errors
@handle_lease_use_result_errors
def _manipulation_api_command_error_from_response(response):
    return None


@handle_common_header_errors
def _manipulation_api_feedback_error_from_response(response):
    return None


@handle_common_header_errors
def _grasp_override_command_error_from_response(response):
    return None