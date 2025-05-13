# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Payload software update initiation gRPC client.

This client uses an insecure channel for signaling to a payload that it should
send its version information or initiate a software update.
"""

from bosdyn.api.payload_software_update_initiation_pb2 import (
    TriggerInitiateUpdateRequest, TriggerSendPayloadSoftwareInfoRequest)
from bosdyn.api.payload_software_update_initiation_service_pb2_grpc import \
    PayloadSoftwareUpdateInitiationServiceStub
from bosdyn.client.common import BaseClient


class PayloadSoftwareUpdateInitiationClient(BaseClient):
    """A client used to direct a payload to send its version information or start an update."""

    def __init__(self):
        super(PayloadSoftwareUpdateInitiationClient,
              self).__init__(PayloadSoftwareUpdateInitiationServiceStub)

    default_service_name = 'payload-software-update-initiation'
    service_type = 'bosdyn.api.PayloadSoftwareUpdateInitiationService'

    def trigger_send_payload_software_info(self, **kwargs):
        """Tell a payload to send its current version information to Spot.

        Returns:
            TriggerSendPayloadSoftwareInfoResponse: The response object from the payload. Currently
                this message is empty.

        Raises:
            RpcError: Problem communicating with the payload.
        """
        return self.call(self._stub.TriggerSendPayloadSoftwareInfo,
                         TriggerSendPayloadSoftwareInfoRequest(), **kwargs)

    def trigger_send_payload_software_info_async(self, **kwargs):
        """Async version of trigger_send_payload_software_info().

        Returns:
            TriggerSendPayloadSoftwareInfoResponse: The response object from the payload. Currently
                this message is empty.

        Raises:
            RpcError: Problem communicating with the payload.
        """
        return self.call_async(self._stub.TriggerSendPayloadSoftwareInfo,
                               TriggerSendPayloadSoftwareInfoRequest(), **kwargs)

    def trigger_initiate_update(self, **kwargs):
        """Tell a payload to initiate its software update logic.

        Returns:
            TriggerInitiateUpdateResponse: The response object from the payload. Currently this
                message is empty.

        Raises:
            RpcError: Problem communicating with the payload.
        """
        return self.call(self._stub.TriggerInitiateUpdate, TriggerInitiateUpdateRequest(), **kwargs)

    def trigger_initiate_update_async(self, **kwargs):
        """Async version of trigger_initiate_update().

        Returns:
            TriggerInitiateUpdateResponse: The response object from the payload. Currently this
                message is empty.

        Raises:
            RpcError: Problem communicating with the payload.
        """
        return self.call_async(self._stub.TriggerInitiateUpdate, TriggerInitiateUpdateRequest(),
                               **kwargs)
