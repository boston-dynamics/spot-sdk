# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from typing import List, Optional

from google.protobuf.wrappers_pb2 import DoubleValue

from bosdyn.api.graph_nav import area_callback_pb2
from bosdyn.util import seconds_to_duration


class AreaCallbackServiceConfig:
    """Config data required to run a area callback service."""

    def __init__(self, service_name: str, required_lease_resources: List[str] = (),
                 log_begin_callback_data: bool = False):
        """AreaCallbackServiceConfig constructor.

        Args:
            service_name (str): The name of the service, for registering with directory.
            required_lease_resources (List[str]): List of required lease resources.
            log_begin_callback_data (bool): Log the data field of the begin callback request.
        """
        self.service_name = service_name
        self.required_lease_resources = required_lease_resources

        self.log_begin_callback_data = log_begin_callback_data

    @property
    def area_callback_information(self):
        """area_callback_pb2.AreaCallbackInformation for a specific AreaCallback implementation.

        Returns:
            area_callback_pb2.AreaCallbackInformation
        """
        return area_callback_pb2.AreaCallbackInformation(
            required_lease_resources=self.required_lease_resources)
