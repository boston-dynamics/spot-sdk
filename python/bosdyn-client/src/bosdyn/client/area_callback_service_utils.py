# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging
import time
from typing import List

from bosdyn.api import service_fault_pb2
from bosdyn.api.graph_nav import area_callback_pb2
from bosdyn.api.service_customization_pb2 import DictParam
from bosdyn.client.directory import NonexistentServiceError
from bosdyn.client.exceptions import RpcError
from bosdyn.client.fault import (FaultResponseError, ServiceFaultAlreadyExistsError,
                                 ServiceFaultDoesNotExistError)
from bosdyn.client.service_customization_helpers import dict_params_to_dict

_LOGGER = logging.getLogger(__name__)


class AreaCallbackServiceConfig:
    """Config data required to run a area callback service."""

    def __init__(self, service_name: str, required_lease_resources: List[str] = (),
                 log_begin_callback_data: bool = False,
                 area_callback_information: area_callback_pb2.AreaCallbackInformation = None):
        """AreaCallbackServiceConfig constructor.

        Args:
            service_name (str): The name of the service, for registering with directory.
            required_lease_resources (List[str]): List of required lease resources.
            log_begin_callback_data (bool): Log the data field of the begin callback request.
            area_callback_information (area_callback_pb2.AreaCallbackInformation): Information describing the area callback.
        """
        self.service_name = service_name
        self.required_lease_resources = required_lease_resources

        self.log_begin_callback_data = log_begin_callback_data
        self.area_callback_information = area_callback_information or \
                                         area_callback_pb2.AreaCallbackInformation(
                                            required_lease_resources=self.required_lease_resources)

    def parse_params(self, params: DictParam):
        """ Parse params and validate they agree with the spec stored in area_callback_information.

        Args:
            params (DictParam): The parameters being validated.
        """
        return dict_params_to_dict(params, self.area_callback_information.custom_params)


# Helper to raise service faults when other services are unavailable.
def handle_service_faults(fault_client, robot_state_client, directory_client, service_name,
                          prereq_services):
    service_fault = service_fault_pb2.ServiceFault()
    service_fault.fault_id.fault_name = f'{service_name}'
    service_fault.fault_id.service_name = service_name
    service_fault.severity = service_fault_pb2.ServiceFault.SEVERITY_CRITICAL
    check_period = 0.5  # seconds.

    while True:
        time.sleep(check_period)

        # Don't fault the service if it doesn't actually exist.
        try:
            registered_service = directory_client.get_entry(service_name)
        except NonexistentServiceError as exc:
            continue

        set_fault = False
        unavailable_services = []
        for service in prereq_services:
            # Make sure the prereq service exists.
            try:
                registered_service = directory_client.get_entry(service)
            except NonexistentServiceError as exc:
                set_fault = True
                unavailable_services.append(service)
                continue

            # Make sure the prereq service isn't faulted.
            state = robot_state_client.get_robot_state()
            for fault in state.service_fault_state.faults:
                if fault.fault_id.service_name == service:
                    set_fault = True
                    unavailable_services.append(service)
                    break

        # Fault the service.
        if set_fault:
            service_fault.error_message = 'Faulted due to issues with ' + ','.join(
                unavailable_services)
            try:
                fault_client.trigger_service_fault(service_fault)
            except ServiceFaultAlreadyExistsError:
                pass
            except (RpcError, FaultResponseError) as exc:
                _LOGGER.error(f"Failed to set {service_name} fault. {exc}")

        # Otherwise, clear the fault if it exists.
        else:
            try:
                fault_client.clear_service_fault(service_fault.fault_id)
                set_fault = False
            except ServiceFaultDoesNotExistError:
                pass
            except (RpcError, FaultResponseError) as exc:
                _LOGGER.error(f"Failed to clear {service_name} fault. {exc}")
