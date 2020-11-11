# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the Spot CAM Version service."""

import logging

_LOGGER = logging.getLogger(__name__)

from bosdyn.client.common import (BaseClient, common_header_errors, handle_common_header_errors)
from bosdyn.api.spot_cam import service_pb2_grpc
from bosdyn.api.spot_cam import version_pb2


class VersionClient(BaseClient):
    """A client calling Spot CAM Version service.
    """
    default_service_name = 'spot-cam-version'
    service_type = 'bosdyn.api.spot_cam.VersionService'

    def __init__(self):
        super(VersionClient, self).__init__(service_pb2_grpc.VersionServiceStub)

    def get_software_version(self, **kwargs):
        """Retrieves the Spot CAM's current software version.

        Returns:
            SoftwareVersion proto for the currently installed version.
        """
        request = version_pb2.GetSoftwareVersionRequest()
        return self.call(self._stub.GetSoftwareVersion, request,
                         self._get_software_version_from_response,
                         self._version_error_from_response, **kwargs)

    def get_software_version_async(self, **kwargs):
        """Async version of get_software_version()"""
        request = version_pb2.GetSoftwareVersionRequest()
        return self.call_async(self._stub.GetSoftwareVersion, request,
                               self._get_software_version_from_response,
                               self._version_error_from_response, **kwargs)

    def get_software_version_full(self, **kwargs):
        """Retrieves the Spot CAM's full version information.

        Returns:
            GetSoftwareVersionResponse proto with all version information.
        """
        request = version_pb2.GetSoftwareVersionRequest()
        return self.call(self._stub.GetSoftwareVersion, request,
                         error_from_response=self._version_error_from_response, **kwargs)

    def get_software_version_full_async(self, **kwargs):
        """Async version of get_software_version_full()"""
        request = version_pb2.GetSoftwareVersionRequest()
        return self.call_async(self._stub.GetSoftwareVersion, request,
                               error_from_response=self._version_error_from_response, **kwargs)

    @staticmethod
    def _get_software_version_from_response(response):
        return response.version

    @staticmethod
    @handle_common_header_errors
    def _version_error_from_response(response):  # pylint: disable=unused-argument
        return None
