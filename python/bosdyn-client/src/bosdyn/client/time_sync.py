# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A client for the time-sync service.

The time-sync service helps track the difference between the robot's system clock and the
system clock of clients, and sends an estimate of this difference to the client.  The client
uses this information when it needs to send a timestamp to the robot in a request proto.
Timestamps in request protos generally need to be specified relative to the robot's system clock.
"""

import time

from threading import Event, Lock, Thread

from bosdyn.api import time_sync_pb2
from bosdyn.api import time_sync_service_pb2_grpc

from bosdyn.util import RobotTimeConverter
from bosdyn.util import now_nsec
from bosdyn.util import set_timestamp_from_nsec
from bosdyn.util import timestamp_to_nsec

from .common import BaseClient
from .common import common_header_errors
from .exceptions import Error


class TimeSyncError(Error):
    """General class of errors for TimeSync non-response / non-grpc errors."""


class NotEstablishedError(TimeSyncError):
    """Client has not established time-sync with the robot."""


class TimedOutError(TimeSyncError):
    """Exceeded deadline to achieve time-sync."""


class InactiveThreadError(TimeSyncError):
    """Time-sync thread is no longer running."""


class TimeSyncClient(BaseClient):
    """A client for establishing time-sync with a server/robot."""
    default_service_name = 'time-sync'
    service_type = 'bosdyn.api.TimeSyncService'

    def __init__(self):
        super(TimeSyncClient, self).__init__(time_sync_service_pb2_grpc.TimeSyncServiceStub)

    def get_time_sync_update(self, previous_round_trip, clock_identifier, **kwargs):
        """Obtain an initial or updated timesync estimate with server.

        Args:
            previous_round_trip (bosdyn.api.TimeSyncRoundTrip): None on first rpc call, then
                                                                fill out with previous response
                                                                from server.
            clock_identifier (string): Empty on first call, assigned by server in first response.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_time_sync_update_request(previous_round_trip, clock_identifier)
        return self.call(self._stub.TimeSyncUpdate, req, None, common_header_errors, **kwargs)

    def get_time_sync_update_async(self, previous_round_trip, clock_identifier, **kwargs):
        """Async version of get_time_sync_update()"""
        req = self._get_time_sync_update_request(previous_round_trip, clock_identifier)
        return self.call_async(self._stub.TimeSyncUpdate, req, None, common_header_errors, **kwargs)


    @staticmethod
    def _get_time_sync_update_request(previous_round_trip, clock_identifier):
        return time_sync_pb2.TimeSyncUpdateRequest(previous_round_trip=previous_round_trip,
                                                   clock_identifier=clock_identifier)


def _get_time_sync_status_value(response):
    return response.time_sync_status_map


