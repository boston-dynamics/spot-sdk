# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the graphnav service."""
import collections
import math
import os
import time

from deprecated.sphinx import deprecated

from bosdyn.api import data_chunk_pb2, lease_pb2
from bosdyn.api.graph_nav import (graph_nav_pb2, graph_nav_service_pb2, graph_nav_service_pb2_grpc,
                                  map_pb2, nav_pb2)
from bosdyn.client.common import (BaseClient, common_header_errors, common_lease_errors,
                                  error_factory, error_pair, handle_common_header_errors,
                                  handle_lease_use_result_errors, handle_unset_status_error)
from bosdyn.client.exceptions import Error, InvalidRequestError, ResponseError
from bosdyn.client.lease import add_lease_wallet_processors


class GraphNavClient(BaseClient):
    """Client to the GraphNav service."""
    default_service_name = 'graph-nav-service'
    service_type = 'bosdyn.api.graph_nav.GraphNavService'

    def __init__(self):
        super(GraphNavClient, self).__init__(graph_nav_service_pb2_grpc.GraphNavServiceStub)
        self._timesync_endpoint = None
        self._data_chunk_size = 1024 * 1024  # bytes = 1 MB

    def update_from(self, other):
        super(GraphNavClient, self).update_from(other)
        if self.lease_wallet:
            add_lease_wallet_processors(self, self.lease_wallet)

        # Grab a timesync endpoint if it is available.
        try:
            self._timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    def set_localization_full_response(
            self, initial_guess_localization, ko_tform_body=None, max_distance=None, max_yaw=None,
            fiducial_init=graph_nav_pb2.SetLocalizationRequest.FIDUCIAL_INIT_NEAREST,
            use_fiducial_id=None, refine_fiducial_result_with_icp=False, do_ambiguity_check=False,
            refine_with_visual_features=False, verify_visual_features_quality=False, **kwargs):
        """Version of set_localization which returns the full response,
        rather than only the Localization message.
        """
        req = self._build_set_localization_request(
            initial_guess_localization, ko_tform_body, max_distance, max_yaw, fiducial_init,
            use_fiducial_id, refine_fiducial_result_with_icp, do_ambiguity_check,
            refine_with_visual_features, verify_visual_features_quality)
        return self.call(self._stub.SetLocalization, req, _get_response, _set_localization_error,
                         copy_request=False, **kwargs)

    def set_localization_async_full_response(
            self, initial_guess_localization, ko_tform_body=None, max_distance=None, max_yaw=None,
            fiducial_init=graph_nav_pb2.SetLocalizationRequest.FIDUCIAL_INIT_NEAREST,
            use_fiducial_id=None, refine_fiducial_result_with_icp=False, do_ambiguity_check=False,
            refine_with_visual_features=False, verify_visual_features_quality=False, **kwargs):
        """Async version of set_localization_full_response()"""
        req = self._build_set_localization_request(
            initial_guess_localization, ko_tform_body, max_distance, max_yaw, fiducial_init,
            use_fiducial_id, refine_fiducial_result_with_icp, do_ambiguity_check,
            refine_with_visual_features, verify_visual_features_quality)
        return self.call_async(self._stub.SetLocalization, req, _get_response,
                               _set_localization_error, copy_request=False, **kwargs)

    def set_localization(
            self, initial_guess_localization, ko_tform_body=None, max_distance=None, max_yaw=None,
            fiducial_init=graph_nav_pb2.SetLocalizationRequest.FIDUCIAL_INIT_NEAREST,
            use_fiducial_id=None, refine_fiducial_result_with_icp=False, do_ambiguity_check=False,
            refine_with_visual_features=False, verify_visual_features_quality=False, **kwargs):
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
            refine_with_visual_features: Boolean determining if visual features should be used to refine the estimate. When set,
            this value overrides refine_fiducial_result_with_icp.
            verify_visual_features_quality: When refine_with_visual_features is set, determines if an error is asserted when the
            refinement is unsuccessful.
        Returns:
            The resulting localization after being triggered with a guess.
        Raises:
            RpcError: Problem communicating with the robot
            RobotFaultedError: Robot is experiencing a fault condition that prevents localization.
            UnknownMapInformationError: Specified waypoint is unknown.
            bosdyn.client.exceptions.InvalidRequestError: The data provided is incomplete or invalid
            GraphNavServiceResponseError: Localization was aborted or failed.
        """
        req = self._build_set_localization_request(
            initial_guess_localization, ko_tform_body, max_distance, max_yaw, fiducial_init,
            use_fiducial_id, refine_fiducial_result_with_icp, do_ambiguity_check,
            refine_with_visual_features, verify_visual_features_quality)
        return self.call(self._stub.SetLocalization, req, _localization_from_response,
                         _set_localization_error, copy_request=False, **kwargs)

    def set_localization_async(
            self, initial_guess_localization, ko_tform_body=None, max_distance=None, max_yaw=None,
            fiducial_init=graph_nav_pb2.SetLocalizationRequest.FIDUCIAL_INIT_NEAREST,
            use_fiducial_id=None, refine_fiducial_result_with_icp=False, do_ambiguity_check=False,
            refine_with_visual_features=False, verify_visual_features_quality=False, **kwargs):
        """Async version of set_localization()"""
        req = self._build_set_localization_request(
            initial_guess_localization, ko_tform_body, max_distance, max_yaw, fiducial_init,
            use_fiducial_id, refine_fiducial_result_with_icp, do_ambiguity_check,
            refine_with_visual_features, verify_visual_features_quality)
        return self.call_async(self._stub.SetLocalization, req, _localization_from_response,
                               _set_localization_error, copy_request=False, **kwargs)

    def get_localization_state(
            self,
            request_live_point_cloud=False,
            request_live_images=False,
            request_live_terrain_maps=False,
            request_live_world_objects=False,
            request_live_robot_state=False,
            waypoint_id=None,
            request_gps_state=False,
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
            request_live_robot_state=request_live_robot_state, waypoint_id=waypoint_id,
            request_gps_state=request_gps_state)
        return self.call(self._stub.GetLocalizationState, req, None, common_header_errors,
                         copy_request=False, **kwargs)

    def get_localization_state_async(
            self, request_live_point_cloud=False, request_live_images=False,
            request_live_terrain_maps=False, request_live_world_objects=False,
            request_live_robot_state=False, waypoint_id=None, request_gps_state=False, **kwargs):
        """Async version of get_localization_state()."""
        req = self._build_get_localization_state_request(
            request_live_point_cloud=request_live_point_cloud,
            request_live_images=request_live_images,
            request_live_terrain_maps=request_live_terrain_maps,
            request_live_world_objects=request_live_world_objects,
            request_live_robot_state=request_live_robot_state, waypoint_id=waypoint_id,
            request_gps_state=request_gps_state)
        return self.call_async(self._stub.GetLocalizationState, req, None, common_header_errors,
                               copy_request=False, **kwargs)

    def navigate_route(self, route, cmd_duration, route_follow_params=None, travel_params=None,
                       leases=None, timesync_endpoint=None, command_id=None,
                       destination_waypoint_tform_body_goal=None, **kwargs):
        """Navigate the given route.

        Args:
            route: Route protobuf of the route to follow.
            route_follow_params: What should the robot do if it is not at the expected point in the
            route, or the route is blocked.
            travel_params: API TravelParams for the route.
            cmd_duration: Number of seconds the command can run for.
            leases: Leases to show ownership of necessary resources. Will use the client's leases by default.
            timesync_endpoint: Use this endpoint for timesync fields. Will use the client's endpoint by default.
            command_id: If not None, this continues an existing navigate_route command with the given ID. If None,
            a new command_id will be used.
            destination_waypoint_tform_body_goal: SE2Pose protobuf of an offset relative to the destination waypoint.
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
            graph_nav.UnknownRouteElementsError: Unknown edges or waypoints
            graph_nav.InvalidEdgeError: Mismatch between edges and waypoints.
            graph_nav.NoPathError: No path to the specified route.
            graph_nav.RobotNotLocalizedToRouteError: The robot is localized somewhere else.
            graph_nav.ConstraintFaultError: The route involves invalid constraints.
            graph_nav.RouteNavigationError: A subclass detailing trouble navigating the route.
        """
        used_endpoint = timesync_endpoint or self._timesync_endpoint
        if not used_endpoint:
            raise GraphNavServiceResponseError(response=None, error_message='No timesync endpoint!')
        request = self._build_navigate_route_request(route, route_follow_params, travel_params,
                                                     cmd_duration, leases, used_endpoint,
                                                     command_id,
                                                     destination_waypoint_tform_body_goal)
        return self.call(self._stub.NavigateRoute, request,
                         _command_id_from_navigate_route_response, _navigate_route_error,
                         copy_request=False, **kwargs)

    def navigate_route_async(self, route, cmd_duration, route_follow_params=None,
                             travel_params=None, leases=None, timesync_endpoint=None,
                             command_id=None, destination_waypoint_tform_body_goal=None, **kwargs):
        """Async version of navigate_route()"""
        used_endpoint = timesync_endpoint or self._timesync_endpoint
        if not used_endpoint:
            raise GraphNavServiceResponseError(response=None, error_message='No timesync endpoint!')
        request = self._build_navigate_route_request(route, route_follow_params, travel_params,
                                                     cmd_duration, leases, used_endpoint,
                                                     command_id,
                                                     destination_waypoint_tform_body_goal)
        return self.call_async(self._stub.NavigateRoute, request,
                               _command_id_from_navigate_route_response, _navigate_route_error,
                               copy_request=False, **kwargs)

    def navigate_route_full(self, route, route_follow_params, cmd_duration, travel_params=None,
                            leases=None, timesync_endpoint=None, command_id=None,
                            destination_waypoint_tform_body_goal=None, **kwargs):
        """Identical to navigate_route(), except will return the full NavigateRouteResponse."""
        used_endpoint = timesync_endpoint or self._timesync_endpoint
        if not used_endpoint:
            raise GraphNavServiceResponseError(response=None, error_message='No timesync endpoint!')
        request = self._build_navigate_route_request(route, route_follow_params, travel_params,
                                                     cmd_duration, leases, used_endpoint,
                                                     command_id,
                                                     destination_waypoint_tform_body_goal)
        return self.call(self._stub.NavigateRoute, request,
                         error_from_response=_navigate_route_error, copy_request=False, **kwargs)

    def navigate_route_full_async(self, route, cmd_duration, route_follow_params=None,
                                  travel_params=None, leases=None, timesync_endpoint=None,
                                  command_id=None, destination_waypoint_tform_body_goal=None,
                                  **kwargs):
        """Async version of navigate_route_full()."""
        used_endpoint = timesync_endpoint or self._timesync_endpoint
        if not used_endpoint:
            raise GraphNavServiceResponseError(response=None, error_message='No timesync endpoint!')
        request = self._build_navigate_route_request(route, route_follow_params, travel_params,
                                                     cmd_duration, leases, used_endpoint,
                                                     command_id,
                                                     destination_waypoint_tform_body_goal)
        return self.call_async(self._stub.NavigateRoute, request,
                               error_from_response=_navigate_route_error, copy_request=False,
                               **kwargs)

    def navigate_to(self, destination_waypoint_id, cmd_duration, route_params=None,
                    travel_params=None, leases=None, timesync_endpoint=None, command_id=None,
                    destination_waypoint_tform_body_goal=None, route_blocked_behavior=None,
                    **kwargs):
        """Navigate to a specific waypoint along a route chosen by the GraphNav service.

        Args:
            destination_waypoint_id: Waypoint id string for where to go to.
            cmd_duration: Number of seconds the command can run for.
            route_params: API RouteGenParams for the route.
            travel_params: API TravelParams for the route.
            leases: Leases to show ownership of necessary resources. Will use the client's leases by default.
            timesync_endpoint: Use this endpoint for timesync fields. Will use the client's endpoint by default.
            command_id: If not None, this continues an existing navigate_to command with the given ID. If None,
            a new command_id will be used.
            destination_waypoint_tform_body_goal: SE2Pose protobuf of an offset relative to the destination waypoint.
            route_blocked_behavior: Defines robot behavior when route is block. If None robot will reroute.
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
                                                  route_params, cmd_duration, leases, used_endpoint,
                                                  command_id, destination_waypoint_tform_body_goal,
                                                  route_blocked_behavior)
        return self.call(self._stub.NavigateTo, request,
                         value_from_response=_command_id_from_navigate_route_response,
                         error_from_response=_navigate_to_error, copy_request=False, **kwargs)

    def navigate_to_async(self, destination_waypoint_id, cmd_duration, route_params=None,
                          travel_params=None, leases=None, timesync_endpoint=None, command_id=None,
                          destination_waypoint_tform_body_goal=None, route_blocked_behavior=None,
                          **kwargs):
        """Async version of navigate_to()."""
        used_endpoint = timesync_endpoint or self._timesync_endpoint
        if not used_endpoint:
            raise GraphNavServiceResponseError(response=None, error_message='No timesync endpoint!')
        request = self._build_navigate_to_request(destination_waypoint_id, travel_params,
                                                  route_params, cmd_duration, leases, used_endpoint,
                                                  command_id, destination_waypoint_tform_body_goal,
                                                  route_blocked_behavior)
        return self.call_async(self._stub.NavigateTo, request,
                               value_from_response=_command_id_from_navigate_route_response,
                               error_from_response=_navigate_to_error, copy_request=False, **kwargs)

    def navigate_to_full(self, destination_waypoint_id, cmd_duration, route_params=None,
                         travel_params=None, leases=None, timesync_endpoint=None, command_id=None,
                         destination_waypoint_tform_body_goal=None, route_blocked_behavior=None,
                         **kwargs):
        """Identical to navigate_to(), except will return the full NavigateToResponse."""
        used_endpoint = timesync_endpoint or self._timesync_endpoint
        if not used_endpoint:
            raise GraphNavServiceResponseError(response=None, error_message='No timesync endpoint!')
        request = self._build_navigate_to_request(destination_waypoint_id, travel_params,
                                                  route_params, cmd_duration, leases, used_endpoint,
                                                  command_id, destination_waypoint_tform_body_goal,
                                                  route_blocked_behavior)
        return self.call(self._stub.NavigateTo, request, error_from_response=_navigate_to_error,
                         copy_request=False, **kwargs)

    def navigate_to_full_async(self, destination_waypoint_id, cmd_duration, route_params=None,
                               travel_params=None, leases=None, timesync_endpoint=None,
                               command_id=None, destination_waypoint_tform_body_goal=None,
                               route_blocked_behavior=None, **kwargs):
        """Async version of navigate_to_full()."""
        used_endpoint = timesync_endpoint or self._timesync_endpoint
        if not used_endpoint:
            raise GraphNavServiceResponseError(response=None, error_message='No timesync endpoint!')
        request = self._build_navigate_to_request(destination_waypoint_id, travel_params,
                                                  route_params, cmd_duration, leases, used_endpoint,
                                                  command_id, destination_waypoint_tform_body_goal,
                                                  route_blocked_behavior)
        return self.call_async(self._stub.NavigateTo, request,
                               error_from_response=_navigate_to_error, copy_request=False, **kwargs)

    def navigate_to_anchor(self, seed_tform_goal, cmd_duration, route_params=None,
                           travel_params=None, leases=None, timesync_endpoint=None,
                           goal_waypoint_rt_seed_ewrt_seed_tolerance=None, command_id=None,
                           gps_navigation_params=None, **kwargs):
        """Navigate to a pose in seed frame along a route chosen by the GraphNav service.

        Args:
            seed_tform_goal: SE3Pose protobuf of the goal pose in seed frame.
            cmd_duration: Number of seconds the command can run for.
            route_params: API RouteGenParams for the route.
            travel_params: API TravelParams for the route.
            leases: Leases to show ownership of necessary resources. Will use the client's leases by default.
            timesync_endpoint: Use this endpoint for timesync fields. Will use the client's endpoint by default.
            goal_waypoint_rt_seed_ewrt_seed_tolerance: Vec3 protobuf of the tolerances for goal waypoint selection.
            command_id: If not None, this continues an existing navigate_to command with the given ID. If None,
            a new command_id will be used.
            gps_navigation_params: API GPSNavigationParams. If not None, this will be interpreted as a GPS-based
            navigation command. seed_tform_goal will be ignored and whatever goal is passed in using the GPS
            navigation params will be used.
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
            graph_nav.NoAnchoringError: There is no anchoring.
            graph_nav.NoPathError: No route to goal waypoint, or no goal waypoint found.
            graph_nav.InvalidPoseError: The requested pose is invalid, or known to be unachievable.
            graph_nav.RobotNotLocalizedToRouteError: The robot not correctly localized.
            graph_nav.RouteNavigationError: A subclass detailing trouble navigating the route.
        """
        used_endpoint = timesync_endpoint or self._timesync_endpoint
        if not used_endpoint:
            raise GraphNavServiceResponseError(response=None, error_message='No timesync endpoint!')
        request = self._build_navigate_to_anchor_request(
            seed_tform_goal, travel_params, route_params, cmd_duration, leases, used_endpoint,
            command_id, goal_waypoint_rt_seed_ewrt_seed_tolerance, gps_navigation_params)
        return self.call(self._stub.NavigateToAnchor, request,
                         value_from_response=_command_id_from_navigate_route_response,
                         error_from_response=_navigate_to_anchor_error, copy_request=False,
                         **kwargs)

    def navigate_to_anchor_async(self, seed_tform_goal, cmd_duration, route_params=None,
                                 travel_params=None, leases=None, timesync_endpoint=None,
                                 goal_waypoint_rt_seed_ewrt_seed_tolerance=None, command_id=None,
                                 gps_navigation_params=None, **kwargs):
        """Async version of navigate_to_anchor()."""
        used_endpoint = timesync_endpoint or self._timesync_endpoint
        if not used_endpoint:
            raise GraphNavServiceResponseError(response=None, error_message='No timesync endpoint!')
        request = self._build_navigate_to_anchor_request(
            seed_tform_goal, travel_params, route_params, cmd_duration, leases, used_endpoint,
            command_id, goal_waypoint_rt_seed_ewrt_seed_tolerance, gps_navigation_params)
        return self.call_async(self._stub.NavigateTo, request,
                               value_from_response=_command_id_from_navigate_route_response,
                               error_from_response=_navigate_to_anchor_error, copy_request=False,
                               **kwargs)

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
                         error_from_response=_navigate_feedback_error, copy_request=False, **kwargs)

    def navigation_feedback_async(self, command_id=0, **kwargs):
        """Async version of navigation_feedback()."""
        request = self._build_navigate_feedback_request(command_id)
        return self.call_async(self._stub.NavigationFeedback, request,
                               value_from_response=_get_response,
                               error_from_response=_navigate_feedback_error, copy_request=False,
                               **kwargs)

    def clear_graph(self, lease=None, **kwargs):
        """Clears the local graph structure. Also erases any snapshots currently in RAM.

        Args:
            lease: Leases to show ownership of necessary resources. Will use the client's leases by default.
        Raises:
            RpcError: Problem communicating with the robot.
            LeaseUseError: Error using provided lease.
        """
        request = self._build_clear_graph_request(lease)
        return self.call(self._stub.ClearGraph, request, value_from_response=None,
                         error_from_response=_clear_graph_error, copy_request=False, **kwargs)

    def clear_graph_async(self, lease=None, **kwargs):
        """Async version of clear_graph()."""
        request = self._build_clear_graph_request(lease)
        return self.call_async(self._stub.ClearGraph, request, value_from_response=None,
                               error_from_response=handle_common_header_errors(common_lease_errors),
                               copy_request=False, **kwargs)

    def upload_graph(self, lease=None, graph=None, generate_new_anchoring=False, **kwargs):
        """Uploads a graph to the server and appends to the existing graph.

        Args:
            lease: Leases to show ownership of necessary resources. Will use the client's leases by default.
            graph: Graph protobuf that represents the map with waypoints and edges.
            generate_new_anchoring: Whether to generate an (overwrite the) anchoring on upload.
        Returns:
            The response, which includes waypoint and edge id's sorted by whether it was cached.
        Raises:
            RpcError: Problem communicating with the robot.
            LeaseUseError: Error using provided lease.
        """
        request = self._build_upload_graph_request(lease, graph, generate_new_anchoring)
        return self.call(self._stub.UploadGraph, request, value_from_response=_get_response,
                         error_from_response=_upload_graph_error, copy_request=False, **kwargs)

    def upload_graph_async(self, lease=None, graph=None, generate_new_anchoring=False, **kwargs):
        """Async version of upload_graph()."""
        request = self._build_upload_graph_request(lease, graph, generate_new_anchoring)
        return self.call_async(self._stub.UploadGraph, request, value_from_response=_get_response,
                               error_from_response=_upload_graph_error, copy_request=False,
                               **kwargs)

    def upload_waypoint_snapshot(self, waypoint_snapshot, lease=None, **kwargs):
        """Uploads large waypoint snapshot as a stream for a particular waypoint.

        Args:
            lease: Leases to show ownership of necessary resources. Will use the client's leases by default.
            waypoint_snapshot: WaypointSnapshot protobuf that will be stream-uploaded to the robot.
        Returns:
            The status of the upload request.
        Raises:
            RpcError: Problem communicating with the robot.
            LeaseUseError: Error using provided lease.
        """
        lease = lease or lease_pb2.Lease()
        serialized = waypoint_snapshot.SerializeToString()
        self.call(
            self._stub.UploadWaypointSnapshot,
            GraphNavClient._data_chunk_iterator_upload_waypoint_snapshot(
                serialized, lease, self._data_chunk_size), value_from_response=None,
            error_from_response=_upload_waypoint_snapshot_error, **kwargs)

    def upload_edge_snapshot(self, edge_snapshot, lease=None, **kwargs):
        """Uploads large edge snapshot as a stream for a particular edge.

        Args:
            lease: Leases to show ownership of necessary resources. Will use the client's leases by default.
            edge_snapshot: EdgeSnapshot protobuf that will be stream-uploaded to the robot.
        Returns:
            The status of the upload request.
        Raises:
            RpcError: Problem communicating with the robot.
            LeaseUseError: Error using provided leases.
        """
        lease = lease or lease_pb2.Lease()
        serialized = edge_snapshot.SerializeToString()
        self.call(
            self._stub.UploadEdgeSnapshot,
            GraphNavClient._data_chunk_iterator_upload_edge_snapshot(serialized, lease,
                                                                     self._data_chunk_size),
            value_from_response=None,
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
                         error_from_response=common_header_errors, copy_request=False, **kwargs)

    def download_graph_async(self, **kwargs):
        """Async version of download_graph()."""
        request = self._build_download_graph_request()
        return self.call_async(self._stub.DownloadGraph, request, value_from_response=_get_graph,
                               error_from_response=common_header_errors, copy_request=False,
                               **kwargs)

    def download_waypoint_snapshot(
            self,
            waypoint_snapshot_id,
            download_images=False,
            do_not_download_point_cloud=False,
            **kwargs):
        """Download a specific waypoint snapshot with streaming from the server.

        Args:
            waypoint_snapshot_id: WaypointSnapshot string ID for which snapshot to download from robot.
            download_images: Boolean indicating whether to include images in the download.
            do_not_download_point_cloud: Boolean indicating if point cloud data should not be downloaded.
        Returns:
            The WaypointSnapshot protobuf from the robot's current map.
        Raises:
            RpcError: Problem communicating with the robot
            UnknownMapInformationError: Snapshot id not found
        """
        request = self._build_download_waypoint_snapshot_request(
            waypoint_snapshot_id,
            download_images,
            do_not_download_point_cloud)
        return self.call(self._stub.DownloadWaypointSnapshot, request,
                         value_from_response=_get_streamed_waypoint_snapshot,
                         error_from_response=_download_waypoint_snapshot_stream_errors,
                         copy_request=False, **kwargs)


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
                         error_from_response=_download_edge_snapshot_stream_errors,
                         copy_request=False, **kwargs)


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
            if len(waypoint.snapshot_id) == 0:
                continue
            waypoint_snapshot = self.download_waypoint_snapshot(waypoint.snapshot_id)
            self._write_bytes(directory + '/waypoint_snapshots', '/' + waypoint.snapshot_id,
                              waypoint_snapshot.SerializeToString())

        for edge in graph.edges:
            if len(edge.snapshot_id) == 0:
                continue
            edge_snapshot = self.download_edge_snapshot(edge.snapshot_id)
            self._write_bytes(directory + '/edge_snapshots', '/' + edge.snapshot_id,
                              edge_snapshot.SerializeToString())

    @staticmethod
    def _build_set_localization_request(
            initial_guess_localization, ko_tform_body=None, max_distance=None, max_yaw=None,
            fiducial_init=graph_nav_pb2.SetLocalizationRequest.FIDUCIAL_INIT_NEAREST,
            use_fiducial_id=None, refine_fiducial_result_with_icp=False, do_ambiguity_check=False,
            refine_with_visual_features=False, verify_visual_features_quality=False):
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

        if refine_with_visual_features:
            request.refine_with_visual_features.verify_refinement_quality = verify_visual_features_quality
        elif refine_fiducial_result_with_icp:
            request.refine_fiducial_result_with_icp = refine_fiducial_result_with_icp
        request.do_ambiguity_check = do_ambiguity_check
        return request

    @staticmethod
    def _build_get_localization_state_request(request_live_point_cloud, request_live_images,
                                              request_live_terrain_maps, request_live_world_objects,
                                              request_live_robot_state, waypoint_id,
                                              request_gps_state):
        return graph_nav_pb2.GetLocalizationStateRequest(
            request_live_point_cloud=request_live_point_cloud,
            request_live_images=request_live_images,
            request_live_terrain_maps=request_live_terrain_maps,
            request_live_world_objects=request_live_world_objects,
            request_live_robot_state=request_live_robot_state, waypoint_id=waypoint_id,
            request_gps_state=request_gps_state)

    @staticmethod
    def _build_navigate_route_request(route, route_follow_params, travel_params, end_time_secs,
                                      leases, timesync_endpoint, command_id,
                                      destination_waypoint_tform_body_goal):
        converter = timesync_endpoint.get_robot_time_converter()
        request = graph_nav_pb2.NavigateRouteRequest(
            route=route, route_follow_params=route_follow_params,
            destination_waypoint_tform_body_goal=destination_waypoint_tform_body_goal,
            clock_identifier=timesync_endpoint.clock_identifier)
        if travel_params is not None:
            request.travel_params.CopyFrom(travel_params)
        request.end_time.CopyFrom(
            converter.robot_timestamp_from_local_secs(time.time() + end_time_secs))
        if command_id is not None:
            request.command_id = command_id
        return request

    @staticmethod
    def _build_navigate_to_request(destination_waypoint_id, travel_params, route_params,
                                   end_time_secs, leases, timesync_endpoint, command_id,
                                   destination_waypoint_tform_body_goal, route_blocked_behavior):
        converter = timesync_endpoint.get_robot_time_converter()
        request = graph_nav_pb2.NavigateToRequest(
            destination_waypoint_id=destination_waypoint_id,
            destination_waypoint_tform_body_goal=destination_waypoint_tform_body_goal,
            clock_identifier=timesync_endpoint.clock_identifier)
        request.end_time.CopyFrom(
            converter.robot_timestamp_from_local_secs(time.time() + end_time_secs))
        if travel_params is not None:
            request.travel_params.CopyFrom(travel_params)
        if route_params is not None:
            request.route_params.CopyFrom(route_params)
        if command_id is not None:
            request.command_id = command_id
        if route_blocked_behavior is not None:
            request.route_blocked_behavior = route_blocked_behavior
        return request

    @staticmethod
    def _build_navigate_to_anchor_request(seed_tform_goal, travel_params, route_params,
                                          end_time_secs, leases, timesync_endpoint, command_id,
                                          goal_waypoint_rt_seed_ewrt_seed_tolerance,
                                          gps_navigation_params):
        converter = timesync_endpoint.get_robot_time_converter()
        request = graph_nav_pb2.NavigateToAnchorRequest(
            seed_tform_goal=seed_tform_goal,
            goal_waypoint_rt_seed_ewrt_seed_tolerance=goal_waypoint_rt_seed_ewrt_seed_tolerance,
            clock_identifier=timesync_endpoint.clock_identifier)
        # Note that this overrides the seed_tform_goal, which is a OneOf.
        if gps_navigation_params:
            request.gps_navigation_params.CopyFrom(gps_navigation_params)
        request.end_time.CopyFrom(
            converter.robot_timestamp_from_local_secs(time.time() + end_time_secs))
        if travel_params is not None:
            request.travel_params.CopyFrom(travel_params)
        if route_params is not None:
            request.route_params.CopyFrom(route_params)
        if command_id is not None:
            request.command_id = command_id
        return request

    @staticmethod
    def _build_clear_graph_request(lease):
        lease = lease or lease_pb2.Lease()
        return graph_nav_pb2.ClearGraphRequest(lease=lease)

    @staticmethod
    def _build_navigate_feedback_request(command_id=0):
        return graph_nav_pb2.NavigationFeedbackRequest(command_id=command_id)

    @staticmethod
    def _build_upload_graph_request(lease, graph, generate_new_anchoring):
        lease = lease or lease_pb2.Lease()
        return graph_nav_pb2.UploadGraphRequest(lease=lease, graph=graph,
                                                generate_new_anchoring=generate_new_anchoring)

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
            req = graph_nav_pb2.UploadEdgeSnapshotRequest(lease=lease, chunk=chunk)
            yield req

    @staticmethod
    def _build_download_graph_request():
        return graph_nav_pb2.DownloadGraphRequest()

    @staticmethod
    def _build_download_waypoint_snapshot_request(
            waypoint_snapshot_id,
            download_images,
            do_not_download_point_cloud=False):
        return graph_nav_pb2.DownloadWaypointSnapshotRequest(
            waypoint_snapshot_id=waypoint_snapshot_id,
            download_images=download_images,
            do_not_download_point_cloud=do_not_download_point_cloud)

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
    def build_route(waypoint_id_list, edge_id_list):
        """ Generate the API Route for navigation requests.

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


class UploadWaypointSnapshotError(GraphNavServiceResponseError):
    """Errors related to uploading a waypoint snapshot"""


class UploadGraphError(GraphNavServiceResponseError):
    """Errors related to uploading a graph."""


class MapTooLargeLicenseError(UploadGraphError):
    """The map is too large for the license on the robot."""


class InvalidGraphError(UploadGraphError):
    """The graph is invalid topologically, e.g. missing waypoints referenced by edges."""


class IncompatibleSensorsError(GraphNavServiceResponseError):
    """The map was recorded with using a sensor configuration which is incompatible with the robot (for example, LIDAR configuration)."""


class AreaCallbackMapError(GraphNavServiceResponseError):
    """The map specified an area callback that is not registered or is faulted."""


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


class CannotModifyMapDuringRecordingError(RobotStateError):
    """Cannot clear the map during recording. Call StopRecording first."""


class RobotImpairedError(RobotStateError):
    """Robot has a critical perception or behavior fault and cannot navigate."""


class RouteError(GraphNavServiceResponseError):
    """Errors associated with the specified route."""


class ConstraintFaultError(RouteError):
    """Route parameters contained a constraint fault."""


class InvalidEdgeError(RouteError):
    """One or more edges do not connect to expected waypoints."""


@deprecated(reason='Use UnknownRouteElementsError instead', version='3.0.0', action='ignore')
class UnkownRouteElementsError(RouteError):
    """One or more waypoints/edges are not in the map."""


class UnknownRouteElementsError(UnkownRouteElementsError):
    """One or more waypoints/edges are not in the map."""


class NoPathError(RouteError):
    """There is no path to the specified waypoint."""


class UnknownWaypointError(RouteError):
    """One or more waypoints are not in the map."""


class NoAnchoringError(RouteError):
    """There is no anchoring."""


class InvalidPoseError(RouteError):
    """The requested pose is invalid, or known to be unachievable."""


class RouteNavigationError(GraphNavServiceResponseError):
    """Errors related to how the robot navigates the route."""


class FeatureDesertError(RouteNavigationError):
    """Route contained too many waypoints with low-quality features."""


class RouteNotUpdatingError(RouteNavigationError):
    """Graph nav was unable to update and follow the specified route."""


class RobotLostError(RouteNavigationError):
    """Cannot issue a navigation request when the robot is already lost."""


class InvalidGPSError(RouteNavigationError):
    """Cannot issue the GPS command because it is invalid."""

    def _gps_status_to_string(self, status):
        if status == graph_nav_pb2.NavigateToAnchorResponse.GPS_STATUS_OK:
            return 'OK'
        elif status == graph_nav_pb2.NavigateToAnchorResponse.GPS_STATUS_NO_COORDS_IN_MAP:
            return 'The uploaded map did not contain any valid GPS coordinates.'
        elif status == graph_nav_pb2.NavigateToAnchorResponse.GPS_STATUS_TOO_FAR_FROM_MAP:
            return 'The given coordinates were too far from any coordinates in the uploaded map.'
        else:
            return 'Unknown error'

    def __str__(self):
        return f'{self.error_message} (reason: {self._gps_status_to_string(self.response.gps_status)})'


class RobotNotLocalizedToRouteError(RouteNavigationError):
    """The current localization doesn't refer to any waypoint in the route (possibly uninitialized localization)."""


