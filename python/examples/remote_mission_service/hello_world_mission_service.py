# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Example of how to run a RemoteMissionService servicer."""

import logging
import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.api.mission import remote_pb2, remote_service_pb2_grpc
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.server_util import GrpcServiceRunner, ResponseContext
from bosdyn.client.service_customization_helpers import (create_value_validator,
                                                         dict_param_coerce_to, make_dict_child_spec,
                                                         make_dict_param_spec,
                                                         make_string_param_spec,
                                                         make_user_interface_info,
                                                         validate_dict_spec)
from bosdyn.client.util import setup_logging

DIRECTORY_NAME = 'hello-world-callback'
AUTHORITY = 'remote-mission'
SERVICE_TYPE = 'bosdyn.api.mission.RemoteMissionService'

_LOGGER = logging.getLogger(__name__)
_WHO_KEY = 'who'


class HelloWorldServicer(remote_service_pb2_grpc.RemoteMissionServiceServicer):
    """Every tick, logs 'Hello world!'

    Shows an example of these concepts:
     - Ticking.
     - Using parameter dictionaries.
    """

    def __init__(self, logger=None, default_name=None, display_name=None, hello_options=None,
                 coerce=False):
        self.logger = logger or _LOGGER
        self.coerce = coerce

        # Create the custom parameters. If no hello_options are provided, allow the text to be edited.
        who_param = make_string_param_spec(options=hello_options, default_value=default_name,
                                           editable=True)
        who_ui_info = make_user_interface_info(display_name, 'Who Spot will say hello to')
        dict_spec = make_dict_param_spec({_WHO_KEY: make_dict_child_spec(who_param, who_ui_info)},
                                         is_hidden_by_default=False)

        # validate spec, error will be raised if invalid
        validate_dict_spec(dict_spec)
        self.custom_params = dict_spec

    def Tick(self, request, context):
        """Logs text, then provides a valid response."""
        response = remote_pb2.TickResponse()
        # This utility context manager will fill out some fields in the message headers.
        with ResponseContext(response, request):
            # Default to saying hello to the default.
            name = self.custom_params.specs[_WHO_KEY].spec.string_spec.default_value

            valid_param = create_value_validator(self.custom_params)(request.params)
            if valid_param is not None:
                if self.coerce:
                    dict_param_coerce_to(request.params, self.custom_params)
                else:
                    self.logger.error('Invalid parameter, not saying hello!')
                    response.status = remote_pb2.TickResponse.STATUS_CUSTOM_PARAMS_ERROR
                    response.custom_param_error.CopyFrom(valid_param)
                    return response

            who = request.params.values.get(_WHO_KEY)
            if who is not None:
                name = who.string_value.value
            self.logger.info('Hello %s!', name)
            response.status = remote_pb2.TickResponse.STATUS_SUCCESS
        return response

    def EstablishSession(self, request, context):
        response = remote_pb2.EstablishSessionResponse()
        with ResponseContext(response, request):
            self.logger.info('EstablishSession unimplemented!')
            response.status = remote_pb2.EstablishSessionResponse.STATUS_OK
        return response

    def Stop(self, request, context):
        response = remote_pb2.StopResponse()
        with ResponseContext(response, request):
            self.logger.info('Stop unimplemented!')
            response.status = remote_pb2.StopResponse.STATUS_OK
        return response

    def TeardownSession(self, request, context):
        response = remote_pb2.TeardownSessionResponse()
        with ResponseContext(response, request):
            self.logger.info('TeardownSession unimplemented!')
            response.status = remote_pb2.TeardownSessionResponse.STATUS_OK
        return response

    def GetRemoteMissionServiceInfo(self, request, context):
        response = remote_pb2.GetRemoteMissionServiceInfoResponse()
        with ResponseContext(response, request):
            response.custom_params.CopyFrom(self.custom_params)
        return response


def run_service(port, logger=None, default_name=None, display_name=None, hello_options=None,
                coerce=False):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = remote_service_pb2_grpc.add_RemoteMissionServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = HelloWorldServicer(logger=logger, default_name=default_name,
                                          display_name=display_name, hello_options=hello_options,
                                          coerce=coerce)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


def main():
    # Define all arguments used by this service.
    import argparse

    # Create the top-level parser.
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Select how this service will be accessed.',
                                       dest='host_type')

    # Create the parser for the "local" command.
    local_parser = subparsers.add_parser('local', help='Run this example locally.')
    bosdyn.client.util.add_service_hosting_arguments(local_parser)

    # Create the parser for the "robot" command.
    robot_parser = subparsers.add_parser('robot', help='Run this example with a robot in the loop.')
    bosdyn.client.util.add_base_arguments(robot_parser)
    bosdyn.client.util.add_service_endpoint_arguments(robot_parser)

    # Create the parser for UI customization
    parser.add_argument('--display-name', help='Title of field that is shown in the display.')
    parser.add_argument('--default-name', default='World',
                        help='Default option for to whom Spot will say hello')
    parser.add_argument('--hello-options', help='Options to whom Spot can say hello.',
                        action='append')
    parser.add_argument(
        '--coerce', help='If parameter does not match spec, coerce the parameter to match spec.',
        action='store_true')

    options = parser.parse_args()

    # If using the example without a robot in the loop, start up the service, which can
    # be accessed directly at localhost:options.port.
    if options.host_type == 'local':
        # Setup logging to use INFO level.
        setup_logging()
        service_runner = run_service(options.port, logger=_LOGGER,
                                     default_name=options.default_name,
                                     display_name=options.display_name,
                                     hello_options=options.hello_options, coerce=options.coerce)
        print(f'{DIRECTORY_NAME} service running.\nCtrl + C to shutdown.')
        service_runner.run_until_interrupt()
        sys.exit(f'Shutting down {DIRECTORY_NAME} service')

    # Else if a robot is available, register the service with the robot so that all clients can
    # access it through the robot directory without knowledge of the service IP or port.

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk('HelloWorldMissionServiceSDK')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(options.port, logger=_LOGGER, default_name=options.default_name,
                                 display_name=options.display_name,
                                 hello_options=options.hello_options, coerce=options.coerce)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, SERVICE_TYPE, AUTHORITY, options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()


if __name__ == '__main__':
    main()
