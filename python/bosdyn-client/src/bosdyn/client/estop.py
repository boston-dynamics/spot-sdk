# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to the emergency stop (estop) service."""

import collections
import ctypes
import enum
import logging
import threading
import time
import os
from six.moves import queue

from google.protobuf.duration_pb2 import Duration

from bosdyn.api import estop_service_pb2_grpc
from bosdyn.api import estop_pb2

from .common import BaseClient
from .common import common_header_errors, handle_common_header_errors, handle_unset_status_error
from .common import error_factory
from .exceptions import Error, ResponseError, RpcError, TimedOutError


class EstopResponseError(ResponseError):
    """General class of errors for Estop service."""


class EndpointUnknownError(EstopResponseError):
    """The endpoint specified in the request is not registered."""


class IncorrectChallengeResponseError(EstopResponseError):
    """The challenge and/or response was incorrect."""


class EndpointMismatchError(EstopResponseError):
    """Target endpoint did not match."""


class ConfigMismatchError(EstopResponseError):
    """Registered to the wrong configuration."""


class InvalidEndpointError(EstopResponseError):
    """New endpoint was invalid."""


class InvalidIdError(EstopResponseError):
    """Tried to replace a EstopConfig, but provided bad ID."""


StopLevel = enum.IntEnum('StopLevel', estop_pb2.EstopStopLevel.items())


