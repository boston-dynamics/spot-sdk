# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client for the payload service.

This allows client code to read from the robot payload registry.
"""

from __future__ import print_function
import logging

import bosdyn.api.payload_pb2 as payload_protos
import bosdyn.api.payload_pb2 as payload_service_protos
import bosdyn.api.payload_service_pb2_grpc as payload_service

from .common import BaseClient, common_header_errors

LOGGER = logging.getLogger('payload_client')


def _get_entry_value(response):
    return response.payloads


class PayloadClient(BaseClient):
    """A client handling payload configs."""

    default_service_name = 'payload'
    service_type = 'bosdyn.api.PayloadService'

    def __init__(self):
        super(PayloadClient, self).__init__(payload_service.PayloadServiceStub)

    def list_payloads(self, **kw_args):
        """List all payloads registered on the robot

        Args:
          kw_args:              Extra arguments to pass to grpc call invocation.
        
        Returns:
          A list of the proto message definitions of all registered payloads

        Raises:
          RpcError: Problem communicating with the robot.
        """
        request = payload_service_protos.ListPayloadsRequest()
        return self.call(self._stub.ListPayloads, request, value_from_response=_get_entry_value,
                         error_from_response=common_header_errors, **kw_args)

    def list_payloads_async(self, **kw_args):
        """List all payloads registered on the robot

        Args:
          kw_args:              Extra arguments to pass to grpc call invocation.
        
        Returns:
          A list of the proto message definitions of all registered payloads

        Raises:
          RpcError: Problem communicating with the robot.
        """
        request = payload_service_protos.ListPayloadsRequest()
        return self.call_async(self._stub.ListPayloads, request,
                               value_from_response=_get_entry_value,
                               error_from_response=common_header_errors, **kw_args)
