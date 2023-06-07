# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the graph_nav module."""
import concurrent

import grpc
import pytest

import bosdyn.client.graph_nav
from bosdyn.api import header_pb2, lease_pb2, time_sync_pb2
from bosdyn.api.graph_nav import graph_nav_pb2, graph_nav_service_pb2_grpc, map_pb2, nav_pb2
from bosdyn.client.exceptions import InternalServerError, UnsetStatusError
from bosdyn.client.graph_nav import GraphNavClient, UnrecognizedCommandError
from bosdyn.client.time_sync import TimeSyncEndpoint


class MockGraphNavServicer(graph_nav_service_pb2_grpc.GraphNavServiceServicer):
    """GraphNav servicer for testing.

    Provides simple, controllable implementations of certain RPCs.
    """

    def __init__(self):
        super(MockGraphNavServicer, self).__init__()
        self.common_header_code = header_pb2.CommonError.CODE_OK
        self.nav_feedback_status = graph_nav_pb2.NavigationFeedbackResponse.STATUS_REACHED_GOAL
        self.modify_navigation_status = graph_nav_pb2.ModifyNavigationResponse.STATUS_OK
        self.nav_to_resp = graph_nav_pb2.NavigateToResponse(
            status=graph_nav_pb2.NavigateToResponse.STATUS_OK)
        self.nav_route_resp = graph_nav_pb2.NavigateRouteResponse(
            status=graph_nav_pb2.NavigateRouteResponse.STATUS_OK)
        self.upload_waypoint_resp = graph_nav_pb2.UploadWaypointSnapshotResponse()
        self.upload_edge_resp = graph_nav_pb2.UploadEdgeSnapshotResponse()
        self.set_loc_resp = graph_nav_pb2.SetLocalizationResponse(
            status=graph_nav_pb2.SetLocalizationResponse.STATUS_OK)
        self.upload_graph_resp = graph_nav_pb2.UploadGraphResponse(
            status=graph_nav_pb2.UploadGraphResponse.STATUS_OK)
        self.download_wp_snapshot_status = graph_nav_pb2.DownloadWaypointSnapshotResponse.STATUS_OK
        self.download_edge_snapshot_status = graph_nav_pb2.DownloadEdgeSnapshotResponse.STATUS_OK
        self.lease_use_result = None

    def SetLocalization(self, request, context):
        resp = graph_nav_pb2.SetLocalizationResponse()
        resp.CopyFrom(self.set_loc_resp)
        resp.header.error.code = self.common_header_code
        if self.lease_use_result:
            resp.lease_use_result.CopyFrom(self.lease_use_result)
        return resp

    def NavigateRoute(self, request, context):
        resp = graph_nav_pb2.NavigateRouteResponse()
        resp.CopyFrom(self.nav_route_resp)
        resp.header.error.code = self.common_header_code
        if self.lease_use_result:
            resp.lease_use_results.add().CopyFrom(self.lease_use_result)
        return resp

    def NavigateTo(self, request, context):
        resp = graph_nav_pb2.NavigateToResponse()
        resp.CopyFrom(self.nav_to_resp)
        resp.header.error.code = self.common_header_code
        if self.lease_use_result:
            resp.lease_use_results.add().CopyFrom(self.lease_use_result)
        return resp

    def ClearGraph(self, request, context):
        resp = graph_nav_pb2.ClearGraphResponse()
        resp.header.error.code = self.common_header_code
        if self.lease_use_result:
            resp.lease_use_result.CopyFrom(self.lease_use_result)
        return resp

    def UploadGraph(self, request, context):
        resp = graph_nav_pb2.UploadGraphResponse()
        resp.CopyFrom(self.upload_graph_resp)
        resp.header.error.code = self.common_header_code
        if self.lease_use_result:
            resp.lease_use_result.CopyFrom(self.lease_use_result)
        return resp

    def UploadWaypointSnapshot(self, request_iterator, context):
        resp = graph_nav_pb2.UploadWaypointSnapshotResponse()
        resp.status = graph_nav_pb2.UploadWaypointSnapshotResponse.STATUS_OK
        resp.header.error.code = self.common_header_code
        if self.lease_use_result:
            resp.lease_use_result.CopyFrom(self.lease_use_result)
        return resp

    def UploadEdgeSnapshot(self, request_iterator, context):
        resp = graph_nav_pb2.UploadEdgeSnapshotResponse()
        resp.header.error.code = self.common_header_code
        if self.lease_use_result:
            resp.lease_use_result.CopyFrom(self.lease_use_result)
        return resp

    def NavigationFeedback(self, request, context):
        """Specific NavigationFeedback responses."""
        resp = graph_nav_pb2.NavigationFeedbackResponse()
        resp.header.error.code = self.common_header_code
        resp.status = self.nav_feedback_status
        return resp

    def ModifyNavigation(self, request, context):
        resp = graph_nav_pb2.ModifyNavigationResponse()
        resp.header.error.code = self.common_header_code
        resp.status = self.modify_navigation_status
        return resp

    def DownloadWaypointSnapshot(self, request, context):
        resp = graph_nav_pb2.DownloadWaypointSnapshotResponse()
        resp.header.error.code = self.common_header_code
        resp.status = self.download_wp_snapshot_status
        yield resp

    def DownloadEdgeSnapshot(self, request, context):
        resp = graph_nav_pb2.DownloadEdgeSnapshotResponse()
        resp.header.error.code = self.common_header_code
        resp.status = self.download_edge_snapshot_status
        yield resp


