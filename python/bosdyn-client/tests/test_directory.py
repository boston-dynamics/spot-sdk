# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the directory module."""
import pytest

import bosdyn.api.directory_pb2 as directory_proto
import bosdyn.api.directory_pb2 as directory_service_proto
import bosdyn.api.directory_service_pb2_grpc as directory_service
import bosdyn.api.header_pb2 as HeaderProto
import bosdyn.client.common
import bosdyn.client.directory
import bosdyn.client.processors
from bosdyn.client import InternalServerError, UnsetStatusError

from . import helpers


class MockDirectoryServicer(directory_service.DirectoryServiceServicer):
    """MockDirectoryService implements the DirectoryService in a simple way.

    MockDirectoryService is only intended to exercise the control paths of the
    directory_client. It does not act like the actual implementation of the
    DirectoryService.
    """

    def __init__(self):
        """Create mock that is a pretend directory."""
        super(MockDirectoryServicer, self).__init__()
        self.service_entries = []
        self.endpoints = []
        self.error_code = HeaderProto.CommonError.CODE_OK
        self.error_message = None
        self.use_unspecified_status = False

    def ListServiceEntries(self, request, context):
        """Implement the ListServiceEntries function of the service."""
        response = directory_service_proto.ListServiceEntriesResponse()
        helpers.add_common_header(response, request, self.error_code, self.error_message)
        if self.error_code != HeaderProto.CommonError.CODE_OK:
            return response
        for service_entry in self.service_entries:
            x = response.service_entries.add()
            x.CopyFrom(service_entry)
        return response

    def GetServiceEntry(self, request, context):
        """Implement the GetServiceEntry function of the service."""
        response = directory_service_proto.GetServiceEntryResponse()
        helpers.add_common_header(response, request, self.error_code, self.error_message)
        if self.error_code != HeaderProto.CommonError.CODE_OK:
            return response
        matching_entry = None
        for service_entry in self.service_entries:
            if service_entry.name == request.service_name:
                matching_entry = service_entry
                break
        if matching_entry:
            response.status = directory_service_proto.GetServiceEntryResponse.STATUS_OK
            response.service_entry.CopyFrom(matching_entry)
        else:
            response.status = directory_service_proto.GetServiceEntryResponse.STATUS_NONEXISTENT_SERVICE
        if self.use_unspecified_status:
            response.status = directory_service_proto.GetServiceEntryResponse.STATUS_UNKNOWN
        return response



def _setup():
    client = bosdyn.client.directory.DirectoryClient()
    client.request_processors.append(bosdyn.client.processors.AddRequestHeader(lambda: 'test'))
    service = MockDirectoryServicer()
    server = helpers.setup_client_and_service(
        client, service, directory_service.add_DirectoryServiceServicer_to_server)
    return client, service, server


def _add_service_details(service, n_entries):
    for i in range(n_entries):
        service.service_entries.append(_SERVICE_ENTRIES[i])
        service.endpoints.append(_ENDPOINTS[i])


_SERVICE_ENTRIES = [
    directory_proto.ServiceEntry(name='foo', type='bosdyn.api.FooService',
                                 authority='foo.spot.robot', user_token_required=True),
    directory_proto.ServiceEntry(name='bar', type='bosdyn.api.BarService',
                                 authority='bar.spot.robot'),
]

_ENDPOINTS = [
    directory_proto.Endpoint(host_ip='1.2.3.4', port=52134),
    directory_proto.Endpoint(host_ip='6.7.8.9', port=52789),
]


def test_list_empty():
    client, service, server = _setup()
    directory_list = client.list()
    assert 0 == len(directory_list)


def _has_service_name(name, directory_list):
    return name in [s.name for s in directory_list]


def _has_service_pair(name, ip, pair_list):
    for p in pair_list:
        if p.service_entry.name == name and p.endpoint.host_ip == ip:
            return True
    return False


# list tests
def test_list_single_entry():
    client, service, server = _setup()
    _add_service_details(service, 1)
    directory_list = client.list()
    assert 1 == len(directory_list)
    assert _has_service_name('foo', directory_list)


def test_list_multiple_entries():
    client, service, server = _setup()
    _add_service_details(service, 2)
    directory_list = client.list()
    assert 2 == len(directory_list)
    assert _has_service_name('foo', directory_list)
    assert _has_service_name('bar', directory_list)


def test_list_internal_error():
    client, service, server = _setup()
    service.error_code = HeaderProto.CommonError.CODE_INTERNAL_SERVER_ERROR
    service.error_message = 'Something is wrong'
    with pytest.raises(InternalServerError):
        directory_list = client.list()


def test_list_empty_async():
    client, service, server = _setup()
    fut = client.list_async()
    directory_list = fut.result()
    assert 0 == len(directory_list)


def test_list_single_entry_async():
    client, service, server = _setup()
    _add_service_details(service, 1)
    fut = client.list_async()
    directory_list = fut.result()
    assert 1 == len(directory_list)
    assert _has_service_name('foo', directory_list)


def test_list_multiple_entries_async():
    client, service, server = _setup()
    _add_service_details(service, 2)
    fut = client.list_async()
    directory_list = fut.result()
    assert 2 == len(directory_list)
    assert _has_service_name('foo', directory_list)
    assert _has_service_name('bar', directory_list)


def test_list_internal_error_async():
    client, service, server = _setup()
    service.error_code = HeaderProto.CommonError.CODE_INTERNAL_SERVER_ERROR
    service.error_message = 'Something is wrong'
    fut = client.list_async()
    with pytest.raises(InternalServerError):
        directory_list = fut.result()


# get_entry tests
def test_get_entry_match():
    client, service, server = _setup()
    _add_service_details(service, 2)
    entry = client.get_entry('foo')
    assert 'foo' == entry.name


def test_get_entry_miss():
    client, service, server = _setup()
    _add_service_details(service, 2)
    with pytest.raises(bosdyn.client.directory.NonexistentServiceError):
        entry = client.get_entry('not-a-match')


def test_get_entry_unspecified():
    client, service, server = _setup()
    _add_service_details(service, 2)
    service.use_unspecified_status = True
    with pytest.raises(UnsetStatusError):
        entry = client.get_entry('foo')


def test_get_entry_match_async():
    client, service, server = _setup()
    _add_service_details(service, 2)
    fut = client.get_entry_async('foo')
    entry = fut.result()
    assert 'foo' == entry.name


def test_get_entry_miss_async():
    client, service, server = _setup()
    _add_service_details(service, 2)
    fut = client.get_entry_async('not-a-match')
    with pytest.raises(bosdyn.client.directory.NonexistentServiceError):
        entry = fut.result()


def test_get_entry_unspecified_async():
    client, service, server = _setup()
    _add_service_details(service, 2)
    service.use_unspecified_status = True
    fut = client.get_entry_async('foo')
    with pytest.raises(UnsetStatusError):
        entry = fut.result()