class EstopClient(BaseClient):
    """Client to the estop service."""

    default_service_name = 'estop'
    service_type = 'bosdyn.api.EstopService'

    def __init__(self, name="EstopClient - PID: " + str(os.getpid())):
        super(EstopClient, self).__init__(estop_service_pb2_grpc.EstopServiceStub, name=name)

    def register(self, target_config_id, endpoint, **kwargs):
        """Register the endpoint in the target configuration.

        Args:
            target_config_id: The identification of the current configuration on the robot.
            endpoint: Estop endpoint.
            kwargs: Passed to underlying RPC. Example: timeout=5 to cancel the RPC after 5 seconds.
        Returns:
            estop_pb2.EstopEndpoint that has been registered.
        """
        req = self._build_register_request(target_config_id, endpoint)
        return self.call(self._stub.RegisterEstopEndpoint, req,
                         _new_endpoint_from_register_response,
                         _register_endpoint_error_from_response, **kwargs)

    def register_async(self, target_config_id, endpoint, **kwargs):
        """Async version of register()"""
        req = self._build_register_request(target_config_id, endpoint)
        return self.call_async(self._stub.RegisterEstopEndpoint, req,
                               _new_endpoint_from_register_response,
                               _register_endpoint_error_from_response, **kwargs)

    def deregister(self, target_config_id, endpoint, **kwargs):
        """Deregister the endpoint in the target configuration.

        Args:
            target_config_id: The identification of the current configuration on the robot.
            endpoint: Estop endpoint.
            kwargs: Passed to underlying RPC. Example: timeout=5 to cancel the RPC after 5 seconds.
        """
        req = self._build_deregister_request(target_config_id, endpoint)
        self.call(self._stub.DeregisterEstopEndpoint, req, None,
                  _deregister_endpoint_error_from_response, **kwargs)

    def deregister_async(self, target_config_id, endpoint, **kwargs):
        """Async version of deregister()"""
        req = self._build_deregister_request(target_config_id, endpoint)
        return self.call_async(self._stub.DeregisterEstopEndpoint, req, None,
                               _deregister_endpoint_error_from_response, **kwargs)

    def get_config(self, **kwargs):
        """Return the estop configuration of the robot.

        Args:
            kwargs: Passed to underlying RPC. Example: timeout=5 to cancel the RPC after 5 seconds.
        Returns:
            estop_pb2.EstopConfig the robot is currently using.
        """
        return self.call(self._stub.GetEstopConfig, estop_pb2.GetEstopConfigRequest(),
                         _active_config_from_config_response, common_header_errors, **kwargs)

    def get_config_async(self, **kwargs):
        """Async version of get_config()"""
        return self.call_async(self._stub.GetEstopConfig, estop_pb2.GetEstopConfigRequest(),
                               _active_config_from_config_response, common_header_errors, **kwargs)

    def set_config(self, config, target_config_id, **kwargs):
        """Change the estop configuration of the robot.

        Args:
            config: New configuration to set.
            target_config_id: The identification of the current configuration on the robot.
            kwargs: Passed to underlying RPC. Example: timeout=5 to cancel the RPC after 5 seconds.
        Returns:
            estop_pb2.EstopConfig the robot is currently using.
        """
        req = estop_pb2.SetEstopConfigRequest(config=config, target_config_id=target_config_id)
        return self.call(self._stub.SetEstopConfig, req, _active_config_from_config_response,
                         _set_config_error_from_response, **kwargs)

    def set_config_async(self, config, target_config_id, **kwargs):
        """Async version of set_config()"""
        req = estop_pb2.SetEstopConfigRequest(config=config, target_config_id=target_config_id)
        return self.call_async(self._stub.SetEstopConfig, req, _active_config_from_config_response,
                               _set_config_error_from_response, **kwargs)

    def get_status(self, **kwargs):
        """Return the estop status of the robot.

        Args:
            kwargs: Passed to underlying RPC. Example: timeout=5 to cancel the RPC after 5 seconds.
        Returns:
            estop_pb2.EstopSystemStatus from the server.
        """
        return self.call(self._stub.GetEstopSystemStatus, estop_pb2.GetEstopSystemStatusRequest(),
                         _estop_sys_status_from_response, common_header_errors, **kwargs)

    def get_status_async(self, **kwargs):
        """Async version of get_status()"""
        return self.call_async(self._stub.GetEstopSystemStatus,
                               estop_pb2.GetEstopSystemStatusRequest(),
                               _estop_sys_status_from_response, common_header_errors, **kwargs)

    def check_in(self, stop_level, endpoint, challenge, response, suppress_incorrect=False,
                 **kwargs):
        """Check in with the estop system.

        Args:
            stop_level: Integer / enum representing desired stop level. See StopLevel enum.
            endpoint: The endpoint asserting the stop level.
            challenge: A previously received challenge from the server.
            response: A response to the 'challenge' argument.
            suppress_incorrect: Set True to prevent an IncorrectChallengeResponseError from being
                raised when STATUS_INVALID is returned. Useful for the first check-in, before a
                challenge has been sent by the server.
            kwargs: Passed to underlying RPC. Example: timeout=5 to cancel the RPC after 5 seconds.
        Returns:
            A new challenge from the server.
        """
        req = self._build_check_in_request(stop_level, endpoint, challenge, response)
        err_from_resp = self._choose_check_in_err_func(suppress_incorrect=suppress_incorrect)
        return self.call(self._stub.EstopCheckIn, req, _challenge_from_check_in_response,
                         err_from_resp, **kwargs)

    def check_in_async(self, stop_level, endpoint, challenge, response, suppress_incorrect=False,
                       **kwargs):
        """Async version of check_in()"""
        req = self._build_check_in_request(stop_level, endpoint, challenge, response)
        err_from_resp = self._choose_check_in_err_func(suppress_incorrect=suppress_incorrect)
        return self.call_async(self._stub.EstopCheckIn, req, _challenge_from_check_in_response,
                               err_from_resp, **kwargs)

    @staticmethod
    def _build_check_in_request(stop_level, endpoint, challenge, response):
        if isinstance(endpoint, EstopEndpoint):
            endpoint = endpoint.to_proto()
        return estop_pb2.EstopCheckInRequest(stop_level=stop_level, endpoint=endpoint,
                                             challenge=challenge, response=response)

    @staticmethod
    def _build_register_request(target_config_id, endpoint):
        if isinstance(endpoint, EstopEndpoint):
            endpoint = endpoint.to_proto()
        req = estop_pb2.RegisterEstopEndpointRequest(target_config_id=target_config_id,
                                                     new_endpoint=endpoint)
        req.target_endpoint.role = endpoint.role
        return req

    @staticmethod
    def _build_deregister_request(target_config_id, endpoint):
        if isinstance(endpoint, EstopEndpoint):
            endpoint = endpoint.to_proto()
        req = estop_pb2.DeregisterEstopEndpointRequest(target_config_id=target_config_id,
                                                       target_endpoint=endpoint)
        return req

    @staticmethod
    def _choose_check_in_err_func(suppress_incorrect):
        if suppress_incorrect:
            return _check_in_error_from_response_no_incorrect
        else:
            return _check_in_error_from_response


