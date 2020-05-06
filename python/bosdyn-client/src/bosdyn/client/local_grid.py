# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client support for the LocalGridService."""

from bosdyn.api import local_grid_pb2, local_grid_service_pb2_grpc
from bosdyn.client.common import BaseClient, common_header_errors


class LocalGridClient(BaseClient):
    """Client to access local grid local_grids from the robot."""

    # Typical name of the service in the robot's directory listing.
    default_service_name = 'local-grid-service'
    # gRPC service proto definition implemented by this service
    service_type = 'bosdyn.api.LocalGridService'

    def __init__(self):
        super(LocalGridClient, self).__init__(local_grid_service_pb2_grpc.LocalGridServiceStub)

    def get_local_grid_types(self, **kwargs):
        """Get a list of the local_grid types available from the robot.

        Returns:
            A list of the different types (string names) of local grids.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        return self.call(self._stub.GetLocalGridTypes, local_grid_pb2.GetLocalGridTypesRequest(),
                         value_from_response=lambda res: res.local_grid_type,
                         error_from_response=common_header_errors, **kwargs)

    def get_local_grid_types_async(self, **kwargs):
        """Async version of get_local_grid_types()."""
        return self.call_async(self._stub.GetLocalGridTypes, local_grid_pb2.GetLocalGridTypesRequest(),
                               value_from_response=lambda res: res.local_grid_type,
                               error_from_response=common_header_errors, **kwargs)

    def get_local_grids(self, local_grid_type_names, **kwargs):
        """Get a selection of local_grids of specified types.

        Args:
           local_grid_type_names (list of strings): List of strings specifying types local_grids to request.
                           Available local_grid types may be requested using get_local_grid_types().

        Returns:
           A list of LocalGridResponseProtos, each containing a local_grid or an error status code.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        request = local_grid_pb2.GetLocalGridsRequest()
        for local_grid_type_name in local_grid_type_names:
            request.local_grid_requests.add(local_grid_type_name=local_grid_type_name)
        return self.call(self._stub.GetLocalGrids, request,
                         value_from_response=lambda res: res.local_grid_responses,
                         error_from_response=common_header_errors, **kwargs)


    def get_local_grids_async(self, local_grid_type_names, **kwargs):
        """Async version of get_local_grids()."""
        request = local_grid_pb2.GetLocalGridsRequest()
        for local_grid_type_name in local_grid_type_names:
            request.local_grid_requests.add(local_grid_type_name=local_grid_type_name)
        return self.call_async(self._stub.GetLocalGrids, request,
                               value_from_response=lambda res: res.local_grid_responses,
                               error_from_response=common_header_errors, **kwargs)
