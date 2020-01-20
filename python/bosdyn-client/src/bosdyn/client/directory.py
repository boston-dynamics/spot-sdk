"""Client for the directory service.

A DirectoryClient allows a client to look-up information about other API services available on a
 robot.
"""
import collections

from bosdyn.api import directory_service_pb2, directory_service_pb2_grpc

from .common import BaseClient
from .common import (common_header_errors, error_factory, handle_unset_status_error,
                     handle_common_header_errors)
from .exceptions import ResponseError

class DirectoryResponseError(ResponseError):
    """General class of errors for Directory service."""


class NonexistentServiceError(DirectoryResponseError):
    """The requested service name does not exist."""


_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_STATUS_TO_ERROR.update({
    directory_service_pb2.GetServiceEntryResponse.STATUS_OK: (None, None),
    directory_service_pb2.GetServiceEntryResponse.STATUS_NONEXISTENT_SERVICE:
    (NonexistentServiceError, NonexistentServiceError.__doc__),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _error_from_response(response):
    """Return a custom exception based on response, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=directory_service_pb2.GetServiceEntryResponse.Status.Name,
                         status_to_error=_STATUS_TO_ERROR)


class DirectoryClient(BaseClient):
    """List robot services and get information on them."""

    default_service_name = 'directory'
    default_authority = 'api.spot.robot'
    service_type = 'bosdyn.api.DirectoryService'

    def __init__(self):
        super(DirectoryClient, self).__init__(directory_service_pb2_grpc.DirectoryServiceStub)

    def list(self, **kwargs):
        """List all services present on the robot."""
        req = directory_service_pb2.ListServiceEntriesRequest()
        return self.call(self._stub.ListServiceEntries, req, value_from_response=_list_value,
                         error_from_response=common_header_errors, **kwargs)

    def list_async(self, **kwargs):
        """List all services present on the robot."""
        req = directory_service_pb2.ListServiceEntriesRequest()
        return self.call_async(self._stub.ListServiceEntries, req, value_from_response=_list_value,
                               error_from_response=common_header_errors, **kwargs)

    def get_entry(self, service_name, **kwargs):
        """Get the service entry for one particular service specified by name.
        Throws NonexistentServiceError if the service is not found."""
        req = directory_service_pb2.GetServiceEntryRequest(service_name=service_name)
        return self.call(self._stub.GetServiceEntry, req, value_from_response=_get_entry_value,
                         error_from_response=_error_from_response, **kwargs)

    def get_entry_async(self, service_name, **kwargs):
        """Get the service entry for one particular service specified by name.
        Throws NonexistentServiceError if the service is not found."""
        req = directory_service_pb2.GetServiceEntryRequest(service_name=service_name)
        return self.call_async(self._stub.GetServiceEntry, req,
                               value_from_response=_get_entry_value,
                               error_from_response=_error_from_response, **kwargs)


def _list_value(response):
    return response.service_entries


def _get_entry_value(response):
    return response.service_entry
