# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tests for the fault client."""

from bosdyn.api import service_fault_pb2
from bosdyn.client import InternalServerError, UnsetStatusError
from bosdyn.client.fault import (ServiceFaultAlreadyExistsError, ServiceFaultDoesNotExistError,
                                 _clear_service_fault_error, _trigger_service_fault_error)


def test_trigger_service_fault_error():
    # Test unset header error
    response = service_fault_pb2.TriggerServiceFaultResponse()
    assert isinstance(_trigger_service_fault_error(response), UnsetStatusError)
    # Test header error
    response.header.error.code = response.header.error.CODE_INTERNAL_SERVER_ERROR
    assert isinstance(_trigger_service_fault_error(response), InternalServerError)
    # Test unset status error
    response.header.error.code = response.header.error.CODE_OK
    assert isinstance(_trigger_service_fault_error(response), UnsetStatusError)
    # Test status error
    response.status = response.STATUS_FAULT_ALREADY_ACTIVE
    assert isinstance(_trigger_service_fault_error(response), ServiceFaultAlreadyExistsError)
    # Test OK
    response.status = response.STATUS_OK
    assert not _trigger_service_fault_error(response)


def test_clear_service_fault_error():
    # Test unset header error
    response = service_fault_pb2.ClearServiceFaultResponse()
    assert isinstance(_clear_service_fault_error(response), UnsetStatusError)
    # Test header error
    response.header.error.code = response.header.error.CODE_INTERNAL_SERVER_ERROR
    assert isinstance(_clear_service_fault_error(response), InternalServerError)
    # Test unset status error
    response.header.error.code = response.header.error.CODE_OK
    assert isinstance(_clear_service_fault_error(response), UnsetStatusError)
    # Test status error
    response.status = response.STATUS_FAULT_NOT_ACTIVE
    assert isinstance(_clear_service_fault_error(response), ServiceFaultDoesNotExistError)
    # Test OK
    response.status = response.STATUS_OK
    assert not _clear_service_fault_error(response)
