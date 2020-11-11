# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the graphnav service."""
import time
import collections
import math
import os
from bosdyn.api.graph_nav import graph_nav_service_pb2_grpc
from bosdyn.api.graph_nav import graph_nav_service_pb2
from bosdyn.api.graph_nav import graph_nav_pb2
from bosdyn.api.graph_nav import nav_pb2
from bosdyn.api.graph_nav import map_pb2
from bosdyn.api import data_chunk_pb2
from bosdyn.client.common import BaseClient, error_pair
from bosdyn.client.common import (common_header_errors, common_lease_errors, error_factory,
                                  handle_common_header_errors, handle_unset_status_error,
                                  handle_lease_use_result_errors)
from bosdyn.client.exceptions import Error, ResponseError, InvalidRequestError
from bosdyn.client.lease import add_lease_wallet_processors


class GraphNavClient(BaseClient):
    """Client to the GraphNav service."""
    default_service_name = 'graph-nav-service'
    service_type = 'bosdyn.api.graph_nav.GraphNavService'

    def __init__(self):
        super(GraphNavClient, self).__init__(graph_nav_service_pb2_grpc.GraphNavServiceStub)
        self._timesync_endpoint = None
        self._data_chunk_size = 1000  # bytes = 1 KB

    def update_from(self, other):
        super(GraphNavClient, self).update_from(other)
        if self.lease_wallet:
            add_lease_wallet_processors(self, self.lease_wallet)

        # Grab a timesync endpoint if it is available.
        try:
            self._timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    def set_localization(self, initial_guess_localization, ko_tform_body=None, max_distance=None,
                         max_yaw=None,
                         fiducial_init=graph_nav_pb2.SetLocalizationRequest.FIDUCIAL_INIT_NEAREST,
                         use_fiducial_id=None, refine_fiducial_result_with_icp=False,
                         do_ambiguity_check=False, **kwargs):
        """Trigger a manual localization. Typically done to provide the initial localization.

        Args:
            initial_guess_localization (nav_pb2.Localization): Operator-supplied guess at localization.
            ko_tform_body: Robot SE3Pose protobuf when the initial_guess was made.
            max_distance: [optional] Margin of distance (meters) away from the initial guess.
            max_yaw: [optional] Margin of angle (radians) away from the initial guess.
            fiducial_init: Tells the initializer whether to use fiducials, and how to use them.
            use_fiducial_id: If using FIDUCIAL_INIT_SPECIFIC, this is the specific fiducial ID to use for initialization.
            refine_fiducial_result_with_icp: Boolean determining if ICP will run after a fiducial is used for an initial guess.
            do_ambiguity_check: Boolean where if true, consider how nearby localizations appear.
        Returns:
            The resulting localization after being triggered with a guess.
        Raises:
            RpcError: Problem communicating with the robot
            RobotFaultedError: Robot is experiencing a fault condition that prevents localization.
            UnknownMapInformationError: Specified waypoint is unknown.
            InvalidRequestError: The data provided is incomplete or invalid
            GraphNavServiceResponseError: Localization was aborted or failed.
        """
        req = self._build_set_localization_request(initial_guess_localization, ko_tform_body,
                                                   max_distance, max_yaw, fiducial_init,
                                                   use_fiducial_id, refine_fiducial_result_with_icp,
                                                   do_ambiguity_check)
        return self.call(self._stub.SetLocalization, req, _localization_from_response,
                         _set_localization_error, **kwargs)

    def set_localization_async(
            self, initial_guess_localization, ko_tform_body=None, max_distance=None, max_yaw=None,
            fiducial_init=graph_nav_pb2.SetLocalizationRequest.FIDUCIAL_INIT_NEAREST,
            use_fiducial_id=None, refine_fiducial_result_with_icp=False, do_ambiguity_check=False,
            **kwargs):
        """Async version of set_localization()"""
        req = self._build_set_localization_request(initial_guess_localization, ko_tform_body,
                                                   max_distance, max_yaw, fiducial_init,
                                                   use_fiducial_id, refine_fiducial_result_with_icp,
                                                   do_ambiguity_check)
        return self.call_async(self._stub.SetLocalization, req, _localization_from_response,
                               _set_localization_error, **kwargs)

    def get_localization_state(self,
                               request_live_point_cloud=False,
                               request_live_images=False,
                               request_live_terrain_maps=False,
                               request_live_world_objects=False,
                               request_live_robot_state=False,
                               waypoint_id=None,
                               **kwargs):
        """Obtain current localization state of the robot.

        Returns:
            The current localization protobuf for the robot.
        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._build_get_localization_state_request(
            request_live_point_cloud=request_live_point_cloud,
            request_live_images=request_live_images,
            request_live_terrain_maps=request_live_terrain_maps,
            request_live_world_objects=request_live_world_objects,
            request_live_robot_state=request_live_robot_state,
            waypoint_id=waypoint_id)
        return self.call(self._stub.GetLocalizationState, req, None, common_header_errors, **kwargs)

    def get_localization_state_async(self, request_live_point_cloud=False,
                                     request_live_images=False, request_live_terrain_maps=False,
                                     request_live_world_objects=False,
                                     request_live_robot_state=False, waypoint_id=None, **kwargs):
        """Async version of get_localization_state()."""
        req = self._build_get_localization_state_request(
            request_live_point_cloud=request_live_point_cloud,
            request_live_images=request_live_images,
            request_live_terrain_maps=request_live_terrain_maps,
            request_live_world_objects=request_live_world_objects,
            request_live_robot_state=request_live_robot_state, waypoint_id=waypoint_id)
        return self.call_async(self._stub.GetLocalizationState, req, None, common_header_errors,
                               **kwargs)

    def navigate_route(self, route, cmd_duration, travel_params=None, leases=None,
                       timesync_endpoint=None, **kwargs):
        """Navigate the given route.

        Args:
            route: Route protobuf of the route to follow.
            travel_params: API TravelParams for the route.
            cmd_duration: Number of seconds the command can run for.
            leases: Leases to show ownership of necessary resources. Will use the client's leases by default.
            timesync_endpoint: Use this endpoint for timesync fields. Will use the client's endpoint by default.
            kwargs: Passed to underlying RPC. Example: timeout=5 to cancel the RPC after 5 seconds.
        Returns:
            Command ID to use in feedback lookup.
        Raises:
            RpcError: Problem communicating with the robot.
            LeaseUseError: Error using provided leases.
            graph_nav.NoTimeSyncError: Missing clock identifier.
            graph_nav.CommandExpiredError: Command already expired.
            graph_nav.TooDistantError: Time too far in the future.
            graph_nav.RobotImpairedError: Robot cannot travel a route.
            graph_nav.IsRecordingError: Robot cannot navigate while recording.
            graph_nav.UnkownRouteElementsError: Unknown edges or waypoints
            graph_nav.InvalidEdgeError: Mismatch between edges and waypoints.
            graph_nav.RobotNotLocalizedToRouteError: The robot is localized somewhere else.
            graph_nav.ConstraintFaultError: The route involves invalid constraints.
            graph_nav.RouteNavigationError: A subclass detailing trouble navigating the route.
        """
        used_endpoint = timesync_endpoint or self._timesync_endpoint
        if not used_endpoint:
            raise GraphNavServiceResponseError(response=None, error_message='No timesync endpoint!')
        request = self._build_navigate_route_request(route, travel_params, cmd_duration, leases,
                                                     used_endpoint)
        return self.call(self._stub.NavigateRoute, request,
                         _command_id_from_navigate_route_response, _navigate_route_error, **kwargs)

    def navigate_route_async(self, route, cmd_duration, travel_params=None, leases=None,
                             timesync_endpoint=None, **kwargs):
        """Async version of navigate_route()"""
        used_endpoint = timesync_endpoint or self._timesync_endpoint
        if not used_endpoint:
            raise GraphNavServiceResponseError(response=None, error_message='No timesync endpoint!')
        request = self._build_navigate_route_request(route, travel_params, cmd_duration, leases,
                                                     used_endpoint)
        return self.call_async(self._stub.NavigateRoute, request,
                               _command_id_from_navigate_route_response, _navigate_route_error,
                               **kwargs)

    def navigate_to(self, destination_waypoint_id, cmd_duration, route_params=None,
                    travel_params=None, leases=None, timesync_endpoint=None, **kwargs):
        """Navigate to a specific waypoint along a route chosen by the GraphNav service.

        Args:
            destination_waypoint_id: Waypoint id string for where to go to.
            cmd_duration: Number of seconds the command can run for.
            route_params: API RouteGenParams for the route.
            travel_params: API TravelParams for the route.
            leases: Leases to show ownership of necessary resources. Will use the client's leases by default.
            timesync_endpoint: Use this endpoint for timesync fields. Will use the client's endpoint by default.
        Returns:
            int: Command ID to use in feedback lookup.
        Raises:
            RpcError: Problem communicating with the robot.
            LeaseUseError: Error using provided leases.
            graph_nav.NoTimeSyncError: Missing clock identifier.
            graph_nav.CommandExpiredError: Command already expired.
            graph_nav.TooDistantError: Time too far in the future.
            graph_nav.RobotImpairedError: Robot cannot travel a route.
            graph_nav.IsRecordingError: Robot cannot navigate while recording.
            graph_nav.UnknownWaypointError: Destination waypoint is unknown.
            graph_nav.NoPathError: No route to destination.
            graph_nav.RobotNotLocalizedToRouteError: The robot not correctly localized.
            graph_nav.RouteNavigationError: A subclass detailing trouble navigating the route.
        """
        used_endpoint = timesync_endpoint or self._timesync_endpoint
        if not used_endpoint:
            raise GraphNavServiceResponseError(response=None, error_message='No timesync endpoint!')
        request = self._build_navigate_to_request(destination_waypoint_id, travel_params,
                                                  route_params, cmd_duration, leases, used_endpoint)
        return self.call(self._stub.NavigateTo, request,
                         value_from_response=_command_id_from_navigate_route_response,
                         error_from_response=_navigate_to_error, **kwargs)

    def navigate_to_async(self, destination_waypoint_id, cmd_duration, route_params=None,
                          travel_params=None, leases=None, timesync_endpoint=None, **kwargs):
        """Async version of navigate_to()."""
        used_endpoint = timesync_endpoint or self._timesync_endpoint
        if not used_endpoint:
            raise GraphNavServiceResponseError(response=None, error_message='No timesync endpoint!')
        request = self._build_navigate_to_request(destination_waypoint_id, travel_params,
                                                  route_params, cmd_duration, leases, used_endpoint)
        return self.call_async(self._stub.NavigateTo, request,
                               value_from_response=_command_id_from_navigate_route_response,
                               error_from_response=_navigate_to_error, **kwargs)

    def navigation_feedback(self, command_id=0, **kwargs):
        """Returns the feedback corresponding to the active route follow command.

        Args:
            command_id (int):  If blank, will return current command status.  If filled
                out, will attempt to return that command status
        Returns:
            NavigationFeedbackResponse
        Raises:
            RpcError: Problem communicating with the robot.
        """
        request = self._build_navigate_feedback_request(command_id)
        return self.call(self._stub.NavigationFeedback, request, value_from_response=_get_response,
                         error_from_response=_navigate_feedback_error, **kwargs)

    def navigation_feedback_async(self, command_id=0, **kwargs):
        """Async version of navigation_feedback()."""
        request = self._build_navigate_feedback_request(command_id)
        return self.call_async(self._stub.NavigationFeedback, request,
                               value_from_response=_get_response,
                               error_from_response=_navigate_feedback_error, **kwargs)

    def clear_graph(self, lease=None, **kwargs):
        """Clears the local graph structure. Also erases any snapshots currently in RAM.

        Args:
            leases: Leases to show ownership of necessary resources. Will use the client's leases by default.
        Raises:
            RpcError: Problem communicating with the robot.
            LeaseUseError: Error using provided lease.
        """
        request = self._build_clear_graph_request(lease)
        return self.call(self._stub.ClearGraph, request, value_from_response=None,
                         error_from_response=handle_common_header_errors(common_lease_errors), **kwargs)

    def clear_graph_async(self, lease=None, **kwargs):
        """Async version of clear_graph()."""
        request = self._build_clear_graph_request(lease)
        return self.call_async(self._stub.ClearGraph, request, value_from_response=None,
                               error_from_response=handle_common_header_errors(common_lease_errors), **kwargs)

    def upload_graph(self, lease=None, graph=None, **kwargs):
        """Uploads a graph to the server and appends to the existing graph.

        Args:
            leases: Leases to show ownership of necessary resources. Will use the client's leases by default.
            graph: Graph protobuf that represents the map with waypoints and edges.
        Returns:
            The response, which includes waypoint and edge id's sorted by whether it was cached.
        Raises:
            RpcError: Problem communicating with the robot.
            LeaseUseError: Error using provided lease.
        """
        request = self._build_upload_graph_request(lease, graph)
        return self.call(self._stub.UploadGraph, request, value_from_response=_get_response,
                         error_from_response=handle_common_header_errors(common_lease_errors), **kwargs)

    def upload_graph_async(self, lease=None, graph=None, **kwargs):
        """Async version of upload_graph()."""
        request = self._build_upload_graph_request(lease, graph)
        return self.call_async(self._stub.UploadGraph, request, value_from_response=_get_response,
                               error_from_response=handle_common_header_errors(common_lease_errors), **kwargs)

    def upload_waypoint_snapshot(self, waypoint_snapshot, lease=None, **kwargs):
        """Uploads large waypoint snapshot as a stream for a particular waypoint.

        Args:
            leases: Leases to show ownership of necessary resources. Will use the client's leases by default.
            waypoint_snapshot: WaypointSnapshot protobuf that will be stream uploaded to the robot.
        Returns:
            The status of the upload request.
        Raises:
            RpcError: Problem communicating with the robot.
            LeaseUseError: Error using provided lease.
        """
        serialized = waypoint_snapshot.SerializeToString()
        self.call(self._stub.UploadWaypointSnapshot,
                  GraphNavClient._data_chunk_iterator_upload_waypoint_snapshot(
                      serialized, lease, self._data_chunk_size), value_from_response=None,
                  error_from_response=handle_common_header_errors(common_lease_errors), **kwargs)

    def upload_edge_snapshot(self, edge_snapshot, lease=None, **kwargs):
        """Uploads large edge snapshot as a stream for a particular edge.

        Args:
            leases: Leases to show ownership of necessary resources. Will use the client's leases by default.
            edge_snapshot: EdgeSnapshot protobuf that will be stream uploaded to the robot.
        Returns:
            The status of the upload request.
        Raises:
            RpcError: Problem communicating with the robot.
            LeaseUseError: Error using provided leases.
        """
        serialized = edge_snapshot.SerializeToString()
        self.call(self._stub.UploadEdgeSnapshot,
                  GraphNavClient._data_chunk_iterator_upload_edge_snapshot(
                      serialized, lease, self._data_chunk_size), value_from_response=None,
                  error_from_response=handle_common_header_errors(common_lease_errors), **kwargs)

    def download_graph(self, **kwargs):
        """Downloads the graph from the server.

        Returns:
            The graph protobuf that represents the current map on the robot (with waypoints and edges).
        Raises:
            RpcError: Problem communicating with the robot
        """
        request = self._build_download_graph_request()
        return self.call(self._stub.DownloadGraph, request, value_from_response=_get_graph,
                         error_from_response=common_header_errors, **kwargs)

    def download_graph_async(self, **kwargs):
        """Async version of download_graph()."""
        request = self._build_download_graph_request()
        return self.call_async(self._stub.DownloadGraph, request, value_from_response=_get_graph,
                               error_from_response=common_header_errors, **kwargs)

    def download_waypoint_snapshot(self,
                                    waypoint_snapshot_id,
                                    download_images=False,
                                    **kwargs):
        """Download a specific waypoint snapshot with streaming from the server.

        Args:
            waypoint_snapshot_id: WaypointSnapshot string ID for which snapshot to download from robot.
            download_images: Boolean indicating whether or not to include images in the download.
        Returns:
            The WaypointSnapshot protobuf from the robot's current map.
        Raises:
            RpcError: Problem communicating with the robot
            UnknownMapInformationError: Snapshot id not found
        """
        request = self._build_download_waypoint_snapshot_request(waypoint_snapshot_id,
                                                                 download_images
                                                                )
        return self.call(self._stub.DownloadWaypointSnapshot, request,
                         value_from_response=_get_streamed_waypoint_snapshot,
                         error_from_response=_download_waypoint_snapshot_stream_errors, **kwargs)

    def download_edge_snapshot(self, edge_snapshot_id, **kwargs):
        """Downloads a specific edge snapshot with streaming from the server.

        Args:
            edge_snapshot_id: EdgeSnapshot string ID for which snapshot to download from robot.
        Returns:
            The EdgeSnapshot protobuf from the robot's current map.
        Raises:
            RpcError: Problem communicating with the robot
            UnknownMapInformationError: Snapshot id not found
        """
        request = self._build_download_edge_snapshot_request(edge_snapshot_id)
        return self.call(self._stub.DownloadEdgeSnapshot, request,
                         value_from_response=_get_streamed_edge_snapshot,
                         error_from_response=_download_edge_snapshot_stream_errors, **kwargs)

    def _write_bytes(self, filepath, filename, data):
        """Write data to a file."""
        os.makedirs(filepath, exist_ok=True)
        with open(filepath + filename, 'wb+') as f:
            f.write(data)
            f.close()

    def write_graph_and_snapshots(self, directory):
        """Download the graph and snapshots from robot to the specified directory."""
        graph = self.download_graph()
        graph_bytes = graph.SerializeToString()
        self._write_bytes(directory, '/graph', graph_bytes)

        for waypoint in graph.waypoints:
            waypoint_snapshot = self.download_waypoint_snapshot(waypoint.snapshot_id)
            self._write_bytes(directory + '/waypoint_snapshots', '/' + waypoint.snapshot_id,
                              waypoint_snapshot.SerializeToString())

        for edge in graph.edges:
            edge_snapshot = self.download_edge_snapshot(edge.snapshot_id)
            self._write_bytes(directory + '/edge_snapshots', '/' + edge.snapshot_id,
                              edge_snapshot.SerializeToString())

    @staticmethod
    def _build_set_localization_request(
            initial_guess_localization, ko_tform_body=None, max_distance=None, max_yaw=None,
            fiducial_init=graph_nav_pb2.SetLocalizationRequest.FIDUCIAL_INIT_NEAREST,
            use_fiducial_id=None, refine_fiducial_result_with_icp=False, do_ambiguity_check=False):
        request = graph_nav_pb2.SetLocalizationRequest(fiducial_init=fiducial_init)
        request.initial_guess.CopyFrom(initial_guess_localization)
        if ko_tform_body is not None:
            request.ko_tform_body.CopyFrom(ko_tform_body)

        if max_distance is not None:
            request.max_distance = max_distance
        if max_yaw is not None:
            request.max_yaw = max_yaw

        if (fiducial_init == graph_nav_pb2.SetLocalizationRequest.FIDUCIAL_INIT_SPECIFIC):
            if use_fiducial_id is not None:
                request.use_fiducial_id = use_fiducial_id

        request.refine_fiducial_result_with_icp = refine_fiducial_result_with_icp
        request.do_ambiguity_check = do_ambiguity_check
        return request

    @staticmethod
    def _build_get_localization_state_request(request_live_point_cloud,
                                              request_live_images, request_live_terrain_maps,
                                              request_live_world_objects, request_live_robot_state,
                                              waypoint_id):
        return graph_nav_pb2.GetLocalizationStateRequest(
            request_live_point_cloud=request_live_point_cloud,
            request_live_images=request_live_images,
            request_live_terrain_maps=request_live_terrain_maps,
            request_live_world_objects=request_live_world_objects,
            request_live_robot_state=request_live_robot_state,
            waypoint_id=waypoint_id)

    @staticmethod
    def _build_navigate_route_request(route, travel_params, end_time_secs, leases,
                                      timesync_endpoint):
        converter = timesync_endpoint.get_robot_time_converter()
        request = graph_nav_pb2.NavigateRouteRequest(
            route=route, clock_identifier=timesync_endpoint.clock_identifier)
        if travel_params is not None:
            request.travel_params.CopyFrom(travel_params)
        request.end_time.CopyFrom(
            converter.robot_timestamp_from_local_secs(time.time() + end_time_secs))
        return request

    @staticmethod
    def _build_navigate_to_request(destination_waypoint_id, travel_params, route_params,
                                   end_time_secs, leases, timesync_endpoint):
        converter = timesync_endpoint.get_robot_time_converter()
        request = graph_nav_pb2.NavigateToRequest(
            destination_waypoint_id=destination_waypoint_id,
            clock_identifier=timesync_endpoint.clock_identifier)
        request.end_time.CopyFrom(
            converter.robot_timestamp_from_local_secs(time.time() + end_time_secs))
        if travel_params is not None:
            request.travel_params.CopyFrom(travel_params)
        if route_params is not None:
            request.route_params.CopyFrom(route_params)
        return request

    @staticmethod
    def _build_clear_graph_request(lease):
        return graph_nav_pb2.ClearGraphRequest(lease=lease)

    @staticmethod
    def _build_navigate_feedback_request(command_id=0):
        return graph_nav_pb2.NavigationFeedbackRequest(command_id=command_id)

    @staticmethod
    def _build_upload_graph_request(lease, graph):
        return graph_nav_pb2.UploadGraphRequest(lease=lease, graph=graph)

    @staticmethod
    def _data_chunk_iterator_upload_waypoint_snapshot(serialized_waypoint_snapshot, lease,
                                                      data_chunk_byte_size):
        total_bytes_size = len(serialized_waypoint_snapshot)
        num_chunks = math.ceil(total_bytes_size / data_chunk_byte_size)
        for i in range(num_chunks):
            start_index = i * data_chunk_byte_size
            end_index = (i + 1) * data_chunk_byte_size
            chunk = data_chunk_pb2.DataChunk(total_size=total_bytes_size)
            if (end_index > total_bytes_size):
                chunk.data = serialized_waypoint_snapshot[start_index:total_bytes_size]
            else:
                chunk.data = serialized_waypoint_snapshot[start_index:end_index]
            req = graph_nav_pb2.UploadWaypointSnapshotRequest(lease=lease, chunk=chunk)
            yield req

    @staticmethod
    def _data_chunk_iterator_upload_edge_snapshot(serialized_edge_snapshot, lease,
                                                  data_chunk_byte_size):
        total_bytes_size = len(serialized_edge_snapshot)
        num_chunks = math.ceil(total_bytes_size / data_chunk_byte_size)
        for i in range(num_chunks):
            start_index = i * data_chunk_byte_size
            end_index = (i + 1) * data_chunk_byte_size
            chunk = data_chunk_pb2.DataChunk(total_size=total_bytes_size)
            if (end_index > total_bytes_size):
                chunk.data = serialized_edge_snapshot[start_index:total_bytes_size]
            else:
                chunk.data = serialized_edge_snapshot[start_index:end_index]
            req = graph_nav_pb2.UploadWaypointSnapshotRequest(lease=lease, chunk=chunk)
            yield req

    @staticmethod
    def _build_download_graph_request():
        return graph_nav_pb2.DownloadGraphRequest()

    @staticmethod
    def _build_download_waypoint_snapshot_request(waypoint_snapshot_id, download_images
                                                  ):
        return graph_nav_pb2.DownloadWaypointSnapshotRequest(
            waypoint_snapshot_id=waypoint_snapshot_id, download_images=download_images
            )

    @staticmethod
    def _build_download_edge_snapshot_request(edge_snapshot_id):
        return graph_nav_pb2.DownloadEdgeSnapshotRequest(edge_snapshot_id=edge_snapshot_id)

    @staticmethod
    def generate_travel_params(max_distance, max_yaw, velocity_limit=None):
        """ Generate the API TravelParams for navigation requests.

        Args:
            max_distance: Distances (meters) threshold for when we've reached the final waypoint.
            max_yaw: Angle (radians) threshold for when we've reached the final waypoint.
            velocity_limit: SE2VelocityLimit protobuf message for the speed the robot should use.
        Returns:
            The API TravelParams protobuf message.
        """
        travel_params = graph_nav_pb2.TravelParams(max_distance=max_distance, max_yaw=max_yaw)
        if velocity_limit is not None:
            travel_params.velocity_limit.CopyFrom(velocity_limit)
        return travel_params

    @staticmethod
    def generate_route_params(waypoint_id_list):
        """ Generate the API RouteGenParams for navigation requests.

        Args:
            waypoint_id_list: List of waypoint id strings in which a route should pass through.
        Returns:
            The API RouteGenParams protobuf message.
        """
        route_params = graph_nav_pb2.RouteGenParams()
        route_params.via_waypoints.extend(waypoint_id_list)
        return route_params

    @staticmethod
    def build_route(waypoint_id_list, edge_id_list):
        """ Generate the API RouteGenParams for navigation requests.

        Args:
            waypoint_id_list: List of waypoint id strings in which a route should pass through.
                                The ids should be ordered from [start waypoint --> destination waypoint].
            edge_id_list: List of the edge_id's which should be in the same ordering as the waypoint list.
        Returns:
            The API Route protobuf message.
        """
        route = nav_pb2.Route()
        route.waypoint_id.extend(waypoint_id_list)
        route.edge_id.extend(edge_id_list)
        return route


'''
Static helper methods for handing responses and errors.
'''


class GraphNavServiceResponseError(ResponseError):
    """General class of errors for the GraphNav Recording Service."""


class RequestAbortedError(GraphNavServiceResponseError):
    """Request was aborted by the system."""


class RequestFailedError(GraphNavServiceResponseError):
    """Request failed to complete by the system."""


class RobotFaultedError(GraphNavServiceResponseError):
    """Robot is experiencing a fault condition that prevents localization."""


class UnknownMapInformationError(GraphNavServiceResponseError):
    """The given map information (waypoints,edges,routes) is unknown by the system."""


class TimeError(GraphNavServiceResponseError):
    """Errors associated with timestamps and time sync."""
class CommandExpiredError(TimeError):
    """The command was received after its end time had already passed."""
class NoTimeSyncError(TimeError):
    """Client has not performed timesync with robot."""
class TooDistantError(TimeError):
    """The command was too far in the future."""


class RobotStateError(GraphNavServiceResponseError):
    """Errors associated with the current state of the robot."""
class IsRecordingError(RobotStateError):
    """Cannot navigate a route while recording a map."""
class RobotImpairedError(RobotStateError):
    """Robot has a critical perception or behavior fault and cannot navigate."""


class RouteError(GraphNavServiceResponseError):
    """Errors associated with the specified route."""
class ConstraintFaultError(RouteError):
    """Route parameters contained a constraint fault."""
class InvalidEdgeError(RouteError):
    """One or more edges do not connect to expected waypoints."""
class UnkownRouteElementsError(RouteError):
    """One or more waypoints/edges are not in the map."""
class NoPathError(RouteError):
    """There is no path to the specified waypoint."""
class UnknownWaypointError(RouteError):
    """One or more waypoints are not in the map."""


class RouteNavigationError(GraphNavServiceResponseError):
    """Errors related to how the robot navigates the route."""
class FeatureDesertError(RouteNavigationError):
    """Route contained too many waypoints with low-quality features."""
class RouteNotUpdatingError(RouteNavigationError):
    """Graph nav was unable to update and follow the specified route."""
class RobotLostError(RouteNavigationError):
    """Cannot issue a navigation request when the robot is already lost."""
class RobotNotLocalizedToRouteError(RouteNavigationError):
    """The current localization doesn't refer to any waypoint in the route (possibly uninitialized localization)."""


