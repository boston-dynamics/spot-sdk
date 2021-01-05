# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to use the choreography service"""
import logging
import os
import collections

from bosdyn.client.common import BaseClient
from bosdyn.client.common import (error_factory, error_pair, common_header_errors, handle_common_header_errors, common_lease_errors,
                                  handle_lease_use_result_errors, handle_unset_status_error)
from bosdyn.client.exceptions import ResponseError, UnsetStatusError
from bosdyn.client.robot_command import NoTimeSyncError, _TimeConverter
from bosdyn.api.spot import choreography_sequence_pb2, choreography_service_pb2, choreography_service_pb2_grpc

from bosdyn.client.lease import add_lease_wallet_processors

from google.protobuf import text_format

LOGGER = logging.getLogger('__name__')

class ChoreographyClient(BaseClient):
    """Client for Choreography Service."""
    default_service_name = 'choreography'
    service_type = 'bosdyn.api.spot.ChoreographyService'

    def __init__(self):
        super(ChoreographyClient, self).__init__(choreography_service_pb2_grpc.ChoreographyServiceStub)
        self._timesync_endpoint = None

    def update_from(self, other):
        super(ChoreographyClient, self).update_from(other)
        if self.lease_wallet:
            add_lease_wallet_processors(self, self.lease_wallet)
        # Grab a timesync endpoint if it is available.
        try:
            self._timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    @property
    def timesync_endpoint(self):
        """Accessor for timesync-endpoint that was grabbed via 'update_from()'."""
        if not self._timesync_endpoint:
            raise NoTimeSyncError("[choreography service] No timesync endpoint set for the robot")
        return self._timesync_endpoint

    def list_all_moves(self, **kwargs):
        """Get a list of the different choreography sequence moves and associated parameters."""
        req = choreography_sequence_pb2.ListAllMovesRequest()
        return self.call(self._stub.ListAllMoves, req,
                         value_from_response=None, # Return the complete response message
                         error_from_response=common_header_errors, **kwargs)

    def list_all_moves_async(self, object_type=None, time_start_point=None, **kwargs):
        """Async version of list_all_moves()."""
        req = choreography_sequence_pb2.ListAllMovesRequest()
        return self.call_async(self._stub.ListAllMoves, req,
                               value_from_response=None, # Return the complete response message
                               error_from_response=common_header_errors, **kwargs)

    def upload_choreography(self, choreography_seq, non_strict_parsing=True, **kwargs):
        """Upload the choreography sequence to the robot."""
        req = choreography_sequence_pb2.UploadChoreographyRequest(choreography_sequence=choreography_seq, non_strict_parsing=non_strict_parsing)
        return self.call(self._stub.UploadChoreography, req,
                        value_from_response=None,  # Return the complete response message
                        error_from_response=common_header_errors,
                        **kwargs)

    def upload_choreography_async(self, choreography_seq, non_strict_parsing=True, **kwargs):
        """Async version of upload_choreography()."""
        req = choreography_sequence_pb2.UploadChoreographyRequest(choreography_sequence=choreography_seq, non_strict_parsing=non_strict_parsing)
        return self.call_async(self._stub.UploadChoreography, req,
                               value_from_response=None, # Return the complete response message
                               error_from_response=common_header_errors, **kwargs)

    def execute_choreography(self, choreography_name, client_start_time, choreography_starting_slice, lease=None, **kwargs):
        """Execute the current choreography sequence loaded on the robot by name."""
        req = self.build_execute_choreography_request(choreography_name, client_start_time, choreography_starting_slice, lease)

        return self.call(self._stub.ExecuteChoreography, req,
                        value_from_response=None,  # Return the complete response message
                        error_from_response=_execute_choreography_errors,
                        **kwargs)

    def execute_choreography_async(self, choreography_name, client_start_time, choreography_starting_slice, lease=None, **kwargs):
        """Async version of execute_choreography()."""
        req = self.build_execute_choreography_request(choreography_name, client_start_time, choreography_starting_slice, lease)
        return self.call_async(self._stub.ExecuteChoreography, req,
                               value_from_response=None, # Return the complete response message
                               error_from_response=_execute_choreography_errors, **kwargs)

    def build_execute_choreography_request(self, choreography_name, client_start_time, choreography_starting_slice, lease=None):
        """Generate the ExecuteChoreographyRequest rpc with the timestamp converted into robot time."""
        # Note the client_start_time is a time expressed in the client's clock for when the choreography sequence should begin.
        request = choreography_sequence_pb2.ExecuteChoreographyRequest(choreography_sequence_name=choreography_name,
                                              choreography_starting_slice=float(choreography_starting_slice),
                                              lease=lease)
        if client_start_time is not None:
            request.start_time.CopyFrom(
                self._update_timestamp_filter(client_start_time, self.timesync_endpoint))
        return request

    def _update_timestamp_filter(self, timestamp, timesync_endpoint):
        """Set or convert fields of the proto that need timestamps in the robot's clock."""
        # Input timestamp is a google.protobuf.Timestamp
        if not timesync_endpoint:
            raise NoTimeSyncError("[choreography service] No timesync endpoint set for the robot.")
        converter = _TimeConverter(self, timesync_endpoint)
        return converter.robot_timestamp_from_local_secs(timestamp)


