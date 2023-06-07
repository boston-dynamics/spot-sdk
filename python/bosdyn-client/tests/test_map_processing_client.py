# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the map processing module."""
import concurrent

import grpc
import pytest

import bosdyn.client.map_processing
from bosdyn.api import header_pb2, lease_pb2, time_sync_pb2
from bosdyn.api.graph_nav import map_pb2, map_processing_pb2, map_processing_service_pb2_grpc
from bosdyn.client.exceptions import InternalServerError, UnsetStatusError
from bosdyn.client.map_processing import __ANCHORING_COMMON_ERRORS, MapProcessingServiceClient
from bosdyn.client.time_sync import TimeSyncEndpoint


class MockMapProcessingServicer(map_processing_service_pb2_grpc.MapProcessingServiceServicer):
    """MapProcessing servicer for testing.

    Provides simple, controllable implementations of certain RPCs.
    """

    def __init__(self):
        super(MockMapProcessingServicer, self).__init__()
        self.common_header_code = header_pb2.CommonError.CODE_OK
        self.topology_process_status = map_processing_pb2.ProcessTopologyResponse.STATUS_OK
        self.anchoring_process_status = map_processing_pb2.ProcessAnchoringResponse.STATUS_OK
        self.graph = map_pb2.Graph()
        ed = self.graph.edges.add()
        ed.id.from_waypoint = 'w1'
        ed.id.to_waypoint = 'w2'

    def ProcessTopology(self, request, context):
        """Fake ProcessTopology responses."""
        resp = map_processing_pb2.ProcessTopologyResponse()
        resp.header.error.code = self.common_header_code
        resp.status = self.topology_process_status
        resp.new_subgraph.CopyFrom(self.graph)
        yield resp

    def ProcessAnchoring(self, request, context):
        """Fake ProcessAnchoring responses."""
        resp = map_processing_pb2.ProcessAnchoringResponse()
        resp.header.error.code = self.common_header_code
        resp.status = self.anchoring_process_status
        yield resp


@pytest.fixture
def client(time_sync):
    c = MapProcessingServiceClient()
    c._timesync_endpoint = time_sync
    return c


@pytest.fixture
def service():
    return MockMapProcessingServicer()


@pytest.fixture
def time_sync():
    ts = TimeSyncEndpoint(None)
    ts._locked_previous_response = time_sync_pb2.TimeSyncUpdateResponse()
    ts.response.state.status = time_sync_pb2.TimeSyncState.STATUS_OK
    return ts


@pytest.fixture
def server(client, service):
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=1))
    map_processing_service_pb2_grpc.add_MapProcessingServiceServicer_to_server(service, server)
    port = server.add_insecure_port('localhost:0')
    channel = grpc.insecure_channel('localhost:{}'.format(port))
    client.channel = channel
    server.start()
    yield server
    server.stop(0)


def test_process_topology_exceptions(client, service, server):
    make_call = lambda: client.process_topology(map_processing_pb2.ProcessTopologyRequest.Params(),
                                                True)
    make_call()

    service.topology_process_status = map_processing_pb2.ProcessTopologyResponse.STATUS_INVALID_GRAPH
    with pytest.raises(bosdyn.client.map_processing.InvalidGraphError):
        make_call()

    service.topology_process_status = map_processing_pb2.ProcessTopologyResponse.STATUS_MISSING_WAYPOINT_SNAPSHOTS
    with pytest.raises(bosdyn.client.map_processing.MissingSnapshotsError):
        make_call()


def test_process_anchoring_exceptions(client, service, server):
    make_call = lambda: client.process_anchoring(
        map_processing_pb2.ProcessAnchoringRequest.Params(), True, False)
    make_call()

    for (status, error) in __ANCHORING_COMMON_ERRORS.items():
        service.anchoring_process_status = status
        with pytest.raises(error):
            make_call()
