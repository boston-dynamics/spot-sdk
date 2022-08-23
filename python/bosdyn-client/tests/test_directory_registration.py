# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the directory registration module."""
import time

import pytest

import bosdyn.api.directory_pb2 as directory_protos
import bosdyn.api.directory_registration_pb2 as directory_registration_protos
import bosdyn.api.directory_registration_service_pb2_grpc as directory_registration_service
import bosdyn.api.header_pb2 as HeaderProto
import bosdyn.client.common
import bosdyn.client.directory_registration
import bosdyn.client.processors
from bosdyn.client import InternalServerError, UnsetStatusError
from bosdyn.client.directory_registration import (DirectoryRegistrationKeepAlive,
                                                  ServiceAlreadyExistsError,
                                                  ServiceDoesNotExistError)
from bosdyn.client.exceptions import InvalidRequestError

from . import helpers


class MockDirectoryRegistrationServicer(
        directory_registration_service.DirectoryRegistrationServiceServicer):
    """MockDirectoryRegistrationServicer implements the DirectoryRegistrationService in a simple way.

    MockDirectoryRegistrationServicer is only intended to exercise the control paths of the
    DirectoryRegistrationClient. It does not act like the actual implementation of the
    DirectoryRegistrationService.
    """

    def __init__(self):
        """Create mock that is a pretend directory."""
        super(MockDirectoryRegistrationServicer, self).__init__()
        self.service_entries = {}
        self.error_code = HeaderProto.CommonError.CODE_OK
        self.error_message = None
        self.use_unspecified_status = False

    def RegisterService(self, request, context):
        """Implement the RegisterService function of the service."""
        response = directory_registration_protos.RegisterServiceResponse()
        helpers.add_common_header(response, request, self.error_code, self.error_message)
        if self.error_code != HeaderProto.CommonError.CODE_OK:
            return response
        if request.service_entry.name not in self.service_entries.keys():
            self.service_entries[request.service_entry.name] = request.service_entry
            response.status = directory_registration_protos.RegisterServiceResponse.STATUS_OK
        else:
            response.status = directory_registration_protos.RegisterServiceResponse.STATUS_ALREADY_EXISTS
        return response

    def UnregisterService(self, request, context):
        """Implement the UnregisterService function of the service."""
        response = directory_registration_protos.UnregisterServiceResponse()
        helpers.add_common_header(response, request, self.error_code, self.error_message)
        if self.error_code != HeaderProto.CommonError.CODE_OK:
            return response
        if request.service_name in self.service_entries.keys():
            del self.service_entries[request.service_name]
            response.status = directory_registration_protos.UnregisterServiceResponse.STATUS_OK
        else:
            response.status = directory_registration_protos.UnregisterServiceResponse.STATUS_NONEXISTENT_SERVICE
        return response

    def UpdateService(self, request, context):
        """Implement the UnregisterService function of the service."""
        response = directory_registration_protos.UpdateServiceResponse()
        helpers.add_common_header(response, request, self.error_code, self.error_message)
        if self.error_code != HeaderProto.CommonError.CODE_OK:
            return response
        if request.service_entry.name in self.service_entries.keys():
            self.service_entries[request.service_entry.name] = request.service_entry
            response.status = directory_registration_protos.UpdateServiceResponse.STATUS_OK
        else:
            response.status = directory_registration_protos.UpdateServiceResponse.STATUS_NONEXISTENT_SERVICE
        return response


def _setup():
    client = bosdyn.client.directory_registration.DirectoryRegistrationClient()
    service = MockDirectoryRegistrationServicer()
    server = helpers.setup_client_and_service(
        client, service,
        directory_registration_service.add_DirectoryRegistrationServiceServicer_to_server)
    return client, service, server


def _add_service_entry(service_entry, service):
    service.service_entries[service_entry.name] = service_entry


def _has_service_name(name, service):
    for entry_name in service.service_entries.keys():
        if entry_name == name:
            return True
    return False


@pytest.fixture(scope='function')
def default_service_entry():
    return directory_protos.ServiceEntry(name='test', type='bosdyn.api.TestService',
                                         authority='test.spot.robot', user_token_required=True,
                                         liveness_timeout_secs=75.0)


@pytest.fixture(scope='function')
def default_service_entry_label_only():
    return directory_protos.ServiceEntry(name='test_auth_label_only', type='bosdyn.api.TestService',
                                         authority='test_label', user_token_required=True)


