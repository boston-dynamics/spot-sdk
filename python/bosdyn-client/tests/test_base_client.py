# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from functools import partial

from bosdyn.client.common import BaseClient


def method_wrapper(func):

    def _future(self, **kwargs):
        partial(func, self, **kwargs)
        return Response()

    def done_callback(func):
        pass

    func.future = _future
    func._method = b"MockStub.rpc_method"
    return func


class ProcessedResponse():
    pass


class Response():

    def __init__(self):
        self.processed_response = ProcessedResponse()
        self.done = True

    def add_done_callback(self, fn):
        pass

    def exception(self):
        return None

    def done(self):
        return True

    def result(self):
        return self


class MockStub():

    @method_wrapper
    def rpc_method(self, request, **kwargs):
        return Response()


def stub_creation_func(channel):
    return MockStub()


def _test_calls():
    pass


def test_base_client():
    client = BaseClient(stub_creation_func)
    client.channel = "test"
    kwargs = {"disable_value_handler": True}

    def value_from_response(response):
        return response.processed_response

    # Test sync
    response = client.call(client._stub.rpc_method, None)
    assert isinstance(response, Response)

    response = client.call(client._stub.rpc_method, None, value_from_response=value_from_response)
    assert isinstance(response, ProcessedResponse)

    response = client.call(client._stub.rpc_method, None, value_from_response=value_from_response,
                           **kwargs)
    assert isinstance(response, Response)

    # Test async
    response = client.call_async(client._stub.rpc_method, None)
    assert isinstance(response.result(), Response)

    response = client.call_async(client._stub.rpc_method, None,
                                 value_from_response=value_from_response)
    assert isinstance(response.result(), ProcessedResponse)

    response = client.call_async(client._stub.rpc_method, None,
                                 value_from_response=value_from_response, **kwargs)
    assert isinstance(response.result(), Response)
