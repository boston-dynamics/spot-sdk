# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Example of how to run a RemoteMissionService servicer."""

import logging
import math
import random
import string
import threading
import time

import bosdyn.client
import bosdyn.client.util
import bosdyn.geometry
from bosdyn.api import header_pb2, units_pb2
from bosdyn.api.mission import remote_pb2, remote_service_pb2_grpc
from bosdyn.client import time_sync
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.lease import Lease, LeaseClient
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client.server_util import GrpcServiceRunner, ResponseContext
from bosdyn.client.service_customization_helpers import (create_value_validator,
                                                         dict_param_coerce_to, make_dict_child_spec,
                                                         make_dict_param_spec,
                                                         make_double_param_spec,
                                                         make_string_param_spec,
                                                         make_user_interface_info,
                                                         validate_dict_spec)
from bosdyn.client.util import setup_logging
from bosdyn.mission import util

DIRECTORY_NAME = 'robot-command-callback'
AUTHORITY = 'remote-mission'
SERVICE_TYPE = 'bosdyn.api.mission.RemoteMissionService'

_LOGGER = logging.getLogger(__name__)

_COMMAND_KEY = 'command'
_COMMAND_OPTIONS = ['wiggle', 'wave']

_DURATION_KEY = 'duration'
_DURATION_MIN = 1  # s
_DURATION_MAX = 20  # s
_DURATION_DEFAULT = 5  # s

_WAVE_HEIGHT_MAX = 0.3  # m
_WAVE_HEIGHT_CONSTANT = 7.5  # Affects the period of the height oscillation
_WAVE_ROLL_OFFSET_MAX = 0.275  # rad
_WAVE_ROLL_CONSTANT = 3.75  # Affects the period of the roll oscillation
_WAVE_PITCH_OFFSET_MAX = 0.375  # rad
_WAVE_PITCH_CONSTANT = 7.5  # Affects the period of the pitch oscillation

_WIGGLE_YAW_OFFSET_MAX = 0.05  # rad
_WIGGLE_YAW_CONSTANT = 8  # Affects the period of the yaw oscillation
_WIGGLE_PITCH_OFFSET_MAX = 0.45  # rad
_WIGGLE_PITCH_OFFSET_MIN = -.1  # rad
_WIGGLE_PITCH_CONSTANT = 25  # Affects the period of the pitch oscillation

_FUNCTION_TIME_CHANGE = 0.05  # Movement function time change for every new command
_COMMAND_TIME_INTERVAL_MIN = 0.05  # s


def interp(x, y1, y2):
    """
            Interpolate a value between y1 and y2 based on the position of x between -1 and
            1.
            If x is outside [-1, 1], saturate the output correctly to y1 or y2.
            """
    if (x <= -1):
        return y1
    elif (x >= 1):
        return y2

    # Range of x is [-1, 1], so dx is 2.
    slope = (y2 - y1) / 2.0
    return slope * (x + 1) + y1