class EstopEndpoint(object):
    """Endpoint in the software estop system."""

    # This is an estop role required in every configuration.
    REQUIRED_ROLE = 'PDB_rooted'

    def __init__(self, client, name, estop_timeout, role=REQUIRED_ROLE, first_checkin=True,
                 estop_cut_power_timeout=None):
        self.client = client
        self.role = role
        self.estop_timeout = estop_timeout
        self.estop_cut_power_timeout = estop_cut_power_timeout
        self._challenge = None
        self._name = name
        self._unique_id = None
        self._config_id = None
        self._lock = threading.Lock()
        self._locked_first_checkin = first_checkin

        self.logger = logging.getLogger(self._name)

    def __str__(self):
        if self.estop_cut_power_timeout is None:
            return '{} (timeout {:.3}s)'.format(self._name, self.estop_timeout)
        else:
            return '{} (timeout {:.3}s, cut_power_timeout {:.3}s)'.format(
                self._name, self.estop_timeout, self.estop_cut_power_timeout)

    def _first_checkin(self):
        with self._lock:
            return self._locked_first_checkin

    def _set_first_checkin(self, val):
        with self._lock:
            self._locked_first_checkin = val

    def _set_challenge_without_exception_from_future(self, fut):
        """Set challenge from response in future, if at all possible."""
        new_challenge = None
        try:
            # Try to get the FutureWrapper.result()
            new_challenge = fut.result()
        except EstopResponseError as exc:
            # If this failed with an EstopResponseError, we can likely still extract a challenge.
            new_challenge = _challenge_from_check_in_response(exc.response)
        except (Error) as exc:
            # Otherwise, if it was a common ResponseError or an issue with the RPC itself,
            # we likely cannot.
            self.logger.warning('Could not set challenge (error: %s)', exc.__class__.__name__)

        # If we got a new challenge, set it.
        if new_challenge is not None:
            self.set_challenge(new_challenge)

    def set_challenge(self, challenge):
        """Thread-safe write to the challenge."""
        with self._lock:
            self._challenge = challenge

    def get_challenge(self):
        """Thread-safe read of the challenge."""
        with self._lock:
            return self._challenge

    def force_simple_setup(self):
        """Replaces the existing estop configuration with a single-endpoint configuration."""
        new_config = estop_pb2.EstopConfig()
        new_config_endpoint = new_config.endpoints.add()
        new_config_endpoint.CopyFrom(self.to_proto())

        active_config = self.client.get_config()
        active_config = self.client.set_config(new_config, active_config.unique_id)
        self._unique_id = active_config.endpoints[0].unique_id
        self.register(active_config.unique_id)

    def stop(self, **kwargs):
        """Issue a CUT stop level command to the robot, cutting motor power immediately.

        Args:
            kwargs: Passed to underlying RPC. Example: timeout=5 to cancel the RPC after 5 seconds.
        Returns:
            None. Will raise an error if RPC failed.
        """
        self.logger.debug('Stopping')
        self.check_in_at_level(StopLevel.ESTOP_LEVEL_CUT, **kwargs)

    def settle_then_cut(self, **kwargs):
        """Issue a SETTLE_THEN_CUT stop level. The robot will attempt to sit before cutting motor power.

        Args:
            kwargs: Passed to underlying RPC. Example: timeout=5 to cancel the RPC after 5 seconds.
        Returns:
            None. Will raise an error if RPC failed.
        """
        self.logger.debug('Stopping with SETTLE_THEN_CUT')
        self.check_in_at_level(StopLevel.ESTOP_LEVEL_SETTLE_THEN_CUT, **kwargs)

    def allow(self, **kwargs):
        """Issue a NONE stop level command to the robot, allowing motor power.

        Args:
            kwargs: Passed to underlying RPC. Example: timeout=5 to cancel the RPC after 5 seconds.
        Returns:
            None. Will raise an error if RPC failed.
        """
        self.logger.debug('Releasing')
        self.check_in_at_level(StopLevel.ESTOP_LEVEL_NONE, **kwargs)

    def check_in_at_level(self, level, **kwargs):
        """Check in at a specified level.

        Meant for internal use, but may be helpful for higher-level wrappers.
        """
        try:
            self.set_challenge(
                self.client.check_in(level, self, self.get_challenge(), self._response(),
                                     suppress_incorrect=self._first_checkin(), **kwargs))
        except EstopResponseError as exc:
            self.set_challenge(_challenge_from_check_in_response(exc.response))
            raise
        self._set_first_checkin(False)

    def deregister(self, **kwargs):
        """Deregister this endpoint from the configuration."""
        self.logger.debug('Deregistering')
        self.client.deregister(self._config_id, self)

    def register(self, target_config_id, **kwargs):
        """Register this endpoint to the given configuration."""
        self.logger.debug('Registering to %s', target_config_id)
        new_endpoint = self.client.register(target_config_id, self)
        # If we were successful, update our config id and the rest of our data from the returned
        # endpoint protobuf.
        self._config_id = target_config_id
        self.from_proto(new_endpoint)

        self.logger.debug('Doing check-in to seed challenge...')
        self.stop()

    def stop_async(self, **kwargs):
        """Async version of stop()"""
        self.logger.debug('Stopping (async)')
        return self.check_in_at_level_async(StopLevel.ESTOP_LEVEL_CUT, **kwargs)

    def settle_then_cut_async(self, **kwargs):
        """Async version of settle_then_cut()"""
        self.logger.debug('Stopping with SETTLE_THEN_CUT (async)')
        return self.check_in_at_level_async(StopLevel.ESTOP_LEVEL_SETTLE_THEN_CUT, **kwargs)

    def allow_async(self, **kwargs):
        """Async version of allow()"""
        self.logger.debug('Releasing (async)')
        return self.check_in_at_level_async(StopLevel.ESTOP_LEVEL_NONE, **kwargs)

    def check_in_at_level_async(self, level, **kwargs):
        fut = self.client.check_in_async(level, self, self.get_challenge(), self._response(),
                                         suppress_incorrect=self._first_checkin(), **kwargs)
        fut.add_done_callback(lambda fut: self._set_challenge_without_exception_from_future(fut))
        fut.add_done_callback(lambda fut: self._set_first_checkin(False))
        return fut

    def deregister_async(self, **kwargs):
        """Async version of deregister()"""
        self.logger.debug('Deregistering (async)')
        return self.client.deregister_async(self._config_id, self)

    def from_proto(self, proto):
        """Set member variables based on given estop_pb2.EstopEndpoint."""
        if self._name != proto.name:
            self.logger.info('Changing name to %s', proto.name)
            self._name = proto.name
            self.logger = logging.getLogger(self._name)
        self.role = proto.role
        self.estop_timeout = proto.timeout.seconds + proto.timeout.nanos * 1e-9
        self._unique_id = proto.unique_id
        if proto.cut_power_timeout is None:
            self.estop_cut_power_timeout = None
        else:
            self.estop_cut_power_timeout = proto.cut_power_timeout.seconds + proto.cut_power_timeout.nanos * 1e-9

    def to_proto(self):
        """Return estop_pb2.EstopEndpoint based on current member variables."""
        t_seconds = int(self.estop_timeout)
        t_nanos = int((self.estop_timeout - t_seconds) * 1e9)
        if self.estop_cut_power_timeout is None:
            return estop_pb2.EstopEndpoint(role=self.role, name=self._name,
                                           unique_id=self._unique_id,
                                           timeout=Duration(seconds=t_seconds, nanos=t_nanos))
        else:
            cpt_seconds = int(self.estop_cut_power_timeout)
            cpt_nanos = int((self.estop_cut_power_timeout - cpt_seconds) * 1e9)
            return estop_pb2.EstopEndpoint(role=self.role, name=self._name,
                                           unique_id=self._unique_id,
                                           timeout=Duration(seconds=t_seconds, nanos=t_nanos),
                                           cut_power_timeout=Duration(seconds=cpt_seconds,
                                                                      nanos=cpt_nanos))

    def _response(self):
        """Generate a response for self._challenge."""
        challenge = self.get_challenge()
        return None if challenge is None else response_from_challenge(challenge)

    @property
    def unique_id(self):
        """Return the _unique_id. Should be used as read-only."""
        return self._unique_id


