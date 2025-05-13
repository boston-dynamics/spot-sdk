# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Example of how to run a RemoteMissionService servicer."""

import logging
import random
import string
import threading
import time
import traceback

from google.protobuf.struct_pb2 import Struct

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import data_acquisition_pb2, header_pb2
from bosdyn.api.mission import remote_pb2, remote_service_pb2_grpc
from bosdyn.api.spot import spot_check_pb2
from bosdyn.client import time_sync
from bosdyn.client.data_acquisition_plugin_service import Capability, DataAcquisitionStoreClient
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.lease import Lease, LeaseClient
from bosdyn.client.power import PowerClient, power_on_motors
from bosdyn.client.server_util import GrpcServiceRunner, ResponseContext
from bosdyn.client.spot_check import SpotCheckClient, SpotCheckError
from bosdyn.client.util import setup_logging
from bosdyn.mission import util

DIRECTORY_NAME = 'spot-check-callback'
AUTHORITY = 'remote-mission'
SERVICE_TYPE = 'bosdyn.api.mission.RemoteMissionService'
CAPABILITY = Capability(name='Spot Check', description='Spot Check Results',
                        channel_name='spot_check')

_LOGGER = logging.getLogger(__name__)


class SpotCheckServicer(remote_service_pb2_grpc.RemoteMissionServiceServicer):
    """Runs Spot Check on the robot.

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

    def Tick(self, request, context):
        """Each Tick represents a point in time.  Users can implement what they would like to happen during a tick in this, case running Spot Check.  In a tick implementation, we need to handling calling our method, checking on how it is running and finishing it out"""

        response = remote_pb2.TickResponse()
        with ResponseContext(response, request):
            with self.lock:
                self._tick_implementation(request, response)

        _LOGGER.info(f"Response status in Tick(): {response.status}")
        if self.bosdyn_sdk_robot.is_powered_on():
            self.bosdyn_sdk_robot.logger.info('Robot powered on in Tick.')
        else:
            self.bosdyn_sdk_robot.logger.info('Power on not finished in Tick')

        return response

    def _tick_implementation(self, request, response):
        """Make a spot check request if none has been made; otherwise check request progress."""

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

        node_name = '<unknown>'
        # This node_name input is provided by the Autowalk missions.
        # To provide other inputs, see the RemoteGrpc message.
        for keyvalue in request.inputs:
            if keyvalue.key == 'user-string':
                node_name = util.get_value_from_constant_value_message(keyvalue.value.constant)
        self.logger.info('Ticked by node "%s"', node_name)

        spot_check_client = self.bosdyn_sdk_robot.ensure_client(
            SpotCheckClient.default_service_name)

        # The client to the robot maintains a "wallet" of leases to use for its requests.
        # Inform it about the lease provided by the client to this service.
        spot_check_client.lease_wallet.add(current_lease)

        # Because SafePowerOff can take a while, we also need to Retain the lease, to tell the
        # robot that we're still using it.
        lease_client = self.bosdyn_sdk_robot.ensure_client(LeaseClient.default_service_name)
        # We'll "fire and forget" the retain RPC -- if it doesn't succeed, the robot will
        # go through its comms loss policy.
        lease_client.retain_lease_async(current_lease)

        self._perform_spot_check(spot_check_client, request.session_id, response, current_lease,
                                 request.group_name)

    def _perform_spot_check(self, spot_check_client, session_id, response, current_lease,
                            group_name):
        """Attempts to run Spot Check on the robot and check progress

        Builds the response in-place, depending on how the spot check command is going for that Tikc

        - Args:
            - spot_check_client: the client we created to manage running Spot Check from the API
            - session_id: id of the current session of this call
            - response: the response we are sending to our remote mission service for that tick
            - current_lease: the current lease of the robot
            - group_name: group_name of the current remote mission service
     
        """

        # Grab the Future for the original command and the feedback.

        command_future, feedback_future = self.sessions_by_id[session_id]

        daq_response = {
            "autowalk_report": {
                "body": "Spot Check has failed!",
                "header": "Mission",
                "severity": 'SEVERITY_LEVEL_WARN',
            }
        }

        # Setup DAQ Store Message and Client

        action_id = data_acquisition_pb2.CaptureActionId(
            action_name=f'Spot_Check_{session_id}', group_name=group_name,
            timestamp=self.bosdyn_sdk_robot.time_sync.robot_timestamp_from_local_secs(time.time()))

        data_identifier = data_acquisition_pb2.DataIdentifier(action_id=action_id,
                                                              channel="SPOT_CHECK")

        message = data_acquisition_pb2.AssociatedMetadata()
        message.reference_id.action_id.CopyFrom(action_id)

        store_client: DataAcquisitionStoreClient = self.bosdyn_sdk_robot.ensure_client(
            DataAcquisitionStoreClient.default_service_name)

        # Attempt to run spot_check, send the original command if it has not been sent...

        if command_future is None:

            try:

                _LOGGER.info("Sending Spot Check Command...")
                # Start spot check procedure.
                req = spot_check_pb2.SpotCheckCommandRequest()
                req.command = spot_check_pb2.SpotCheckCommandRequest.COMMAND_START
                req.lease.CopyFrom(current_lease.lease_proto)

                # Try to send the command
                command_future = spot_check_client.spot_check_command(req)

            except SpotCheckError as exc:
                _LOGGER.error("Failed Spot Check")
                _LOGGER.error(exc)

            # Store the future, so we can reference it on later ticks.
            self.sessions_by_id[session_id] = (command_future, None)

        # Issue the request for feedback if no request is outstanding.

        if feedback_future is None:
            # _LOGGER.info("Feedback future is none!")
            feedback_req = spot_check_pb2.SpotCheckFeedbackRequest()
            feedback_future = spot_check_client.spot_check_feedback_async(feedback_req)
            self.sessions_by_id[session_id] = (command_future, feedback_future)

        # If the feedback request is done...
        if feedback_future.done():
            try:

                feedback_response = feedback_future.result()
                _LOGGER.info(f"Feedback_response state is.. {feedback_response.state}")

            except Exception as exc:
                self.logger.exception('Feedback failed!')
                response.error_message = str(exc)
                response.status = remote_pb2.TickResponse.STATUS_FAILURE
                # We've failed!
                # We do not reset the session information here, expecting that Stop will be
                # called.
                _LOGGER.info("Failed! Trying to power on motors...")
                self.power_motors()
                return

            # Shortname for the object that holds the feedback status codes.
            feedback_status_codes = spot_check_pb2.SpotCheckFeedbackResponse

            # Call a helper method to parse our feedback response and set our response and message accordingly
            feedback_response, feedback_status_codes, response, message, current_state = self.process_feedback(
                feedback_response, feedback_status_codes, response, message)

            if response.status == remote_pb2.TickResponse.STATUS_RUNNING:
                self.sessions_by_id[session_id] = (command_future, None)
            else:

                _LOGGER.info("Powering motors back on.")

                # Power on the robot
                self.power_motors(current_lease)

                # Save to DAQ
                try:

                    proto_struct = Struct()
                    proto_struct.update(daq_response)
                    metadata = data_acquisition_pb2.Metadata()
                    metadata.data.CopyFrom(proto_struct)

                    _LOGGER.info("Writing to DAQ")
                    _LOGGER.info(f"Metadata: {metadata}")
                    message.metadata.CopyFrom(metadata)
                    _LOGGER.info(message)
                    store_client.store_metadata(message, data_identifier)

                except Exception as e:
                    _LOGGER.error("Could not store Spot Check data to DAQ")
                    print(traceback.format_exc())
                return

            feedback_future = None
        response.status = remote_pb2.TickResponse.STATUS_RUNNING

    def process_feedback(self, feedback_response, feedback_status_codes, response, message):
        """Proccesses Spot Check Feedback and helps prepare a reponse for the DAQ and remote mission service.
        
        - Args:
            - feedback_response: the response from our request for feedback. Contains message about the current state of Spot Check
            - feedback_status_codes: How we should interpret the status code
            - response: the response we are sending to our remote mission service for that tick
            - message: the message we will later store in the DAQ
        - Returns:
            - Args
            - current_state(str): String representing the current state based on the feedback codes 
        """
        current_state = ""

        match feedback_response.state:

            case feedback_status_codes.STATE_FINISHED:
                response.status = remote_pb2.TickResponse.STATUS_SUCCESS

                # Save results to DAQ

                _LOGGER.info("Success, Getting Spot Check Results")
                camera_results = feedback_response.camera_results
                load_cell_results = feedback_response.load_cell_results
                kinematic_cal_results = feedback_response.kinematic_cal_results
                payload_result = feedback_response.payload_result
                hip_range_of_motion_results = feedback_response.hip_range_of_motion_results
                current_state = "Success!"

                results_string = f"Spot Check has passed! \n Camera results: {camera_results} \n Load cell results: {load_cell_results} \n Kinematic results: {kinematic_cal_results} \n Payload results:{payload_result} \n Hip range of motion results: {hip_range_of_motion_results} \n"

                daq_response = {
                    "autowalk_report": {
                        "header": "Mission",
                        "body": results_string,
                        "severity": 'SEVERITY_LEVEL_INFO'
                    }
                }

                message.metadata.data.update(daq_response)
            case feedback_status_codes.STATE_WAITING_FOR_COMMAND:
                response.status = remote_pb2.TickResponse.STATUS_SUCCESS
                response.error_message = f'Waiting for command "{feedback_response.state}"!'
                current_state = 'Spot is waiting for a command'
                daq_response['autowalk_report']['body'] = 'Spot is waiting for a command'
            case feedback_status_codes.STATE_UNKNOWN:
                response.status = remote_pb2.TickResponse.STATUS_FAILURE
                response.error_message = f'Unknown feedback status "{feedback_response.state}"!'
                message.metadata.data.update({'body': 'Spot check FAILED'})
                current_state = 'Unknown feedback status'
            case feedback_status_codes.STATE_USER_ABORTED:
                response.status = remote_pb2.TickResponse.STATUS_FAILURE
                response.error_message = f'User Aborted! "{feedback_response.state}"!'
                message.metadata.data.update({'body': 'Spot check FAILED'})
                current_state = 'User aborted'
            case feedback_status_codes.STATE_STARTING:
                response.status = remote_pb2.TickResponse.STATUS_RUNNING
                _LOGGER.info("Spot Check starting...")
                _LOGGER.info(f"Response status at starting: {response.status}")
                current_state = "Starting"
            case feedback_status_codes.STATE_LOADCELL_CAL:
                response.status = remote_pb2.TickResponse.STATUS_RUNNING
                current_state = "Load cell calibration underway"
            case feedback_status_codes.STATE_ENDSTOP_CAL:
                response.status = remote_pb2.TickResponse.STATUS_RUNNING
                current_state = "Endstop calibration underway"
            case feedback_status_codes.STATE_CAMERA_CHECK:
                response.status = remote_pb2.TickResponse.STATUS_RUNNING
                current_state = "Camera check underway"
            case feedback_status_codes.STATE_BODY_POSING:
                response.status = remote_pb2.TickResponse.STATUS_RUNNING
                current_state = "Body pose routine underway"
            case feedback_status_codes.STATE_REVERTING_CAL:
                response.status = remote_pb2.TickResponse.STATUS_FAILURE
                response.error_message = "Reverting calibrations"
                message.metadata.data.update({'body': 'Spot check FAILED - reverting calibrations'})
                current_state = "Reverting Calibrations"
            case feedback_status_codes.STATE_ERROR:
                response.status = remote_pb2.TickResponse.STATUS_RUNNING
                current_state = "Error occurred while running spotcheck. Inspect error for more info."
            case feedback_status_codes.STATE_SIT_DOWN_AFTER_RUN:
                response.status = remote_pb2.TickResponse.STATUS_RUNNING
                current_state = "Sitting down after run"
            case feedback_status_codes.STATE_HIP_RANGE_OF_MOTION_CHECK:
                response.status = remote_pb2.TickResponse.STATUS_RUNNING
                current_state = "Hip range of motion check underway"
            case feedback_status_codes.STATE_ARM_JOINT_CHECK:
                response.status = remote_pb2.TickResponse.STATUS_RUNNING
                current_state = 'Arm calibration underway'
            case feedback_status_codes.STATE_GRIPPER_CAL:
                response.status = remote_pb2.TickResponse.STATUS_RUNNING
                current_state = 'Arm calibration underway'
            case remote_pb2.TickResponse.STATUS_FAILURE:
                response.error_message = f'Unexpected feedback status "{feedback_response.state}"!'
                current_state = "Unexpected feedback status "

        return feedback_response, feedback_status_codes, response, message, current_state

    def _sublease_or_none(self, leases, response, error_code):
        """Helper method to check we have the correct lease on our resource"""
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

        response.header.error.code = header_pb2.CommonError.CODE_INVALID_REQUEST
        response.header.error.message = f'{len(matching_leases)} leases on resource {self.RESOURCE}'
        return None

    def power_motors(self, current_lease):
        """Power on the motors of the robot."""

        power_client = self.bosdyn_sdk_robot.ensure_client(PowerClient.default_service_name)

        try:
            self.bosdyn_sdk_robot.logger.info(
                'Powering on robot... This may take a several seconds.')
            power_client.lease_wallet.add(current_lease)
            power_on_motors(power_client, timeout_sec=30)

            # self.bosdyn_sdk_robot.power_on(timeout_sec=20)
            assert self.bosdyn_sdk_robot.is_powered_on(), 'Robot power on failed.'
            self.bosdyn_sdk_robot.logger.info('Robot powered on.')

        except Exception as e:
            self.bosdyn_sdk_robot.logger.info('Error while powering on motors')

        if self.bosdyn_sdk_robot.is_powered_on():
            self.bosdyn_sdk_robot.logger.info('Robot powered on.')
        else:
            self.bosdyn_sdk_robot.logger.info('Power on not finished')

    def EstablishSession(self, request, context):
        """Establish a session with the robot."""
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
        self.sessions_by_id[session_id] = (None, None)
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

        command_future, feedback_future = self.sessions_by_id[session_id]
        if command_future:
            pass
            # command_future.cancel()
        if feedback_future:
            feedback_future.cancel()
        # By resetting the session ID's state, the next Tick RPC will behave as if Tick had not been
        # called yet. You, as an implementer, can decide what exactly happens as part of Stop().
        # It will usually be called immediately after Tick returns a SUCCESS or FAILURE status code.
        self.sessions_by_id[session_id] = (None, None)
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


def run_service(bosdyn_sdk_robot, port, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = remote_service_pb2_grpc.add_RemoteMissionServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = SpotCheckServicer(bosdyn_sdk_robot, logger=logger)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


def main():
    # Define all arguments used by this service.
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser, required=False)

    options = parser.parse_args()
    _LOGGER.info(options)

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk('SpotCheckMissionServiceSDK')
    robot = sdk.create_robot(options.hostname)
    if options.guid and options.secret or options.payload_credentials_file:
        robot.authenticate_from_payload_credentials(
            *bosdyn.client.util.get_guid_and_secret(options))
    else:
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