class InvalidUploadedChoreographyError(ResponseError):
    """The uploaded choreography is invalid and unable to be performed."""

class RobotCommandIssuesError(ResponseError):
    """A problem occurred when issuing the robot command containing the dance."""

class LeaseError(ResponseError):
    """Incorrect or invalid leases for data acquisition. Check the lease use results."""

_EXECUTE_CHOREOGRAPHY_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_EXECUTE_CHOREOGRAPHY_STATUS_TO_ERROR.update({
    choreography_sequence_pb2.ExecuteChoreographyResponse.STATUS_OK: (None, None),
    choreography_sequence_pb2.ExecuteChoreographyResponse.STATUS_INVALID_UPLOADED_CHOREOGRAPHY: (InvalidUploadedChoreographyError,
                                                             InvalidUploadedChoreographyError.__doc__),
    choreography_sequence_pb2.ExecuteChoreographyResponse.STATUS_ROBOT_COMMAND_ISSUES:
    (RobotCommandIssuesError, RobotCommandIssuesError.__doc__),
    choreography_sequence_pb2.ExecuteChoreographyResponse.STATUS_LEASE_ERROR:
        (LeaseError, LeaseError.__doc__),
})

@handle_common_header_errors
@handle_lease_use_result_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _execute_choreography_errors(response):
    """Return an exception based on response from ExecuteChoreography RPC, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=choreography_sequence_pb2.ExecuteChoreographyResponse.Status.Name,
                         status_to_error=_EXECUTE_CHOREOGRAPHY_STATUS_TO_ERROR)

'''
Static helper methods.
'''

def load_choreography_sequence_from_binary_file(file_path):
    """Read a choreography sequence file into a protobuf ChoreographySequence message."""
    if not os.path.exists(file_path):
        LOGGER.error("File not found at: %s" % file_path)
        raise IOError("File not found at: %s" % file_path)

    choreography_sequence = choreography_sequence_pb2.ChoreographySequence()
    with open(file_path, "rb") as f:
        data = f.read()
        choreography_sequence.ParseFromString(data)

    return choreography_sequence

def load_choreography_sequence_from_txt_file(file_path):
    if not os.path.exists(file_path):
        LOGGER.error("File not found at: %s" % file_path)
        raise IOError("File not found at: %s" % file_path)

    choreography_sequence = choreography_sequence_pb2.ChoreographySequence()
    with open(file_path, "r") as f:
        data = f.read()
        text_format.Merge(data, choreography_sequence)

    return choreography_sequence

def save_choreography_sequence_to_file(file_path, file_name, choreography):
    """Saves a choreography sequence to a file."""
    if (file_name is None or len(file_name) == 0):
        LOGGER.error("Invalid file name, cannot save choreography sequence.")
        raise IOError("Invalid file name, cannot save choreography sequence.")

    if not os.path.exists(file_path):
        LOGGER.error("Path(%s) to save file does not exist. Creating it." % file_path)
        os.makedirs(file_path, exist_ok=True)

    choreography_sequence_bytes = choreography.SerializeToString()
    with open(str(os.path.join(file_path, file_name)), 'wb') as f:
        f.write(choreography_sequence_bytes)
