# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client for the point cloud service.

This allows client code to read from a point cloud service.
"""

from __future__ import print_function
import collections
import logging

import bosdyn.api.point_cloud_pb2 as point_cloud_protos
import bosdyn.api.point_cloud_service_pb2_grpc as point_cloud_service

from .common import BaseClient
from bosdyn.client.common import (error_factory, error_pair, common_header_errors, handle_common_header_errors)
from bosdyn.client.exceptions import ResponseError, UnsetStatusError

LOGGER = logging.getLogger('point_cloud_client')

class PointCloudResponseError(ResponseError):
    """General class of errors for PointCloud service."""


class UnknownPointCloudSourceError(PointCloudResponseError):
    """System cannot find the requested point cloud source name."""


class SourceDataError(PointCloudResponseError):
    """System cannot generate the PointCloudSource at this time."""


class PointCloudDataError(PointCloudResponseError):
    """System cannot generate point cloud data at this time."""


_STATUS_TO_ERROR = collections.defaultdict(lambda: (PointCloudResponseError, None))
_STATUS_TO_ERROR.update({
    point_cloud_protos.PointCloudResponse.STATUS_OK: (None, None),
    point_cloud_protos.PointCloudResponse.STATUS_UNKNOWN_SOURCE: error_pair(UnknownPointCloudSourceError),
    point_cloud_protos.PointCloudResponse.STATUS_SOURCE_DATA_ERROR: error_pair(SourceDataError),
    point_cloud_protos.PointCloudResponse.STATUS_UNKNOWN: error_pair(UnsetStatusError),
    point_cloud_protos.PointCloudResponse.STATUS_POINT_CLOUD_DATA_ERROR: error_pair(PointCloudDataError),
})

@handle_common_header_errors
def _error_from_response(response):
    """Return a custom exception based on the first invalid point_cloud response, None if no error."""
    for point_cloud_response in response.point_cloud_responses:

        result = error_factory(response, point_cloud_response.status,
                               status_to_string=point_cloud_protos.PointCloudResponse.Status.Name,
                               status_to_error=_STATUS_TO_ERROR)
        if result is not None:
            return result
    return None

class PointCloudClient(BaseClient):
    """A client handling point clouds."""

    default_service_name = 'point-cloud'
    service_type = 'bosdyn.api.PointCloudService'

    def __init__(self):
        super(PointCloudClient, self).__init__(point_cloud_service.PointCloudServiceStub)

    def list_point_cloud_sources(self, **kwargs):
        """ Obtain the list of PointCloudSources.

        Returns:
            A list of the different point cloud sources as strings.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_list_point_cloud_source_request()
        return self.call(self._stub.ListPointCloudSources, req, _list_point_cloud_sources_value,
                         common_header_errors, **kwargs)

    def list_point_cloud_sources_async(self, **kwargs):
        """Async version of list_point_cloud_sources()"""
        req = self._get_list_point_cloud_source_request()
        return self.call_async(self._stub.ListPointCloudSources, req, _list_point_cloud_sources_value,
                               common_header_errors, **kwargs)

    def get_point_cloud_from_sources(self, point_cloud_sources, **kwargs):
        """Obtain point clouds from sources using default parameters.

        Args:
            point_cloud_sources (list of strings): The source names to request point clouds from.

        Returns:
            A list of point cloud responses for each of the requested sources.

        Raises:
            RpcError: Problem communicating with the robot.
            UnknownPointCloudSourceError: Provided point cloud source was invalid or not found
            point_cloud.SourceDataError: Failed to fill out PointCloudSource. All other fields
                are not filled
            UnsetStatusError: An internal PointCloudService issue has happened
            PointCloudDataError: Problem with the point cloud data. Only PointCloudSource is filled
        """
        return self.get_point_cloud([build_pc_request(src) for src in point_cloud_sources], **kwargs)

    def get_point_cloud_from_sources_async(self, point_cloud_sources, **kwargs):
        """Obtain point clouds from sources using default parameters."""
        return self.get_point_cloud_async([build_pc_request(src) for src in point_cloud_sources],
                                    **kwargs)

    def get_point_cloud(self, point_cloud_requests, **kw_args):
        """Get the most recent point cloud

        Args:
            point_cloud_requests (list of PointCloudRequest): A list of PointCloudRequest protobuf
                                                messages which specify which point clouds to collect
            kw_args:              Extra arguments to pass to grpc call invocation.

        Returns:
            A list of point cloud responses for each of the requested sources.

        Raises:
            RpcError: Problem communicating with the robot.
            UnknownPointCloudSourceError: Provided point cloud source was invalid or not found
            point_cloud.SourceDataError: Failed to fill out PointCloudSource. All other fields
                are not filled
            UnsetStatusError: An internal PointCloudService issue has happened
            PointCloudDataError: Problem with the point cloud data. Only PointCloudSource is filled
        """
        request = self._get_point_cloud_request(point_cloud_requests)
        return self.call(self._stub.GetPointCloud, request,
                         value_from_response=_get_point_cloud_value,
                         error_from_response=_error_from_response, **kw_args)

    def get_point_cloud_async(self, point_cloud_requests, **kw_args):
        """Get the most recent point cloud

        Args:
            point_cloud_requests (list of PointCloudRequest): A list of PointCloudRequest protobuf
                                                messages which specify which point clouds to collect
            kw_args:              Extra arguments to pass to grpc call invocation.

        Raises:
            RpcError: Problem communicating with the robot.
            UnknownPointCloudSourceError: Provided point cloud source was invalid or not found
            point_cloud.SourceDataError: Failed to fill out PointCloudSource. All other fields
                are not filled
            UnsetStatusError: An internal PointCloudService issue has happened
            PointCloudDataError: Problem with the point cloud data. Only PointCloudSource is filled

        Returns:
            A list of point cloud responses for each of the requested sources.
        """
        request = self._get_point_cloud_request(point_cloud_requests)
        return self.call_async(self._stub.GetPointCloud, request,
                               value_from_response=_get_point_cloud_value,
                               error_from_response=_error_from_response, **kw_args)

    @staticmethod
    def _get_point_cloud_request(point_cloud_requests):
        return point_cloud_protos.GetPointCloudRequest(point_cloud_requests=point_cloud_requests)

    @staticmethod
    def _get_list_point_cloud_source_request():
        return point_cloud_protos.ListPointCloudSourcesRequest()

def build_pc_request(point_cloud_source_name):
    """Helper function which builds an PointCloudRequest from an point cloud source name.

    Args:
        point_cloud_source_name (string): The point cloud source to query.

    Returns:
        The PointCloudRequest protobuf message for the given parameters.
    """
    return point_cloud_protos.PointCloudRequest(point_cloud_source_name=point_cloud_source_name)

def _list_point_cloud_sources_value(response):
    return response.point_cloud_sources


def _get_point_cloud_value(response):
    return response.point_cloud_responses