def _localization_from_response(response):
    """Return the localization state from the response."""
    return response.localization


def _command_id_from_navigate_route_response(response):
    """Return the navigation command id from the response."""
    return response.command_id


def _get_status(response):
    """Return the status of the response."""
    return response.status


def _get_response(response):
    """Return full response for RecordStatus to get environment and is_recording information."""
    return response


def _get_graph(response):
    """Returns the graph from the response."""
    return response.graph


def _get_streamed_waypoint_snapshot(response):
    """Reads a streamed response to recreate a waypoint snapshot."""
    data = ''
    num_chunks = 0
    for resp in response:
        if num_chunks == 0:
            data = resp.chunk.data
        else:
            data += resp.chunk.data
        num_chunks += 1
    waypoint_snapshot = map_pb2.WaypointSnapshot()
    if (num_chunks > 0):
        waypoint_snapshot.ParseFromString(data)
    return waypoint_snapshot


def _get_streamed_edge_snapshot(response):
    """Reads a streamed response to recreate a edge snapshot."""
    data = ''
    num_chunks = 0
    for resp in response:
        if num_chunks == 0:
            data = resp.chunk.data
        else:
            data += resp.chunk.data
        num_chunks += 1
    edge_snapshot = map_pb2.EdgeSnapshot()
    if (num_chunks > 0):
        edge_snapshot.ParseFromString(data)
    return edge_snapshot


