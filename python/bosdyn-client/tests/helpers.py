# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Common unit test helpers for bosdyn.client tests."""

import concurrent

import grpc

import bosdyn.api.header_pb2 as HeaderProto


def setup_client_and_service(client, service, service_adder):
    """Starts a service listening on a port and points client to it.

    The service should have already been instantiated. It will be
    attached to a server listening on an ephemeral port and started.

    The client will have a networking channel which points to that service.

    Args:
        * client: The common.BaseClient derived client to use in a test.
        * service: The implementation of a gRPC service
        * service_adder: The function to add a service to a server. This is
        specified in the gRPC generated python, with a name like
        add_FooServiceServicer_to_server. Unfortunately, there's not an easy
        way to get to that method from the Service class.
    """
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
    service_adder(service, server)
    port = server.add_insecure_port('localhost:0')
    server.start()
    channel = grpc.insecure_channel('localhost:{}'.format(port))
    client.channel = channel
    return server


def add_common_header(response, request, error_code=HeaderProto.CommonError.CODE_OK,
                      error_message=None):
    """Sets the common header on the response.

    Args:
        response: The response object to fill the header with.
        request: The request to be echoed in the response common header.
        error_code: The code to use, OK by default.
        error_message: Any error message to include, empty by default.
    """
    header = HeaderProto.ResponseHeader()
    header.request_header.CopyFrom(request.header)
    header.error.code = error_code
    if error_message:
        header.error.message = error_message
    response.header.CopyFrom(header)


def make_async(fn):
    """Make an async version of a regular function"""

    def output_fn(*args, **kwargs):
        future = concurrent.futures.Future()
        try:
            future.set_result(fn(*args, **kwargs))
        except Exception as exc:
            future.set_exception(exc)
        return future

    return output_fn
