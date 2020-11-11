# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to use the fault service."""
import collections

from bosdyn.client.common import (BaseClient, common_header_errors, error_factory, error_pair,
                                  handle_unset_status_error, handle_common_header_errors)
from .exceptions import ResponseError

from bosdyn.api import service_fault_pb2
from bosdyn.api import fault_service_pb2_grpc


class FaultResponseError(ResponseError):
    """General class of errors for directory registration responses."""


class ServiceFaultAlreadyExistsError(FaultResponseError):
    """The specified service fault id already exists as an active fault on the robot."""


class ServiceFaultDoesNotExistError(FaultResponseError):
    """The specified service fault id does not match any active service faults on the robot."""


class FaultClient(BaseClient):
    """Client for the Fault service."""
    default_service_name = 'fault'
    service_type = 'bosdyn.api.FaultService'

    def __init__(self):
        super(FaultClient, self).__init__(fault_service_pb2_grpc.FaultServiceStub)

    def trigger_service_fault(self, service_fault, **kwargs):
        """Broadcast a new service fault through the robot.

        Args:
            service_fault (bosdyn.api.ServiceFault): Populated fault message to broadcast.

        Returns:
            An instance of bosdyn.api.TriggerServiceFaultResponse

        Raises:
            RpcError: Problem communicating with the robot.
            ServiceFaultAlreadyExistsError: The service fault already exists.
            FaultResponseError: Something went wrong during the fault trigger.
        """
        req = service_fault_pb2.TriggerServiceFaultRequest()
        req.fault.CopyFrom(service_fault)
        return self.call(self._stub.TriggerServiceFault, req, None,
                         error_from_response=_trigger_service_fault_error, **kwargs)

    def trigger_service_fault_async(self, service_fault, **kwargs):
        """Async version of trigger_service_fault()"""
        req = service_fault_pb2.TriggerServiceFaultRequest()
        req.fault.CopyFrom(service_fault)
        return self.call_async(self._stub.TriggerServiceFault, req, None,
                               error_from_response=_trigger_service_fault_error, **kwargs)

    def clear_service_fault(self, service_fault_id, clear_all_service_faults=False,
                            clear_all_payload_faults=False, **kwargs):
        """Clear a service fault from the robot state.

        Args:
            service_fault_id (bosdyn.api.ServiceFaultId): ServiceFault to clear.
            clear_all_service_faults (bool): Clear all faults associated with the service name.
            clear_all_payload_faults (bool): Clear all faults associated with the payload guid.

        Returns:
            An instance of bosdyn.api.ClearServiceFaultResponse

        Raises:
            RpcError: Problem communicating with the robot.
            ServiceFaultDoesNotExistError: The service fault does not exist in active service faults.
            FaultResponseError: Something went wrong during the fault clear.
        """
        req = service_fault_pb2.ClearServiceFaultRequest()
        req.fault_id.CopyFrom(service_fault_id)
        req.clear_all_service_faults = clear_all_service_faults
        req.clear_all_payload_faults = clear_all_payload_faults
        return self.call(self._stub.ClearServiceFault, req, None,
                         error_from_response=_clear_service_fault_error, **kwargs)

    def clear_service_fault_async(self, service_fault_id, clear_all_service_faults=False,
                                  clear_all_payload_faults=False, **kwargs):
        """Async version of clear_service_fault()"""
        req = service_fault_pb2.ClearServiceFaultRequest()
        req.fault_id.CopyFrom(service_fault_id)
        req.clear_all_service_faults = clear_all_service_faults
        req.clear_all_payload_faults = clear_all_payload_faults
        return self.call_async(self._stub.ClearServiceFault, req, None,
                               error_from_response=_clear_service_fault_error, **kwargs)


_TRIGGER_STATUS_TO_ERROR = collections.defaultdict(lambda: (FaultResponseError, None))
_TRIGGER_STATUS_TO_ERROR.update({
    service_fault_pb2.TriggerServiceFaultResponse.STATUS_OK: (None, None),
    service_fault_pb2.TriggerServiceFaultResponse.STATUS_FAULT_ALREADY_ACTIVE:
        error_pair(ServiceFaultAlreadyExistsError),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _trigger_service_fault_error(response):
    """Return an exception based on response from Trigger RPC, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=service_fault_pb2.TriggerServiceFaultResponse.Status.Name,
                         status_to_error=_TRIGGER_STATUS_TO_ERROR)


_CLEAR_STATUS_TO_ERROR = collections.defaultdict(lambda: (FaultResponseError, None))
_CLEAR_STATUS_TO_ERROR.update({
    service_fault_pb2.ClearServiceFaultResponse.STATUS_OK: (None, None),
    service_fault_pb2.ClearServiceFaultResponse.STATUS_FAULT_NOT_ACTIVE:
        error_pair(ServiceFaultDoesNotExistError),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _clear_service_fault_error(response):
    """Return an exception based on response from Clear RPC, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=service_fault_pb2.ClearServiceFaultResponse.Status.Name,
                         status_to_error=_CLEAR_STATUS_TO_ERROR)
