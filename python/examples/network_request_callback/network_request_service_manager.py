# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Base class to create a remote mission callback service which executes a worker
function on a background thread, responding to Ticks with 'running' until that
function is complete."""

import logging
import random
import string
import threading

from bosdyn.api import header_pb2
from bosdyn.api.mission import remote_pb2, remote_service_pb2_grpc
from bosdyn.client import time_sync
from bosdyn.client.server_util import GrpcServiceRunner, ResponseContext

_LOGGER = logging.getLogger(__name__)


class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


class RemoteCallbackSessionInfo:
    """Helper class to track session information for a remote callback session."""

    def __init__(self, session_id):
        self.session_id = session_id
        self.session_thread = None
        self.final_session_status = None


def run_network_request_service(thread_fn, bosdyn_sdk_robot, port, logger=None):
    """Helper to create the remote mission service using a specific worker function."""
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = remote_service_pb2_grpc.add_RemoteMissionServiceServicer_to_server
    # Instance of the servicer to be run.
    service_servicer = NetworkRequestCallbackServicer(thread_fn, bosdyn_sdk_robot, logger=logger)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


class NetworkRequestCallbackServicer(remote_service_pb2_grpc.RemoteMissionServiceServicer):

    def __init__(self, thread_fn, bosdyn_sdk_bot, logger=None):
        self.logger = logger or _LOGGER
        self.lock = threading.Lock()
        self.bosdyn_sdk_robot = bosdyn_sdk_bot
        self.thread_fn = thread_fn

        # session id mapped to RemoteCallbackSessionInfo
        self.sessions_by_id = {}

        # List of already used session ids
        self._used_session_ids = []

        # Map of the session id to the current exit status for the TickResponse.
        self.exit_status = {}

    def Tick(self, request, context):
        """Logs text, then provides a valid response."""
        response = remote_pb2.TickResponse()
        self.logger.debug('Ticked with session ID "%s" & %i inputs', request.session_id,
                          len(request.inputs))
        with ResponseContext(response, request):
            with self.lock:
                self._tick_implementation(request, response)
        return response

    def _tick_implementation(self, request, response):
        # Verify we know about the session ID.
        if request.session_id not in self.sessions_by_id:
            self.logger.error('Do not know about session ID "%s"', request.session_id)
            response.status = remote_pb2.TickResponse.STATUS_INVALID_SESSION_ID
            return
        sid = request.session_id
        # A status for the session will only be set once everything is started up.
        # Therefore, if the status is still none, that indicates it has not yet been run.
        if self.sessions_by_id[sid].final_session_status is None:
            if self.sessions_by_id[sid].session_thread is None:

                # Create a stoppable thread running the capture function.
                self.sessions_by_id[sid].session_thread = StoppableThread(
                    target=self.thread_fn, args=(sid, self.exit_status, request.inputs))
                # start the task.
                self.sessions_by_id[sid].session_thread.start()

                # Set the response status for the Tick to running.
                response.status = remote_pb2.TickResponse.STATUS_RUNNING
            elif self.sessions_by_id[sid].session_thread.is_alive():
                # Thread was created and is still running.
                response.status = remote_pb2.TickResponse.STATUS_RUNNING
            else:
                # The thread has completed. Set the response to the tick as the return value from the
                # thread which is set in the exit_status variable.
                response.status = self.exit_status[sid]
                self.sessions_by_id[sid].final_session_status = response.status
        else:
            # If we've already finished running and there is a status, just keep setting our status to what
            # our thread returned
            response.status = self.sessions_by_id[sid].final_session_status

    def EstablishSession(self, request, context):
        response = remote_pb2.EstablishSessionResponse()
        self.logger.debug('Establishing session with %i inputs', len(request.inputs))
        with ResponseContext(response, request):
            with self.lock:
                self._establish_session_implementation(request, response)
        return response

    def _get_unique_random_session_id(self):
        """Create a random 16-character session ID that hasn't been used."""
        while True:
            session_id = ''.join([random.choice(string.ascii_letters) for _ in range(16)])
            if session_id not in self._used_session_ids:
                return session_id

    def _establish_session_implementation(self, request, response):
        try:
            # We need to establish a time synchronization in order to send commands.
            self.bosdyn_sdk_robot.time_sync.wait_for_sync()
        except time_sync.TimedOutError:
            response.header.error.code = header_pb2.CommonError.CODE_INTERNAL_SERVER_ERROR
            response.header.error.message = 'Failed to time sync with robot'
            return

        session_id = self._get_unique_random_session_id()
        self.sessions_by_id[session_id] = RemoteCallbackSessionInfo(session_id)
        self._used_session_ids.append(session_id)
        response.session_id = session_id
        self.exit_status[session_id] = 0  # set the exit status to unknown
        response.status = remote_pb2.EstablishSessionResponse.STATUS_OK

    def Stop(self, request, context):
        response = remote_pb2.StopResponse()
        self.logger.debug('Stopping session "%s"', request.session_id)
        with ResponseContext(response, request):
            with self.lock:
                self._stop_implementation(request, response)
        return response

    def _stop_implementation(self, request, response):
        # Try to cancel any extant futures, then clear them from internal state.
        session_id = request.session_id
        if session_id not in self.sessions_by_id:
            response.status = remote_pb2.StopResponse.STATUS_INVALID_SESSION_ID
            return

        session = self.sessions_by_id[session_id]

        # Stop any threads that may be running
        if session.final_session_status is None:
            if session.session_thread.is_alive():
                # Otherwise, if the thread is still running, stop it, and join the thread
                session.session_thread.stop()
                session.session_thread.join()
                self.logger.debug('Successfully stopped the session thread "%s"',
                                  request.session_id)
                self.sessions_by_id[session_id].session_thread = None
            else:
                # Trivial stop because we haven't started the thread yet or it is already stopped.
                pass
        # else: if there is a final session status, then that indicates the thread is also fully complete.

        # Set the status as ok for stopping the threads and clear out the session id information.
        self.sessions_by_id[session_id] = RemoteCallbackSessionInfo(session_id)
        response.status = remote_pb2.StopResponse.STATUS_OK

    def TeardownSession(self, request, context):
        response = remote_pb2.TeardownSessionResponse()
        self.logger.debug('Tearing down session "%s"', request.session_id)
        with ResponseContext(response, request):
            with self.lock:
                self._teardown_session_implementation(request, response)
        return response

    def _teardown_session_implementation(self, request, response):
        if request.session_id in self.sessions_by_id:
            # This session has ended. Tick RPCs made with this session ID will fail.
            del self.sessions_by_id[request.session_id]
            response.status = remote_pb2.TeardownSessionResponse.STATUS_OK
        else:
            response.status = remote_pb2.TeardownSessionResponse.STATUS_INVALID_SESSION_ID

    def GetRemoteMissionServiceInfo(self, request, context):
        response = remote_pb2.GetRemoteMissionServiceInfoResponse()
        with ResponseContext(response, request):
            return response