class TimeSyncEndpoint(object):
    """A wrapper that uses a TimeSyncClient object to establish and maintain timesync with a robot.

    This class manages internal state, including a clock identifier and previous best time sync
    estimates. This class automatically builds requests passed to the TimeSyncClient, so users
    don't have to worry about the details of establishing and maintaining timesync.

    This object is thread-safe.
    """

    def __init__(self, time_sync_client):
        self._client = time_sync_client
        self._lock = Lock()
        # Access these using the lock.
        # These should be updated by replacement, not mutation so that they may be used
        #  outside the lock after being accessed via the lock.
        self._locked_previous_round_trip = None
        self._locked_previous_response = None
        self._locked_clock_identifier = ""

    @property
    def response(self):
        """The last response message from the time-sync service.

        Returns:
          The bosdyn.api.TimeSyncResponse proto last returned by the server, or None if unset.
        """
        with self._lock:
            return self._locked_previous_response

    @property
    def has_established_time_sync(self):
        """Checks if the client has successfully established time-sync with the robot.

        Returns:
            Boolean true if the previous time-sync update returned that time sync is OK.
        """
        response = self.response
        return response and response.state.status == time_sync_pb2.TimeSyncState.STATUS_OK

    @property
    def round_trip_time(self):
        """"The previous round trip time.

        Returns:
          Round trip time as google.protobuf.Duration proto if available, otherwise None.
        """
        response = self.response
        if response is None:
            return None
        return response.state.best_estimate.round_trip_time

    @property
    def clock_identifier(self):
        """The clock identifier for the instance of the time-sync client.

        Returns:
          A unique identifier for this client. Empty if get_new_estimate has not been called.
        """
        with self._lock:
            return self._locked_clock_identifier

    @property
    def clock_skew(self):
        """The best current estimate of clock skew from the time-sync service.

        Returns:
            The google.protobuf.Duration representing the clock skew.

        Raises:
            NotEstablishedError: Time sync has not yet been established.
        """
        response = self.response
        if not response or response.state.status != time_sync_pb2.TimeSyncState.STATUS_OK:
            raise NotEstablishedError
        return response.state.best_estimate.clock_skew

    def establish_timesync(self, max_samples=25, break_on_success=False):
        """Perform time-synchronization until time sync established.

        Args:
            max_samples (int): The maximum number of times to attempt to establish time-sync
                               through time-synchronization.
            break_on_success (bool): If true, stop performing the time-synchronization after
                                     time-sync is established.

        Return:
            Boolean true if valid timesync has been established.
        """
        counter = 0
        while counter < max_samples:
            if break_on_success and self.has_established_time_sync:
                return True
            self.get_new_estimate()
            counter += 1
        return self.has_established_time_sync

    def _get_update(self):
        round_trip = None
        clock_identifier = None
        with self._lock:
            # Only add a round trip to the request along with a clock identifier, otherwise
            #  the sever will respond with an invalid request error.
            # Responses with errors may not contain a clock identifier.
            # This may happen, for example, if the service was not yet ready at the time of
            #  the request.
            if self._locked_clock_identifier:
                round_trip = self._locked_previous_round_trip
                clock_identifier = self._locked_clock_identifier
        return self._client.get_time_sync_update(previous_round_trip=round_trip,
                                                 clock_identifier=clock_identifier)

    def get_new_estimate(self):
        """Perform an update-cycle toward achieving time-synchronization.

        Return:
            Boolean true if valid timesync has been established.
        """
        response = self._get_update()
        rx_time = now_nsec()

        # Record the timing information for this GRPC call to pass to the next update
        round_trip = time_sync_pb2.TimeSyncRoundTrip()
        round_trip.client_tx.CopyFrom(response.header.request_header.request_timestamp)
        round_trip.server_rx.CopyFrom(response.header.request_received_timestamp)
        round_trip.server_tx.CopyFrom(response.header.response_timestamp)
        set_timestamp_from_nsec(round_trip.client_rx, rx_time)

        with self._lock:
            self._locked_previous_round_trip = round_trip
            # Store the response to get clock-skew estimate, etc.
            self._locked_previous_response = response
            self._locked_clock_identifier = response.clock_identifier

        return self.has_established_time_sync

    def get_robot_time_converter(self):
        """Get a RobotTimeConverter for current estimate for robot clock skew from local time.

        Returns:
          An instance of RobotTimeConvertor for the time-sync client.

        Raises:
          NotEstablishedError: If time sync has not yet been established.
        """
        return RobotTimeConverter(timestamp_to_nsec(self.clock_skew))

    def robot_timestamp_from_local_secs(self, local_time_secs):
        """Convert a local time in seconds to a timestamp proto in robot time.

        Args:
            local_time_secs (float): Timestamp in seconds since the unix epoch (e.g.,
                                     from time.time()).

        Returns:
            google.protobuf.Timestamp representing local_time_secs in robot clock, or None if
                local_time_secs is None.

        Raises:
            NotEstablishedError:  Time sync has not yet been established.
        """
        if not local_time_secs:
            return None
        converter = self.get_robot_time_converter()
        return converter.robot_timestamp_from_local_secs(local_time_secs)