@pytest.fixture
def client(time_sync):
    c = GraphNavClient()
    c._timesync_endpoint = time_sync
    return c


@pytest.fixture
def service():
    return MockGraphNavServicer()


@pytest.fixture
def time_sync():
    ts = TimeSyncEndpoint(None)
    ts._locked_previous_response = time_sync_pb2.TimeSyncUpdateResponse()
    ts.response.state.status = time_sync_pb2.TimeSyncState.STATUS_OK
    return ts


@pytest.fixture
def server(client, service):
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=1))
    graph_nav_service_pb2_grpc.add_GraphNavServiceServicer_to_server(service, server)
    port = server.add_insecure_port('localhost:0')
    channel = grpc.insecure_channel('localhost:{}'.format(port))
    client.channel = channel
    server.start()
    yield server
    server.stop(0)


@pytest.mark.parametrize('func', ('navigation_feedback_async', 'navigation_feedback'))
def test_feedback_exceptions(client, service, server, func):
    """Client's navigation feedback should provide expected exceptions/responses."""

    if 'async' in func:
        call = lambda: getattr(client, func)().result()
    else:
        call = getattr(client, func)

    # Service starts with valid status codes.
    resp = call()
    assert resp.status == service.nav_feedback_status

    # Check every non-unknown status code -- they should all be OK.
    for _, value in graph_nav_pb2.NavigationFeedbackResponse.Status.items():
        # Skip the unset/UNKNOWN value.
        if value == 0:
            continue
        service.nav_feedback_status = value
        assert call().status == value

    # UNKNOWN should cause an exception.
    service.nav_feedback_status = graph_nav_pb2.NavigationFeedbackResponse.STATUS_UNKNOWN
    with pytest.raises(UnsetStatusError):
        call()

    # Errors in the common header should cause an exception.
    service.common_header_code = header_pb2.CommonError.CODE_INTERNAL_SERVER_ERROR
    with pytest.raises(InternalServerError):
        call()




def test_navigate_to_exceptions(client, service, server):
    make_call = lambda: client.navigate_to('somewhere-id', 2.0)
    cmd_id = make_call()
    assert type(cmd_id) is int

    service.lease_use_result = lease_pb2.LeaseUseResult(
        status=lease_pb2.LeaseUseResult.STATUS_OLDER)
    with pytest.raises(bosdyn.client.LeaseUseError):
        make_call()

    service.lease_use_result = lease_pb2.LeaseUseResult(status=lease_pb2.LeaseUseResult.STATUS_OK)
    cmd_id = make_call()
    assert type(cmd_id) is int

    service.nav_to_resp.status = service.nav_to_resp.STATUS_NO_TIMESYNC
    with pytest.raises(bosdyn.client.graph_nav.NoTimeSyncError):
        make_call()

    service.nav_to_resp.status = service.nav_to_resp.STATUS_EXPIRED
    with pytest.raises(bosdyn.client.graph_nav.CommandExpiredError):
        make_call()

    service.nav_to_resp.status = service.nav_to_resp.STATUS_TOO_DISTANT
    with pytest.raises(bosdyn.client.graph_nav.TooDistantError):
        make_call()

    service.nav_to_resp.status = service.nav_to_resp.STATUS_ROBOT_IMPAIRED
    with pytest.raises(bosdyn.client.graph_nav.RobotImpairedError):
        make_call()

    service.nav_to_resp.status = service.nav_to_resp.STATUS_RECORDING
    with pytest.raises(bosdyn.client.graph_nav.IsRecordingError):
        make_call()

    service.nav_to_resp.status = service.nav_to_resp.STATUS_UNKNOWN_WAYPOINT
    with pytest.raises(bosdyn.client.graph_nav.UnknownWaypointError):
        make_call()

    service.nav_to_resp.status = service.nav_to_resp.STATUS_NO_PATH
    with pytest.raises(bosdyn.client.graph_nav.NoPathError):
        make_call()

    service.nav_to_resp.status = service.nav_to_resp.STATUS_FEATURE_DESERT
    with pytest.raises(bosdyn.client.graph_nav.FeatureDesertError):
        make_call()

    service.nav_to_resp.status = service.nav_to_resp.STATUS_LOST
    with pytest.raises(bosdyn.client.graph_nav.RobotLostError):
        make_call()

    service.nav_to_resp.status = service.nav_to_resp.STATUS_NOT_LOCALIZED_TO_MAP
    with pytest.raises(bosdyn.client.graph_nav.RobotNotLocalizedToRouteError):
        make_call()

    service.nav_to_resp.status = service.nav_to_resp.STATUS_COULD_NOT_UPDATE_ROUTE
    with pytest.raises(bosdyn.client.graph_nav.RouteNotUpdatingError):
        make_call()


