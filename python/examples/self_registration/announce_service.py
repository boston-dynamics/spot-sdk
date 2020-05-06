# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
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
import time
import sys
from concurrent import futures
import grpc

import announce_pb2 as announce_protos
import announce_service_pb2_grpc as announce_service_protos_grpc


class Announce(announce_service_protos_grpc.AnnounceServiceServicer):
    """GRPC Service to handle announcements."""

    def Announce(self, request, context):
        logging.info("Got request")
        if request.message:
            announcement = request.message.upper()
        else:
            announcement = "DEFAULT ANNOUNCEMENT!"
        response = announce_protos.AnnounceResponse(message=announcement)

        return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True, help="Insecure server port")
    options = parser.parse_args()

    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)

    # Create & initialize python service server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4),)
    announce_service_protos_grpc.add_AnnounceServiceServicer_to_server(Announce(), server)

    server.add_insecure_port('[::]:' + str(options.port))

    server.start()

    # Keep service alive until a keyboard interrupt
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        server.stop(0)

    return True


if __name__ == '__main__':
    if not main():
        sys.exit(1)