class EstopKeepAlive(object):
    """Wraps an EstopEndpoint to do periodic check-ins, keeping software estop from timing out.

    This is intended to be the common implementation of both periodic checking-in and one-time
    check-ins. See the command line utility and the "Big Red Button" application for examples.

    You should not access any of the "private" members, or the wrapped endpoint.
    """

    def __init__(self, endpoint, rpc_timeout_seconds=None, rpc_interval_seconds=None,
                 keep_running_cb=None):
        """Kicks off periodic check-in on a thread."""

        self._endpoint = endpoint
        self._lock = threading.Lock()
        self._end_check_in_signal = threading.Event()
        self._desired_stop_level = StopLevel.ESTOP_LEVEL_NONE
        # By default, only let our RPCs last as long as the estop timeout.
        self._rpc_timeout = rpc_timeout_seconds or self._endpoint.estop_timeout
        self._check_in_period = rpc_interval_seconds or self._endpoint.estop_timeout / 3.0
        if self._rpc_timeout <= 0:
            raise ValueError('Invalid rpc_timeout_seconds "{}"'.format(self._rpc_timeout))
        if self._check_in_period < 0:
            raise ValueError('Invalid rpc_interval_seconds "{}"'.format(self._check_in_period))

        self._keep_running = keep_running_cb or (lambda: True)

        self.logger.debug('New %s for endpoint "%s"', self.__class__, self._endpoint)

        self.status_queue = queue.Queue()
        self._update_status(self.KeepAliveStatus.OK)

        # Do an initial check-in, and just log any errors that occur.
        # This lets us get a challenge from the estop system, so we can begin using
        # valid challenge/response pairs.
        try:
            self._check_in()
        #pylint: disable=broad-except
        except Exception as exc:
            self.logger.warning('Estop initial check-in exception:\n{}\n'.format(exc))

        # Configure the thread to do check-ins, and begin checking in.
        self._thread = threading.Thread(target=self._periodic_check_in)
        self._thread.daemon = True
        self._thread.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def shutdown(self):
        self.logger.debug('Shutting down')
        self._end_periodic_check_in()
        self._thread.join()

    @property
    def logger(self):
        return self._endpoint.logger

    def allow(self):
        with self._lock:
            self._desired_stop_level = StopLevel.ESTOP_LEVEL_NONE
        self._check_in()

    def settle_then_cut(self):
        with self._lock:
            self._desired_stop_level = StopLevel.ESTOP_LEVEL_SETTLE_THEN_CUT
        # In the case of stopping, we want the RPC to timeout only after the estop itself has
        # timed out. This handles the case where a user calls settle_then_cut() with :
        #  - a very low self._rpc_timeout and
        #  - a very large check-in period and
        #  - doesn't handle RPC timeout errors themselves.
        self._check_in(rpc_timeout=self._endpoint.estop_timeout)

    def stop(self):
        with self._lock:
            self._desired_stop_level = StopLevel.ESTOP_LEVEL_CUT
        # In the case of stopping, we want the RPC to timeout only after the estop itself has
        # timed out. This handles the case where a user calls stop() with :
        #  - a very low self._rpc_timeout and
        #  - a very large check-in period and
        #  - doesn't handle RPC timeout errors themselves.
        self._check_in(rpc_timeout=self._endpoint.estop_timeout)

    def _end_periodic_check_in(self):
        """Stop checking into the robot estop system."""
        self.logger.debug('Stopping check-in')
        self._end_check_in_signal.set()

    def _error(self, msg, exception=None, disable=False):
        """Handle an error message; optionally disable the application.

        GUI applications should override this function, to make sure the error_msg gets to the GUI.
        """
        self._update_status(self.KeepAliveStatus.ERROR, msg)
        self.logger.error(msg)
        if disable:
            self._end_periodic_check_in()
            self._update_status(self.KeepAliveStatus.DISABLED, msg)

    def _ok(self):
        """Handle an ok message.

        GUI applications should override this function, to make sure the error_msg gets to the GUI.
        """
        self._update_status(self.KeepAliveStatus.OK)
        self.logger.debug('Check-in successful')

    def _update_status(self, status, msg=''):
        """Update the estop_keep_alive status by populating the queue. Raise exception if full."""
        self.status_queue.put((status, msg), block=False)

    def _check_in(self, rpc_timeout=None):
        """Check in, optionally specifying a non-standard RPC timeout."""
        rpc_timeout = rpc_timeout or self._rpc_timeout
        with self._lock:
            self._endpoint.check_in_at_level(self._desired_stop_level, timeout=rpc_timeout)

    def _periodic_check_in(self):
        """Send estop API CheckIn messages to robot estop system in loop."""
        # Sleep for portion of the timeout (and convert from nanoseconds to seconds)
        self.logger.info('Starting estop check-in')
        while True:
            # Include the time it takes to execute keep_running, in case it takes a significant
            # portion of our check in period.
            exec_start = time.time()
            if not self._keep_running():
                break
            try:
                self._check_in()
            except TimedOutError as exc:
                self._error('RPC took longer than {:.2f} seconds'.format(self._rpc_timeout),
                            exception=exc)
            except RpcError as exc:
                self._error('Transport exception during check-in:\n{}\n'
                            '    (resuming check-in)'.format(exc), exception=exc)
            except EndpointUnknownError as exc:
                # Disable ourself to show we cannot estop any longer.
                self._error(str(exc), exception=exc, disable=True)

            # We really do want to catch anything.
            #pylint: disable=broad-except
            except Exception as exc:
                self.logger.warning(('Generic exception during check-in:\n{}\n'
                                     '    (resuming check-in)').format(exc))
            else:
                # No errors!
                self._ok()

            # How long did the RPC and processing of said RPC take?
            exec_sec = time.time() - exec_start

            # Block and wait for the stop signal. If we receive it within the check-in period,
            # leave the loop. This check must be at the end of the loop!
            # Wait up to self._check_in_period seconds, minus the RPC processing time.
            # (values < 0 are OK and will return immediately)
            if self._end_check_in_signal.wait(self._check_in_period - exec_sec):
                break
        self.logger.info('Estop check-in stopped')

    @property
    def endpoint(self):
        """Return the _endpoint. Should be used as read-only."""
        return self._endpoint

    @property
    def client(self):
        """Return the _endpoint.client. Should be used as read-only."""
        return self._endpoint.client

    class KeepAliveStatus(enum.Enum):
        OK = 0
        ERROR = 1
        DISABLED = 2