_SET_LOCALIZATION_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_SET_LOCALIZATION_STATUS_TO_ERROR.update({
    graph_nav_pb2.SetLocalizationResponse.STATUS_OK: (None, None),
    graph_nav_pb2.SetLocalizationResponse.STATUS_ROBOT_IMPAIRED: error_pair(RobotFaultedError),
    graph_nav_pb2.SetLocalizationResponse.STATUS_UNKNOWN_WAYPOINT:
        (UnknownMapInformationError,
         UnknownMapInformationError.__doc__ + " The waypoint is unknown."),
    graph_nav_pb2.SetLocalizationResponse.STATUS_ABORTED: error_pair(RequestAbortedError),
    graph_nav_pb2.SetLocalizationResponse.STATUS_FAILED: error_pair(RequestFailedError),
})


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _set_localization_error(response):
    """Return a custom exception based on set localization response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=graph_nav_pb2.SetLocalizationResponse.Status.Name,
                         status_to_error=_SET_LOCALIZATION_STATUS_TO_ERROR)


_NAVIGATE_ROUTE_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_NAVIGATE_ROUTE_STATUS_TO_ERROR.update({
    graph_nav_pb2.NavigateRouteResponse.STATUS_OK: (None, None),
    graph_nav_pb2.NavigateRouteResponse.STATUS_NO_TIMESYNC:
        error_pair(NoTimeSyncError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_EXPIRED:
        error_pair(CommandExpiredError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_TOO_DISTANT:
        error_pair(TooDistantError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_ROBOT_IMPAIRED:
        error_pair(RobotImpairedError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_RECORDING:
        error_pair(IsRecordingError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_UNKNOWN_ROUTE_ELEMENTS:
        error_pair(UnkownRouteElementsError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_INVALID_EDGE:
        error_pair(InvalidEdgeError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_CONSTRAINT_FAULT:
        error_pair(ConstraintFaultError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_FEATURE_DESERT:
        error_pair(FeatureDesertError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_LOST:
        error_pair(RobotLostError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_NOT_LOCALIZED_TO_ROUTE:
        error_pair(RobotNotLocalizedToRouteError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_COULD_NOT_UPDATE_ROUTE:
        error_pair(RouteNotUpdatingError)
})


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _navigate_route_error(response):
    """Return a custom exception based on navigate route response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=graph_nav_pb2.NavigateRouteResponse.Status.Name,
                         status_to_error=_NAVIGATE_ROUTE_STATUS_TO_ERROR)