def test_navigate_route_exceptions(client, service, server):
    make_call = lambda: client.navigate_route(nav_pb2.Route(), 2.0)
    cmd_id = make_call()
    assert cmd_id == 0
    service.lease_use_result = lease_pb2.LeaseUseResult(
        status=lease_pb2.LeaseUseResult.STATUS_OLDER)
    with pytest.raises(bosdyn.client.LeaseUseError):
        make_call()

    service.lease_use_result = lease_pb2.LeaseUseResult(status=lease_pb2.LeaseUseResult.STATUS_OK)
    cmd_id = make_call()
    assert type(cmd_id) is int

    service.nav_route_resp.status = service.nav_route_resp.STATUS_NO_TIMESYNC
    with pytest.raises(bosdyn.client.graph_nav.NoTimeSyncError):
        make_call()

    service.nav_route_resp.status = service.nav_route_resp.STATUS_EXPIRED
    with pytest.raises(bosdyn.client.graph_nav.CommandExpiredError):
        make_call()

    service.nav_route_resp.status = service.nav_route_resp.STATUS_TOO_DISTANT
    with pytest.raises(bosdyn.client.graph_nav.TooDistantError):
        make_call()

    service.nav_route_resp.status = service.nav_route_resp.STATUS_ROBOT_IMPAIRED
    with pytest.raises(bosdyn.client.graph_nav.RobotImpairedError):
        make_call()

    service.nav_route_resp.status = service.nav_route_resp.STATUS_RECORDING
    with pytest.raises(bosdyn.client.graph_nav.IsRecordingError):
        make_call()

    service.nav_route_resp.status = service.nav_route_resp.STATUS_UNKNOWN_ROUTE_ELEMENTS
    with pytest.raises(bosdyn.client.graph_nav.UnknownRouteElementsError):
        make_call()
    #make sure the misspelled error works for backwards compatibility.
    with pytest.raises(bosdyn.client.graph_nav.UnkownRouteElementsError):
        make_call()

    service.nav_route_resp.status = service.nav_route_resp.STATUS_INVALID_EDGE
    with pytest.raises(bosdyn.client.graph_nav.InvalidEdgeError):
        make_call()

    service.nav_route_resp.status = service.nav_route_resp.STATUS_CONSTRAINT_FAULT
    with pytest.raises(bosdyn.client.graph_nav.ConstraintFaultError):
        make_call()

    service.nav_route_resp.status = service.nav_route_resp.STATUS_FEATURE_DESERT
    with pytest.raises(bosdyn.client.graph_nav.FeatureDesertError):
        make_call()

    service.nav_route_resp.status = service.nav_route_resp.STATUS_LOST
    with pytest.raises(bosdyn.client.graph_nav.RobotLostError):
        make_call()

    service.nav_route_resp.status = service.nav_route_resp.STATUS_NOT_LOCALIZED_TO_ROUTE
    with pytest.raises(bosdyn.client.graph_nav.RobotNotLocalizedToRouteError):
        make_call()

    service.nav_route_resp.status = service.nav_route_resp.STATUS_COULD_NOT_UPDATE_ROUTE
    with pytest.raises(bosdyn.client.graph_nav.RouteNotUpdatingError):
        make_call()


