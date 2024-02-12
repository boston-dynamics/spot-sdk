# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients of the graph_nav map processing service."""

import collections
from enum import Enum

from bosdyn.api.graph_nav import map_pb2, map_processing_pb2, map_processing_service_pb2
from bosdyn.api.graph_nav import map_processing_service_pb2_grpc as map_processing
from bosdyn.client.common import (BaseClient, common_header_errors, error_factory,
                                  handle_common_header_errors, handle_lease_use_result_errors,
                                  handle_unset_status_error)
from bosdyn.client.exceptions import ResponseError


class MapProcessingServiceResponseError(ResponseError):
    """General class of errors for the GraphNav map processing service."""


class MissingSnapshotsError(MapProcessingServiceResponseError):
    """The uploaded map has missing waypoint snapshots."""


class OptimizationFailureError(MapProcessingServiceResponseError):
    """The anchoring optimization failed."""


class InvalidGraphError(MapProcessingServiceResponseError):
    """The graph is invalid topologically, for example containing missing waypoints referenced by edges."""


class InvalidParamsError(MapProcessingServiceResponseError):
    """The parameters passed to the optimizer do not make sense (e.g. negative weights)."""


class MaxIterationsError(MapProcessingServiceResponseError):
    """The optimizer reached the maximum number of iterations before converging."""


class MaxTimeError(MapProcessingServiceResponseError):
    """The optimizer timed out before converging."""


class InvalidHintsError(MapProcessingServiceResponseError):
    """One or more of the hints passed in to the optimizer are invalid (do not correspond to real waypoints or objects)."""


class InvalidGravityAlignmentError(MapProcessingServiceResponseError):
    """One or more anchoring hints disagrees with gravity. Ensure the orientation of any hints is correct."""


class ConstraintViolationError(MapProcessingServiceResponseError):
    """One or more anchors were moved outside of the desired constraints."""


class MapModifiedError(MapProcessingServiceResponseError):
    """The map was modified on the server by another client during processing. Please try again."""


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _process_topology_common_errors(response):
    # Handle error statuses from the request.
    if (response.status == map_processing_pb2.ProcessTopologyResponse.STATUS_INVALID_GRAPH):
        return InvalidGraphError(response=response, error_message=InvalidGraphError.__doc__)
    elif (response.status ==
          map_processing_pb2.ProcessTopologyResponse.STATUS_MISSING_WAYPOINT_SNAPSHOTS):
        return MissingSnapshotsError(response=response, error_message=MissingSnapshotsError.__doc__)
    elif (response.status ==
          map_processing_pb2.ProcessTopologyResponse.STATUS_MAP_MODIFIED_DURING_PROCESSING):
        return MapModifiedError(response=response, error_message=MapModifiedError.__doc__)
    return None


def _process_topology_streamed_errors(responses):
    """Return a custom exception based on process topology streaming response, None if no error."""
    # Iterate through the response since the request responds with a stream.
    for resp in responses:
        exception = _process_topology_common_errors(resp)
        if exception:
            return exception

    # All responses (in the iterator) had status_ok
    return None


__ANCHORING_COMMON_ERRORS = {
    map_processing_pb2.ProcessAnchoringResponse.STATUS_MISSING_WAYPOINT_SNAPSHOTS:
        MissingSnapshotsError,
    map_processing_pb2.ProcessAnchoringResponse.STATUS_OPTIMIZATION_FAILURE:
        OptimizationFailureError,
    map_processing_pb2.ProcessAnchoringResponse.STATUS_INVALID_GRAPH:
        InvalidGraphError,
    map_processing_pb2.ProcessAnchoringResponse.STATUS_INVALID_PARAMS:
        InvalidParamsError,
    map_processing_pb2.ProcessAnchoringResponse.STATUS_CONSTRAINT_VIOLATION:
        ConstraintViolationError,
    map_processing_pb2.ProcessAnchoringResponse.STATUS_MAX_ITERATIONS:
        MaxIterationsError,
    map_processing_pb2.ProcessAnchoringResponse.STATUS_MAX_TIME:
        MaxTimeError,
    map_processing_pb2.ProcessAnchoringResponse.STATUS_INVALID_HINTS:
        InvalidHintsError,
    map_processing_pb2.ProcessAnchoringResponse.STATUS_INVALID_GRAVITY_ALIGNMENT:
        InvalidGravityAlignmentError,
    map_processing_pb2.ProcessAnchoringResponse.STATUS_MAP_MODIFIED_DURING_PROCESSING:
        MapModifiedError
}


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _process_anchoring_common_errors(response):
    # Handle error statuses from the request.
    if response.status in __ANCHORING_COMMON_ERRORS:
        type_name = __ANCHORING_COMMON_ERRORS[response.status]
        return type_name(response=response, error_message=type_name.__doc__)
    return None


