# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client for the directory registration service.

A DirectoryRegistrationClient allows a client to modify information about other API services
available on a robot.
"""
import collections
import logging
import threading
import time

from bosdyn.api import (directory_pb2, directory_registration_pb2,
                        directory_registration_service_pb2_grpc)

from bosdyn.client.common import (BaseClient, error_factory, error_pair, handle_unset_status_error,
                                  handle_common_header_errors)
from .exceptions import ResponseError, TimedOutError


_LOGGER = logging.getLogger(__name__)


class DirectoryRegistrationResponseError(ResponseError):
    """General class of errors for directory registration responses."""


class ServiceAlreadyExistsError(DirectoryRegistrationResponseError):
    """The service already exists on the robot."""


class ServiceDoesNotExistError(DirectoryRegistrationResponseError):
    """The specified service does not exist on the robot."""


class DirectoryRegistrationClient(BaseClient):
    """Write off-robot services and modify their information."""

    default_service_name = 'directory-registration'
    service_type = 'bosdyn.api.DirectoryRegistrationService'

    def __init__(self):
        super(DirectoryRegistrationClient, self).__init__(
            directory_registration_service_pb2_grpc.DirectoryRegistrationServiceStub)

    def register(self, name, service_type, authority, host_ip, port, user_token_required=True,
                 application_token_required=False, liveness_timeout_secs=0, **kwargs):
        """Register a service routing with the robot. 
        
        If service name already registered, no change will be applied and will raise ServiceAlreadyExistsError.
        Every request received by the robot will serve as a heartbeat and update the service last_update field.
        
        Args:
          name: The name of the service. Must be unique.
          service_type: The GRPC service definition defining the calls to/from this service.
            (authority, service_type) must be unique in the directory.
          authority: The authority used to direct calls to this service.
            (authority, service_type) must be unique in the directory.
          host_ip: The ip address of the system that the service is being hosted on.
          port: The port number the service can be accessed through on the host system.
          user_token_required: If a user token should be verified to access the service.
          application_token_required: Deprecated - Do not use.
          liveness_timeout_secs: Number of seconds without directory heartbeat before timeout fault.

        Raises:
          RpcError: Problem communicating with the robot.
          ServiceAlreadyExistsError: The service already exists.
          DirectoryRegistrationResponseError: Something went wrong during the directory registration.
        """
        if (application_token_required):
            _LOGGER.warning(
                'The application_token_required parameter has been deprecated and will have no effect.'
            )

        service_entry = directory_pb2.ServiceEntry(name=name, type=service_type,
                                                   authority=authority,
                                                   user_token_required=user_token_required,
                                                   liveness_timeout_secs=liveness_timeout_secs)
        endpoint = directory_pb2.Endpoint(host_ip=host_ip, port=port)

        req = directory_registration_pb2.RegisterServiceRequest(service_entry=service_entry,
                                                                endpoint=endpoint)

        return self.call(self._stub.RegisterService, req,
                         error_from_response=_directory_register_error, **kwargs)

    def update(self, name, service_type, authority, host_ip, port, user_token_required=True,
               application_token_required=False, liveness_timeout_secs=0, **kwargs):
        """Update a service definition of an existing service that matches the service name.

        If service name is not registered, will raise ServiceDoesNotExistError.
        Every request received by the robot will serve as a heartbeat and update the service last_update field.

        Args:
          name: The name of the service to be updated.
          service_type: The GRPC service definition defining the calls to/from this service.
            (authority, service_type) must be unique in the directory.
          authority: The authority used to direct calls to this service.
            (authority, service_type) must be unique in the directory.
          host_ip: The ip address of the system that the service is being hosted on.
          port: The port number the service can be accessed through on the host system.
          user_token_required: If a user token should be verified to access the service.
          application_token_required Deprecated - Do not use.
          liveness_timeout_secs: Number of seconds without directory heartbeat before timeout fault.
          
        Raises:
          RpcError: Problem communicating with the robot.
          ServiceDoesNotExistError: The service does not exist.
          DirectoryRegistrationResponseError: Something went wrong during the directory registration.
        """
        if (application_token_required):
            _LOGGER.warning(
                'The application_token_required parameter has been deprecated and will have no effect.'
            )

        service_entry = directory_pb2.ServiceEntry(name=name, type=service_type,
                                                   authority=authority,
                                                   user_token_required=user_token_required,
                                                   liveness_timeout_secs=liveness_timeout_secs)
        endpoint = directory_pb2.Endpoint(host_ip=host_ip, port=port)

        req = directory_registration_pb2.UpdateServiceRequest(service_entry=service_entry,
                                                              endpoint=endpoint)

        return self.call(self._stub.UpdateService, req, error_from_response=_directory_update_error,
                         **kwargs)

    def unregister(self, name, **kwargs):
        """Remove a service routing with the robot.
        
        Args:
          name: The name of the service to be removed.
          
        Raises:
          RpcError: Problem communicating with the robot.
          ServiceDoesNotExistError: The service does not exist.
          DirectoryRegistrationResponseError: Something went wrong during the directory registration.
        """
        req = directory_registration_pb2.UnregisterServiceRequest(service_name=name)

        return self.call(self._stub.UnregisterService, req,
                         error_from_response=_directory_unregister_error, **kwargs)


_REGISTER_STATUS_TO_ERROR = collections.defaultdict(lambda:
                                                    (DirectoryRegistrationResponseError, None))
_REGISTER_STATUS_TO_ERROR.update({
    directory_registration_pb2.RegisterServiceResponse.STATUS_OK: (None, None),
    directory_registration_pb2.RegisterServiceResponse.STATUS_ALREADY_EXISTS:
        error_pair(ServiceAlreadyExistsError),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _directory_register_error(response):
    """Return an exception based on response from Register RPC, None if no error."""
    return error_factory(
        response, response.status,
        status_to_string=directory_registration_pb2.RegisterServiceResponse.Status.Name,
        status_to_error=_REGISTER_STATUS_TO_ERROR)


_UPDATE_STATUS_TO_ERROR = collections.defaultdict(lambda:
                                                  (DirectoryRegistrationResponseError, None))
_UPDATE_STATUS_TO_ERROR.update({
    directory_registration_pb2.UpdateServiceResponse.STATUS_OK: (None, None),
    directory_registration_pb2.UpdateServiceResponse.STATUS_NONEXISTENT_SERVICE:
        error_pair(ServiceDoesNotExistError),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _directory_update_error(response):
    """Return an exception based on response from Update RPC, None if no error."""
    return error_factory(
        response, response.status,
        status_to_string=directory_registration_pb2.UpdateServiceResponse.Status.Name,
        status_to_error=_UPDATE_STATUS_TO_ERROR)


_UNREGISTER_STATUS_TO_ERROR = collections.defaultdict(lambda:
                                                      (DirectoryRegistrationResponseError, None))
_UNREGISTER_STATUS_TO_ERROR.update({
    directory_registration_pb2.UnregisterServiceResponse.STATUS_OK: (None, None),
    directory_registration_pb2.UnregisterServiceResponse.STATUS_NONEXISTENT_SERVICE:
        error_pair(ServiceDoesNotExistError),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _directory_unregister_error(response):
    """Return an exception based on response from Unregister RPC, None if no error."""
    return error_factory(
        response, response.status,
        status_to_string=directory_registration_pb2.UnregisterServiceResponse.Status.Name,
        status_to_error=_UNREGISTER_STATUS_TO_ERROR)


def reset_service_registration(directory_registration_client, name, service_type, authority,
                               host_ip, port, user_token_required=True, liveness_timeout_secs=0):
    """Reset a service registration by unregistering the service and then re-registering it.

    This is useful when a program wants to register a new service but there may be an old entry
    in the robot directory from a previous instance of the program. If the service
    does not already exists, the exception will be surpressed and a new registration will
    still be performed. Unregistering the service has the advantage of clearing all service
    faults, if any existed.
    """
    try:
        directory_registration_client.unregister(name)
    except ServiceDoesNotExistError:
        pass
    directory_registration_client.register(name, service_type, authority, host_ip, port,
                                           user_token_required=user_token_required,
                                           liveness_timeout_secs=liveness_timeout_secs)


class DirectoryRegistrationKeepAlive(object):
    """Helper class to keep a directory entry updated.

    Assuming the directory itself is hosted on the robot, and the service being registered in the
    directory is on a payload, use of this class streamlines the following cases:

    1) The payload, or the payload-hosted service, is restarted.
    2) The robot is restarted.
    3) On-robot processes clear out the directory. This can happen in rare cases.

    This class will also maintain liveness status with the robot directory, if enabled for this
    service, by sending a registration/update request at the specified interval.

    Args:
      dir_reg_client: Client to the directory registration service.
      logger: logging.Logger object to log with. Defaults to None, in which case one with the
          class name is acquired.
      rpc_timeout_seconds: Number of seconds to wait for a dir_reg_client RPC. Defaults to None,
          for no timeout.
      rpc_interval_seconds: Interval at which to request service registrations.
    """

    def __init__(self, dir_reg_client, logger=None, rpc_timeout_seconds=None,
                 rpc_interval_seconds=30):
        self.authority = None
        self.directory_name = None
        self.host = None
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.port = None
        self.service_type = None
        self.dir_reg_client = dir_reg_client

        self._end_reregister_signal = threading.Event()
        self._lock = threading.Lock()
        self._rpc_timeout = rpc_timeout_seconds
        self._reregister_period = rpc_interval_seconds

        # Configure the thread to do re-registration.
        self._thread = threading.Thread(target=self._periodic_reregister)
        self._thread.daemon = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        self.unregister()

    def start(self, directory_name, service_type, authority, host, port, liveness_timeout_secs=None,
              user_token_required=True, reset_service=True):
        """Register, optionally update, and then kick off thread.
        
        Can not be restarted with this method after a shutdown.
        
        Args:
            directory_name: See directory.proto for details.
            service_type: See directory.proto for details.
            authority: See directory.proto for details.
            host: See directory.proto for details.
            port: See directory.proto for details.
            liveness_timeout_secs: See directory.proto for details. Defaults to
                                   2.5x rpc_interval_seconds.
            user_token_required: See directory.proto for details.
            reset_service: Fully reset the service registration before the periodic registrations.

        Raises:
          RpcError: Problem communicating with the robot.
        """
        if liveness_timeout_secs is None:
            liveness_timeout_secs = self._reregister_period * 2.5
        if reset_service:
            reset_service_registration(self.dir_reg_client, directory_name, service_type, authority,
                                       host, port, user_token_required=user_token_required,
                                       liveness_timeout_secs=liveness_timeout_secs)
        else:
            try:
                self.dir_reg_client.register(directory_name, service_type, authority, host, port,
                                             user_token_required=user_token_required,
                                             liveness_timeout_secs=liveness_timeout_secs)
            except ServiceAlreadyExistsError as exc:
                self.dir_reg_client.update(directory_name, service_type, authority, host, port,
                                           user_token_required=user_token_required,
                                           liveness_timeout_secs=liveness_timeout_secs)
        self.logger.info('{} service registered/updated.'.format(directory_name))

        self.authority = authority
        self.directory_name = directory_name
        self.host = host
        self.port = port
        self.service_type = service_type
        self.liveness_timeout_secs = liveness_timeout_secs

        # This will raise an exception if the thread has already started.
        self._thread.start()

    def is_alive(self):
        """Are we still periodically re-registering?
        
        Returns:
          A bool stating if still alive
        """
        return self._thread.is_alive()

    def shutdown(self):
        """Stop the background thread."""
        self.logger.info('Shutting down {} keep alive'.format(self.directory_name))
        self._end_reregister_signal.set()
        self._thread.join()

    def unregister(self):
        """Remove service from the directory.
        
        Raises:
          RpcError: Problem communicating with the robot.
          ServiceDoesNotExistError: The service does not exist.
        """
        self.logger.info('Unregistering {} from directory'.format(self.directory_name))
        self.dir_reg_client.unregister(self.directory_name, timeout=self._rpc_timeout)

    def _periodic_reregister(self):
        """Handles an accidental removal of the service from the directory.
        
        Raises:
          RpcError: Problem communicating with the robot.
        """
        self.logger.info('Starting directory registration loop for {}'.format(self.directory_name))
        while True:
            exec_start = time.time()
            try:
                self.dir_reg_client.register(self.directory_name, self.service_type, self.authority,
                                             self.host, self.port,
                                             liveness_timeout_secs=self.liveness_timeout_secs,
                                             timeout=self._rpc_timeout)
            except ServiceAlreadyExistsError:
                # Ignore "already registered" errors -- we expect those.
                # We do not allow anyone to change the directory parameters with an "update" call,
                # because we assume that the lifespan of this thread matches the lifespan of the
                # service being registered.
                pass
            except TimedOutError:
                self.logger.warning('Timed out, timeout set to "{}"'.format(self._rpc_timeout))
            except Exception:
                # Log all other exceptions, but continue looping in hopes that it resolves itself
                self.logger.exception('Caught general exception')
            exec_sec = time.time() - exec_start
            if self._end_reregister_signal.wait(self._reregister_period - exec_sec):
                break
