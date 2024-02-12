# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Data Acquisition plugin with params
"""
import logging

import bosdyn.client.util
from bosdyn.api import data_acquisition_pb2, data_acquisition_plugin_service_pb2_grpc
from bosdyn.client.data_acquisition_plugin_service import Capability, DataAcquisitionPluginService
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.server_util import GrpcServiceRunner
from bosdyn.client.util import setup_logging

_LOGGER = logging.getLogger(__name__)

DIRECTORY_NAME = 'data-acquisition-custom-params-plugin'
AUTHORITY = 'data-acquisition-custom-params-plugin'
CHANNEL_NAME = 'data'

TOGGLE_PARAM_NAME = "Toggle Option"
TOGGLE_PARAM_OPTIONS = ["option 1", "option 2"]

# Constants related to timeout on recording.
NUMBER_NAME = "Random number"
NUMBER_MIN = 0.0
NUMBER_MAX = 100.0

STRING_PARAMS_NAME = 'Favorite Phrase'
STRING_DEFAULT = 'Hi spot!'


class HelloAdapter:
    """Basic plugin for saving data to DAQ"""

    # Parse through the request's data
    def handle_request(self, request, store_helper):
        for capture in request.acquisition_requests.data_captures:
            if capture.name == 'data':
                self.handle_data(capture, store_helper, request.action_id)

    def handle_data(self, capture, store_helper, action_id):
        # Pull the custom parameters from the data capture
        params = capture.custom_params.values
        toggle = params.get(TOGGLE_PARAM_NAME).string_value.value
        num = params.get(NUMBER_NAME).double_value.value
        phrase = params.get(STRING_PARAMS_NAME).string_value.value

        # Check if the request has been cancelled.
        store_helper.cancel_check()

        data_id = data_acquisition_pb2.DataIdentifier(action_id=action_id, channel=CHANNEL_NAME)
        message = data_acquisition_pb2.AssociatedMetadata()
        message.reference_id.action_id.CopyFrom(action_id)
        message.metadata.data.update({
            "Option": toggle,
            "Random number": num,
            "Phrase": phrase,
        })
        # Store the data and manage store state.
        store_helper.store_metadata(message, data_id)
        store_helper.state.set_status(data_acquisition_pb2.GetStatusResponse.STATUS_SAVING)


def make_service(robot):
    capability = Capability(name='data', description='Loading Data', channel_name=CHANNEL_NAME)

    # Custom parameters on UI
    custom_params = capability.custom_params

    # Toggle Params (when two options) Drop down menu when 3 or more options
    toggle_params = custom_params.specs[TOGGLE_PARAM_NAME].spec.string_spec
    toggle_params.default_value = TOGGLE_PARAM_OPTIONS[0]
    toggle_params.editable = False
    toggle_params.options.extend(TOGGLE_PARAM_OPTIONS)

    # Number Slider
    number_params = custom_params.specs[NUMBER_NAME].spec.double_spec
    number_params.default_value.value = NUMBER_MIN
    number_params.min_value.value = NUMBER_MIN
    number_params.max_value.value = NUMBER_MAX

    # User input string
    string_params = custom_params.specs[STRING_PARAMS_NAME].spec.string_spec
    string_params.default_value = STRING_DEFAULT
    string_params.editable = True

    adapter = HelloAdapter()
    return DataAcquisitionPluginService(robot, [capability], adapter.handle_request)


def run_service(bosdyn_sdk_robot, port, hostname, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = data_acquisition_plugin_service_pb2_grpc.add_DataAcquisitionPluginServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = make_service(bosdyn_sdk_robot)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


if __name__ == '__main__':
    # Define all arguments used by this service.
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    options = parser.parse_args()

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk("DAQCustomParamsPlugin")
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options.port, options.hostname)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, DataAcquisitionPluginService.service_type, AUTHORITY,
                     options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()
