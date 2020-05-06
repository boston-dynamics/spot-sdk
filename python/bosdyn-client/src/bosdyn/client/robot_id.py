# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the robot id service.

RobotIdClient -- Wrapper around service stub.
"""

from bosdyn.api import robot_id_pb2, robot_id_service_pb2_grpc
from bosdyn.client.common import BaseClient, common_header_errors
from distutils.version import StrictVersion


def _get_entry_value(response):
    return response.robot_id


class RobotIdClient(BaseClient):
    """Client to access robot info."""

    # Typical name of the service in the robot's directory listing.
    default_service_name = 'robot-id'
    # gRPC service proto definition implemented by this service
    service_type = 'bosdyn.api.RobotIdService'

    def __init__(self):
        super(RobotIdClient, self).__init__(robot_id_service_pb2_grpc.RobotIdServiceStub)

    def get_id(self, **kwargs):
        """Get the robot's robot/id.proto."""
        req = robot_id_pb2.RobotIdRequest()
        return self.call(self._stub.GetRobotId, req, value_from_response=_get_entry_value,
                         error_from_response=common_header_errors, **kwargs)

    def get_id_async(self, **kwargs):
        """Return a future to results of "get_id". See "get_id" for further docs."""
        req = robot_id_pb2.RobotIdRequest()
        return self.call_async(self._stub.GetRobotId, req, value_from_response=_get_entry_value,
                               error_from_response=common_header_errors, **kwargs)


def create_strict_version(robot_id):
    """Create and return a StrictVersion object, from a robot_id, which can be compared easily."""
    if robot_id == None:
        return None

    version_string = str(robot_id.software_release.version.major_version) + '.' + \
                            str(robot_id.software_release.version.minor_version) + '.' + \
                            str(robot_id.software_release.version.patch_level)

    return StrictVersion(version_string)
