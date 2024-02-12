# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Network requests can be used to trigger external devices such as doors or elevators, query a machine status, or
interact with payloads along with many other possibilities. This remote mission service provides a callback that
 queries a network endpoint and then checks if the response contains a particular String.

The callback expects the following user parameters. These should be added manually after starting the service.

"Url" <String> - The address which receives the network request
"MustContain" <String> - The string which the response must contain for the action to succeed

"""

import logging
import sys
import time

import network_request_service_manager
import requests

import bosdyn.client
import bosdyn.client.util
from bosdyn.api.mission import remote_pb2
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.util import setup_logging
from bosdyn.mission import util

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.INFO)

SERVICE_TYPE = 'bosdyn.api.mission.RemoteMissionService'

NETWORK_REQUEST_SERVICE_PORT = 55015  # Change to desired port
NETWORK_REQUEST_SERVICE_NAME = 'network-request-service'
NETWORK_REQUEST_SERVICE_AUTH = 'remote-mission'

PARAM_NAME_URL = 'Url'
PARAM_NAME_MUSTCONTAIN = 'MustContain'

logging.basicConfig()


class NetworkRequestServiceTool:

    def __init__(self, robot):
        self.robot = robot

    # Reading response content can also be useful depending on the data types
    # def read_content(self, url):
    #     r = requests.get(url).content
    #     return r

    def read_text(self, url):
        r = requests.get(url).text
        return r

    def http_request(self, session_id, exit_status, inputs):
        _LOGGER.debug('http_request:')
        exit_status[session_id] = remote_pb2.TickResponse.STATUS_UNKNOWN
        for keyvalue in inputs:
            if keyvalue.key == PARAM_NAME_URL:
                param_url = util.get_value_from_constant_value_message(keyvalue.value.constant)
            if keyvalue.key == PARAM_NAME_MUSTCONTAIN:
                param_must_contain = util.get_value_from_constant_value_message(
                    keyvalue.value.constant)

        _LOGGER.debug('Making request to URL %s \r\n Checking for content')
        network_response = self.read_text(param_url)

        if (param_must_contain in network_response):
            exit_status[session_id] = remote_pb2.TickResponse.STATUS_SUCCESS
        else:
            exit_status[session_id] = remote_pb2.TickResponse.STATUS_FAILURE

        _LOGGER.debug('Checking if response: %s contains %s', network_response, param_must_contain)
        return exit_status[session_id]


def main():
    # Define all arguments used by this service.
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    bosdyn.client.util.add_service_hosting_arguments(parser)
    options = parser.parse_args()

    # Setup logging to use either INFO level or DEBUG level to see status.
    setup_logging()

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk('NetworkRequestServiceSDK')
    robot = sdk.create_robot(options.hostname)
    robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(options))
    network_request_tool = NetworkRequestServiceTool(robot)

    # Create a service runner for remote mission callbacks to control the shared state
    service_active = False
    while service_active is False:
        try:
            network_request_service = network_request_service_manager.run_network_request_service(
                network_request_tool.http_request, robot, NETWORK_REQUEST_SERVICE_PORT,
                logger=_LOGGER)
            service_active = True
            time.sleep(1)
        except Exception as e:
            _LOGGER.fatal('An error occurred: %s', e)
            service_active = False

    # Use a keep alive to register the service with the robot directory
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive_service = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)

    # Start the keep alives. If any of them fail, exit the program and let docker restart the entire container
    try:
        keep_alive_service.start(NETWORK_REQUEST_SERVICE_NAME, SERVICE_TYPE,
                                 NETWORK_REQUEST_SERVICE_AUTH,
                                 bosdyn.client.common.get_self_ip(options.hostname),
                                 network_request_service.port)
    except Exception as e:
        _LOGGER.info('A keep_alive error occurred: %s', e)
        sys.exit(1)

    # Attach the keep alive to the service runner and run until a SIGINT is received.

    with keep_alive_service:
        network_request_service.run_until_interrupt()


if __name__ == '__main__':
    main()
