"""Common message processors."""

from bosdyn.api.header_pb2 import RequestHeader
from bosdyn.util import now_nsec, set_timestamp_from_nsec  # bosdyn-core


class AddRequestHeader(object):
    """Sets header fields common to all bosdyn.api requests."""

    def __init__(self, client_name_func):
        """Constructor, takes function to access the client name to insert into request headers."""
        self.get_client_name = client_name_func

    def _create_header(self):
        header = RequestHeader()
        header.client_name = self.get_client_name()
        set_timestamp_from_nsec(header.request_timestamp, now_nsec())
        return header

    def mutate(self, request):
        """Mutate request such that its header contains a client name and a timestamp."""
        header = self._create_header()
        request.header.CopyFrom(header)
