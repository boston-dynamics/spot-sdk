# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
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

import announce_pb2 as announce_protos
import announce_service_pb2_grpc as announce_service_protos_grpc

import bosdyn.client.util
from bosdyn.client.common import BaseClient


class AnnounceClient(BaseClient):
    """Client to announce strings."""

    # Typical name of the service in the robot's directory listing.
    default_service_name = 'announce-service'
    # gRPC service proto definition implemented by this service. Must be available locally.
    service_type = 'AnnounceService'

    def __init__(self):
        super(AnnounceClient, self).__init__(announce_service_protos_grpc.AnnounceServiceStub)

    def make_announcement(self, message, **kwargs):
        """Announce a message."""
        req = announce_protos.AnnounceRequest(message=message)
        return self.call(self._stub.Announce, req,
                         value_from_response=lambda response: response.message, copy_request=False,
                         **kwargs)


def run_announce_client(config):
    sdk = bosdyn.client.create_standard_sdk('AnnounceClient')

    # Register the announce client with the SDK instance.
    sdk.register_service_client(AnnounceClient)

    robot = sdk.create_robot(config.hostname)

    # Get a user token for this payload.
    # This request will block if the payload has not been authorized by an admin via the web UI.
    robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(config))

    # Create the announce client.
    announce_client = robot.ensure_client(AnnounceClient.default_service_name)

    # Make an announcement through the announce service.
    announcement = announce_client.make_announcement(config.message)

    print('AnnounceClient received: ' + announcement)


def main():
    """Create an AnnounceClient and use it to make a single announcement with a message."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    parser.add_argument("--message", required=True, type=str, help="Message to send to server")
    options = parser.parse_args()

    run_announce_client(options)

    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
