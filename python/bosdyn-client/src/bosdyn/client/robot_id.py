"""For clients to the robot id service.

RobotIdClient -- Wrapper around service stub.
"""

from bosdyn.api import robot_id_service_pb2, robot_id_service_pb2_grpc

from bosdyn.client.common import BaseClient, common_header_errors


def _get_entry_value(response):
    return response.robot_id


class RobotIdClient(BaseClient):
    """Client to access robot info."""

    # Typical authority of the service on the robot we want to talk to.
    default_authority = 'id.spot.robot'
    # Typical name of the service in the robot's directory listing.
    default_service_name = 'robot-id'
    # Full service name in the robot's directory listing.
    service_type = 'bosdyn.api.RobotIdService'

    def __init__(self):
        super(RobotIdClient, self).__init__(robot_id_service_pb2_grpc.RobotIdServiceStub)

    def get_id(self, **kwargs):
        """Get the robot's robot/id.proto."""
        req = robot_id_service_pb2.RobotIdRequest()
        return self.call(self._stub.GetRobotId, req, value_from_response=_get_entry_value,
                         error_from_response=common_header_errors, **kwargs)

    def get_id_async(self, **kwargs):
        """Return a future to results of "get_id". See "get_id" for further docs."""
        req = robot_id_service_pb2.RobotIdRequest()
        return self.call_async(self._stub.GetRobotId, req, value_from_response=_get_entry_value,
                               error_from_response=common_header_errors, **kwargs)