def test_clear_graph(client, service, server):
    make_call = lambda: client.clear_graph()

    make_call()

    service.lease_use_result = lease_pb2.LeaseUseResult(
        status=lease_pb2.LeaseUseResult.STATUS_OLDER)
    with pytest.raises(bosdyn.client.LeaseUseError):
        make_call()


def test_upload_graph_exceptions(client, service, server):
    make_call = lambda: client.upload_graph(graph=map_pb2.Graph())
    make_call()

    service.lease_use_result = lease_pb2.LeaseUseResult(
        status=lease_pb2.LeaseUseResult.STATUS_OLDER)
    with pytest.raises(bosdyn.client.LeaseUseError):
        make_call()

    service.lease_use_result = lease_pb2.LeaseUseResult(status=lease_pb2.LeaseUseResult.STATUS_OK)
    make_call()

    service.upload_graph_resp.status = service.upload_graph_resp.STATUS_MAP_TOO_LARGE_LICENSE
    with pytest.raises(bosdyn.client.graph_nav.MapTooLargeLicenseError):
        make_call()

    service.upload_graph_resp.status = service.upload_graph_resp.STATUS_INVALID_GRAPH
    with pytest.raises(bosdyn.client.graph_nav.InvalidGraphError):
        make_call()


def test_upload_waypoint_exceptions(client, service, server):
    make_call = lambda: client.upload_waypoint_snapshot(map_pb2.WaypointSnapshot())
    make_call()

    service.lease_use_result = lease_pb2.LeaseUseResult(
        status=lease_pb2.LeaseUseResult.STATUS_OLDER)
    with pytest.raises(bosdyn.client.LeaseUseError):
        make_call()


def test_upload_edge_exceptions(client, service, server):
    make_call = lambda: client.upload_edge_snapshot(map_pb2.EdgeSnapshot())
    make_call()

    service.lease_use_result = lease_pb2.LeaseUseResult(
        status=lease_pb2.LeaseUseResult.STATUS_OLDER)
    with pytest.raises(bosdyn.client.LeaseUseError):
        make_call()


def test_set_localization_exceptions(client, service, server):
    make_call = lambda: client.set_localization(nav_pb2.Localization())
    make_call()

    service.lease_use_result = lease_pb2.LeaseUseResult(
        status=lease_pb2.LeaseUseResult.STATUS_OLDER)
    with pytest.raises(bosdyn.client.LeaseUseError):
        make_call()

    service.lease_use_result = lease_pb2.LeaseUseResult(status=lease_pb2.LeaseUseResult.STATUS_OK)
    make_call()

    service.set_loc_resp.status = service.set_loc_resp.STATUS_ROBOT_IMPAIRED
    with pytest.raises(bosdyn.client.graph_nav.RobotFaultedError):
        make_call()

    service.set_loc_resp.status = service.set_loc_resp.STATUS_UNKNOWN_WAYPOINT
    with pytest.raises(bosdyn.client.graph_nav.UnknownMapInformationError):
        make_call()

    service.set_loc_resp.status = service.set_loc_resp.STATUS_ABORTED
    with pytest.raises(bosdyn.client.graph_nav.RequestAbortedError):
        make_call()

    service.set_loc_resp.status = service.set_loc_resp.STATUS_FAILED
    with pytest.raises(bosdyn.client.graph_nav.RequestFailedError):
        make_call()


def test_download_waypoint_snapshot(client, service, server):
    make_call = lambda: client.download_waypoint_snapshot(waypoint_snapshot_id="mywaypoint")
    make_call()

    service.common_header_code = header_pb2.CommonError.CODE_INTERNAL_SERVER_ERROR
    with pytest.raises(InternalServerError):
        make_call()

    service.common_header_code = header_pb2.CommonError.CODE_OK
    service.download_wp_snapshot_status = graph_nav_pb2.DownloadWaypointSnapshotResponse.STATUS_SNAPSHOT_DOES_NOT_EXIST
    with pytest.raises(bosdyn.client.graph_nav.UnknownMapInformationError):
        make_call()


def test_download_edge_snapshot(client, service, server):
    make_call = lambda: client.download_edge_snapshot(edge_snapshot_id="myedge")
    make_call()

    service.common_header_code = header_pb2.CommonError.CODE_INTERNAL_SERVER_ERROR
    with pytest.raises(InternalServerError):
        make_call()

    service.common_header_code = header_pb2.CommonError.CODE_OK
    service.download_edge_snapshot_status = graph_nav_pb2.DownloadEdgeSnapshotResponse.STATUS_SNAPSHOT_DOES_NOT_EXIST
    with pytest.raises(bosdyn.client.graph_nav.UnknownMapInformationError):
        make_call()
