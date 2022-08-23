# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Docking callback to automatically upload DAQ data to a destination."""

import argparse
import datetime
import glob
import logging
import os
import random
import string
import threading
import time
import zipfile

import boto3
import botocore
import google.auth
import requests
from google.cloud import storage
from google.protobuf.timestamp_pb2 import Timestamp

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import data_acquisition_pb2, data_acquisition_store_pb2
from bosdyn.api.mission import remote_pb2, remote_service_pb2_grpc
from bosdyn.client.auth import AuthResponseError
from bosdyn.client.data_acquisition_helpers import download_data_REST, make_time_query_params
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.server_util import GrpcServiceRunner, ResponseContext
from bosdyn.client.util import setup_logging
from bosdyn.mission import server_util, util

DIRECTORY_NAME = 'daq-docking-upload-callback'
AUTHORITY = 'remote-mission'
SERVICE_TYPE = 'bosdyn.api.mission.RemoteMissionService'

_LOGGER = logging.getLogger(__name__)


class Session:

    def __init__(self, thread=None, tick_status=None):
        self.thread = thread
        self.tick_status = tick_status


class DaqDockingUploadServicer(remote_service_pb2_grpc.RemoteMissionServiceServicer):
    """When run, uploads all DAQ data to an S3 bucket.
    """

    def __init__(self, bosdyn_sdk_robot, options, logger=None):
        self.logger = logger or _LOGGER
        self.bosdyn_sdk_robot = bosdyn_sdk_robot
        self.sessions_by_id = {}
        self._used_session_ids = []
        self.lock = threading.Lock()
        self.options = options
        self.destination_folder = options.destination_folder
        self.start_time = time.time()
        if self.options.destination == 'aws':
            self.check_for_config()
            self.s3_client = boto3.client('s3')
        elif self.options.destination == 'gcp':
            self.storage_client = storage.Client.from_service_account_json(options.key_filepath)
            self.bucket = self.storage_client.bucket(options.bucket_name)

    def check_for_config(self):
        key_path = os.path.join(os.path.expanduser('~'), '.aws', 'config')
        if not os.path.exists(key_path):
            if self.options.aws_access_key is not None and self.options.aws_secret_key is not None:
                with open(key_path, 'w') as config_file:
                    config_file.writelines([
                        '[default]\n', 'aws_access_key_id=' + self.options.aws_access_key + '\n',
                        'aws_secret_access_key=' + self.options.aws_secret_key
                    ])
            else:
                print('Config file does not exist. Please provide AWS keys and try again.')
                exit()

    def Tick(self, request, context):
        response = remote_pb2.TickResponse()
        self.logger.debug('Ticked with session ID "%s" %i leases and %i inputs', request.session_id,
                          len(request.leases), len(request.inputs))
        with ResponseContext(response, request):
            with self.lock:
                self._tick_implementation(request, response)
        return response

    def _tick_implementation(self, request, response):

        if request.session_id not in self.sessions_by_id:
            self.logger.error('Do not know about session ID "%s"', request.session_id)
            response.status = remote_pb2.TickResponse.STATUS_INVALID_SESSION_ID
            return

        tick_background_thread = self.sessions_by_id[request.session_id].thread
        if tick_background_thread is None:
            tick_background_thread_start = threading.Thread(target=self.callback_code,
                                                            args=(request,))
            tick_background_thread_start.start()
            self.sessions_by_id[request.session_id] = Session(
                tick_background_thread_start, remote_pb2.TickResponse.STATUS_RUNNING)
            response.status = remote_pb2.TickResponse.STATUS_RUNNING

        elif tick_background_thread.is_alive():
            response.status = remote_pb2.TickResponse.STATUS_RUNNING
        else:
            session_status = self.sessions_by_id[request.session_id].tick_status
            if (session_status == remote_pb2.TickResponse.STATUS_UNKNOWN) or (
                    session_status == remote_pb2.TickResponse.STATUS_RUNNING):
                self.logger.info('TickResponse was not updated. Default to STATUS_SUCCESS')
                response.status = remote_pb2.TickResponse.STATUS_SUCCESS
            else:
                response.status = session_status

        return response

    def callback_code(self, request):
        query_params = None
        try:
            current_time = time.time()
            query_params = make_time_query_params(self.start_time, current_time, robot)
        except ValueError as val_err:
            print("Value Exception:\n" + str(val_err))

        retry = 0
        success = False
        while not success and retry < 10:
            success = download_data_REST(query_params, options.hostname, robot.user_token,
                                         self.destination_folder)
            retry += 1

        if not success:
            self.logger.info('Unable to download mission data for {} through {}.'.format(
                self.start_time, current_time))
            return

        downloaded_zip_file = max(glob.glob(os.path.join(self.destination_folder, 'REST/*')),
                                  key=os.path.getctime)

        if self.options.unzip:
            with zipfile.ZipFile(downloaded_zip_file, 'r') as zip_file:
                zip_file.extractall(path=self.options.destination_folder)
                list_of_files = [
                    os.path.join(self.options.destination_folder, file)
                    for file in zip_file.namelist()
                ]
        else:
            list_of_files = [downloaded_zip_file]

        upload = None
        if self.options.destination == 'local':
            return
        elif self.options.destination == 'aws':
            upload = self.upload_to_aws
        else:
            upload = self.upload_to_gcp

        retry = 0
        start_time_string = datetime.datetime.fromtimestamp(
            self.start_time).strftime('%Y-%m-%d_%H:%M:%S')
        current_time_string = datetime.datetime.fromtimestamp(current_time).strftime(
            '%Y-%m-%d_%H:%M:%S')
        while len(list_of_files) != 0 and retry < 10:
            list_of_files = upload(list_of_files, start_time_string, current_time_string)
            retry += 1
        if len(list_of_files) != 0:
            self.logger.info('Unable to upload {}'.format(list_of_files))

        self.start_time = time.time()

    def upload_to_aws(self, source_files, start_time, current_time):
        """ Uploads a list of files to your S3 bucket """
        failed_files = []
        for source_file in source_files:
            try:
                destination_file = '{}_{}/{}'.format(start_time, current_time,
                                                     source_file.split('/')[-1])
                self.s3_client.upload_file(source_file, self.options.bucket_name, destination_file)
                self.logger.info('Upload of file {} as {} to {} successful'.format(
                    source_file, destination_file, self.options.bucket_name))
            except IOError:
                self.logger.info('The file {} was not found'.format(source_files))
                failed_files.append(source_file)
            except botocore.exceptions.EndpointConnectionError:
                self.logger.info(
                    'Could not connect to AWS. File is available at {}'.format(source_file))
                failed_files.append(source_file)
            except Exception as e:
                self.logger.info('Unknown exception occurred when trying to upload {}. {}'.format(
                    source_file, e))
                failed_files.append(source_file)
        return failed_files

    def upload_to_gcp(self, source_files, start_time, current_time):
        """Uploads a list of files to the bucket."""
        failed_files = []
        for source_file in source_files:
            destination = '{}_{}/{}'.format(start_time, current_time, source_file.split('/')[-1])
            blob = self.bucket.blob(destination)
            try:
                blob.upload_from_filename(source_file)
                self.logger.info('Upload of file {} as {} to {} successful'.format(
                    source_file, source_file, self.options.bucket_name))
            except IOError:
                self.logger.info('The file {} was not found'.format(source_file))
                failed_files.append(source_file)
            except (requests.exceptions.ReadTimeout, google.auth.exceptions.TransportError):
                self.logger.info(
                    'Could not connect to GCP. File is available at {}'.format(source_file))
                failed_files.append(source_file)
            except Exception as e:
                self.logger.info('Unknown exception occurred when trying to upload {}. {}'.format(
                    source_file, e))
                failed_files.append(source_file)
        return failed_files

    def _get_unique_random_session_id(self):
        """Create a random 16-character session ID that hasn't been used."""
        while True:
            session_id = ''.join([random.choice(string.ascii_letters) for _ in range(16)])
            if session_id not in self._used_session_ids:
                return session_id

    def EstablishSession(self, request, context):
        response = remote_pb2.EstablishSessionResponse()
        with ResponseContext(response, request):
            response.status = remote_pb2.EstablishSessionResponse.STATUS_OK
        session_id = self._get_unique_random_session_id()
        self.sessions_by_id[session_id] = Session()
        self._used_session_ids.append(session_id)
        response.session_id = session_id
        if self.options.time_period:
            self.start_time = (
                datetime.datetime.utcnow() -
                datetime.timedelta(minutes=self.options.time_period)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return response

    def Stop(self, request, context):
        response = remote_pb2.StopResponse()
        with ResponseContext(response, request):
            self.logger.info('Stopping session.')
            self.sessions_by_id[request.session_id] = Session()
            response.status = remote_pb2.StopResponse.STATUS_OK
        return response

    def TeardownSession(self, request, context):
        response = remote_pb2.TeardownSessionResponse()
        with ResponseContext(response, request):
            self.logger.info('Tearing down session.')
            if request.session_id in self.sessions_by_id:
                del self.sessions_by_id[request.session_id]
                response.status = remote_pb2.TeardownSessionResponse.STATUS_OK
            else:
                response.status = remote_pb2.TeardownSessionResponse.STATUS_INVALID_SESSION_ID
        return response


def run_service(bosdyn_sdk_robot, options, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = remote_service_pb2_grpc.add_RemoteMissionServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = DaqDockingUploadServicer(bosdyn_sdk_robot, options, logger=logger)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, options.port,
                             logger=logger)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    parser.add_argument('--destination', default='local', choices=['aws', 'gcp', 'local'])
    parser.add_argument('--time-period', help=('How far back to download DAQ data in minutes.'),
                        required=False, type=int)
    parser.add_argument('--bucket-name', help=('The S3 or GCP bucket to save the acquired data.'))
    parser.add_argument('--aws-access-key', help=('Required if ~/.aws/config does not exist.'),
                        default=None, type=str)
    parser.add_argument('--aws-secret-key', help=('Required if ~/.aws/config does not exist.'),
                        default=None, type=str)
    parser.add_argument('--key-filepath', help=('The filepath of your GCP key.'))
    parser.add_argument('--destination-folder', help=('The folder to save the acquired data'),
                        required=False, default='/tmp')
    parser.add_argument('--unzip', action='store_true', help='Unzip the acquired DAQ file.')

    options = parser.parse_args()

    if (options.destination == 'aws' and options.bucket_name is None):
        print('No bucket name passed for AWS. Please specify your bucket name and try again.')
        exit()

    elif (options.destination == 'gcp' and options.key_filepath is None):
        print('No key filepath passed for GCP. Please provide your key and try again.')
        exit()

    elif (options.destination == 'gcp' and options.bucket_name is None):
        print('No bucket name passed for GCP. Please specify your bucket name and try again.')
        exit()

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk("DaqUploadMissionServiceSDK")
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options, logger=_LOGGER)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, SERVICE_TYPE, AUTHORITY, options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()
