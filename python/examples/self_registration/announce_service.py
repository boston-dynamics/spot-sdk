# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Example code demonstrating a basic python announce rpc service that handles announce requests.

This is a generic python grpc server set up.
"""
import argparse
import logging
import sys
import time
from concurrent import futures

import announce_pb2 as announce_protos
import announce_service_pb2_grpc as announce_service_protos_grpc
import grpc

import bosdyn.client.util
from bosdyn.client.server_util import GrpcServiceRunner
from bosdyn.client.util import setup_logging


class AnnounceServicer(announce_service_protos_grpc.AnnounceServiceServicer):
    """GRPC Service to handle announcements."""

    def Announce(self, request, context):
        logging.info('Got request')
        if request.message:
            announcement = request.message.upper()
        else:
            announcement = 'DEFAULT ANNOUNCEMENT!'
        response = announce_protos.AnnounceResponse(message=announcement)

        return response


def main():
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_service_hosting_arguments(parser)
    options = parser.parse_args()

    setup_logging()

    # Create & initialize python service server
    announce_service_servicer = AnnounceServicer()
    service_runner = GrpcServiceRunner(
        announce_service_servicer,
        announce_service_protos_grpc.add_AnnounceServiceServicer_to_server, options.port)

    # Keep service alive until a keyboard interrupt.
    service_runner.run_until_interrupt()

    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
