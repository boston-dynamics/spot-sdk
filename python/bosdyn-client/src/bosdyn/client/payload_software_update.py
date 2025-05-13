# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Payload software update service gRPC client.

This is used by Spot payloads to coordinate updates of their own software with Spot.
"""

import datetime

from google.protobuf import timestamp_pb2

from bosdyn.api.payload_software_update_pb2 import (GetAvailableSoftwareUpdatesRequest,
                                                    SendCurrentVersionInfoRequest,
                                                    SendSoftwareUpdateStatusRequest)
from bosdyn.api.payload_software_update_service_pb2_grpc import PayloadSoftwareUpdateServiceStub
from bosdyn.api.robot_id_pb2 import SoftwareVersion
from bosdyn.api.software_package_pb2 import SoftwarePackageVersion, SoftwareUpdateStatus
from bosdyn.client.common import BaseClient


class PayloadSoftwareUpdateClient(BaseClient):
    """A client for payloads to coordinate software updates with a robot."""

    default_service_name = 'payload-software-update'
    service_type = 'bosdyn.api.PayloadSoftwareUpdateService'

    def __init__(self):
        super(PayloadSoftwareUpdateClient, self).__init__(PayloadSoftwareUpdateServiceStub)

    def send_current_software_info(
            self, package_name: str, version: SoftwareVersion | list[int],
            release_date: float | timestamp_pb2.Timestamp | datetime.datetime, build_id: str,
            **kwargs):
        """Send version information about the currently installed payload software to Spot.

        Args:
            package_name: Name of the package, e.g., "coreio"
            version: Current semantic version of the installed software.
            release_date: Release date of the currently installed software.
            build_id: Unique identifier of the build.

        Returns:
            SendCurrentVersionInfoResponse: The response object from Spot. Currently this message
                contains no information other than a standard response header.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        request = self.make_info_request(package_name, version, release_date, build_id)
        return self.call(self._stub.SendCurrentVersionInfo, request, **kwargs)

    def send_current_software_info_async(
            self, package_name: str, version: SoftwareVersion | list[int],
            release_date: float | timestamp_pb2.Timestamp | datetime.datetime, build_id: str,
            **kwargs):
        """Async version of send_current_software_info().

        Args:
            package_name: Name of the package, e.g., "coreio"
            version: Current semantic version of the installed software.
            release_date: Release date of the currently installed software.
            build_id: Unique identifier of the build.

        Returns:
            SendCurrentVersionInfoResponse: The response object from Spot. Currently this message
                contains no information other than a standard response header.
        Raises:
            RpcError: Problem communicating with the robot.
        """
        request = self.make_info_request(package_name, version, release_date, build_id)
        return self.call_async(self._stub.SendCurrentVersionInfo, request, **kwargs)

    def get_available_updates(self, package_names: str | list[str], **kw_args):
        """Get a list of package information for the named package(s).

        Args:
            package_names: The package name or list of package names to query.

        Returns:
            GetAvailableSoftwareUpdatesResponse: The response object from Spot containing the
                version info for packages cached by Spot.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        if not isinstance(package_names, list):
            package_names = [package_names]
        request = GetAvailableSoftwareUpdatesRequest(package_names=package_names)
        return self.call(self._stub.GetAvailableSoftwareUpdates, request, **kw_args)

    def get_available_updates_async(self, package_names: str | list[str], **kw_args):
        """Async version of get_available_updates().

        Args:
            package_names: The package name or list of package names to query.

        Returns:
            GetAvailableSoftwareUpdatesResponse: The response object from Spot containing the
                version info for packages cached by Spot.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        if not isinstance(package_names, list):
            package_names = [package_names]
        request = GetAvailableSoftwareUpdatesRequest(package_names=package_names)
        return self.call_async(self._stub.GetAvailableSoftwareUpdates, request, **kw_args)

    def send_installation_status(self, package_name: str, status: SoftwareUpdateStatus.Status,
                                 error_code: SoftwareUpdateStatus.ErrorCode, **kw_args):
        """Send a status update of a payload software installation operation to Spot.

        Args:
            package_name: Name of the package being updated
            status: Status code of installation operation
            error_code: Error code of the installation operation, or ERROR_NONE if no error has
                been encountered.

        Returns:
            SendSoftwareUpdateStatusResponse: The response object from Spot. Currently this message
                contains nothing beyond a standard response header.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        status = SoftwareUpdateStatus(package_name=package_name, status=status,
                                      error_code=error_code)
        request = SendSoftwareUpdateStatusRequest(update_status=status)
        return self.call(self._stub.SendSoftwareUpdateStatus, request, **kw_args)

    def send_installation_status_async(self, package_name: str, status: SoftwareUpdateStatus.Status,
                                       error_code: SoftwareUpdateStatus.ErrorCode, **kw_args):
        """Async version of send_installation_status().

        Args:
            package_name: Name of the package being updated
            status: Status code of installation operation
            error_code: Error code of the installation operation, or ERROR_NONE if no error has
                been encountered.

        Returns:
            SendSoftwareUpdateStatusResponse: The response object from Spot. Currently this message
                contains nothing beyond a standard response header.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        status = SoftwareUpdateStatus(package_name=package_name, status=status,
                                      error_code=error_code)
        request = SendSoftwareUpdateStatusRequest(update_status=status)
        return self.call_async(self._stub.SendSoftwareUpdateStatus, request, **kw_args)

    @staticmethod
    def make_info_request(package_name: str, version: SoftwareVersion,
                          release_date: float | timestamp_pb2.Timestamp | datetime.datetime,
                          build_id: str):
        """Make a SendCurrentVersionInfoRequest message using the supplied information.

        Args:
            package_name: Name of the package, e.g., "coreio"
            version: Current semantic version of the installed software.
            release_date: Release date of the currently installed software.
            build_id: Unique identifier of the build.

        Returns:
            SendCurrentVersionInfoRequest: Message communicating to Spot the version information
                    of the currently installed payload software.
        """
        if not isinstance(version, SoftwareVersion):
            version = SoftwareVersion(major_version=version[0], minor_version=version[1],
                                      patch_level=version[2])
        if isinstance(release_date, float):
            release_date = datetime.datetime.fromtimestamp(release_date)
        if isinstance(release_date, datetime.datetime):
            pb_release_date = timestamp_pb2.Timestamp()
            pb_release_date.FromDatetime(release_date)
            release_date = pb_release_date

        return SendCurrentVersionInfoRequest(
            package_version=SoftwarePackageVersion(package_name=package_name, version=version,
                                                   release_date=release_date, build_id=build_id))