_NAVIGATE_TO_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_NAVIGATE_TO_STATUS_TO_ERROR.update({
    graph_nav_pb2.NavigateToResponse.STATUS_OK: (None, None),
    graph_nav_pb2.NavigateToResponse.STATUS_NO_TIMESYNC:
        error_pair(NoTimeSyncError),
    graph_nav_pb2.NavigateToResponse.STATUS_EXPIRED:
        error_pair(CommandExpiredError),
    graph_nav_pb2.NavigateToResponse.STATUS_TOO_DISTANT:
        error_pair(TooDistantError),
    graph_nav_pb2.NavigateToResponse.STATUS_ROBOT_IMPAIRED:
        error_pair(RobotImpairedError),
    graph_nav_pb2.NavigateToResponse.STATUS_RECORDING:
        error_pair(IsRecordingError),
    graph_nav_pb2.NavigateToResponse.STATUS_NO_PATH:
        error_pair(NoPathError),
    graph_nav_pb2.NavigateToResponse.STATUS_UNKNOWN_WAYPOINT:
        error_pair(UnknownWaypointError),
    graph_nav_pb2.NavigateToResponse.STATUS_FEATURE_DESERT:
        error_pair(FeatureDesertError),
    graph_nav_pb2.NavigateToResponse.STATUS_LOST:
        error_pair(RobotLostError),
    graph_nav_pb2.NavigateToResponse.STATUS_NOT_LOCALIZED_TO_MAP:
        error_pair(RobotNotLocalizedToRouteError),
    graph_nav_pb2.NavigateToResponse.STATUS_COULD_NOT_UPDATE_ROUTE:
        error_pair(RouteNotUpdatingError)
})


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _navigate_to_error(response):
    """Return a custom exception based on navigate to response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=graph_nav_pb2.NavigateToResponse.Status.Name,
                         status_to_error=_NAVIGATE_TO_STATUS_TO_ERROR)


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _navigate_feedback_error(response):
    """Return a custom exception based on navigate to response, None if no error."""
    # If the common response header is OK and the status is set, no error.
    return None


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _download_waypoint_snapshot_stream_errors(response):
    """Return a custom exception based on download waypoint snapshot streaming response, None if no error."""
    # Iterate through the response since the download request responds with a stream.
    for resp in response:
        # Handle error statuses from the request.
        if (resp.status ==
                graph_nav_pb2.DownloadWaypointSnapshotResponse.STATUS_SNAPSHOT_DOES_NOT_EXIST):
            return UnknownMapInformationError(response=resp,
                                              error_message=UnknownMapInformationError.__doc__)
    # All responses (in the iterator) had status_ok
    return None


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _download_edge_snapshot_stream_errors(response):
    """Return a custom exception based on download edge snapshot streaming response, None if no error."""
    # Iterate through the response since the download request responds with a stream.
    for resp in response:
        # Handle error statuses from the request.
        if (resp.status == graph_nav_pb2.DownloadEdgeSnapshotResponse.STATUS_SNAPSHOT_DOES_NOT_EXIST
           ):
            return UnknownMapInformationError(response=resp,
                                              error_message=UnknownMapInformationError.__doc__)
    # All responses (in the iterator) had status_ok
    return None