class RobotCommandMissionServicer(remote_service_pb2_grpc.RemoteMissionServiceServicer):
    """Powers off the robot.

    Shows an example of these concepts:
     - Ticking.
     - Using a lease to control the robot.
     - Using inputs.
     - Maintaining state for multiple sessions.

     Args:
        logger (logging.Logger): logging.Logger instance.
    """

    RESOURCE = 'body'

    def __init__(self, bosdyn_sdk_robot, logger=None):
        self.lock = threading.Lock()
        self.logger = logger or _LOGGER
        self.bosdyn_sdk_robot = bosdyn_sdk_robot
        self.sessions_by_id = {}
        self._used_session_ids = []

        # Create the custom parameters.
        command_param = make_string_param_spec(options=_COMMAND_OPTIONS,
                                               default_value=_COMMAND_OPTIONS[0], editable=False)
        command_ui_info = make_user_interface_info('Performance Type',
                                                   'What movement spot will do for the duration.')
        duration_param = make_double_param_spec(max_value=_DURATION_MAX, min_value=_DURATION_MIN,
                                                units=units_pb2.Units(name='seconds'),
                                                default_value=_DURATION_DEFAULT)
        duration_ui_info = make_user_interface_info('Wave Duration',
                                                    'How long Spot will perform the wave.')
        dict_spec = make_dict_param_spec(
            {
                _COMMAND_KEY: make_dict_child_spec(command_param, command_ui_info),
                _DURATION_KEY: make_dict_child_spec(duration_param, duration_ui_info)
            }, is_hidden_by_default=False)
        # Validate spec, error will be raised if invalid
        validate_dict_spec(dict_spec)
        self.custom_params = dict_spec

    def Tick(self, request, context):
        response = remote_pb2.TickResponse()
        self.logger.debug('Ticked with session ID "%s" %i leases and %i inputs', request.session_id,
                          len(request.leases), len(request.inputs))
        with ResponseContext(response, request):
            with self.lock:
                self._tick_implementation(request, response)
        return response

    def _tick_implementation(self, request, response):
        """Make a power off request if none has been made; otherwise check request progress."""

        # Verify we know about the session ID.
        if request.session_id not in self.sessions_by_id:
            self.logger.error('Do not know about session ID "%s"', request.session_id)
            response.status = remote_pb2.TickResponse.STATUS_INVALID_SESSION_ID
            return

        # Make a sublease of the provided lease, or fill out the response with an error.
        current_lease = self._sublease_or_none(request.leases, response,
                                               remote_pb2.TickResponse.STATUS_MISSING_LEASES)
        if current_lease is None:
            return

        # Default to spec command and duration.
        command = self.custom_params.specs[_COMMAND_KEY].spec.string_spec.default_value
        duration = self.custom_params.specs[_DURATION_KEY].spec.double_spec.default_value.value

        valid_param = create_value_validator(self.custom_params)(request.params)
        if valid_param is not None:
            if self.coerce:
                dict_param_coerce_to(request.params, self.custom_params)
            else:
                self.logger.error('Invalid parameter, not saying hello!')
                response.status = remote_pb2.TickResponse.STATUS_CUSTOM_PARAMS_ERROR
                response.custom_param_error.CopyFrom(valid_param)
                return response

        param_command = request.params.values.get(_COMMAND_KEY)
        if param_command is not None:
            command = param_command.string_value.value
        param_duration = request.params.values.get(_DURATION_KEY)
        if param_duration is not None:
            duration = param_duration.double_value.value

        node_name = '<unknown>'
        # This node_name input is provided by the Autowalk missions.
        # To provide other inputs, see the RemoteGrpc message.
        for keyvalue in request.inputs:
            if keyvalue.key == 'user-string':
                node_name = util.get_value_from_constant_value_message(keyvalue.value.constant)
        self.logger.info('Ticked by node "%s"', node_name)

        cmd_client = self.bosdyn_sdk_robot.ensure_client(RobotCommandClient.default_service_name)

        # The client to the robot maintains a "wallet" of leases to use for its requests.
        # Inform it about the lease provided by the client to this service.
        cmd_client.lease_wallet.add(current_lease)

        # We also need to Retain the lease, to tell the
        # robot that we're still using it.
        lease_client = self.bosdyn_sdk_robot.ensure_client(LeaseClient.default_service_name)
        # We'll "fire and forget" the retain RPC -- if it doesn't succeed, the robot will
        # go through its comms loss policy.
        lease_client.retain_lease_async(current_lease)

        self._perform_robot_movement(cmd_client, command, duration, request.session_id, response)

    def _perform_robot_movement(self, cmd_client, command, duration, session_id, response):
        """Attempts to power off the robot and check on power off progress.

        Builds the response in-place, depending on how the power off command is going.
        """

        # Grab the Future for the original command and the feedback.
        command_future, start_wave_time, last_cmd_time, wave_time_value = self.sessions_by_id[
            session_id]

        # Default to normal stand values
        height = yaw = roll = pitch = 0.0
        if start_wave_time is not None:
            if time.time() - start_wave_time > duration:
                # Build and issue normal stand command
                footprint_R_body = bosdyn.geometry.EulerZXY(yaw=yaw, roll=roll, pitch=pitch)
                cmd = RobotCommandBuilder.synchro_stand_command(footprint_R_body=footprint_R_body)
                command_future = cmd_client.robot_command(cmd)
                self.logger.info('Performance complete!')
                response.status = remote_pb2.TickResponse.STATUS_SUCCESS
                return

        # Check last command sent to make sure it succeeded
        if command_future is not None:
            # If the command is done...
            if command_future.done():
                # See what the result was. On a successful RPC, the result is the ID of the command.
                # If the command failed, an exception will be raised. We do not monitor feedback afterward since we will override this command shortly anyway.
                try:
                    command_future.result()
                except bosdyn.client.LeaseUseError as exc:
                    self.logger.error('LeaseUseError: "%s"', str(exc))
                    # We often treat LeaseUseErrors as a recoverable thing, so you may want to do the
                    # same. A newer lease may come in with the next TickRequest.
                    # It could be that the lease received for this tick is already newer than the lease
                    # that was used in the command_future being checked right now. In that case, the
                    # mission service will typically just try again. You have the option of doing your
                    # own "try again" logic in this servicer, but it's not typically necessary.
                    response.status = remote_pb2.TickResponse.STATUS_RUNNING
                    response.lease_use_results.add().CopyFrom(exc.response.lease_use_result)
                    # Reset the information for this session, so the next tick will make another call.
                    self.sessions_by_id[session_id] = (None, start_wave_time, last_cmd_time,
                                                       wave_time_value)
                    return
                except bosdyn.client.Error as exc:
                    self.logger.error('Command failed: "%s"', str(exc))
                    response.error_message = str(exc)
                    response.status = remote_pb2.TickResponse.STATUS_FAILURE
                    # We've failed!
                    # We do not reset the session information here, expecting that Stop will be called.
                    return
        # Wait until its time to send command
        if last_cmd_time is not None and time.time() - last_cmd_time > _COMMAND_TIME_INTERVAL_MIN:
            if command == 'wave':
                # Calculate desired robot stand position
                height = interp(math.cos(wave_time_value * _WAVE_HEIGHT_CONSTANT),
                                -_WAVE_HEIGHT_MAX, _WAVE_HEIGHT_MAX)
                pitch = interp(math.sin(wave_time_value * _WAVE_PITCH_CONSTANT),
                               -_WAVE_PITCH_OFFSET_MAX, _WAVE_PITCH_OFFSET_MAX)
                roll = interp(math.cos(wave_time_value * _WAVE_ROLL_CONSTANT),
                              -_WAVE_ROLL_OFFSET_MAX, _WAVE_ROLL_OFFSET_MAX)
            elif command == 'wiggle':
                # Calculate desired robot stand position
                pitch = interp(math.sin(wave_time_value * _WIGGLE_PITCH_CONSTANT),
                               _WIGGLE_PITCH_OFFSET_MIN, _WIGGLE_PITCH_OFFSET_MAX)
                yaw = interp(math.cos(wave_time_value * _WIGGLE_YAW_CONSTANT),
                             -_WIGGLE_YAW_OFFSET_MAX, _WIGGLE_YAW_OFFSET_MAX)

            # Build and issue the command
            footprint_R_body = bosdyn.geometry.EulerZXY(yaw=yaw, roll=roll, pitch=pitch)
            cmd = RobotCommandBuilder.synchro_stand_command(footprint_R_body=footprint_R_body,
                                                            body_height=height)
            command_future = cmd_client.robot_command_async(cmd)

            # Set start time if we haven't already
            if start_wave_time is None:
                start_wave_time = time.time()

            # Set last sent command time
            last_cmd_time = time.time()
            # Increase wave function time for next command
            wave_time_value += _FUNCTION_TIME_CHANGE
            # Update session info
            self.sessions_by_id[session_id] = (command_future, start_wave_time, last_cmd_time,
                                               wave_time_value)
            response.status = remote_pb2.TickResponse.STATUS_RUNNING
            return
        self.sessions_by_id[session_id] = (None, start_wave_time, last_cmd_time, wave_time_value)
        response.status = remote_pb2.TickResponse.STATUS_RUNNING

    def _sublease_or_none(self, leases, response, error_code):
        # Look for the lease that we want.
        matching_leases = [lease for lease in leases if lease.resource == self.RESOURCE]

        # There should be exactly one match.
        if len(matching_leases) == 1:
            provided_lease = Lease(matching_leases[0])
            return provided_lease.create_sublease()
        # If there are NO leases, that's definitely an error.
        if not matching_leases:
            response.status = error_code
            response.missing_lease_resources.append(self.RESOURCE)
            return None

        # Provided more than one lease for the resource!
        response.header.error.code = header_pb2.CommonError.CODE_INVALID_REQUEST
        response.header.error.message = f'{len(matching_leases)} leases on resource {self.RESOURCE}'
        return None

    def EstablishSession(self, request, context):
        response = remote_pb2.EstablishSessionResponse()
        self.logger.debug('Establishing session with %i leases and %i inputs', len(request.leases),
                          len(request.inputs))
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
        # Get a new session ID.
        current_lease = self._sublease_or_none(
            request.leases, response, remote_pb2.EstablishSessionResponse.STATUS_MISSING_LEASES)
        if current_lease is None:
            return

        try:
            # We need to establish a time synchronization in order to send commands.
            self.bosdyn_sdk_robot.time_sync.wait_for_sync()
        except time_sync.TimedOutError:
            response.header.error.code = header_pb2.CommonError.CODE_INTERNAL_SERVER_ERROR
            response.header.error.message = 'Failed to time sync with robot'
            return

        session_id = self._get_unique_random_session_id()
        # Note: If you plan to run this servicer for a long time, you may want to bound the size of
        # sessions_by_id and _used_session_ids.
        self.sessions_by_id[session_id] = (None, None, 0, 0)
        self._used_session_ids.append(session_id)
        response.session_id = session_id

        # If you're using leases, you can also be sure that the client has indicated the
        # correct lease resources in their EstablishSessionRequest. For now, assume no leases
        # are needed, and return an OK status.
        response.status = remote_pb2.EstablishSessionResponse.STATUS_OK

    def Stop(self, request, context):
        # Called when the client has decided it doesn't need to continue checking on this
        # service. For example, if this service is running as part of a Mission, some other part
        # of the Mission may have been activated.
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

        command_future, start_movement_time, last_cmd_time, movement_time_value = self.sessions_by_id[
            session_id]
        if command_future:
            command_future.cancel()
        # By resetting the session ID's state, the next Tick RPC will behave as if Tick had not been
        # called yet. You, as an implementer, can decide what exactly happens as part of Stop().
        # It will usually be called immediately after Tick returns a SUCCESS or FAILURE status code.
        self.sessions_by_id[session_id] = (None, None, None, None)
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
            response.custom_params.CopyFrom(self.custom_params)
        return response


def run_service(bosdyn_sdk_robot, port, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = remote_service_pb2_grpc.add_RemoteMissionServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = RobotCommandMissionServicer(bosdyn_sdk_robot, logger=logger)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


def main():
    # Define all arguments used by this service.
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    options = parser.parse_args()

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk('PowerOffMissionServiceSDK')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options.port, logger=_LOGGER)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, SERVICE_TYPE, AUTHORITY, options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()


if __name__ == '__main__':
    main()
