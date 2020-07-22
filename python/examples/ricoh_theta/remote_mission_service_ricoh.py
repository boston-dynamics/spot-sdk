# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""This is a remote mission service example with the Ricoh Theta camera. This script
 can be used to command a ricoh theta to take images, download them to the host computer,
 and upload the images to the cloud during an autowalk mission."""

from __future__ import absolute_import
from __future__ import print_function

import argparse
from concurrent import futures
import logging
import os
import sys
import time
import threading
import grpc

from bosdyn.api import header_pb2
from bosdyn.api.mission import remote_service_pb2_grpc, remote_pb2
import bosdyn.client
import bosdyn.client.util
import bosdyn.client.lease
from bosdyn.client.payload_registration import PayloadRegistrationClient 
from bosdyn.client.directory_registration import DirectoryRegistrationKeepAlive, DirectoryRegistrationClient
from bosdyn.mission import server_util, util
from bosdyn.client.exceptions import ResponseError

# Ricoh Theta Imports & Settings
from ricoh_theta import Theta
from requests.exceptions import RequestException
# An adjustment to PYTHONPATH for cloud_upload may be required.
from cloud_upload.cloud_upload import upload_to_gcp, upload_to_aws

# Adjust these variables for download/upload options.
DEFAULT_PATH = '/home/spot/Pictures/'
GCP_BUCKET_NAME = 'c-imagedemo'
AWS_BUCKET_NAME = 'aws-imagedemo'
YOUR_THETA_SSID = 'THETAYN14103427'

DIRECTORY_NAME = 'callback-default'
AUTHORITY = 'remote-mission.spot.robot'
SERVICE_TYPE = 'bosdyn.api.mission.RemoteMissionService'

class RicohThetaServicer(remote_service_pb2_grpc.RemoteMissionServiceServicer):
    """Ricoh Theta Service Example Class"""

    def __init__(self, logger, use_static_ip):
        """Constructor."""
        self.camera = None # will be a Theta() instance
        self.use_static_ip = use_static_ip
        self.lock = threading.Lock()
        self.logger = logger
        self.active_session_id = None

    def Tick(self, request, context):
        response = remote_pb2.TickResponse()
        self.logger.debug('Ticked with session ID "%s"', request.session_id)
        with server_util.ResponseContext(response, request):
            with self.lock:
                self._tick_implementation(request, response)
            return response

    # Ricoh Theta Integration Notes: _tick_implementation():
    # This is the core of the integration where the callback_text is analyzed.
    # Review the if/else statements such as "if callback_text.startswith("take theta image")".
    # Each callback_text triggers specific helper functions to execute commands
    # with error handling. See "def take_picture_helper():".
    def _tick_implementation(self, request, response):
        # This callback_text input is provided by the Autowalk missions.
        callback_text = '<unknown>'
        for keyvalue in request.inputs:
            if keyvalue.key == 'user-string':
                callback_text = util.get_value_from_constant_value_message(keyvalue.value.constant)
        self.logger.info("The callback text is {}.".format(callback_text))

        # Defining helper functions for appropriate Error handling.
        def populate_error_response(mesg):
            self.logger.exception(mesg)
            response.header.error.code = header_pb2.CommonError.CODE_INTERNAL_SERVER_ERROR
            response.header.error.message = mesg
            response.status = remote_pb2.TickResponse.STATUS_FAILURE

        def take_picture_helper():
            try:
                self.camera.takePicture()
                self.logger.info('theta took a picture')
                response.status = remote_pb2.TickResponse.STATUS_SUCCESS
            except RequestException as e:
                populate_error_response('Ricoh take picture command failed. Ensure ricoh theta is connected to spot. ' + str(e))

        def download_helper():
            try:
                self.camera.downloadMissionImages(DEFAULT_PATH)
                self.logger.info('theta downloaded mission images')
                response.status = remote_pb2.TickResponse.STATUS_SUCCESS
            except RequestException as e:
                populate_error_response('Download attempt failed. Ensure ricoh theta is connected to spot. ' + str(e))
            except Exception as e:
                populate_error_response('Download failed. Please check download/file path. ' + str(e))

        def upload_to_cloud_helper(upload_func, bucket_name):
            """Uploads all images taken during mission to cloud service.

            Args:
                upload_func (function): upload_to_aws or upload_to_gcp
                bucket_name (str): "cloud-bucket-name"
            """
            for dir_path in self.camera.download_paths:
                for image_file in os.listdir(dir_path):
                    src_filename = os.path.join(dir_path, image_file)
                    try:
                        upload_func(bucket_name, src_filename, image_file)
                        response.status = remote_pb2.TickResponse.STATUS_SUCCESS
                    except Exception as e:
                        populate_error_response('Upload to cloud failed. Please check cloud storage parameters/credentials. ' + str(e))

        # Check callback_text for applicable commands.
        if callback_text.startswith("take theta image"):
            take_picture_helper()
        elif callback_text.startswith("download theta images"):
            download_helper()
        elif callback_text.startswith("upload to gcp"):
            # download remaining images
            download_helper()
            # upload all mission images
            upload_to_cloud_helper(upload_to_gcp, GCP_BUCKET_NAME)
        elif callback_text.startswith("upload to aws"):
            # download remaining images
            download_helper()
            # upload all mission images
            upload_to_cloud_helper(upload_to_aws, AWS_BUCKET_NAME)
        else:
            self.logger.info('Callback text \'' + str(callback_text) + '\' is not a valid option.')
            response.status = remote_pb2.TickResponse.STATUS_FAILURE

    def EstablishSession(self, request, context):
        response = remote_pb2.EstablishSessionResponse()
        self.logger.debug('Establishing session with %i leases and %i inputs', len(request.leases),
                          len(request.inputs))
        with server_util.ResponseContext(response, request):
            with self.lock:
                self._establish_session_implementation(response)
            return response


    # Ricoh Theta Integration Notes: _establish_session_implementation()
    # The camera object is created at the beginning of the session. See "self.camera = Theta(...)".
    # The settings are reset if the session is restarted, review the "else:" statement.
    def _establish_session_implementation(self, response):
        # Create new instance of Theta class
        self.logger.info('---CREATING NEW SESSION---')

        # Creat object and check connection with ricoh theta vi http state request.
        try:
            if self.camera is None:
                self.camera = Theta(theta_ssid=YOUR_THETA_SSID, client_mode=self.use_static_ip)
            else:
                self.camera.showState()
                self.camera.mission_image_count = 0
                self.camera.download_paths.clear()
        except RequestException as e:
            mesg = 'Ricoh theta connection failed. Ensure ricoh theta is connected to spot. ' + str(e)
            self.logger.exception(mesg)
            response.header.error.code = header_pb2.CommonError.CODE_INTERNAL_SERVER_ERROR
            response.header.error.message = mesg
            return

        response.status = remote_pb2.EstablishSessionResponse.STATUS_OK # pylint: disable=no-member

def get_guid_and_secret():
    # Returns the GUID and secret on the Spot CORE
    kGuidAndSecretPath = '/opt/payload_credentials/payload_guid_and_secret'
    payload_file = open(kGuidAndSecretPath)
    guid = payload_file.readline().strip('\n')
    secret = payload_file.readline()
    return guid, secret

# Ricoh Theta Integration Notes: main()
# Argparse takes additional parameters to adjust ricoh integration settings. See --theta-client.
# This example also uses the limited-access user token for directory registration in order
# to avoid username, password, and app_token requirements. Review call to get_guid_and_secret().
def main():
    """Main remote mission service function"""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument('--my-host', help='Address to register into the directory with')
    parser.add_argument('--directory-host',
                        help='Host running the directory service. Omit to skip directory registration')
    parser.add_argument('--port', default=0, type=int,
                        help='Listening port for server. Omit to choose a port at random')
    parser.add_argument('--theta-client', dest='theta_client', action='store_true',
                        help='Use theta client or direct mode ip settings')
    parser.add_argument('--payload-token', dest='payload_token', action='store_true',
                        help='Use limited-access user token')
    options = parser.parse_args()

    level = logging.DEBUG if options.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(message)s (%(filename)s:%(lineno)d)')
    logger = logging.getLogger()

    sdk = bosdyn.client.create_standard_sdk('run-ricoh-service')
    guid = None
    secret = None
    if options.payload_token:
        guid, secret = get_guid_and_secret()

    server = grpc.server(futures.ThreadPoolExecutor())
    service = RicohThetaServicer(logger, options.theta_client)

    remote_service_pb2_grpc.add_RemoteMissionServiceServicer_to_server(service, server)
    port = server.add_insecure_port('[::]:{}'.format(options.port))
    server.start()
    logger.info('Starting server on port %i', port)

    dir_keepalive = None

    if options.directory_host:
        robot = sdk.create_robot(options.directory_host)
        # Check authentication method
        if guid:
            payload_registration_client = robot.ensure_client(PayloadRegistrationClient.default_service_name)
            limited_token = payload_registration_client.get_payload_auth_token(guid, secret)
            robot.update_user_token(limited_token)
        else:
            robot.authenticate(options.username, options.password)

        # Register with the directory
        dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
        dir_keepalive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=logger)
        dir_keepalive.start(DIRECTORY_NAME, SERVICE_TYPE, AUTHORITY, options.my_host, port)

    try:
        while True:
            # Nothing for this thread to do.
            time.sleep(100)
    except KeyboardInterrupt:
        logger.info('Cancelled by keyboard interrupt')

    if dir_keepalive:
        dir_keepalive.shutdown()
        dir_keepalive.unregister()

    logger.info('Stopping server.')
    # Stop with no grace period.
    shutdown_complete = server.stop(None)
    # Wait up to 1 second for a clean shutdown.
    shutdown_complete.wait(1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