def response_from_challenge(challenge):
    return ctypes.c_ulonglong(~challenge).value


_CHECK_IN_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_CHECK_IN_STATUS_TO_ERROR.update({
    estop_pb2.EstopCheckInResponse.STATUS_OK: (None, None),
    estop_pb2.EstopCheckInResponse.STATUS_ENDPOINT_UNKNOWN: (EndpointUnknownError,
                                                             EndpointUnknownError.__doc__),
    estop_pb2.EstopCheckInResponse.STATUS_INCORRECT_CHALLENGE_RESPONSE:
    (IncorrectChallengeResponseError, IncorrectChallengeResponseError.__doc__),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _check_in_error_from_response(response):
    """Return an exception based on response from EstopCheckIn RPC, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=estop_pb2.EstopCheckInResponse.Status.Name,
                         status_to_error=_CHECK_IN_STATUS_TO_ERROR)


def _check_in_error_from_response_no_incorrect(resp):
    """Return an exception based on response from EstopCheckIn RPC, ignoring incorrect chal/resp"""
    if resp.status == estop_pb2.EstopCheckInResponse.STATUS_INCORRECT_CHALLENGE_RESPONSE:
        return None
    return _check_in_error_from_response(resp)


_SET_CONFIG_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_SET_CONFIG_STATUS_TO_ERROR.update({
    estop_pb2.SetEstopConfigResponse.STATUS_SUCCESS: (None, None),
    estop_pb2.SetEstopConfigResponse.STATUS_INVALID_ID: (InvalidIdError, InvalidIdError.__doc__),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _set_config_error_from_response(response):
    """Return an exception based on response from SetEstopConfig RPC, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=estop_pb2.SetEstopConfigResponse.Status.Name,
                         status_to_error=_SET_CONFIG_STATUS_TO_ERROR)


_DEREGISTER_ENDPOINT_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_DEREGISTER_ENDPOINT_STATUS_TO_ERROR.update({
    estop_pb2.DeregisterEstopEndpointResponse.STATUS_SUCCESS: (None, None),
    estop_pb2.DeregisterEstopEndpointResponse.STATUS_ENDPOINT_MISMATCH:
    (EndpointMismatchError, EndpointMismatchError.__doc__),
    estop_pb2.DeregisterEstopEndpointResponse.STATUS_CONFIG_MISMATCH: (ConfigMismatchError,
                                                                       ConfigMismatchError.__doc__),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _deregister_endpoint_error_from_response(response):
    """Return an exception based on response from DeregisterEstopEndpoint RPC, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=estop_pb2.DeregisterEstopEndpointResponse.Status.Name,
                         status_to_error=_DEREGISTER_ENDPOINT_STATUS_TO_ERROR)


_REGISTER_ENDPOINT_STATUS_TO_ERROR = collections.defaultdict(lambda: (ResponseError, None))
_REGISTER_ENDPOINT_STATUS_TO_ERROR.update({
    estop_pb2.RegisterEstopEndpointResponse.STATUS_SUCCESS: (None, None),
    estop_pb2.RegisterEstopEndpointResponse.STATUS_ENDPOINT_MISMATCH:
    (EndpointMismatchError, EndpointMismatchError.__doc__),
    estop_pb2.RegisterEstopEndpointResponse.STATUS_CONFIG_MISMATCH: (ConfigMismatchError,
                                                                     ConfigMismatchError.__doc__),
    estop_pb2.RegisterEstopEndpointResponse.STATUS_INVALID_ENDPOINT: (InvalidEndpointError,
                                                                      InvalidEndpointError.__doc__),
})


@handle_common_header_errors
@handle_unset_status_error(unset='STATUS_UNKNOWN')
def _register_endpoint_error_from_response(response):
    """Return an exception based on response from RegisterEstopEndpoint RPC, None if no error."""
    return error_factory(response, response.status,
                         status_to_string=estop_pb2.RegisterEstopEndpointResponse.Status.Name,
                         status_to_error=_REGISTER_ENDPOINT_STATUS_TO_ERROR)


def _new_endpoint_from_register_response(response):
    return response.new_endpoint


def _active_config_from_config_response(response):
    return response.active_config


def _challenge_from_check_in_response(response):
    return response.challenge


def _estop_sys_status_from_response(response):
    return response.status
