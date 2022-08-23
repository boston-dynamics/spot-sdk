# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import copy
import logging
from threading import Event, Lock

from bosdyn.api.graph_nav import area_callback_pb2
from bosdyn.api.graph_nav.area_callback_pb2 import (BeginCallbackRequest, BeginCallbackResponse,
                                                    UpdateCallbackRequest, UpdateCallbackResponse)
from bosdyn.client.area_callback_service_utils import AreaCallbackServiceConfig
from bosdyn.client.common import LeaseUseError
from bosdyn.client.robot import Robot

_LOGGER = logging.getLogger(__name__)


class IncorrectUsage(Exception):
    """Error raised by calling a helper function incorrectly.

    Raised when a call would block forever has otherwise been used in an incorrect manner.
    This exception is not intended to be caught, but indicates a programming error.
    """


class HandlerError(Exception):
    """Error base class for errors raised from the internals of the AreaCallbackRegionHandlerBase.

    This error will be raised when the shutdown_event signal is set, or can be raised by the user
    to signal an error. A wrapper around the run implementation will catch this exception and
    report back to a client a UpdateCallbackResponse error.
    """


class CallbackEnded(HandlerError):
    """The callback has already been stopped, via an EndCallback call."""


class CallbackTimedOutError(HandlerError):
    """The callback has already been stopped, via passing the end time. If caught, it should be
    re-raised to make sure the response is set correctly."""


