# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Code for attaching and detaching a payload via the payload service API
"""
import argparse
import logging
import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.payload import PayloadClient
from bosdyn.client.payload_registration import PayloadRegistrationClient

LOGGER = logging.getLogger()


def payload_attach_detach(config):
    """A simple example of using the Boston Dynamics API to attach and detach payloads on Spot.

    A payload may only be modified in this way if it is authorized. See the readme for more information.

    First, this example uses a payload registration client to attach or detach the payload. Then,
    this example uses a payload client to list all of the payloads currently on the robot.
    """
    sdk = bosdyn.client.create_standard_sdk('SpotPayloadAttachDetachClient')

    robot = sdk.create_robot(config.hostname)

    # Get a payload registration client
    payload_registration_client = robot.ensure_client(
        PayloadRegistrationClient.default_service_name)

    #We should have a payload credentials file already created by this part of the example
    guid, secret = bosdyn.client.util.read_payload_credentials(config.payload_credentials_file)

    if (config.detach):
        # Call the helper function to detach a payload from the robot
        payload_registration_client.detach_payload(guid, secret)
    elif (config.attach):
        # Call the helper function to attach a payload to the robot
        payload_registration_client.attach_payload(guid, secret)

    # Get a token using the guid & secret of the payload
    token = payload_registration_client.get_payload_auth_token(guid, secret)

    # Authenticate the robot before being able to get a payload client
    robot.authenticate_with_token(token)

    # Get a payload client
    payload_client = robot.ensure_client(PayloadClient.default_service_name)

    # List all payloads using the payload client
    payloads = payload_client.list_payloads()
    print('\n\n Payload Listing  \n' + '-' * 40)
    print(payloads)


def main():
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_file_argument(parser)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--attach', help='Attach the payload.', action='store_true')
    group.add_argument('--detach', help='Detach the payload.', action='store_true')
    options = parser.parse_args()

    payload_attach_detach(options)

    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
