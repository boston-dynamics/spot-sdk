# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""General client implementation for all data-acquisition plugin services."""

from __future__ import print_function
import sys

from bosdyn.client.common import BaseClient
from bosdyn.client.data_acquisition import (DataAcquisitionClient, get_request_id,
                                            acquire_data_error, metadata_to_proto)
from bosdyn.api import data_acquisition_pb2 as data_acquisition
from bosdyn.api import data_acquisition_plugin_service_pb2_grpc as data_acquisition_plugin_service

from bosdyn.util import now_timestamp


class DataAcquisitionPluginClient(BaseClient):
    """A client for triggering data acquision plugin and logging. This client is not intended for
    use directly by users or applications. All acquisition requests should go to the data
    acquisition service first, which is responsible for forwarding the requests to the right data
    acquisition plugin services through this client."""

    default_service_name = None
    service_type = 'bosdyn.api.DataAcquisitionPluginService'

    def __init__(self):
        super(DataAcquisitionPluginClient,
              self).__init__(data_acquisition_plugin_service.DataAcquisitionPluginServiceStub)

    def update_from(self, other):
        super(DataAcquisitionPluginClient, self).update_from(other)

    def acquire_plugin_data(self, acquisition_requests, action_id, data_identifiers=None,
                            metadata=None, **kwargs):
        """Trigger a data acquisition to save data and metadata to the data acquisition store service.

        Args:
          acquisition_requests (bosdyn.api.AcquisitionRequestList): The different image sources and
                data sources to capture from and save to the data acquisition store service with
                the same timestamp.
          action_id (bosdyn.api.CaptureActionId): The unique action that all data should be saved
                with.
          data_identifiers (bosdyn.api.DataIdentifier) : List of data identifiers to associate with
                metadata.
          metadata (bosdyn.api.Metadata | dict): The JSON structured metadata to be associated with
                the data returned by the DataAcquisitionService when logged in the data acquisition
                store service.

        Raises:
          RpcError: Problem communicating with the robot.

        Returns:
            If the RPC is successful, then it will return the acquire data response, which can be
            used to check the status of the acquisition and get feedback.
        """

        metadata_proto = metadata_to_proto(metadata)
        request = data_acquisition.AcquirePluginDataRequest(
            metadata=metadata_proto, acquisition_requests=acquisition_requests,
            data_id=data_identifiers, action_id=action_id)
        return self.call(self._stub.AcquirePluginData, request,
                         error_from_response=acquire_data_error, **kwargs)

    def acquire_plugin_data_async(self, acquisition_requests, action_id, data_identifiers=None,
        metadata=None, **kwargs):
        """Async version of the acquire_plugin_data() RPC."""

        metadata_proto = metadata_to_proto(metadata)
        request = data_acquisition.AcquirePluginDataRequest(
            metadata=metadata_proto, acquisition_requests=acquisition_requests,
            data_id=data_identifiers, action_id=action_id)
        return self.call_async(self._stub.AcquirePluginData, request,
                               error_from_response=acquire_data_error, **kwargs)

    # The get_status, get_service_info, and cancel_acquisition methods are identical to the ones
    # implemented in the DataAcquisitionClient.
    if sys.version_info.major == 2:
        get_status = DataAcquisitionClient.__dict__['get_status']
        get_status_async = DataAcquisitionClient.__dict__['get_status_async']

        get_service_info = DataAcquisitionClient.__dict__['get_service_info']
        get_service_info_async = DataAcquisitionClient.__dict__['get_service_info_async']

        cancel_acquisition = DataAcquisitionClient.__dict__['cancel_acquisition']
        cancel_acquisition_async = DataAcquisitionClient.__dict__['cancel_acquisition_async']
    else:
        get_status = DataAcquisitionClient.get_status
        get_status_async = DataAcquisitionClient.get_status_async

        get_service_info = DataAcquisitionClient.get_service_info
        get_service_info_async = DataAcquisitionClient.get_service_info_async

        cancel_acquisition = DataAcquisitionClient.cancel_acquisition
        cancel_acquisition_async = DataAcquisitionClient.cancel_acquisition_async