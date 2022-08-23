# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Example code demonstrating how a service can be registered from a payload.

Directory access and registration requires an auth token with appropriate permissions. This
token can be retrieved via the payload registration service, without need for credentials, by
using an authorized payload guid & secret combination.
"""
import argparse
import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.directory import DirectoryClient, NonexistentServiceError
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive,
                                                  ServiceAlreadyExistsError)

DIRECTORY_NAME = 'announce-service'
AUTHORITY = 'announce-service'
SERVICE_TYPE = 'AnnounceService'  # AnnounceService protos should be available locally.


def self_register_service(config):
    """An example of using the Boston Dynamics API to self register a service using payload auth.

    This function represents code that would run directly on a payload to set itself up. It
    registers a single leaf service without access to a pre-existing credentials.
    """
    # Create an sdk and robot instance.
    sdk = bosdyn.client.create_standard_sdk('SelfRegisterServiceExampleClient')
    robot = sdk.create_robot(config.hostname)

    # Authenticate by using the credentials of a registered & authorized payload.
    robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(config))

    # Create the directory registration client after getting the user token.
    directory_registration_client = robot.ensure_client(
        DirectoryRegistrationClient.default_service_name)

    # Create a keep_alive to reset and maintain registration of service.
    keep_alive = DirectoryRegistrationKeepAlive(directory_registration_client)
    keep_alive.start(DIRECTORY_NAME, SERVICE_TYPE, AUTHORITY, config.host_ip, config.port)

    # List all services. Success if above test service is shown.
    directory_client = robot.ensure_client(DirectoryClient.default_service_name)
    try:
        registered_service = directory_client.get_entry(DIRECTORY_NAME)
    except NonexistentServiceError:
        print('\nSelf-registered service not found. Failure.')
        return False

    print('\nService registration confirmed. Self-registration was a success.')
    return True


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    options = parser.parse_args()

    return self_register_service(options)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
