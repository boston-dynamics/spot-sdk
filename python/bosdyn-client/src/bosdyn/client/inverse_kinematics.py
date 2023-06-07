# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A client for the inverse-kinematics service."""

from bosdyn.api.spot.inverse_kinematics_pb2 import InverseKinematicsRequest
from bosdyn.api.spot.inverse_kinematics_service_pb2_grpc import InverseKinematicsServiceStub
from bosdyn.client.common import BaseClient, common_header_errors


class InverseKinematicsClient(BaseClient):
    """Client to request inverse kinematics solutions."""

    # Name of the service in the robot's directory listing.
    default_service_name = 'inverse-kinematics'
    # gRPC service proto definition implemented by this service
    service_type = 'bosdyn.api.spot.InverseKinematicsService'

    def __init__(self):
        super(InverseKinematicsClient, self).__init__(InverseKinematicsServiceStub)

    def inverse_kinematics(self, request: InverseKinematicsRequest, **kwargs):
        """ Request an IK solution.

        Args:
            request (InverseKinematicsRequest): Request to issue

        Returns:
            The InverseKinematicsResponse message
        """
        return self.call(self._stub.InverseKinematics, request,
                         error_from_response=common_header_errors, **kwargs)

    def inverse_kinematics_async(self, request: InverseKinematicsRequest, **kwargs):
        """Async version of inverse_kinematics()"""
        return self.call_async(self._stub.InverseKinematics, request,
                               error_from_response=common_header_errors, **kwargs)

