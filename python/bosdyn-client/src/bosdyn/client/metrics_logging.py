# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Clients for the metrics logging service."""
import collections
import threading

from google.protobuf.duration_pb2 import Duration
from google.protobuf.timestamp_pb2 import Timestamp

from bosdyn.api.metrics_logging import (absolute_metrics_pb2, metrics_logging_robot_pb2,
                                        metrics_logging_robot_service_pb2_grpc)
from bosdyn.client.common import (BaseClient, common_header_errors, error_factory,
                                  handle_common_header_errors, handle_unset_status_error)
from bosdyn.client.data_buffer import make_parameter
from bosdyn.client.exceptions import ResponseError


class MissingKeysError(ResponseError):
    """Metrics requested from the metrics service did not exist."""


class UnableToOptOutError(ResponseError):
    """Unable to opt-out of metrics logging due to invalid license permissions."""


class MetricsLoggingClient(BaseClient):
    """A client for the metrics logging service on the robot.
    """
    default_service_name = 'metrics-logging'
    service_type = 'bosdyn.api.metrics_logging.MetricsLoggingRobotService'

    def __init__(self):
        super(MetricsLoggingClient,
              self).__init__(metrics_logging_robot_service_pb2_grpc.MetricsLoggingRobotServiceStub)

    def get_metrics(self, keys=None, include_events=False, **kwargs):
        """Get metrics from the robot.

        Args:
            keys(List[strings]): A list of strings representing the keys for metrics that should be returned.
            include_events(bool): Whether events should be included in the response.

        Returns:
            The GetMetricsResponse response.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = self._get_metrics_request(keys, include_events)
        return self.call(self._stub.GetMetrics, req, None, _get_metrics_error_from_response,
                         copy_request=False, **kwargs)

    def get_metrics_async(self, keys=None, include_events=False, **kwargs):
        """Async version of get_metrics()."""
        req = self._get_metrics_request(keys, include_events)
        return self.call_async(self._stub.GetMetrics, req, None, _get_metrics_error_from_response,
                               copy_request=False, **kwargs)


    def get_store_sequence_range(self, **kwargs):
        """Determine the range of sequence numbers currently being used by the metrics system's store.

        Returns:
            A list where the first number represents the starting index (inclusive), and the second number represents
            the final index (inclusive) for the entries in the metrics store.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = metrics_logging_robot_pb2.GetStoreSequenceRangeRequest()
        return self.call(self._stub.GetStoreSequenceRange, req,
                         self._store_sequence_range_from_response, common_header_errors,
                         copy_request=False, **kwargs)

    def get_store_sequence_range_async(self, **kwargs):
        """Async version of get_store_sequence_range()."""
        req = metrics_logging_robot_pb2.GetStoreSequenceRangeRequest()
        return self.call_async(self._stub.GetStoreSequenceRange, req,
                               self._store_sequence_range_from_response, common_header_errors,
                               copy_request=False, **kwargs)

    def get_absolute_metric_snapshot(self, sequence_numbers, **kwargs):
        """Get absolute metric snapshots for specific sequence numbers' entries.

        Args:
            sequence_numbers(List(int)): The list of sequence numbers whose entries should be returned as
                                         absolute metric snapshots.

        Returns:
            A list of signed_proto_pb2.SignedProto(). Each signed proto will contain the serialized
            absolute_metric_pb2.AbsoluteMetricsSnapshot() for the requested sequence number's timestamp.
            The robot will exclude snapshots if the sequence number does not exist, or the response will exceed
            the grpc limit.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        req = metrics_logging_robot_pb2.GetAbsoluteMetricSnapshotRequest(
            sequence_numbers=sequence_numbers)
        return self.call(self._stub.GetAbsoluteMetricSnapshot, req,
                         self._get_absolute_metric_snapshots_from_response, common_header_errors,
                         copy_request=False, **kwargs)

    def get_absolute_metric_snapshot_async(self, sequence_numbers, **kwargs):
        """Async version of get_absolute_metric_snapshot()."""
        req = metrics_logging_robot_pb2.GetAbsoluteMetricSnapshotRequest(
            sequence_numbers=sequence_numbers)
        return self.call_async(self._stub.GetAbsoluteMetricSnapshot, req,
                               self._get_absolute_metric_snapshots_from_response,
                               common_header_errors, copy_request=False, **kwargs)


    @staticmethod
    def _get_metrics_request(keys, include_events):
        return metrics_logging_robot_pb2.GetMetricsRequest(keys=keys, include_events=include_events)

    @staticmethod
    def _store_sequence_range_from_response(response):
        return [response.first_sequence_number, response.last_sequence_number]

    @staticmethod
    def _get_absolute_metric_snapshots_from_response(response):
        return response.snapshots


def make_parameter_update(label, value, is_incremental, units="", notes=""):
    """Create a parameter update proto from the label, param value, and if it is incremental."""
    param_update = absolute_metrics_pb2.ParameterUpdate(incremental=is_incremental)
    param = make_parameter(label, value, units, notes)
    if param is not None:
        param_update.parameter.CopyFrom(param)
    return param_update


@handle_common_header_errors
def _get_metrics_error_from_response(response):
    """Return an exception based on response from GetMetrics RPC, None if no error."""
    # This could return a MissingKeysError for invalid keys, but at the time of writing
    # this would cause it to throw errors on unreported metrics (not just invalid).
    # Eg, this consistently would throw errors on a new robot with no metrics reported yet.
    return None


