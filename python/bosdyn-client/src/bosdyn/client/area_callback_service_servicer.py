# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

# pylint: disable=missing-module-docstring
import copy
import logging
from threading import Event, Lock, Thread
from typing import Callable

from bosdyn.api import lease_pb2
from bosdyn.api.graph_nav import area_callback_pb2, area_callback_service_pb2_grpc
from bosdyn.client.area_callback_region_handler_base import AreaCallbackRegionHandlerBase
from bosdyn.client.area_callback_service_utils import AreaCallbackServiceConfig
from bosdyn.client.data_buffer import DataBufferClient
from bosdyn.client.lease import Lease, LeaseNotOwnedByWallet, NoSuchLease
from bosdyn.client.lease_validator import LeaseValidator, LeaseValidatorResponseProcessor
from bosdyn.client.robot import Robot
from bosdyn.client.server_util import ResponseContext
from bosdyn.util import timestamp_to_sec

_LOGGER = logging.getLogger(__name__)

CallbackBuilderFn = Callable[[AreaCallbackServiceConfig, Robot], AreaCallbackRegionHandlerBase]


class AreaCallbackServiceServicer(area_callback_service_pb2_grpc.AreaCallbackServiceServicer):
    """Implementation of area callback service.

    Args:
        robot: The Robot object used to create service clients.
        config: The AreaCallbackServiceConfig defining the data for the AreaCallbackInformation
            response.
        area_callback_builder_fn: Callable to create the AreaCallbackRegionHandlerBase subclass that
            implements the details of the callback.  Usually this will simply be the class itself.
    """
    SERVICE_TYPE = "bosdyn.api.graph_nav.AreaCallbackService"

    def __init__(self, robot: Robot, config: AreaCallbackServiceConfig,
                 area_callback_builder_fn: CallbackBuilderFn):
        super().__init__()
        self.area_callback_service_config = config
        self.area_callback_builder_fn = area_callback_builder_fn
        self.area_callback_region_handler = None
        self.area_callback_active_thread = None
        self.area_callback_active_thread_event = None
        self.robot = robot

        self._lock = Lock()
        self._next_command_id = 1
        self._active_command_id = None
        self._rpc_logger = self.robot.ensure_client(DataBufferClient.default_service_name)
        self._lease_validator = LeaseValidator(self.robot)
        self._shutdown_timeout = 5
        self.robot.response_processors.append(LeaseValidatorResponseProcessor(
            self._lease_validator))

    def AreaCallbackInformation(self, request, context):
        """Return the configured AreaCallbackInformation."""
        response = area_callback_pb2.AreaCallbackInformationResponse()
        with ResponseContext(response, request, self._rpc_logger), self._lock:
            response.info.CopyFrom(self.area_callback_service_config.area_callback_information)
        return response

    def BeginCallback(self, request, context):
        """Begin the callback in a new region."""
        _LOGGER.info('Received BeginCallback')
        request_to_log = request
        if not self.area_callback_service_config.log_begin_callback_data:
            request_to_log = copy.deepcopy(request)
        response = area_callback_pb2.BeginCallbackResponse()
        with ResponseContext(response, request_to_log, self._rpc_logger), self._lock:
            if self._is_expired(request.end_time):
                response.status = area_callback_pb2.BeginCallbackResponse.STATUS_EXPIRED_END_TIME
                return response
            self._begin_callback_region_handler(request, response)
            if response.status == area_callback_pb2.BeginCallbackResponse.STATUS_OK:
                self.area_callback_active_thread_event = Event()
                self.area_callback_active_thread = Thread(
                    target=self.area_callback_region_handler.internal_run_wrapper,
                    args=[self.area_callback_active_thread_event])
                self.area_callback_active_thread.start()
                _LOGGER.info('Created thread for command id %d', response.command_id)
        return response

    def _begin_callback_region_handler(
            self, request: area_callback_pb2.AreaCallbackInformationRequest,
            response: area_callback_pb2.AreaCallbackInformationResponse) -> None:
        self.area_callback_region_handler = self.area_callback_builder_fn(
            self.area_callback_service_config, self.robot)
        self.area_callback_region_handler.internal_set_end_time(timestamp_to_sec(request.end_time))
        response.status = self.area_callback_region_handler.begin(request)
        response.command_id = self._next_command_id
        self._active_command_id = self._next_command_id
        self._next_command_id += 1
        self.area_callback_region_handler.internal_begin_complete()

    def BeginControl(self, request, context):
        """Receive robot control from GraphNav."""
        _LOGGER.info('Received BeginControl for command id %d', request.command_id)
        response = area_callback_pb2.BeginControlResponse()
        with ResponseContext(response, request, self._rpc_logger), self._lock:
            if (not self.area_callback_region_handler or
                    not self._is_active_command_id(request.command_id)):
                response.status = area_callback_pb2.BeginControlResponse.STATUS_INVALID_COMMAND_ID
                return response
            if not self._test_and_forward_leases(request.leases, response):
                return response
            self.area_callback_region_handler.internal_give_control()
            response.status = area_callback_pb2.BeginControlResponse.STATUS_OK
        return response

    def UpdateCallback(self, request, context):
        """Regular updates from GraphNav, with responses to update the policy."""
        response = area_callback_pb2.UpdateCallbackResponse()
        with ResponseContext(response, request, self._rpc_logger), self._lock:
            if (not self.area_callback_region_handler or
                    not self._is_active_command_id(request.command_id)):
                response.status = area_callback_pb2.UpdateCallbackResponse.STATUS_INVALID_COMMAND_ID
                return response
            response.CopyFrom(self.area_callback_region_handler.update_response)
            if request.HasField("end_time"):
                if self._is_expired(request.end_time):
                    response.status = area_callback_pb2.UpdateCallbackResponse.STATUS_EXPIRED_END_TIME
                    return response
                self.area_callback_region_handler.internal_set_end_time(
                    timestamp_to_sec(request.end_time))
            self.area_callback_region_handler.internal_set_stage(request.stage)
            response.status = area_callback_pb2.UpdateCallbackResponse.STATUS_OK
            # TODO Update LeaseValidator in case of LeaseUseError.
        return response

    def EndCallback(self, request, context):
        """Terminate handling of this region."""
        _LOGGER.info('Received EndCallback for command %d', request.command_id)
        response = area_callback_pb2.EndCallbackResponse()
        with ResponseContext(response, request, self._rpc_logger):
            if (not self.area_callback_region_handler or
                    not self._is_active_command_id(request.command_id)):
                response.status = area_callback_pb2.EndCallbackResponse.STATUS_INVALID_COMMAND_ID
                return response
            if not self.Shutdown(timeout=self._shutdown_timeout):
                _LOGGER.error('Failed to shut down thread for command id %d', request.command_id)
                response.status = area_callback_pb2.EndCallbackResponse.STATUS_SHUTDOWN_CALLBACK_FAILED
                return response
            response.status = area_callback_pb2.EndCallbackResponse.STATUS_OK
            self.area_callback_region_handler.end()
            self._clear_lease_wallet()
            self.area_callback_region_handler = None
        return response

    def _is_expired(self, end_time):
        current_robot_time_secs = self.robot.time_sec()
        end_time_secs = timestamp_to_sec(end_time)
        return end_time_secs < current_robot_time_secs

    def _is_active_command_id(self, command_id):
        return command_id == self._active_command_id

    def _test_and_forward_leases(self, leases, response) -> bool:
        # Check if all leases are supplied.
        leases_to_add = []

        supplied_lease_set = set(lease.resource for lease in leases)
        expected_lease_set = set(self.area_callback_service_config.required_lease_resources)
        if supplied_lease_set != expected_lease_set:
            response.status = area_callback_pb2.BeginControlResponse.STATUS_MISSING_LEASE_RESOURCES
            return False

        # Check if leases are valid.
        lease_error = False
        for lease_proto in leases:
            lease = Lease(lease_proto)
            # We allow for different epochs to handle the case when the robot has rebooted.
            # Because the lease is coming directly from graph nav, we can be fairly sure the
            # epoch is correct, and it is okay to overwrite our lease if the epoch doesn't match.
            lease_use_result = self._lease_validator.test_and_set_active_lease(
                lease, allow_super_leases=False, allow_different_epoch=True)
            response.lease_use_results.add().CopyFrom(lease_use_result)
            if lease_use_result.status == lease_pb2.LeaseUseResult.STATUS_OK:
                leases_to_add.append(lease)
            else:
                response.status = area_callback_pb2.BeginControlResponse.STATUS_LEASE_ERROR
                lease_error = True
        if lease_error:
            return False

        # Add leases to lease wallet after they've all passed validation.
        for lease in leases_to_add:
            self.robot.lease_wallet.add(lease)

        return True

    def _clear_lease_wallet(self):
        for resource in self.area_callback_service_config.required_lease_resources:
            try:
                lease = self.robot.lease_wallet.get_lease(resource=resource)
                self.robot.lease_wallet.remove(lease)
            except (LeaseNotOwnedByWallet, NoSuchLease):
                pass

    def Shutdown(self, timeout=5):
        """Call to force run thread to terminate.

        Args:
            timeout (float, optional): Time allowed to run thread to shutdown. Defaults to 5.

        Returns:
            bool: True if the thread correctly shut down within the allowed time.
        """
        if not self.area_callback_active_thread:
            return True
        self.area_callback_active_thread_event.set()
        self.area_callback_active_thread.join(timeout)
        return not self.area_callback_active_thread.is_alive()