@pytest.fixture(scope='function')
def default_service_endpoint():
    return directory_protos.Endpoint(host_ip='0.0.0.0', port=0)


def test_header_error(default_service_entry, default_service_endpoint):
    client, service, server = _setup()
    service.error_code = HeaderProto.CommonError.CODE_INVALID_REQUEST
    with pytest.raises(InvalidRequestError):
        client.register(default_service_entry.name, default_service_entry.type,
                        default_service_entry.authority, default_service_endpoint.host_ip,
                        default_service_endpoint.port)


def test_registration(default_service_entry, default_service_endpoint,
                      default_service_entry_label_only):
    client, service, server = _setup()
    client.register(default_service_entry.name, default_service_entry.type,
                    default_service_entry.authority, default_service_endpoint.host_ip,
                    default_service_endpoint.port)
    assert _has_service_name(default_service_entry.name, service)
    client.register(default_service_entry_label_only.name, default_service_entry_label_only.type,
                    default_service_entry_label_only.authority, default_service_endpoint.host_ip,
                    default_service_endpoint.port)
    assert _has_service_name(default_service_entry_label_only.name, service)


def test_register_errors(default_service_entry, default_service_endpoint):
    client, service, server = _setup()
    _add_service_entry(default_service_entry, service)
    with pytest.raises(ServiceAlreadyExistsError):
        client.register(default_service_entry.name, default_service_entry.type,
                        default_service_entry.authority, default_service_endpoint.host_ip,
                        default_service_endpoint.port)


def test_update(default_service_entry, default_service_endpoint):
    client, service, server = _setup()
    _add_service_entry(default_service_entry, service)
    client.update(default_service_entry.name, default_service_entry.type, 'test.spot.UPDATEDrobot',
                  default_service_endpoint.host_ip, default_service_endpoint.port)
    assert _has_service_name(default_service_entry.name, service)
    updated_entry = service.service_entries[default_service_entry.name]
    assert updated_entry.authority == 'test.spot.UPDATEDrobot'


def test_update_errors(default_service_entry, default_service_endpoint):
    client, service, server = _setup()
    with pytest.raises(ServiceDoesNotExistError):
        client.update(default_service_entry.name, default_service_entry.type,
                      default_service_entry.authority, default_service_endpoint.host_ip,
                      default_service_endpoint.port)


def test_unregister(default_service_entry):
    client, service, server = _setup()
    _add_service_entry(default_service_entry, service)
    client.unregister(default_service_entry.name)
    assert len(service.service_entries) == 0


def test_unregister_errors(default_service_entry):
    client, service, server = _setup()
    with pytest.raises(ServiceDoesNotExistError):
        client.unregister(default_service_entry.name)


def test_keep_alive(default_service_entry, default_service_endpoint):
    client, service, server = _setup()
    keepalive = DirectoryRegistrationKeepAlive(client)
    name = default_service_entry.name
    assert name not in service.service_entries
    with keepalive.start(name, default_service_entry.type, default_service_entry.authority,
                         default_service_endpoint.host_ip, default_service_endpoint.port):
        assert name in service.service_entries

        # Just have some statement inside the "with" context.
        assert service.service_entries[name] == default_service_entry

    # Now that we've exited the "with" block, the internal thread should have ended and the service
    # should be unregistered.
    assert not keepalive.is_alive()
    assert name not in service.service_entries


def test_keep_alive_update(default_service_entry, default_service_endpoint):
    client, service, server = _setup()
    interval_seconds = 0.1
    keepalive = DirectoryRegistrationKeepAlive(client, rpc_interval_seconds=interval_seconds)
    name = default_service_entry.name
    assert name not in service.service_entries

    client.register(default_service_entry.name, default_service_entry.type,
                    default_service_entry.authority, default_service_endpoint.host_ip,
                    default_service_endpoint.port)

    new_authority = default_service_entry.authority + 'woo-hoo'
    with keepalive.start(name, default_service_entry.type, new_authority,
                         default_service_endpoint.host_ip, default_service_endpoint.port):
        assert service.service_entries[name].authority == new_authority

        # Make sure the thread is still alive after a few loops.
        time.sleep(interval_seconds * 3)
        assert keepalive.is_alive()
