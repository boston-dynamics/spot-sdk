# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client implementation of the RayCast service."""

import collections

from bosdyn.api import geometry_pb2, ray_cast_pb2, ray_cast_service_pb2_grpc
from bosdyn.client.common import (BaseClient, error_factory, error_pair,
                                  handle_common_header_errors, handle_unset_status_error)
from bosdyn.client.exceptions import ResponseError


class RayCastResponseError(ResponseError):
    """General class of errors for ray cast service."""


class InvalidRequestError(RayCastResponseError):
    """Request was invalid / malformed in some way."""


class InvalidIntersectionTypeError(RayCastResponseError):
    """Requested source not valid for current robot configuration."""


class UnknownFrameError(RayCastResponseError):
    """The frame_name for a command was not a known frame."""


# yapf: disable
# pylint: disable=line-too-long
_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_STATUS_TO_ERROR.update({
    ray_cast_pb2.RaycastResponse.STATUS_OK: (None, None),
    ray_cast_pb2.RaycastResponse.STATUS_INVALID_REQUEST: error_pair(InvalidRequestError),
    ray_cast_pb2.RaycastResponse.STATUS_INVALID_INTERSECTION_TYPE: error_pair(InvalidIntersectionTypeError),
    ray_cast_pb2.RaycastResponse.STATUS_UNKNOWN_FRAME: error_pair(UnknownFrameError),
})
# pylint: enable=line-too-long
# yapf: enable


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _error_from_response(response):
    """Return a custom exception, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=ray_cast_pb2.RaycastResponse.Status.Name,
                         status_to_error=_STATUS_TO_ERROR)


class RayCastClient(BaseClient):
    """A client that allows arbitrary rays to be queried against the robot."""
    default_authority = 'ray-cast.spot.robot'
    default_service_name = 'ray-cast'
    service_type = 'bosdyn.api.RayCastService'

    def __init__(self):
        super(RayCastClient, self).__init__(ray_cast_service_pb2_grpc.RayCastServiceStub)

    def raycast(self, ray_origin, ray_direction, raycast_types, min_distance=0, frame_name=None,
                **kwargs):
        """Requests robot to intersect ray against the environment it built up.

        Args:
            ray_origin: (x, y, z) position of the ray in the specified frame.
            ray_direction: (x, y, z) vector denoting the direction of the ray in the specified
                           frame.
            raycast_types: array of 0 or more raycast types. 0 will cast into all sources.
            min_distance: a positive real value denoting how far (meters) behind a ray an
                          intersection can occur.
            frame_name: the frame the ray is in.

        Returns:
            RaycastResponse
        """
        req = self._raycast_request(ray_origin, ray_direction, raycast_types, min_distance,
                                    frame_name)
        return self.call(self._stub.Raycast, req, None, _error_from_response, copy_request=False,
                         **kwargs)

    def raycast_async(self, ray_origin, ray_direction, raycast_types, min_distance=0,
                      frame_name=None, **kwargs):
        """Async version of raycast()."""
        req = self._raycast_request(ray_origin, ray_direction, raycast_types, min_distance,
                                    frame_name)
        return self.call_async(self._stub.Raycast, req, None, _error_from_response,
                               copy_request=False, **kwargs)

    @staticmethod
    def _raycast_request(ray_origin, ray_direction, raycast_types, min_distance, frame_name):
        origin_proto = geometry_pb2.Vec3(x=ray_origin[0], y=ray_origin[1], z=ray_origin[2])
        dir_proto = geometry_pb2.Vec3(x=ray_direction[0], y=ray_direction[1], z=ray_direction[2])
        ray = geometry_pb2.Ray(origin=origin_proto, direction=dir_proto)
        proto = ray_cast_pb2.RaycastRequest(ray=ray, min_intersection_distance=min_distance,
                                            ray_frame_name=frame_name)
        proto.intersection_types.extend(raycast_types)
        return proto
