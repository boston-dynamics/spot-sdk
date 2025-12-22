# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to use the hazard_avoidance service"""

import collections

from bosdyn.api import hazard_avoidance_pb2
from bosdyn.api import hazard_avoidance_service_pb2_grpc as hazard_avoidance_service
from bosdyn.client.common import (BaseClient, custom_params_error, error_factory, error_pair,
                                  handle_common_header_errors)
from bosdyn.client.exceptions import InvalidRequestError, ResponseError, UnsetStatusError
from bosdyn.client.robot_command import NoTimeSyncError
from bosdyn.client.time_sync import update_timestamp_filter


class AddHazardsResponseError(ResponseError):
    """General class of errors for hazard avoidance service."""


_ADD_HAZARD_STATUS_TO_ERROR = collections.defaultdict(lambda: (AddHazardsResponseError, None))
_ADD_HAZARD_STATUS_TO_ERROR.update({
    hazard_avoidance_pb2.AddHazardResult.STATUS_HAZARDS_UPDATED: (None, None),
    hazard_avoidance_pb2.AddHazardResult.STATUS_IGNORED: (None, None),
    hazard_avoidance_pb2.AddHazardResult.STATUS_INVALID_DATA: error_pair(InvalidRequestError),
    hazard_avoidance_pb2.AddHazardResult.STATUS_UNKNOWN: error_pair(UnsetStatusError),
})


@handle_common_header_errors
def _error_from_response(response):
    """Return a custom exception based on the first invalid add hazard result, None if no error."""
    for add_hazard_result in response.add_hazard_results:
        result = custom_params_error(add_hazard_result, total_response=response)
        if result is not None:
            return result

        result = error_factory(response, add_hazard_result.status,
                               status_to_string=hazard_avoidance_pb2.AddHazardResult.Status.Name,
                               status_to_error=_ADD_HAZARD_STATUS_TO_ERROR)
        if result is not None:
            # The exception is using the add hazards result.  Replace it with the full response.
            result.response = response
            return result
    return None


def _get_add_hazards_value(response):
    return response.add_hazard_results


class HazardAvoidanceClient(BaseClient):
    """Client for Hazard avoidance service."""
    default_service_name = 'hazard-avoidance-service'
    service_type = 'bosdyn.api.HazardAvoidanceService'

    def __init__(self):
        super(HazardAvoidanceClient,
              self).__init__(hazard_avoidance_service.HazardAvoidanceServiceStub)
        self._timesync_endpoint = None

    def update_from(self, other):
        super(HazardAvoidanceClient, self).update_from(other)
        # Grab a timesync endpoint if it is available.
        try:
            self._timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    @property
    def timesync_endpoint(self):
        """Accessor for timesync-endpoint that is grabbed via 'update_from()'.

        Raises:
            bosdyn.client.robot_command.NoTimeSyncError: Could not find the timesync endpoint for
                the robot.
        """
        if not self._timesync_endpoint:
            raise NoTimeSyncError("[world object service] No timesync endpoint set for the robot")
        return self._timesync_endpoint

    def add_hazards(self, add_hazards_req, **kwargs):
        """Add hazards to the hazard map.

        Args:
            add_hazards_req (hazard_avoidance_pb2.AddHazardsRequest): The request including the hazard observations to add.
        Returns:
            response (hazard_avoidance_pb2.AddHazardsResponse): Contains the status of adding each observation,

        Raises:
            RpcError: Problem communicating with the robot.
            bosdyn.client.robot_command.NoTimeSyncError: Couldn't convert the timestamp into robot
                time.
            UnsetStatusError: An internal HazardAvoidanceService issue has happened.
            AddHazardsResponseError: General problem with the request.
            bosdyn.client.exceptions.InvalidRequestError: One or more hazard observations contained errors.
        """
        for hazard_obs in add_hazards_req.hazards:
            if hazard_obs.HasField("acquisition_time"):
                # Ensure the hazard observation's time of detection is in robot time.
                client_timestamp = hazard_obs.acquisition_time
                hazard_obs.acquisition_time.CopyFrom(
                    update_timestamp_filter(self, client_timestamp, self.timesync_endpoint))
        return self.call(self._stub.AddHazards, add_hazards_req, _get_add_hazards_value,
                         _error_from_response, copy_request=False, **kwargs)

    def add_hazards_async(self, add_hazards_req, **kwargs):
        """Async version of add_hazards()."""
        for hazard_obs in add_hazards_req.hazards:
            if hazard_obs.HasField("acquisition_time"):
                # Ensure the hazard observation's time of detection is in robot time.
                client_timestamp = hazard_obs.acquisition_time
                hazard_obs.acquisition_time.CopyFrom(
                    update_timestamp_filter(self, client_timestamp, self.timesync_endpoint))
        return self.call_async(self._stub.AddHazards, add_hazards_req, _get_add_hazards_value,
                               _error_from_response, copy_request=False, **kwargs)