def _process_anchoring_streamed_errors(responses):
    """Return a custom exception based on process anchoring streaming response, None if no error."""
    # Iterate through the response since the request responds with a stream.
    for resp in responses:
        exception = _process_anchoring_common_errors(resp)
        if exception:
            return exception

    # All responses (in the iterator) had status_ok
    return None


def _get_streamed_topology_response(response):
    """Reads a streamed response to recreate a merged topology response."""
    merged_response = map_processing_pb2.ProcessTopologyResponse()

    for resp in response:
        merged_response.MergeFrom(resp)
    return merged_response


def _get_streamed_anchoring_response(response):
    """Reads a streamed response to recreate a merged anchoring response."""
    merged_response = map_processing_pb2.ProcessAnchoringResponse()

    for resp in response:
        merged_response.MergeFrom(resp)
    return merged_response


class MapProcessingServiceClient(BaseClient):
    """Client for the GraphNav map processing service."""
    default_service_name = 'map-processing-service'
    service_type = 'bosdyn.api.graph_nav.MapProcessingService'

    def __init__(self):
        super(MapProcessingServiceClient, self).__init__(map_processing.MapProcessingServiceStub)

    @staticmethod
    def _build_process_topology_request(params, modify_map_on_server):
        return map_processing_pb2.ProcessTopologyRequest(params=params,
                                                         modify_map_on_server=modify_map_on_server)

    @staticmethod
    def _build_process_anchoring_request(params, modify_anchoring_on_server,
                                         stream_intermediate_results, initial_hint,
                                         apply_gps_results):
        return map_processing_pb2.ProcessAnchoringRequest(
            params=params, initial_hint=initial_hint,
            modify_anchoring_on_server=modify_anchoring_on_server,
            stream_intermediate_results=stream_intermediate_results,
            apply_gps_result_to_waypoints_on_server=apply_gps_results)

    def process_topology(self, params, modify_map_on_server, **kwargs):
        """Process the topology of the map on the server, closing loops and producing a
         consistent topology.

        Args:
            params: a ProcessTopologyRequest.Params object
            modify_map_on_server: if true, the map will be modified on the server. If false,
            the subgraph returned by this function should be uploaded back to the server if it
            is to be reused.

        Returns:
            The ProcessTopologyResponse containing new edges to add to the map.

        Raises:
            RpcError: Problem communicating with the robot
        """
        request = self._build_process_topology_request(params, modify_map_on_server)
        return self.call(self._stub.ProcessTopology, request,
                         value_from_response=_get_streamed_topology_response,
                         error_from_response=_process_topology_streamed_errors, copy_request=False,
                         **kwargs)

    def process_anchoring(self, params, modify_anchoring_on_server, stream_intermediate_results,
                          initial_hint=None, apply_gps_results=False, **kwargs):
        """Process the anchoring of the map on the server, producing a metrically consistent anchoring.

        Args:
            params: a ProcessAnchoringRequest.Params object
            modify_anchoring_on_server: if true, the map will be modified on the server. If false,
            the anchoring returned by this function should be uploaded back to the server if it
            is to be reused.
            stream_intermediate_results: if true, anchorings from earlier optimizer
            iterations may be included in the response. If false, only the last iteration will be returned.
            initial_hint: Initial guess at some number of waypoints and world objects and their anchorings.
            This field is an AnchoringHint object (see map_processing.proto)
            apply_gps_results: if true, the annotations of waypoints in the graph will be modified to include
            the pose of each waypoint in a GPS centered frame, if the map has GPS (see map_processing.proto)
        Returns:
            The ProcessAnchoringResponse containing a new optimized anchoring.
        Raises:
            RpcError: Problem communicating with the robot
        """
        request = self._build_process_anchoring_request(params, modify_anchoring_on_server,
                                                        stream_intermediate_results, initial_hint,
                                                        apply_gps_results)

        return self.call(self._stub.ProcessAnchoring, request,
                         value_from_response=_get_streamed_anchoring_response,
                         error_from_response=_process_anchoring_streamed_errors, copy_request=False,
                         **kwargs)