class RobotStuckError(RouteNavigationError):
    """The robot is stuck or unable to find a way forward. Resend the command with a new ID, or send a different command to try again."""


@deprecated(reason='Use UnrecognizedCommandError instead', version='3.1.0', action='ignore')
class UnrecongizedCommandError(RouteNavigationError):
    """Happens when you try to continue a command that was either expired, or had an unrecognized id."""


class UnrecognizedCommandError(UnrecongizedCommandError):
    """Happens when you try to continue a command that was either expired, or had an unrecognized id."""


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
    """Reads a streamed response to recreate an edge snapshot."""
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


_UPLOAD_GRAPH_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_UPLOAD_GRAPH_STATUS_TO_ERROR.update({
    graph_nav_pb2.UploadGraphResponse.STATUS_OK: (None, None),
    graph_nav_pb2.UploadGraphResponse.STATUS_MAP_TOO_LARGE_LICENSE:
        error_pair(MapTooLargeLicenseError),
    graph_nav_pb2.UploadGraphResponse.STATUS_INVALID_GRAPH:
        error_pair(InvalidGraphError),
    graph_nav_pb2.UploadGraphResponse.STATUS_INCOMPATIBLE_SENSORS:
        error_pair(IncompatibleSensorsError),
    graph_nav_pb2.UploadGraphResponse.STATUS_AREA_CALLBACK_ERROR:
        error_pair(AreaCallbackMapError),
})


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _upload_graph_error(response):
    """Return a custom exception based on upload graph response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=graph_nav_pb2.UploadGraphResponse.Status.Name,
                         status_to_error=_UPLOAD_GRAPH_STATUS_TO_ERROR)


_UPLOAD_WAYPOINT_SNAPSHOT_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_UPLOAD_WAYPOINT_SNAPSHOT_TO_ERROR.update({
    graph_nav_pb2.UploadWaypointSnapshotResponse.STATUS_UNKNOWN: (None, None),
    graph_nav_pb2.UploadWaypointSnapshotResponse.STATUS_OK: (None, None),
    graph_nav_pb2.UploadWaypointSnapshotResponse.STATUS_INCOMPATIBLE_SENSORS:
        error_pair(IncompatibleSensorsError)
})

_CLEAR_GRAPH_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_CLEAR_GRAPH_STATUS_TO_ERROR.update({
    # Unknown should not produce an error for backwards compatibility purposes (introduced in 3.1).
    graph_nav_pb2.ClearGraphResponse.STATUS_UNKNOWN: (None, None),
    graph_nav_pb2.ClearGraphResponse.STATUS_OK: (None, None),
    graph_nav_pb2.ClearGraphResponse.STATUS_RECORDING:
        error_pair(CannotModifyMapDuringRecordingError),
})


@handle_common_header_errors
@handle_lease_use_result_errors
def _clear_graph_error(response):
    """Return a custom exception based on upload graph response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=graph_nav_pb2.ClearGraphResponse.Status.Name,
                         status_to_error=_CLEAR_GRAPH_STATUS_TO_ERROR)