class TimeSyncThread(object):
    """Background thread for achieving and maintaining time-sync to the robot."""

    # After achieving time sync, update estimate every minute.
    DEFAULT_TIME_SYNC_INTERVAL_SEC = 60

    # When time-sync service is not yet ready, poll it at this interval
    TIME_SYNC_SERVICE_NOT_READY_INTERVAL_SEC = 5

    def __init__(self, time_sync_client):
        self._time_sync_endpoint = TimeSyncEndpoint(time_sync_client)
        self._lock = Lock()
        self._locked_time_sync_interval_sec = self.DEFAULT_TIME_SYNC_INTERVAL_SEC
        self._locked_should_exit = False  # Used to tell the thread to stop running.
        self._locked_thread_exception = None  # Stores any exception which ends the thread.
        self._event = Event()  # Used to wait for next time sync, or until thread should exit.
        self._thread = None

    def __del__(self):
        # Stop the thread when this object is deleted.
        self.stop()

    def start(self):
        """Start the thread."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._locked_should_exit = False
            self._locked_thread_exception = None
            self._event.clear()
            self._thread = Thread(target=self._timesync_thread)
            self._thread.daemon = True
        self._thread.start()

    def stop(self):
        """Shut down the thread if it is running."""
        if self._thread:
            with self._lock:
                self._locked_should_exit = True  # Signal the thread to exit.
            self._event.set()  # Stop the thread's wait for the next time-sync update.
            self._thread.join()  # Join the thread after it exits.
            self._thread = None

    @property
    def time_sync_interval_sec(self):
        """Returns interval at which time-sync is updated in the thread."""
        with self._lock:
            return self._locked_time_sync_interval_sec

    @time_sync_interval_sec.setter
    def time_sync_interval_sec(self, val):
        """Set interval at which time-sync is updated in the thread after sync is established.

        Args:
            val (float): The interval (in seconds) that the time-sync estimate should be updated.
        """
        with self._lock:
            self._locked_time_sync_interval_sec = val
            self._event.set()

    @property
    def should_exit(self):
        """Returns True if thread should stop iterating."""
        with self._lock:
            return self._locked_should_exit

    def wait_for_sync(self, timeout_sec=3.0):
        """Wait for up to the given timeout for time-sync to be achieved

        Args:
          timeout_sec (float): Maximum time (seconds) to wait for time-sync to be achieved.

        Raises:
          InactiveThreadError:  Thread is not running.
          time_sync.TimedOutError:  Deadline to achieve time-sync is exceeded.
          Threading Exceptions: Errors from threading the processes.
        """
        if self.has_established_time_sync:
            return
        end_time_sec = time.time() + timeout_sec
        while not self.stopped:
            if self.endpoint.has_established_time_sync:
                return
            if time.time() > end_time_sec:
                raise TimedOutError
            time.sleep(0.1)
        thread_exc = self.thread_exception
        if thread_exc:
            raise thread_exc
        raise InactiveThreadError

    @property
    def has_established_time_sync(self):
        """Checks if the client has successfully established time-sync with the robot.

        Returns:
            Boolean true if the previous time-sync update returned that time sync is OK.
        """
        return self.endpoint.has_established_time_sync

    @property
    def stopped(self):
        """Returns True if thread is no longer running."""
        with self._lock:
            return not self._thread or not self._thread.is_alive()

    @property
    def thread_exception(self):
        """Return any exception which ended the time-sync thread."""
        with self._lock:
            return self._locked_thread_exception

    @property
    def endpoint(self):
        """Return the TimeSyncEndpoint used by this thread."""
        return self._time_sync_endpoint

    def get_robot_clock_skew(self, timesync_timeout_sec=0):
        """Get current estimate for robot clock skew from local time.

        Args:
          timesync_timeout_sec (float):  Time to wait for timesync before doing conversion.

        Returns:
          Clock skew as a google.protobuf.Duration object

        Raises:
          InactiveThreadError: Time-sync thread exits before time-sync.
          time_sync.TimedOutError: Deadline to achieve time-sync is exceeded.
          Threading Exceptions: Errors from threading the processes.
        """
        self.wait_for_sync(timeout_sec=timesync_timeout_sec)
        return self.endpoint.clock_skew

    def get_robot_time_converter(self, timesync_timeout_sec=0):
        """Get a RobotTimeConverter for current estimate for robot clock skew from local time.

        Args:
            timesync_timeout_sec (float):  Time to wait for timesync before doing conversion.

        Raises:
          InactiveThreadError: Time-sync thread exits before time-sync.
          time_sync.TimedOutError: Deadline to achieve time-sync is exceeded.
          Threading Exceptions: Errors from threading the processes.
        """
        self.wait_for_sync(timeout_sec=timesync_timeout_sec)
        return self.endpoint.get_robot_time_converter()

    def robot_timestamp_from_local_secs(self, local_time_secs, timesync_timeout_sec=0):
        """Convert a local time in seconds to a timestamp proto in robot time.

        Args:
            local_time_secs (float): Timestamp in seconds since the unix epoch (e.g.,
                from time.time()).
            timesync_timeout_sec (float): Time to wait for timesync before doing conversion.

        Returns:
            google.protobuf.Timestamp representing local_time_secs in robot clock, or None if
            local_time_secs is None.

        Raises:
            InactiveThreadError: Time-sync thread exits before time-sync.
            time_sync.TimedOutError: Deadline to achieve time-sync is exceeded.
            Threading Exceptions: Errors from threading the processes.
        """
        if not local_time_secs:
            return None
        converter = self.get_robot_time_converter(timesync_timeout_sec)
        return converter.robot_timestamp_from_local_secs(local_time_secs)

    def _timesync_thread(self):
        """Background thread which communicates with the time-sync service on robot.

        The purpose of this thread is to achieve and maintain time-sync, which is an estimate
        of the difference between the robot's and client's system clocks.
        """
        try:
            while not self.should_exit:
                response = self._time_sync_endpoint.response
                if (not response or response.state.status ==
                        time_sync_pb2.TimeSyncState.STATUS_MORE_SAMPLES_NEEDED):
                    # No wait between updates while time-sync is not established.
                    pass
                elif response.state.status == time_sync_pb2.TimeSyncState.STATUS_SERVICE_NOT_READY:
                    # Wait a few seconds between updates while waiting for time-sync service
                    #  to be ready.
                    self._event.wait(self.TIME_SYNC_SERVICE_NOT_READY_INTERVAL_SEC)
                else:
                    # When sync has been established, use default wait time.
                    self._event.wait(self.time_sync_interval_sec)

                # Do RPC call to update time-sync information.
                if not self.should_exit:
                    self._time_sync_endpoint.get_new_estimate()

        # For now, on GRPC error, store the error object and exit the thread.
        except Error as err:
            with self._lock:
                self._locked_thread_exception = err
