# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to use the Gps Aggregator service."""
import collections

from bosdyn.api.gps import aggregator_pb2, aggregator_service_pb2_grpc, gps_pb2
from bosdyn.client.common import (BaseClient, common_header_errors, error_factory, error_pair,
                                  handle_common_header_errors, handle_unset_status_error)
from bosdyn.client.exceptions import ResponseError


class AggregatorClient(BaseClient):
    """Client for the Gps Aggregator service."""
    default_service_name = 'gps-aggregator'
    service_type = 'bosdyn.api.gps.AggregatorService'

    def __init__(self):
        super(AggregatorClient, self).__init__(aggregator_service_pb2_grpc.AggregatorServiceStub)

    def new_gps_data(self, data_points, gps_device, **kwargs):
        """Tell the robot about new GPS data that was collected.

        Args:
            data_points (collection of bosdyn.api.gps.GpsDataPoint): All the data you want to send.
            gps_device (collection of bosdyn.api.gps.GpsDevice): The identifier of this device.

        Returns:
            An instance of bosdyn.api.NewGpsDataResponse

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = aggregator_pb2.NewGpsDataRequest()
        req.data_points.extend(data_points)
        req.gps_device.CopyFrom(gps_device)
        return self.call(self._stub.NewGpsData, req, None, error_from_response=_new_gps_data_error,
                         copy_request=False, **kwargs)

    def new_gps_data_async(self, data_points, gps_device, **kwargs):
        """Async version of new_gps_data()"""
        req = aggregator_pb2.NewGpsDataRequest()
        req.data_points.extend(data_points)
        req.gps_device.CopyFrom(gps_device)
        return self.call_async(self._stub.NewGpsData, req, None,
                               error_from_response=_new_gps_data_error, copy_request=False,
                               **kwargs)


@handle_common_header_errors
def _new_gps_data_error(response):
    """Return an exception based on response from New GPS Data RPC, None if no error."""
    return None