@handle_common_header_errors
@handle_lease_use_result_errors
def _upload_waypoint_snapshot_error(response):
    """Return a custom exception based on upload graph response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=graph_nav_pb2.UploadWaypointSnapshotResponse.Status.Name,
                         status_to_error=_UPLOAD_WAYPOINT_SNAPSHOT_TO_ERROR)


_SET_LOCALIZATION_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_SET_LOCALIZATION_STATUS_TO_ERROR.update({
    graph_nav_pb2.SetLocalizationResponse.STATUS_OK: (None, None),
    graph_nav_pb2.SetLocalizationResponse.STATUS_ROBOT_IMPAIRED:
        error_pair(RobotFaultedError),
    graph_nav_pb2.SetLocalizationResponse.STATUS_UNKNOWN_WAYPOINT:
        (UnknownMapInformationError,
         UnknownMapInformationError.__doc__ + " The waypoint is unknown."),
    graph_nav_pb2.SetLocalizationResponse.STATUS_ABORTED:
        error_pair(RequestAbortedError),
    graph_nav_pb2.SetLocalizationResponse.STATUS_FAILED:
        error_pair(RequestFailedError),
    graph_nav_pb2.SetLocalizationResponse.STATUS_INCOMPATIBLE_SENSORS:
        error_pair(IncompatibleSensorsError)
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
        error_pair(UnknownRouteElementsError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_INVALID_EDGE:
        error_pair(InvalidEdgeError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_NO_PATH:
        error_pair(NoPathError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_CONSTRAINT_FAULT:
        error_pair(ConstraintFaultError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_FEATURE_DESERT:
        error_pair(FeatureDesertError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_LOST:
        error_pair(RobotLostError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_NOT_LOCALIZED_TO_ROUTE:
        error_pair(RobotNotLocalizedToRouteError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_NOT_LOCALIZED_TO_MAP:
        error_pair(RobotNotLocalizedToRouteError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_COULD_NOT_UPDATE_ROUTE:
        error_pair(RouteNotUpdatingError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_STUCK:
        error_pair(RobotStuckError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_UNRECOGNIZED_COMMAND:
        error_pair(UnrecognizedCommandError),
    graph_nav_pb2.NavigateRouteResponse.STATUS_AREA_CALLBACK_ERROR:
        error_pair(AreaCallbackMapError),
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
        error_pair(RouteNotUpdatingError),
    graph_nav_pb2.NavigateToResponse.STATUS_STUCK:
        error_pair(RobotStuckError),
    graph_nav_pb2.NavigateToResponse.STATUS_UNRECOGNIZED_COMMAND:
        error_pair(UnrecognizedCommandError),
    graph_nav_pb2.NavigateToResponse.STATUS_AREA_CALLBACK_ERROR:
        error_pair(AreaCallbackMapError),
})


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _navigate_to_error(response):
    """Return a custom exception based on navigate to response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=graph_nav_pb2.NavigateToResponse.Status.Name,
                         status_to_error=_NAVIGATE_TO_STATUS_TO_ERROR)


