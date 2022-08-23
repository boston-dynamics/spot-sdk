# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A client for the ir-enable-disable service."""
from bosdyn.api import ir_enable_disable_pb2, ir_enable_disable_service_pb2_grpc
from bosdyn.client.common import BaseClient, common_header_errors


class IREnableDisableServiceClient(BaseClient):
    """Client to enable and/or disable the robot's IR light emitters in the body and hand sensors."""

    # Name of the service in the robot's directory listing.
    default_service_name = 'ir-enable-disable-service'
    # gRPC service proto definition implemented by this service
    service_type = 'bosdyn.api.IREnableDisableService'

    def __init__(self):
        super(IREnableDisableServiceClient,
              self).__init__(ir_enable_disable_service_pb2_grpc.IREnableDisableServiceStub)

    def set_ir_enabled(self, enable, **kwargs):
        """ Enable and/or disable the robot's IR light emitters.

        Args:
            enable (bool): Whether or not to enable the emitters.
        """
        if enable:
            request = ir_enable_disable_pb2.IREnableDisableRequest.REQUEST_ON
        else:
            request = ir_enable_disable_pb2.IREnableDisableRequest.REQUEST_OFF
        return self.call(self._stub.IREnableDisable,
                         ir_enable_disable_pb2.IREnableDisableRequest(request=request),
                         error_from_response=common_header_errors, **kwargs)

    def set_ir_enabled_async(self, enable, **kwargs):
        """Async version of set_ir_enabled()"""
        if enable:
            request = ir_enable_disable_pb2.IREnableDisableRequest.REQUEST_ON
        else:
            request = ir_enable_disable_pb2.IREnableDisableRequest.REQUEST_OFF
        return self.call_async(self._stub.IREnableDisable,
                               ir_enable_disable_pb2.IREnableDisableRequest(request=request),
                               error_from_response=common_header_errors, **kwargs)