# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Example of how to run a RemoteMissionService servicer.

You can use this file, paired with a servicer, to run your own remote mission service.
For example servicer implementations, see "example_servicers.py".
"""

from __future__ import absolute_import
from __future__ import print_function

import argparse
from concurrent import futures
import logging
import signal
import sys
import threading
import time
import traceback

import grpc

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.directory_registration import DirectoryRegistrationKeepAlive, DirectoryRegistrationClient
from bosdyn.api.mission import remote_service_pb2_grpc

from example_servicers import HelloWorldServicer, PowerOffServicer

# This is the name of the service as it will appear in the directory.
# It defaults to 'callback-default', which is what Autowalk missions will look for by default.
SERVICE_NAME_IN_DIRECTORY = 'callback-default'
AUTHORITY = 'remote-mission.spot.robot'
SERVICE_TYPE = 'bosdyn.api.mission.RemoteMissionService'

_STOP_RUNNING = threading.Event()


def main(server):
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument('--my-host', help='Address to register into the directory with')
    parser.add_argument(
        '--directory-host',
        help='Host running the directory service. Omit to skip directory registration')
    parser.add_argument('--port', default=0, type=int,
                        help='Listening port for server. Omit to choose a port at random')
    parser.add_argument('--servicer', default='HelloWorld', help='Type of servicer to launch.')
    options = parser.parse_args()

    sdk = bosdyn.client.create_standard_sdk('run-mission-service')
    sdk.load_app_token(options.app_token)

    level = logging.DEBUG if options.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(message)s (%(filename)s:%(lineno)d)')
    logger = logging.getLogger()

    # Map options.servicer to a function that will build the appropriate instance.
    string_to_servicer = {
        'HelloWorld':
        lambda: HelloWorldServicer(logger),
        'PowerOff':
        lambda: PowerOffServicer(logger, sdk, options.hostname, options.username, options.password)
    }

    # Build whatever service the user specified.
    servicer = string_to_servicer[options.servicer]()

    # Start the server, talking over an insecure channel.
    remote_service_pb2_grpc.add_RemoteMissionServiceServicer_to_server(servicer, server)
    port = server.add_insecure_port('[::]:{}'.format(options.port))
    server.start()
    logger.info('Starting server on port %i', port)

    dir_keepalive = None

    # If a directory host was specified, register with the directory there.
    # This will often be the robot. For example, if this program is running on a payload computer
    # like the Spot CORE, directory_host would be 192.168.50.3.
    # Registering with the directory will be important when running with a robot, but it's useful
    # to skip directory registration when you're just testing your service locally.
    if options.directory_host:
        # Register with the directory.
        robot = sdk.create_robot(options.directory_host)
        robot.authenticate(options.username, options.password)
        dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)

        dir_keepalive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=logger)
        dir_keepalive.start(SERVICE_NAME_IN_DIRECTORY, SERVICE_TYPE, AUTHORITY, options.my_host,
                            port)

    try:
        # Nothing for this thread to do. The server / servicer pair handles all incoming
        # requests.
        while not _STOP_RUNNING.wait(1):
            pass
    except KeyboardInterrupt:
        logger.info('Cancelled by keyboard interrupt')

    if dir_keepalive:
        dir_keepalive.shutdown()
        dir_keepalive.unregister()

    logger.info('Stopping server.')
    return 0


def stop_running(sig, frame):
    global _STOP_RUNNING
    _STOP_RUNNING.set()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, stop_running)
    # Build a server with the default number of thread executors.
    server = grpc.server(futures.ThreadPoolExecutor())
    try:
        return_code = main(server)
    except Exception:
        print('Uncaught exception!')
        traceback.print_exc()
        return_code = 1

    # Stop with no grace period.
    shutdown_complete = server.stop(None)
    # Wait up to 1 second for a clean shutdown.
    shutdown_complete.wait(1)
    sys.exit(return_code)
