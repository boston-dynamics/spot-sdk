# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to use the graph nav recording service"""

import collections
from enum import Enum

from bosdyn.api.graph_nav import map_pb2, nav_pb2, recording_pb2, recording_service_pb2
from bosdyn.api.graph_nav import recording_service_pb2_grpc as recording_service
from bosdyn.client.common import (BaseClient, common_header_errors, error_factory,
                                  handle_common_header_errors, handle_lease_use_result_errors,
                                  handle_unset_status_error)
from bosdyn.client.exceptions import ResponseError


class WaypointRegion(Enum):
    """Helper enum to describe the localization region type for a waypoint."""
    DEFAULT_REGION = 1
    EMPTY_REGION = 2
    CIRCLE_REGION = 3


class GraphNavRecordingServiceClient(BaseClient):
    """Client for the GraphNav recording service."""
    default_service_name = 'recording-service'
    service_type = 'bosdyn.api.graph_nav.GraphNavRecordingService'

    def __init__(self):
        super(GraphNavRecordingServiceClient,
              self).__init__(recording_service.GraphNavRecordingServiceStub)

    def start_recording(self, lease=None, recording_environment=None, require_fiducials=None,
                        **kwargs):
        """Start the recording service to create/update a map.

        Args:
            lease: Leases to show ownership of necessary resources. Will use the client's leases by default.
            recording_environment: RecordingEnvironment protobuf to be used for the initial waypoint created at start.
            require_fiducials: Boolean to show whether a fiducial is needed to start the recording.
        Returns:
            The status of the start recording request.
        """
        request = self._build_start_recording_request(lease, recording_environment,
                                                      require_fiducials)
        return self.call(self._stub.StartRecording, request, value_from_response=_get_status,
                         error_from_response=_start_recording_error, copy_request=False, **kwargs)

    def start_recording_full(self, lease=None, recording_environment=None, require_fiducials=None,
                             **kwargs):
        """Same as start_recording() but returns a full response"""
        request = self._build_start_recording_request(lease, recording_environment,
                                                      require_fiducials)
        return self.call(self._stub.StartRecording, request, value_from_response=_get_response,
                         error_from_response=_start_recording_error, copy_request=False, **kwargs)

    def start_recording_async(self, lease=None, recording_environment=None, require_fiducials=None,
                              **kwargs):
        """Async version of start_recording()."""
        request = self._build_start_recording_request(lease, recording_environment,
                                                      require_fiducials)
        return self.call_async(self._stub.StartRecording, request, value_from_response=_get_status,
                               error_from_response=_start_recording_error, copy_request=False,
                               **kwargs)

    def start_recording_full_async(self, lease=None, recording_environment=None,
                                   require_fiducials=None, **kwargs):
        """Async version of start_recording_full()."""
        request = self._build_start_recording_request(lease, recording_environment,
                                                      require_fiducials)
        return self.call_async(self._stub.StartRecording, request,
                               value_from_response=_get_response,
                               error_from_response=_start_recording_error, copy_request=False,
                               **kwargs)

    def stop_recording(self, lease=None, **kwargs):
        """Stop the recording service.

        Args:
            lease: Leases to show ownership of necessary resources. Will use the client's leases by default.
        Returns:
            The status of the start recording request.
        """
        request = self._build_stop_recording_request(lease)
        return self.call(self._stub.StopRecording, request, value_from_response=_get_status,
                         error_from_response=_stop_recording_error, copy_request=False, **kwargs)

    def stop_recording_async(self, lease=None, **kwargs):
        """Async version of stop_recording()."""
        request = self._build_stop_recording_request(lease)
        return self.call_async(self._stub.StopRecording, request, value_from_response=_get_status,
                               error_from_response=_stop_recording_error, copy_request=False,
                               **kwargs)

    def get_record_status(self, **kwargs):
        """Get the status of the recording service.

        Returns:
            The record service status, which indicates the current persistent environment and if it's recording a map.
        """
        request = self._build_get_record_status_request()
        return self.call(self._stub.GetRecordStatus, request, value_from_response=_get_response,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def get_record_status_async(self, **kwargs):
        """Async version of get_record_status()."""
        request = self._build_get_record_status_request()
        return self.call_async(self._stub.GetRecordStatus, request,
                               value_from_response=_get_response,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def set_recording_environment(self, lease=None, recording_environment=None, **kwargs):
        """Set the persistent recording environment.

        Args:
            lease: Leases to show ownership of necessary resources. Will use the client's leases by default.
            recording_environment: RecordingEnvironment protobuf to be set as the persistent environment.
        Returns:
            Nothing unless an error occurs.
        """
        request = self._build_set_recording_environment_request(lease, recording_environment)
        return self.call(self._stub.SetRecordingEnvironment, request, value_from_response=None,
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def set_recording_environment_async(self, lease=None, recording_environment=None, **kwargs):
        """Async version of set_recording_environment()."""
        request = self._build_set_recording_environment_request(lease, recording_environment)
        return self.call_async(self._stub.SetRecordingEnvironment, request,
                               value_from_response=None, error_from_response=common_header_errors,
                               copy_request=False, **kwargs)

    def create_waypoint(self, lease=None, waypoint_name=None, recording_environment=None, **kwargs):
        """Create a waypoint in the map at the current robot state.

        Args:
            lease: Leases to show ownership of necessary resources. Will use the client's leases by default.
            waypoint_name: Human readable string for the waypoint name.
            recording_environment: RecordingEnvironment protobuf to be used for the waypoint (will overwrite
                                     and merge with any persistent env).
        Returns:
            The response, which includes the created waypoint and any associated edges created.
        """
        request = self._build_create_waypoint_request(waypoint_name, recording_environment, lease)
        return self.call(self._stub.CreateWaypoint, request, value_from_response=_get_response,
                         error_from_response=_create_waypoint_error, copy_request=False, **kwargs)

    def create_waypoint_async(self, lease=None, waypoint_name=None, recording_environment=None,
                              **kwargs):
        """Async version of create_waypoint()."""
        request = self._build_create_waypoint_request(waypoint_name, recording_environment, lease)
        return self.call_async(self._stub.CreateWaypoint, request,
                               value_from_response=_get_response,
                               error_from_response=_create_waypoint_error, copy_request=False,
                               **kwargs)

    def create_edge(self, lease=None, edge=None, **kwargs):
        """Create an edge in the map between two existing waypoints.

        Args:
            lease: Leases to show ownership of necessary resources. Will use the client's leases by default.
            edge: An edge protobuf, which must include valid from/to waypoint id's and a from_T_to transform.
        Returns:
            The response status.
        """
        request = self._build_create_edge_request(edge, lease)
        return self.call(self._stub.CreateEdge, request, value_from_response=_get_status,
                         error_from_response=_create_edge_error, copy_request=False, **kwargs)

    def create_edge_async(self, lease=None, edge=None, **kwargs):
        """Async version of create_edge()."""
        request = self._build_create_edge_request(edge, lease)
        return self.call_async(self._stub.CreateEdge, request, value_from_response=_get_status,
                               error_from_response=_create_edge_error, copy_request=False, **kwargs)

    @staticmethod
    def _build_start_recording_request(lease, recording_env, require_fiducials):
        return recording_pb2.StartRecordingRequest(lease=lease, recording_environment=recording_env,
                                                   require_fiducials=require_fiducials)

    @staticmethod
    def _build_stop_recording_request(lease):
        return recording_pb2.StopRecordingRequest(lease=lease)

    @staticmethod
    def _build_get_record_status_request():
        return recording_pb2.GetRecordStatusRequest()

    @staticmethod
    def _build_set_recording_environment_request(lease, recording_env):
        return recording_pb2.SetRecordingEnvironmentRequest(lease=lease, environment=recording_env)

    @staticmethod
    def _build_create_waypoint_request(waypoint_name, recording_env, lease):
        return recording_pb2.CreateWaypointRequest(waypoint_name=waypoint_name,
                                                   recording_environment=recording_env, lease=lease)

    @staticmethod
    def _build_create_edge_request(edge, lease):
        return recording_pb2.CreateEdgeRequest(edge=edge, lease=lease)

    @staticmethod
    def make_recording_environment(name=None, waypoint_env=None, edge_env=None):
        """Construct a complete recording environment from the waypoint and edge environments.

        Args:
            name: A string name prefix which will prefix waypoint names (human-readable).
            waypoint_env: Waypoint.Annotations protobuf which includes information for the waypoint environment.
            edge_env: Edge.Annotations protobuf which includes information for the edge environment.
        Returns:
            The API RecordingEnvironment protobuf message.
        """
        return recording_pb2.RecordingEnvironment(name_prefix=name,
                                                  waypoint_environment=waypoint_env,
                                                  edge_environment=edge_env)

    @staticmethod
    def make_waypoint_environment(name=None, region=WaypointRegion.DEFAULT_REGION, dist_2d=None,
                                  client_metadata=None, **kwargs):
        """Create a waypoint environment.

        Args:
            name: A string name for the waypoint (human-readable).
            region: A WaypointRegion enum representing the region in which we are localizing in. This can be
                      either a default region, an empty region (don't localize to this waypoint), or a circular region.
            dist_2d: If the region is circular, then this is set as a distance (meters) representing the number
                       of meters away we can be from the waypoint before scan matching.
            client_metadata: Info about the client which will be stored in the waypoints.
        Returns:
            The API Waypoint.Annotations protobuf message.
        """
        waypoint_env = map_pb2.Waypoint.Annotations(name=name, client_metadata=client_metadata)
        if region == WaypointRegion.DEFAULT_REGION:
            waypoint_env.scan_match_region.default_region.CopyFrom(
                map_pb2.Waypoint.Annotations.LocalizeRegion.Default())
            waypoint_env.scan_match_region.state = map_pb2.ANNOTATION_STATE_SET
        elif region == WaypointRegion.EMPTY_REGION:
            waypoint_env.scan_match_region.empty.CopyFrom(
                map_pb2.Waypoint.Annotations.LocalizeRegion.Empty())
            waypoint_env.scan_match_region.state = map_pb2.ANNOTATION_STATE_SET
        elif region == WaypointRegion.CIRCLE_REGION:
            if dist_2d is not None:
                waypoint_env.scan_match_region.circle.CopyFrom(
                    map_pb2.Waypoint.Annotations.LocalizeRegion.Circle2D(dist_2d=dist_2d))
                waypoint_env.scan_match_region.state = map_pb2.ANNOTATION_STATE_SET
            else:
                waypoint_env.scan_match_region.state = map_pb2.ANNOTATION_STATE_NONE
        else:
            waypoint_env.scan_match_region.state = map_pb2.ANNOTATION_STATE_NONE
        return waypoint_env

    @staticmethod
    def make_client_metadata(session_name=None, client_username=None, client_software_version=None,
                             client_id=None, client_type=None):
        """Creates client metadata for recording.

        Args:
            session_name: User-provided name for this recording "session". For example, the user
              may start and stop recording at various times and assign a name to a region
              that is being recorded. Usually, this will just be the map name.
            client_username: If the application recording the map has a special user name,
              this is the name of that user.
            client_software_version: Version string of any client software that generated this object.
            client_id: Identifier of any client software that generated this object
            client_type: Special tag for the client software which created this object.
              For example, "Tablet", "Scout", "Python SDK", etc.
        """
        return map_pb2.ClientMetadata(session_name=session_name, client_username=client_username,
                                      client_software_version=client_software_version,
                                      client_type=client_type)

    @staticmethod
    def make_edge_environment(
            vel_limit=None, direction_constraint=map_pb2.Edge.Annotations.DIRECTION_CONSTRAINT_NONE,
            require_alignment=False, flat_ground=False, ground_mu_hint=.8, grated_floor=False):
        """Create an edge environment.

        Args:
            vel_limit: A SE2VelocityLimit to use while traversing the edge. Note this is not a target speed, just a max/min.
            direction_constraint: A direction constraints on the robot's orientation when traversing the edge.
            require_alignment: Boolean where if true, the robot must be aligned with the edge in yaw before traversing it.
            flat_ground: Boolean where if true, the edge crosses flat ground and the robot shouldn't try to climb over obstacles.
            ground_mu_hint: Terrain coefficient of friction user hint. Suggested values lie between [.4, .8].
            grated_floor: Boolean where if true, the edge crosses over grated metal.
        Returns:
            The API Edge.Annotations protobuf message.
        """
        edge_env = map_pb2.Edge.Annotations()
        edge_env.require_alignment.value.CopyFrom(require_alignment)
        edge_env.flat_ground.value.CopyFrom(flat_ground)
        edge_env.grated_floor.value.CopyFrom(grated_floor)
        if (ground_mu_hint > 0):
            edge_env.ground_mu_hint.value.CopyFrom(ground_mu_hint)
        if vel_limit is not None:
            edge_env.vel_limit.CopyFrom(vel_limit)
        edge_env.direction_constraint.CopyFrom(direction_constraint)
        edge_env.stairs.state.CopyFrom(map_pb2.AnnotationState.ANNOTATION_STATE_NONE)
        return edge_env

    @staticmethod
    def make_edge(from_waypoint_id, to_waypoint_id, from_tform_to, edge_environment=None):
        """Create an edge between two waypoint ids.

        Args:
            from_waypoint_id: A waypoint string id for the from waypoint.
            to_waypoint_id: A waypoint string id for the to waypoint.
            from_tform_to: An SE3Pose representing the transform of from_waypoint to to_waypoint.
            edge_environment: Any edge environment to be associated with the created edge.
        Returns:
            The API Edge protobuf message.
        """
        edge_id = map_pb2.Edge.Id(from_waypoint=from_waypoint_id, to_waypoint=to_waypoint_id)
        edge = map_pb2.Edge(id=edge_id, from_tform_to=from_tform_to)
        if edge_environment is not None:
            edge.annotations.CopyFrom(edge_environment)
        return edge


'''
Static helper methods for handing responses and errors.
'''


class RecordingServiceResponseError(ResponseError):
    """General class of errors for the GraphNav Recording Service."""


class CouldNotCreateWaypointError(RecordingServiceResponseError):
    """Service could not create a waypoint."""


class NotRecordingError(RecordingServiceResponseError):
    """The recording service has not been started."""


class UnknownWaypointError(RecordingServiceResponseError):
    """The edge requested has a waypoint id that is unknown."""


class EdgeExistsError(RecordingServiceResponseError):
    """The edge requested with the given ID already exists in the map."""


class EdgeMissingTransformError(RecordingServiceResponseError):
    """The edge requested is missing the from_T_to transform in the edge."""


class NotLocalizedToEndError(RecordingServiceResponseError):
    """Stop recording failed to localize to the last created waypoint."""


class FollowingRouteError(RecordingServiceResponseError):
    """Cannot start recording while the robot is already following a route."""


class NotLocalizedToExistingMapError(RecordingServiceResponseError):
    """The robot is not localized to the existing map and cannot start recording."""


class TooFarFromExistingMapError(RecordingServiceResponseError):
    """The robot is too far from the existing map and cannot start recording."""


class RemoteCloudFailureNotInDirectoryError(RecordingServiceResponseError):
    """Failed to start recording because a remote point cloud (e.g. a LIDAR) is not registered to the service directory."""


class RemoteCloudFailureNoDataError(RecordingServiceResponseError):
    """Failed to start recording because a remote point cloud (e.g. a LIDAR) is not delivering data."""


class NotReadyYetError(RecordingServiceResponseError):
    """The service is processing the map at its current position. Try again in 1-2 seconds."""


class MapTooLargeLicenseError(RecordingServiceResponseError):
    """Map exceeds the size allowed by the license."""


class MissingFiducialsError(RecordingServiceResponseError):
    """One or more required fiducials were not detected."""


class FiducialPoseError(RecordingServiceResponseError):
    """The pose of one or more required fiducials could not be determined accurately."""


class RobotImpairedError(RecordingServiceResponseError):
    """Failed to start recording because the robot is impaired."""

    def __init__(self, response, error_message):
        RecordingServiceResponseError.__init__(self, response, error_message)
        self.impaired_state = response.impaired_state

    def __str__(self):
        base = RecordingServiceResponseError.__str__(self)
        base += "\nImpaired state: {}".format(self.impaired_state)
        return base


def _get_status(response):
    return response.status


def _get_response(response):
    # Return full response for RecordStatus to get environment and is_recording information.
    return response


_START_RECORDING_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_START_RECORDING_STATUS_TO_ERROR.update({
    recording_pb2.StartRecordingResponse.STATUS_OK: (None, None),
    recording_pb2.StartRecordingResponse.STATUS_COULD_NOT_CREATE_WAYPOINT:
        (CouldNotCreateWaypointError, CouldNotCreateWaypointError.__doc__),
    recording_pb2.StartRecordingResponse.STATUS_FOLLOWING_ROUTE:
        (FollowingRouteError, FollowingRouteError.__doc__),
    recording_pb2.StartRecordingResponse.STATUS_NOT_LOCALIZED_TO_EXISTING_MAP:
        (NotLocalizedToExistingMapError, NotLocalizedToExistingMapError.__doc__),
    recording_pb2.StartRecordingResponse.STATUS_MISSING_FIDUCIALS:
        (MissingFiducialsError, MissingFiducialsError.__doc__),
    recording_pb2.StartRecordingResponse.STATUS_MAP_TOO_LARGE_LICENSE:
        (MapTooLargeLicenseError, MapTooLargeLicenseError.__doc__),
    recording_pb2.StartRecordingResponse.STATUS_REMOTE_CLOUD_FAILURE_NOT_IN_DIRECTORY:
        (RemoteCloudFailureNotInDirectoryError, RemoteCloudFailureNotInDirectoryError.__doc__),
    recording_pb2.StartRecordingResponse.STATUS_REMOTE_CLOUD_FAILURE_NO_DATA:
        (RemoteCloudFailureNoDataError, RemoteCloudFailureNoDataError.__doc__),
    recording_pb2.StartRecordingResponse.STATUS_FIDUCIAL_POSE_NOT_OK:
        (FiducialPoseError, FiducialPoseError.__doc__),
    recording_pb2.StartRecordingResponse.STATUS_TOO_FAR_FROM_EXISTING_MAP:
        (TooFarFromExistingMapError, TooFarFromExistingMapError.__doc__),
    recording_pb2.StartRecordingResponse.STATUS_ROBOT_IMPAIRED:
        (RobotImpairedError, RobotImpairedError.__doc__)
})


@handle_common_header_errors
# @handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _start_recording_error(response):
    """Return a custom exception based on start recording response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=recording_pb2.StartRecordingResponse.Status.Name,
                         status_to_error=_START_RECORDING_STATUS_TO_ERROR)


_STOP_RECORDING_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_STOP_RECORDING_STATUS_TO_ERROR.update({
    recording_pb2.StopRecordingResponse.STATUS_OK: (None, None),
    recording_pb2.StopRecordingResponse.STATUS_NOT_LOCALIZED_TO_END:
        (NotLocalizedToEndError, NotLocalizedToEndError.__doc__),
    recording_pb2.StopRecordingResponse.STATUS_NOT_READY_YET:
        (NotReadyYetError, NotReadyYetError.__doc__)
})


@handle_common_header_errors
# @handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _stop_recording_error(response):
    """Return a custom exception based on stop recording response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=recording_pb2.StopRecordingResponse.Status.Name,
                         status_to_error=_STOP_RECORDING_STATUS_TO_ERROR)


_CREATE_WAYPOINT_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_CREATE_WAYPOINT_STATUS_TO_ERROR.update({
    recording_pb2.CreateWaypointResponse.STATUS_OK: (None, None),
    recording_pb2.CreateWaypointResponse.STATUS_NOT_RECORDING:
        (NotRecordingError, NotRecordingError.__doc__),
    recording_pb2.CreateWaypointResponse.STATUS_COULD_NOT_CREATE_WAYPOINT:
        (CouldNotCreateWaypointError, CouldNotCreateWaypointError.__doc__),
    recording_pb2.CreateWaypointResponse.STATUS_REMOTE_CLOUD_FAILURE_NOT_IN_DIRECTORY:
        (RemoteCloudFailureNotInDirectoryError, RemoteCloudFailureNotInDirectoryError.__doc__),
    recording_pb2.CreateWaypointResponse.STATUS_REMOTE_CLOUD_FAILURE_NO_DATA:
        (RemoteCloudFailureNoDataError, RemoteCloudFailureNoDataError.__doc__),
})


@handle_common_header_errors
# @handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _create_waypoint_error(response):
    """Return a custom exception based on create waypoint response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=recording_pb2.CreateWaypointResponse.Status.Name,
                         status_to_error=_CREATE_WAYPOINT_STATUS_TO_ERROR)


_CREATE_EDGE_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_CREATE_EDGE_STATUS_TO_ERROR.update({
    recording_pb2.CreateEdgeResponse.STATUS_OK: (None, None),
    recording_pb2.CreateEdgeResponse.STATUS_NOT_RECORDING:
        (NotRecordingError, NotRecordingError.__doc__),
    recording_pb2.CreateEdgeResponse.STATUS_EXISTS: (EdgeExistsError, EdgeExistsError.__doc__),
    recording_pb2.CreateEdgeResponse.STATUS_UNKNOWN_WAYPOINT:
        (UnknownWaypointError, UnknownWaypointError.__doc__),
    recording_pb2.CreateEdgeResponse.STATUS_MISSING_TRANSFORM:
        (EdgeMissingTransformError, EdgeMissingTransformError.__doc__)
})


@handle_common_header_errors
# @handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _create_edge_error(response):
    """Return a custom exception based on create edge response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=recording_pb2.CreateEdgeResponse.Status.Name,
                         status_to_error=_CREATE_EDGE_STATUS_TO_ERROR)
