# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from bosdyn.api import arm_surface_contact_pb2, arm_surface_contact_service_pb2_grpc
from bosdyn.client.common import BaseClient, common_header_errors
from bosdyn.client.robot_command import NoTimeSyncError, _edit_proto, _TimeConverter

from .lease import add_lease_wallet_processors


class ArmSurfaceContactClient(BaseClient):
    """Client for the ArmSurfaceContact service."""
    default_service_name = 'arm-surface-contact'
    service_type = 'bosdyn.api.ArmSurfaceContactService'

    def __init__(self):
        super(ArmSurfaceContactClient,
              self).__init__(arm_surface_contact_service_pb2_grpc.ArmSurfaceContactServiceStub)
        self._timesync_endpoint = None

    def update_from(self, other):
        """Update instance from another object.

        Args:
            other: The object where to copy from.
        """
        super(ArmSurfaceContactClient, self).update_from(other)
        if self.lease_wallet:
            add_lease_wallet_processors(self, self.lease_wallet)

        # Grab a timesync endpoint if it is available.
        try:
            self._timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    def _update_command_timestamps(self, command):
        """Set or convert fields of the command proto that need timestamps in the robot's clock.

        Args:
            command: Command message to update.
        """
        if self._timesync_endpoint is None:
            raise NoTimeSyncError

        converter = _TimeConverter(self, self._timesync_endpoint)

        def _to_robot_time(key, proto):
            """If proto has a field named key with a timestamp, convert timestamp to robot time."""
            if not (key in proto.DESCRIPTOR.fields_by_name and proto.HasField(key)):
                return  # No such field in proto, or field does not contain a timestamp.
            timestamp = getattr(proto, key)
            converter.convert_timestamp_from_local_to_robot(timestamp)

        # Convert timestamps from local time to robot time.
        _edit_proto(command, EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME, _to_robot_time)

    def arm_surface_contact_command(self, request, **kwargs):
        """Issue an arm surface contact command to the robot.

        Args:
            request (arm_surface_contact_pb2.ArmSurfaceContactRequest): The command request.

        Returns:
            The full arm surface contact response message.
        """
        self._update_command_timestamps(request)
        return self.call(self._stub.ArmSurfaceContact, request, **kwargs)

    def arm_surface_contact_command_async(self, request, **kwargs):
        """Async version of arm_surface_contact_command()."""
        self._update_command_timestamps(request)
        return self.call_async(self._stub.ArmSurfaceContact, request, **kwargs)


# Tree of proto fields leading to Timestamp protos which need to be converted from
# client clock to robot clock values using timesync information from the robot.
# Note, the "@" sign indicates a oneof field. The "None" indicates the field which
# contains the timestamp to be updated.
EDIT_TREE_CONVERT_LOCAL_TIME_TO_ROBOT_TIME = {
    'request': {
        'pose_trajectory_in_task': {
            'reference_time': None
        },
        'gripper_command': {
            'trajectory': {
                'reference_time': None
            }
        }
    }
}