_NAVIGATE_TO_ANCHOR_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_NAVIGATE_TO_ANCHOR_STATUS_TO_ERROR.update({
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_OK: (None, None),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_NO_TIMESYNC:
        error_pair(NoTimeSyncError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_EXPIRED:
        error_pair(CommandExpiredError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_TOO_DISTANT:
        error_pair(TooDistantError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_ROBOT_IMPAIRED:
        error_pair(RobotImpairedError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_RECORDING:
        error_pair(IsRecordingError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_NO_PATH:
        error_pair(NoPathError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_NO_ANCHORING:
        error_pair(NoAnchoringError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_FEATURE_DESERT:
        error_pair(FeatureDesertError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_LOST:
        error_pair(RobotLostError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_NOT_LOCALIZED_TO_MAP:
        error_pair(RobotNotLocalizedToRouteError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_COULD_NOT_UPDATE_ROUTE:
        error_pair(RouteNotUpdatingError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_STUCK:
        error_pair(RobotStuckError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_INVALID_POSE:
        error_pair(InvalidPoseError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_UNRECOGNIZED_COMMAND:
        error_pair(UnrecognizedCommandError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_AREA_CALLBACK_ERROR:
        error_pair(AreaCallbackMapError),
    graph_nav_pb2.NavigateToAnchorResponse.STATUS_INVALID_GPS_COMMAND:
        error_pair(InvalidGPSError)
})


@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _navigate_to_anchor_error(response):
    """Return a custom exception based on navigate to anchor response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=graph_nav_pb2.NavigateToAnchorResponse.Status.Name,
                         status_to_error=_NAVIGATE_TO_ANCHOR_STATUS_TO_ERROR)


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
