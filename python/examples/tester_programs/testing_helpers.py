# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging
import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.directory import DirectoryClient, NonexistentServiceError
from bosdyn.client.exceptions import (InvalidRequestError, ResponseError, ServiceUnavailableError,
                                      TimedOutError, UnableToConnectToRobotError)
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.server_util import strip_large_bytes_fields

# Logger for all the debug information from the tests.
_LOGGER = logging.getLogger()


def test_directory_registration(robot, service_name, expected_service_type):
    """Check that the service is registered with the robot's directory service.

    Args:
        robot (Robot): The robot to make client connections to.
        service_name (string): The name of the service being tested.
        expected_service_type(string): The service type of the service being tested.
                                       This can be found by doing Client.service_type.

    Returns:
        A boolean indicating if the service name was found as a registered service in the robot's directory.
    """
    directory_client = robot.ensure_client(DirectoryClient.default_service_name)
    try:
        # Check the directory service for the new service's name.
        directory_result = directory_client.get_entry(service_name)
        assert directory_result.name == service_name
        assert directory_result.type == expected_service_type
        return True
    except NonexistentServiceError:
        _LOGGER.error(
            "The service %s is not registered in the directory currently.\n Make sure the "
            "service code is running, and starts a DirectoryRegistrationKeepAlive.", service_name)
        return False
    except ResponseError as err:
        _LOGGER.error("Exception raised when checking the directory registration: %s", err)
        return False


def test_if_service_has_active_service_faults(robot, service_name):
    """Check if the service has any active service faults.

    Args:
        robot (Robot): The robot to make client connections to.
        service_name (string): The name of the service being tested.

    Returns:
        A boolean, such that True is returned if no service faults are found for the service name.
    """
    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    robot_state = robot_state_client.get_robot_state()
    service_faults = robot_state.service_fault_state.faults
    # Check for all service faults associated with the service name.
    faults = [fault for fault in service_faults if fault.fault_id.service_name == service_name]

    if faults:
        _LOGGER.error(
            "The service %s had the following active service faults (found in "
            "RobotState): ", service_name)
        for fault in faults:
            _LOGGER.info("Service fault: %s", fault)
        return False

    # No service faults were associated with the service name.
    return True


def test_if_service_is_reachable(service_call, *args):
    """Checks that the service being tested can be communicated to with gRPC.

    Args:
        service_call (Function): A RPC function call sent through a service client.
                                 The functions arguments can be passed through *args.
        args: Additional arguments to be passed to the service_call function.

    Returns:
        A boolean indicating if an RPC to the service can successfully
        be completed without errors.
    """
    try:
        # Try the RPC to communicate with the service.
        service_call(*args)
        return True
    except ServiceUnavailableError as err:
        _LOGGER.error(
            "The service is unreachable with a gRPC service call. Check "
            "the --host-ip argument (for running the service python file) matches the IP address of the computer "
            "running the file and that the service is still running.")
        _LOGGER.warning("The full error message is %s", err)
        return False
    except TimedOutError as err:
        _LOGGER.error(
            "The gRPC service call has timed out. Check that the "
            "service is still running and the service port is NOT blocked by any firewalls.")
        _LOGGER.warning("The full error message is %s", err)
        return False
    except UnableToConnectToRobotError as err:
        _LOGGER.error(
            "The gRPC service call is unable to connect to robot %s. Check that the service port is specified "
            "as an argument (`--port`) when running the service, and that the port is NOT blocked by an firewalls."
        )
        _LOGGER.warning("The full error message is %s", err)
        return False
    except ResponseError as err:
        _LOGGER.error("Exception raised when testing the network connection to the service: %s",
                      err)
        return False


def run_test(test_function, test_name, *args):
    """Run a given test with logging on success or failure.

    Args:
        test_function(Function): The test function.
        test_name(string): The name of the test being run.
        args: Additional arguments to be passed to the test function.
    """
    _LOGGER.info("TEST: %s" % test_name)
    if test_function(*args):
        _LOGGER.info("SUCCESS!\n")
    else:
        sys.exit(1)


def log_debug_information(response_error, request_msg=None, strip_response=False):
    """Extensive logging of an error message, and potentially the request/response RPCs.

    Args:
        response_error (Exception | ResponseError): The error to be logged. Errors of type
                                                    ResponseError will be able to log the RPC
                                                    responses and error messages as well.
        request_msg (RPC request): The protobuf RPC request to be logged.
        strip_response (boolean): If true, any bytes fields will be removed before logging the
                                  error message.
    """
    if isinstance(response_error, ResponseError):
        _LOGGER.info("Complete error message: %s %s", type(response_error),
                     response_error.error_message)
        if strip_response:
            # Make a copy of the proto message to prevent modifying the original.
            copied_message = type(response_error.response)()
            copied_message.CopyFrom(response_error.response)
            strip_large_bytes_fields(copied_message)
            _LOGGER.info("RPC response (with bytes removed) from the service: %s", copied_message)
        else:
            _LOGGER.info("RPC response from the service: %s", response_error.response)
    else:
        _LOGGER.info("Complete error message: %s %s", type(response_error), response_error)

    if request_msg is not None:
        _LOGGER.info("RPC request: %s", request_msg)
