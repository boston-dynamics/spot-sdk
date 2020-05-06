# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
This file defines a basic announce client.

The announce client can be used to communicate with an announce service running on a connected
system through the robot.
"""
import argparse
import sys

import bosdyn.client.util
from bosdyn.client.common import BaseClient
from bosdyn.client.payload_registration import PayloadRegistrationClient

import announce_pb2 as announce_protos
import announce_service_pb2_grpc as announce_service_protos_grpc


class AnnounceClient(BaseClient):
    """Client to announce strings."""

    def __init__(self):
        super(AnnounceClient, self).__init__(announce_service_protos_grpc.AnnounceServiceStub)

    def make_announcement(self, message, **kwargs):
        """Announce a message."""
        req = announce_protos.AnnounceRequest(message=message)
        return self.call(self._stub.Announce, req,
                         value_from_response=lambda response: response.message, **kwargs)


def run_announce_client(config):
    sdk = bosdyn.client.create_standard_sdk('AnnounceClient')

    sdk.register_service_client(AnnounceClient, service_name=config.service_name,
                                service_type=config.service_type)

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

    # Create the announce client.
    announce_channel = robot.ensure_secure_channel(config.service_authority)
    announce_client = robot.ensure_client(config.service_name, announce_channel)

    announcement = announce_client.make_announcement(config.message)

    print("AnnounceClient received: " + announcement)


def main():
    """Create an AnnounceClient and use it to make a single announcement with a message."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument("--guid", required=True, type=str,
                        help="Unique GUID of the payload for auth")
    parser.add_argument("--secret", required=True, type=str, help="Secret of the payload for auth")
    parser.add_argument("--service-name", required=True, type=str,
                        help="Unique name of the service")
    parser.add_argument("--service-type", required=True, type=str,
                        help="RPC service type of the service")
    parser.add_argument("--service-authority", required=True, type=str,
                        help="Unique authority of the service")
    parser.add_argument("--message", required=True, type=str, help="Message to send to server")
    options = parser.parse_args()

    run_announce_client(options)

    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
