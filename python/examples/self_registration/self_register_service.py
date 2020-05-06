# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Example code demonstrating how a service can be registered from a payload.

Directory access and registration requires an auth token with appropriate permissions. This
token can be retrived via the payload registration service, without need for credentials, by
using an authorized payload guid & secret combination.
"""
import argparse
import sys

import bosdyn.client
from bosdyn.client.directory import DirectoryClient, NonexistentServiceError
from bosdyn.client.directory_registration import DirectoryRegistrationClient, ServiceAlreadyExistsError
from bosdyn.client.payload_registration import PayloadRegistrationClient
import bosdyn.client.util


def self_register_service(config):
    """A simple example of using the Boston Dynamics API to self register from a payload.
    
    This function represents code that would run directly on a payload to set itself up. It
    registers a single leaf service without access to a pre-existing  app token or credentials.
    """
    # Create an sdk and robot instance.
    sdk = bosdyn.client.create_standard_sdk('SelfRegisterServiceExampleClient')
    robot = sdk.create_robot(config.hostname)

    # Since we are not using an auth token, we do not yet have access to the directory service.
    # As a result, we cannot look up the Payload Registration Service by service name. Instead,
    # we need to manually establish the channel with the authority of the Payload Registration
    # Service.
    kPayloadRegistrationAuthority = 'payload-registration.spot.robot'
    payload_registration_channel = robot.ensure_secure_channel(kPayloadRegistrationAuthority)

    # Create a payload registration client.
    payload_registration_client = robot.ensure_client(
        PayloadRegistrationClient.default_service_name, channel=payload_registration_channel)

    # Get a limited-access auth token for this payload.
    # This request will fail if the payload has not been authorized by an admin via the web UI.
    limited_token = payload_registration_client.get_payload_auth_token(config.guid, config.secret)
    robot.update_user_token(limited_token)

    # Set up a directory registration client with the limtied access token.
    # Depending on the permissions included in your limited-access payload token, it may be
    # possible to create the client using only service name.
    kDirectoryRegistrationAuthority = 'api.spot.robot'
    directory_registration_channel = robot.ensure_secure_channel(kDirectoryRegistrationAuthority)
    directory_registration_client = robot.ensure_client(
        DirectoryRegistrationClient.default_service_name, channel=directory_registration_channel)

    # Register a service with the robot.
    try:
        directory_registration_client.register(name=config.name, service_type=config.type,
                                               authority=config.authority,
                                               user_token_required=config.user_token_required,
                                               host_ip=config.host_ip, port=config.port)
    except ServiceAlreadyExistsError:
        directory_registration_client.update(name=config.name, service_type=config.type,
                                             authority=config.authority,
                                             user_token_required=config.user_token_required,
                                             host_ip=config.host_ip, port=config.port)
        print('Service already existed. Service updated.')

    # List all services. Success if above test service is shown.
    kDirectoryAuthority = 'api.spot.robot'
    directory_channel = robot.ensure_secure_channel(kDirectoryAuthority)
    directory_client = robot.ensure_client(DirectoryClient.default_service_name,
                                           channel=directory_channel)
    try:
        registered_service = directory_client.get_entry(config.name)
    except NonexistentServiceError:
        print('\nSelf-registered service not found. Failure.')
        return False

    return True


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument("--guid", required=True, type=str, help="Unique GUID of the payload")
    parser.add_argument("--secret", required=True, type=str, help="Secret of the payload")
    parser.add_argument("--name", required=True, type=str,
                        help="Unique name of the service instance")
    parser.add_argument("--type", required=True, type=str,
                        help="The rpc service type used to communicate with the service")
    parser.add_argument("--authority", required=True, type=str,
                        help="Authority to direct requests to the service")
    parser.add_argument("--user-token-required", action='store_true',
                        help="Require requests to this service to include a token")
    parser.add_argument("--host-ip", required=True, type=str,
                        help="IP address the service can be reached at")
    parser.add_argument("--port", required=True, type=int,
                        help="Port the service can be reached at")
    options = parser.parse_args()

    return self_register_service(options)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
