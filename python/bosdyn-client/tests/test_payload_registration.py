# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tests for the payload registration client."""

from bosdyn.client import InternalServerError, UnsetStatusError
from bosdyn.client.payload_registration import (_payload_registration_error,
                                                PayloadAlreadyExistsError)

import bosdyn.api.payload_registration_pb2 as payload_registration_protos


def test_payload_registration_error():
    # Test unset header error
    response = payload_registration_protos.RegisterPayloadResponse()
    assert isinstance(_payload_registration_error(response), UnsetStatusError)
    # Test header error
    response.header.error.code = response.header.error.CODE_INTERNAL_SERVER_ERROR
    assert isinstance(_payload_registration_error(response), InternalServerError)
    response.header.error.code = response.header.error.CODE_OK
    # Test unset status error
    assert isinstance(_payload_registration_error(response), UnsetStatusError)
    # Test status error
    response.status = response.STATUS_ALREADY_EXISTS
    assert isinstance(_payload_registration_error(response), PayloadAlreadyExistsError)
    # Test OK
    response.status = response.STATUS_OK
    assert not _payload_registration_error(response)