class AreaCallbackRegionHandlerBase:
    """Base class for implementing a AreaCallbackRegionHandler.

    A AreaCallbackRegionHandler is an object responsible for running a single instance of an
    AreaCallback.  The AreaCallbackServiceServicer will construct an AreaCallbackRegionHandler
    object each time GraphNav starts an Area Callback region. The servicer will execute the run()
    function in a thread and read update_response to send status back to the client.
    After EndCallback, this object will be discarded and a new AreaCallbackRegionHandlerBase will
    be constructed to handle the next region.

    Args:
        config: The AreaCallbackServiceConfig defining the data for the AreaCallbackInformation
            response.
        robot: The Robot object used to create service clients.

    """

    def __init__(self, config: AreaCallbackServiceConfig, robot: Robot):
        self._lock = Lock()
        # Set up a response with the default policy
        self._update_response = UpdateCallbackResponse()
        self._update_response.policy.at_start = UpdateCallbackResponse.NavPolicy.OPTION_STOP
        self._update_response.policy.at_end = UpdateCallbackResponse.NavPolicy.OPTION_CONTINUE
        self._shutdown_event = Event()
        self._lease_event = Event()
        self._end_time = None
        self.robot = robot
        self._config = config
        self._stage = UpdateCallbackRequest.STAGE_TO_START
        self._begin_complete = False

    def begin(self, request: BeginCallbackRequest) -> BeginCallbackResponse.Status:
        """Validates that configuration passed to BeginCallback is valid.

        Args:
            request (area_callback_pb2.BeginCallbackRequest): The BeginCallback request.

        Returns:
            area_callback_pb2.BeginCallbackResponse.Status: OK when configuration_data is valid.
        """
        raise NotImplementedError("Derived class must implement this function.")

    def run(self):
        """This function is run on a worker thread after BeginCallback is called."""
        raise NotImplementedError("Derived class must implement this function.")

    def end(self):
        """This function is called after run thread has finished and client calls EndCallback."""
        raise NotImplementedError("Derived class must implement this function.")

    @property
    def area_callback_information(self) -> area_callback_pb2.AreaCallbackInformation:
        """Get area_callback_pb2.AreaCallbackInformation."""
        return self._config.area_callback_information()

    @property
    def config(self) -> AreaCallbackServiceConfig:
        """Get AreaCallbackServiceConfig"""
        return self._config

    # Policy functions, which change the policy that the callback is returning to the robot.

    def stop_at_start(self):
        """Tell graph nav that it should wait at the start of the region."""
        with self._lock:
            self._update_response.policy.at_start = UpdateCallbackResponse.NavPolicy.OPTION_STOP
            if self.stage == UpdateCallbackRequest.STAGE_AT_START:
                self._lease_event.clear()

    def continue_past_start(self):
        """Tell graph nav that it should continue on past the start of the region."""
        with self._lock:
            self._update_response.policy.at_start = UpdateCallbackResponse.NavPolicy.OPTION_CONTINUE
            if self.stage == UpdateCallbackRequest.STAGE_AT_START:
                self._lease_event.clear()

    def control_at_start(self):
        """Tell graph nav that it transfer control at the start of the region."""
        with self._lock:
            self._update_response.policy.at_start = UpdateCallbackResponse.NavPolicy.OPTION_CONTROL

    def stop_at_end(self):
        """Tell graph nav that it should wait at the end of the region."""
        with self._lock:
            self._update_response.policy.at_end = UpdateCallbackResponse.NavPolicy.OPTION_STOP
            if self.stage == UpdateCallbackRequest.STAGE_AT_END:
                self._lease_event.clear()

    def continue_past_end(self):
        """Tell graph nav that it should continue on past the ends of the region."""
        with self._lock:
            self._update_response.policy.at_end = UpdateCallbackResponse.NavPolicy.OPTION_CONTINUE
            if self.stage == UpdateCallbackRequest.STAGE_AT_END:
                self._lease_event.clear()

    def control_at_end(self):
        """Tell graph nav that it should transfer control at the end of the region."""
        with self._lock:
            self._update_response.policy.at_end = UpdateCallbackResponse.NavPolicy.OPTION_CONTROL

    def set_complete(self):
        with self._lock:
            self._update_response.complete.SetInParent()

    # Blocking functions to check for a particular event.

    def block_until_control(self):
        """Block waiting for the robot to pass the sublease to this callback.

        Raises:
            HandlerError: When a shutdown is requested before a lease is received.
        """
        if not self._begin_complete:
            raise IncorrectUsage('block_until_control should only be called from within run()')
        if not self.will_get_control():
            raise IncorrectUsage(
                'block_until_control should only be called if the callback will be given control. '
                'The current stage is {} and the policy is {}'.format(self.stage,
                                                                      self.update_response.policy))
        while not self._lease_event.wait(0.1):
            self.check()

    def has_control(self):
        """Check in a non-blocking way if the callback has been given a sublease.

        Returns:
            True if the callback is now in control of the robot.
        """
        return self._lease_event.is_set()

    def block_until_arrived_at_start(self) -> bool:
        """Block until the robot arrives at the start of the area callback.
        If the robot is already past the start, this will return immediately.

        Returns:
            True if the robot is at the start, False if the robot is already beyond the start.

        Raises:
            HandlerError: When a shutdown is requested before the robot reaches the start of the
            region.
        """
        if not self._begin_complete:
            raise IncorrectUsage(
                'block_until_arrived_at_start should only be called from within run()')
        while self._stage < UpdateCallbackRequest.STAGE_AT_START:
            self.safe_sleep(0.1)
        return self._stage == UpdateCallbackRequest.STAGE_AT_START

    def block_until_arrived_at_end(self):
        """Block until the robot arrives at the end of the area callback.

        Raises:
            HandlerError: When a shutdown is requested before the robot reaches the end of the
            region.
        """
        if not self._begin_complete:
            raise IncorrectUsage(
                'block_until_arrived_at_end should only be called from within run()')
        while self._stage < UpdateCallbackRequest.STAGE_AT_END:
            self.safe_sleep(0.1)

    @property
    def stage(self):
        """Check the current stage of traversal in a non-blocking way.

        Returns:
            bosdyn.api.UpdateCallbackRequest.Stage enum of the current stage of crossing the region.
        """
        return self._stage

    def safe_sleep(self, sleep_time_secs: float):
        """Run impl should use this sleep function to make sure thread does not hang.

        Args:
            sleep_time_secs (float): Time to sleep, in seconds.

        Raises:
            HandlerError: When a shutdown is requested during the sleep time..
        """
        if self.robot.time_sec() > self._end_time:
            raise CallbackTimedOutError()
        if self._shutdown_event.wait(sleep_time_secs):
            raise CallbackEnded()
        if self.robot.time_sec() > self._end_time:
            raise CallbackTimedOutError()

    def check(self):
        """Check if callback shutdown has been requested via client call to EndCallback or passing
        the end time.

        The run thread is responsible for checking and cleanly exiting.

        Raises:
            HandlerError: If the thread should shut down.
        """
        if self.robot.time_sec() > self._end_time:
            raise CallbackTimedOutError()
        if self._shutdown_event.is_set():
            raise CallbackEnded()

    @property
    def update_response(self):
        """Get current UpdateCallbackResponse."""
        with self._lock:
            return copy.deepcopy(self._update_response)

    def will_get_control(self):
        """Determine if the current policy and stage mean that the callback will eventually be
        given control without any further action on its part"""

        response = self.update_response
        # Check if the policy wants control at the start, and we haven't passed the start.
        want_control_at_start = (response.policy.at_start
                                 == UpdateCallbackResponse.NavPolicy.OPTION_CONTROL and
                                 self.stage <= UpdateCallbackRequest.Stage.STAGE_AT_START)
        # Check if the policy wants control at the end,
        # and we've either passed the start or we're set to continue past it.
        want_control_at_end = (
            response.policy.at_end == UpdateCallbackResponse.NavPolicy.OPTION_CONTROL and
            (self.stage > UpdateCallbackRequest.Stage.STAGE_AT_START or
             response.policy.at_start == UpdateCallbackResponse.NavPolicy.OPTION_CONTINUE))
        return want_control_at_start or want_control_at_end

    # All following functions will be called by the AreaCallbackServiceServicer,
    # and should not be called by subclasses.

    def internal_begin_complete(self):
        """The handler finished BeginCallback and is ready to start run().
        Blocking calls may now be used."""
        self._begin_complete = True

    def internal_set_stage(self, stage: UpdateCallbackRequest.Stage):
        """Update the stage via an incoming UpdateCallbackRequest."""
        if stage != self._stage:
            _LOGGER.info('Stage changed from %s to %s',
                         UpdateCallbackRequest.Stage.Name(self._stage),
                         UpdateCallbackRequest.Stage.Name(stage))
        self._stage = stage

    def internal_set_end_time(self, end_time: float):
        """Update the end time from an incoming request."""
        self._end_time = end_time

    def internal_give_control(self):
        """Set Event indicating region handler has been given control. Lease is available in wallet.
        """
        self._lease_event.set()

    def internal_run_wrapper(self, shutdown_event):
        """Wrapper around the run function which catches exceptions and set update response.

        Args:
            shutdown_event (Event): Event that signals the run thread to shutdown.
        """
        self._shutdown_event = shutdown_event
        _LOGGER.info('Beginning callback')
        try:
            self.run()
            with self._lock:
                if not self._update_response.HasField("error"):
                    self._update_response.complete.SetInParent()
        except LeaseUseError as lease_use_error:
            _LOGGER.warning('Something else has taken control, aborting.')
            error = UpdateCallbackResponse.Error()
            error.error = UpdateCallbackResponse.Error.ERROR_LEASE
            if hasattr(lease_use_error.response, "lease_use_result"):
                error.lease_use_results.add().CopyFrom(lease_use_error.response.lease_use_result)
            elif hasattr(lease_use_error.response, "lease_use_results"):
                error.lease_use_results.extend(lease_use_error.response.lease_use_results)
            with self._lock:
                self._update_response.error.CopyFrom(error)
        except CallbackTimedOutError:
            # The callback already passed the end time, which is an error.
            _LOGGER.warning(
                'The callback did not receive an UpdateCallback for too long, aborting.')
            with self._lock:
                self._update_response.error.error = UpdateCallbackResponse.Error.ERROR_TIMED_OUT
        except CallbackEnded:
            # This was raised to cause run() to stop due to EndCallback. This is not an error.
            self.set_complete()
        except IncorrectUsage:
            raise
        # We want to keep running and just report an error regardless of what run() raises.
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception('Failed during run()')
            with self._lock:
                self._update_response.error.error = UpdateCallbackResponse.Error.ERROR_CALLBACK_FAILED
        _LOGGER.info('Callback ended')
