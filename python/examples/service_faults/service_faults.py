# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

# This script demonstrates some possible usage of ServiceFaults.
# The first set of service faults demonstrated are directory liveness faults. These faults are
# automatically raised by the directory-registration service on robot when a registered service
# fails to maintain the liveness checks it registered with. They can be cleared by re-establishing
# liveness or unregistering the service.
# The second set of service faults demonstrated are directly managed faults. These faults are
# triggered and cleared directly by using the fault-service API.

import argparse
import logging
import sys
import time

import bosdyn.client.util
from bosdyn.api import service_fault_pb2
from bosdyn.client.directory import DirectoryClient
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive,
                                                  ServiceAlreadyExistsError)
from bosdyn.client.exceptions import InvalidRequestError
from bosdyn.client.fault import FaultClient, ServiceFaultAlreadyExistsError
from bosdyn.client.robot_state import RobotStateClient

_LOGGER = logging.getLogger(__name__)

# Phony service values for a service that we do not need to be able to actually reach.
kServiceName = 'live-service-test'
kServiceType = 'void'
kServiceAuthority = 'void'
kServiceIp = '0.0.0.0'
kServicePort = 0
kTimeoutSecs = 5
kKeepAliveIntervalSecs = 2


def watch_service_fault_state(robot_state_client, watch_duration_secs=10):
    """Continually print out the service fault state."""
    end_epoch_time = int(time.time()) + watch_duration_secs
    while (int(time.time()) < end_epoch_time):
        state = robot_state_client.get_robot_state()
        print('\nCurrent ServiceFaults:\n' + str(state.service_fault_state.faults or ''))
        time.sleep(1)


def liveness_faulting(robot):
    """Force ServiceFaults to be raised indirectly via the directory registration liveness."""
    # Set up robot state client
    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)

    # Set up directory client
    directory_client = robot.ensure_client(DirectoryClient.default_service_name)

    # Set up a directory registration client.
    directory_registration_client = robot.ensure_client(
        DirectoryRegistrationClient.default_service_name)

    # Unregister the service if it already exists
    try:
        directory_registration_client.unregister(kServiceName)
        # Wait for a few seconds to give old liveness faults a chance to clear themselves.
        time.sleep(2)
    except:
        pass

    # Use keep alive helper class to maintain liveness with repeated registration/update requests.
    directory_keep_alive = DirectoryRegistrationKeepAlive(
        directory_registration_client, rpc_interval_seconds=kKeepAliveIntervalSecs)
    directory_keep_alive.start(kServiceName, kServiceType, kServiceAuthority, kServiceIp,
                               kServicePort, kTimeoutSecs)

    # Verify the service is listed
    services = directory_client.list()
    for service in services:
        if service.name == kServiceName:
            print('Service registration confirmed with liveness timeout == ' +
                  str(service.liveness_timeout_secs))

    # Continually display ServiceFaults. Should not see liveness fault from service_name
    print('\n\n\nHeartbeat thread is active. Should not see liveness fault from ' + kServiceName +
          ':')
    watch_service_fault_state(robot_state_client, 8)

    # Stop the service and display ServiceFaults. New liveness fault from service_name should appear.
    print('\n\n\nHeartbeat thread is shutting down. Expect liveness faults from ' + kServiceName +
          ':')
    directory_keep_alive.shutdown()
    watch_service_fault_state(robot_state_client, 8)

    # Start a keep alive again, which should re-establish liveness and automatically clear the liveness fault.
    # Unregistering the service will also automatically clear liveness faults.
    print('\n\n\nHeartbeat thread is starting again. Expect ' + kServiceName +
          ' liveness faults to clear')
    directory_keep_alive_2 = DirectoryRegistrationKeepAlive(
        directory_registration_client, rpc_interval_seconds=kKeepAliveIntervalSecs)
    directory_keep_alive_2.start(kServiceName, kServiceType, kServiceAuthority, kServiceIp,
                                 kServicePort, kTimeoutSecs)
    watch_service_fault_state(robot_state_client, 4)


def direct_faulting(robot):
    """Trigger and clear ServiceFaults directly using the SDK clients methods."""
    # Set up robot state client
    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)

    # Set up fault client
    fault_client = robot.ensure_client(FaultClient.default_service_name)

    # Set up fake service fault
    service_fault = service_fault_pb2.ServiceFault()
    service_fault.fault_id.fault_name = 'ManualExampleFault'
    service_fault.fault_id.service_name = kServiceName
    service_fault.error_message = 'Example service fault triggered by the service_faults.py SDK example.'
    service_fault.severity = service_fault_pb2.ServiceFault.SEVERITY_WARN

    # Trigger the service fault
    try:
        fault_client.trigger_service_fault(service_fault)
    except ServiceFaultAlreadyExistsError:
        print('\nServiceFault was already registered. Proceeding...')

    # Continually display ServiceFaults. Should see the manually triggered fault.
    print('\n\n\nShould see locally triggered fault')
    watch_service_fault_state(robot_state_client, 4)

    # Clear the service fault
    fault_client.clear_service_fault(service_fault.fault_id)

    # Continually display ServiceFaults. Should not see the manually triggered fault.
    print('\n\n\nShould not see locally triggered fault.')
    watch_service_fault_state(robot_state_client, 4)


def main(argv):
    """Demonstrate usage of service faults."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser, required=False)
    config = parser.parse_args(argv)

    bosdyn.client.util.setup_logging(config.verbose)

    # Create an sdk and robot instance.
    sdk = bosdyn.client.create_standard_sdk('ServiceFaultsExampleClient')
    robot = sdk.create_robot(config.hostname)

    # We want to register the fake service with a payload, so that future fault reporting can
    # display associated payload info. The GUID provided will be associated with the service
    # and all future service faults.
    if (config.guid and config.secret) or config.payload_credentials_file:
        robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(config))
    else:
        bosdyn.client.util.authenticate(robot)

    # Demonstrate directory liveness service faults
    liveness_faulting(robot)

    # Demonstrate direct service faults
    direct_faulting(robot)


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
