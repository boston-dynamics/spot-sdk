# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name
import threading
import time
from unittest import mock

import pytest
from google.protobuf import text_format

from bosdyn.api import lease_pb2
from bosdyn.api.graph_nav import area_callback_pb2
from bosdyn.client.area_callback_region_handler_base import (AreaCallbackRegionHandlerBase,
                                                             IncorrectUsage)
from bosdyn.client.area_callback_service_servicer import AreaCallbackServiceServicer
from bosdyn.client.area_callback_service_utils import AreaCallbackServiceConfig
from bosdyn.client.data_buffer import DataBufferClient
from bosdyn.client.lease import LeaseClient, LeaseWallet
from bosdyn.client.robot import Robot
from bosdyn.util import seconds_to_timestamp


class MockLeaseClient:

    def __init__(self, should_throw):
        self.should_throw = should_throw

    def list_leases_full(self):
        lease_str = """
resources {
  resource: "all-leases"
  lease {
    resource: "all-leases"
    epoch: "zJTwcBbRxKAovmdS"
    sequence: 8
    client_names: "root"
  }
  lease_owner {
  }
}
resources {
  resource: "body"
  lease {
    resource: "body"
    epoch: "zJTwcBbRxKAovmdS"
    sequence: 8
    client_names: "root"
  }
  lease_owner {
  }
}
resources {
  resource: "mobility"
  lease {
    resource: "mobility"
    epoch: "zJTwcBbRxKAovmdS"
    sequence: 8
    client_names: "root"
  }
  lease_owner {
  }
}
resource_tree {
  resource: "all-leases"
  sub_resources {
    resource: "body"
    sub_resources {
      resource: "mobility"
    }
  }
}
"""
        list_leases_full = lease_pb2.ListLeasesResponse()
        text_format.Parse(lease_str, list_leases_full)
        return list_leases_full


class MockRobot:

    def __init__(self, lease_client):
        self.lease_client = lease_client
        self._name = "test-robot"
        self.response_processors = []
        self.lease_wallet = LeaseWallet()
        self.time = 0

    def ensure_client(self, service_name):
        if service_name == LeaseClient.default_service_name:
            return self.lease_client
        elif service_name == DataBufferClient.default_service_name:
            return mock.Mock()

    def time_sec(self):
        return self.time


class AreaCallbackRegionHandlerImpl(AreaCallbackRegionHandlerBase):

    def __init__(self, config: AreaCallbackServiceConfig, robot: Robot):
        super().__init__(config, robot)
        self.is_in_control = False
        self.start_called = False
        self.end_called = False

        self.event_set_stop = threading.Event()
        self.event_at_start = threading.Event()
        self.event_at_control = threading.Event()
        self.event_set_continue = threading.Event()
        self.event_returning = threading.Event()

    def begin(
        self, request: area_callback_pb2.BeginCallbackRequest
    ) -> area_callback_pb2.BeginCallbackResponse.Status:
        # Reset variables to run test twice.
        self.is_in_control = False
        self.end_called = False
        # Start called.
        self.start_called = True
        return area_callback_pb2.BeginCallbackResponse.STATUS_OK

    def run(self):
        self.stop_at_start()
        self.event_set_stop.set()
        self.block_until_arrived_at_start()
        self.control_at_start()
        self.event_at_start.set()
        self.block_until_control()
        self.event_at_control.set()

        while self.is_in_control:
            self.check()
            self.continue_past_start()
            self.event_set_continue.set()
            time.sleep(0.01)

        self.event_returning.set()
        # Do not set complete. This should happen inside the base class when run impl finishes.

    def end(self):
        self.end_called = True


def _run_callback(service):
    response = service.AreaCallbackInformation(area_callback_pb2.AreaCallbackInformationRequest(),
                                               None)
    assert response.HasField("info")
    assert len(response.info.required_lease_resources) == 1
    assert response.info.required_lease_resources[0] == "body"

    end_time = seconds_to_timestamp(service.robot.time_sec() + 5)
    response = service.BeginCallback(area_callback_pb2.BeginCallbackRequest(end_time=end_time),
                                     None)
    handler = service.area_callback_region_handler
    assert handler
    assert response.command_id != 0
    assert handler.start_called
    command_id = response.command_id

    request = area_callback_pb2.UpdateCallbackRequest(command_id=101)
    response = service.UpdateCallback(request, None)
    assert response.status == area_callback_pb2.UpdateCallbackResponse.STATUS_INVALID_COMMAND_ID

    handler.event_set_stop.wait(0.1)
    request = area_callback_pb2.UpdateCallbackRequest(
        command_id=command_id, stage=area_callback_pb2.UpdateCallbackRequest.STAGE_TO_START)
    response = service.UpdateCallback(request, None)
    assert response.status == area_callback_pb2.UpdateCallbackResponse.STATUS_OK
    assert response.policy.at_start == response.policy.OPTION_STOP

    request = area_callback_pb2.UpdateCallbackRequest(
        command_id=command_id, stage=area_callback_pb2.UpdateCallbackRequest.STAGE_AT_START)
    response = service.UpdateCallback(request, None)
    assert response.status == area_callback_pb2.UpdateCallbackResponse.STATUS_OK
    handler.event_at_start.wait(0.5)

    request = area_callback_pb2.UpdateCallbackRequest(
        command_id=command_id, stage=area_callback_pb2.UpdateCallbackRequest.STAGE_AT_START)
    response = service.UpdateCallback(request, None)
    assert response.status == area_callback_pb2.UpdateCallbackResponse.STATUS_OK
    assert response.policy.at_start == response.policy.OPTION_CONTROL

    lease = lease_pb2.Lease(resource="body", sequence=[1])
    request = area_callback_pb2.BeginControlRequest(leases=[lease], command_id=command_id + 101)
    response = service.BeginControl(request, None)
    assert response.status == area_callback_pb2.BeginControlResponse.STATUS_INVALID_COMMAND_ID

    lease = lease_pb2.Lease(resource="mobility", sequence=[1])
    request = area_callback_pb2.BeginControlRequest(leases=[lease], command_id=command_id)
    response = service.BeginControl(request, None)
    assert response.status == area_callback_pb2.BeginControlResponse.STATUS_MISSING_LEASE_RESOURCES

    # Inject a newer lease into the lease validator and make sure it fails.
    new_lease = lease_pb2.Lease(resource="body", sequence=[2])
    service._lease_validator.test_and_set_active_lease(new_lease, allow_super_leases=False)
    old_lease = lease_pb2.Lease(resource="body", sequence=[1])
    request = area_callback_pb2.BeginControlRequest(leases=[old_lease], command_id=command_id)
    response = service.BeginControl(request, None)
    assert response.status == area_callback_pb2.BeginControlResponse.STATUS_LEASE_ERROR

    handler.is_in_control = True
    lease = lease_pb2.Lease(resource="body", sequence=[3])
    request = area_callback_pb2.BeginControlRequest(leases=[lease], command_id=command_id)
    response = service.BeginControl(request, None)
    assert response.status == area_callback_pb2.BeginControlResponse.STATUS_OK

    handler.event_at_control.wait(0.5)
    handler.event_set_continue.wait(0.5)
    end_time = seconds_to_timestamp(service.robot.time_sec() + 5)
    request = area_callback_pb2.UpdateCallbackRequest(command_id=command_id, end_time=end_time)
    response = service.UpdateCallback(request, None)
    assert response.policy.at_start == response.policy.OPTION_CONTINUE

    handler.is_in_control = False
    handler.event_returning.wait(0.5)
    time.sleep(0.01)  # Let the returning code set complete.
    request = area_callback_pb2.UpdateCallbackRequest(command_id=command_id)
    response = service.UpdateCallback(request, None)
    assert response.HasField("complete")

    request = area_callback_pb2.EndCallbackRequest(command_id=command_id + 101)
    response = service.EndCallback(request, None)
    assert response.status == area_callback_pb2.EndCallbackResponse.STATUS_INVALID_COMMAND_ID

    request = area_callback_pb2.EndCallbackRequest(command_id=command_id)
    response = service.EndCallback(request, None)
    assert response.status == area_callback_pb2.EndCallbackResponse.STATUS_OK
    assert handler.end_called


@pytest.fixture
def area_callback_service_test_impl():
    mock_lease = MockLeaseClient(should_throw=False)
    mock_robot = MockRobot(mock_lease)
    config = AreaCallbackServiceConfig("service-name", required_lease_resources=["body"],
                                       log_begin_callback_data=False)
    service = AreaCallbackServiceServicer(mock_robot, config, AreaCallbackRegionHandlerImpl)
    yield service
    service.Shutdown()


@pytest.mark.timeout(10)
def test_basic_callback(area_callback_service_test_impl):
    _run_callback(area_callback_service_test_impl)
    _run_callback(area_callback_service_test_impl)


@pytest.mark.timeout(10)
def test_wait_at_start_ends(area_callback_service_test_impl):
    """Make sure that ending from a block_until_arrived_at_start works"""

    def run(service):
        end_time = seconds_to_timestamp(service.robot.time_sec() + 5)
        response = service.BeginCallback(area_callback_pb2.BeginCallbackRequest(end_time=end_time),
                                         None)
        handler = service.area_callback_region_handler
        assert handler
        assert response.command_id != 0
        assert handler.start_called
        command_id = response.command_id

        handler.event_set_stop.wait(0.1)
        request = area_callback_pb2.UpdateCallbackRequest(
            command_id=command_id, stage=area_callback_pb2.UpdateCallbackRequest.STAGE_TO_START)
        response = service.UpdateCallback(request, None)
        assert response.status == area_callback_pb2.UpdateCallbackResponse.STATUS_OK
        assert response.policy.at_start == response.policy.OPTION_STOP

        request = area_callback_pb2.EndCallbackRequest(command_id=command_id)
        response = service.EndCallback(request, None)
        assert response.status == area_callback_pb2.EndCallbackResponse.STATUS_OK

    run(area_callback_service_test_impl)
    run(area_callback_service_test_impl)


@pytest.mark.timeout(10)
def test_wait_for_control_ends(area_callback_service_test_impl):
    """Make sure that ending from a block_until_control works"""

    def run(service):
        end_time = seconds_to_timestamp(service.robot.time_sec() + 5)
        response = service.BeginCallback(area_callback_pb2.BeginCallbackRequest(end_time=end_time),
                                         None)
        handler = service.area_callback_region_handler
        assert handler
        assert response.command_id != 0
        assert handler.start_called
        command_id = response.command_id

        request = area_callback_pb2.UpdateCallbackRequest(
            command_id=command_id, stage=area_callback_pb2.UpdateCallbackRequest.STAGE_AT_START)
        response = service.UpdateCallback(request, None)
        assert response.status == area_callback_pb2.UpdateCallbackResponse.STATUS_OK
        handler.event_at_start.wait(0.5)

        request = area_callback_pb2.UpdateCallbackRequest(
            command_id=command_id, stage=area_callback_pb2.UpdateCallbackRequest.STAGE_AT_START)
        response = service.UpdateCallback(request, None)
        assert response.status == area_callback_pb2.UpdateCallbackResponse.STATUS_OK
        assert response.policy.at_start == response.policy.OPTION_CONTROL

        request = area_callback_pb2.EndCallbackRequest(command_id=command_id)
        response = service.EndCallback(request, None)
        assert response.status == area_callback_pb2.EndCallbackResponse.STATUS_OK

    run(area_callback_service_test_impl)
    run(area_callback_service_test_impl)


@pytest.mark.timeout(10)
def test_expired_end_times(area_callback_service_test_impl):
    service = area_callback_service_test_impl
    end_time = seconds_to_timestamp(service.robot.time_sec() - 1)
    response = service.BeginCallback(area_callback_pb2.BeginCallbackRequest(end_time=end_time),
                                     None)
    assert response.command_id == 0
    assert response.status == area_callback_pb2.BeginCallbackResponse.STATUS_EXPIRED_END_TIME

    end_time = seconds_to_timestamp(service.robot.time_sec() + 5)
    response = service.BeginCallback(area_callback_pb2.BeginCallbackRequest(end_time=end_time),
                                     None)
    assert response.command_id != 0
    assert response.status == area_callback_pb2.BeginCallbackResponse.STATUS_OK

    time.sleep(0.5)
    command_id = response.command_id
    end_time = seconds_to_timestamp(service.robot.time_sec() - 1)
    request = area_callback_pb2.UpdateCallbackRequest(command_id=command_id, end_time=end_time)
    response = service.UpdateCallback(request, None)
    assert response.status == area_callback_pb2.UpdateCallbackResponse.STATUS_EXPIRED_END_TIME

    request = area_callback_pb2.EndCallbackRequest(command_id=command_id)
    response = service.EndCallback(request, None)


class AreaCallbackServiceRegionHandlerThrows(AreaCallbackRegionHandlerBase):

    def begin(self, request):
        return area_callback_pb2.BeginCallbackResponse.STATUS_OK

    def run(self):
        raise Exception("User run impl threw an exception.")

    def end(self):
        pass


def _run_callback_throws(service):
    end_time = seconds_to_timestamp(service.robot.time_sec() + 2)
    response = service.BeginCallback(area_callback_pb2.BeginCallbackRequest(end_time=end_time),
                                     None)
    assert response.command_id != 0
    command_id = response.command_id

    # Make sure the run impl has time to throw.
    now = time.time()
    while time.time() < now + 1:
        request = area_callback_pb2.UpdateCallbackRequest(command_id=command_id)
        response = service.UpdateCallback(request, None)
        assert response.status == area_callback_pb2.UpdateCallbackResponse.STATUS_OK
        if response.HasField("error"):
            break
        time.sleep(0.01)
    assert response.HasField("error")

    request = area_callback_pb2.EndCallbackRequest(command_id=command_id)
    service.EndCallback(request, None)


@pytest.fixture
def area_callback_service_run_throws():
    mock_lease = MockLeaseClient(should_throw=False)
    mock_robot = MockRobot(mock_lease)
    config = AreaCallbackServiceConfig("service-name", required_lease_resources=["body"])
    service = AreaCallbackServiceServicer(mock_robot, config,
                                          AreaCallbackServiceRegionHandlerThrows)
    return service


@pytest.mark.timeout(10)
def test_callback_throws(area_callback_service_run_throws):
    _run_callback_throws(area_callback_service_run_throws)
    _run_callback_throws(area_callback_service_run_throws)


class AreaCallbackRegionHandlerRunForever(AreaCallbackRegionHandlerBase):

    def __init__(self, config, robot):
        super().__init__(config, robot)
        self.shutdown = False

    def begin(self, request):
        return area_callback_pb2.BeginCallbackResponse.STATUS_OK

    def run(self):
        while not self.shutdown:
            time.sleep(0.05)

    def end(self):
        pass


@pytest.fixture
def area_callback_service_run_forever():
    mock_lease = MockLeaseClient(should_throw=False)
    mock_robot = MockRobot(mock_lease)
    config = AreaCallbackServiceConfig("service-name", required_lease_resources=["body"])
    service = AreaCallbackServiceServicer(mock_robot, config, AreaCallbackRegionHandlerRunForever)
    return service


@pytest.mark.timeout(20)
def test_callback_run_forever(area_callback_service_run_forever):
    service = area_callback_service_run_forever
    service._shutdown_timeout = 0.5
    end_time = seconds_to_timestamp(service.robot.time_sec() + 5)
    response = service.BeginCallback(area_callback_pb2.BeginCallbackRequest(end_time=end_time),
                                     None)
    assert response.command_id != 0

    command_id = response.command_id
    request = area_callback_pb2.EndCallbackRequest(command_id=command_id)
    response = service.EndCallback(request, None)
    assert response.status == area_callback_pb2.EndCallbackResponse.STATUS_SHUTDOWN_CALLBACK_FAILED

    # Calling EndCallback multiple times not a supported workflow,
    # but required so test does not hang.
    service.area_callback_region_handler.shutdown = True
    request = area_callback_pb2.EndCallbackRequest(command_id=command_id)
    response = service.EndCallback(request, None)
    assert response.status == area_callback_pb2.EndCallbackResponse.STATUS_OK


@pytest.mark.timeout(10)
def test_callback_end_early(area_callback_service_test_impl):
    """If a callback ends early via end_callback, make sure it actually ends."""

    def run_service(service):
        end_time = seconds_to_timestamp(service.robot.time_sec() + 5)
        response = service.BeginCallback(area_callback_pb2.BeginCallbackRequest(end_time=end_time),
                                         None)
        handler = service.area_callback_region_handler
        assert handler
        assert response.command_id != 0
        assert handler.start_called
        command_id = response.command_id

        response = service.EndCallback(area_callback_pb2.EndCallbackRequest(command_id=command_id),
                                       None)
        assert response.status == response.STATUS_OK

    run_service(area_callback_service_test_impl)
    area_callback_service_test_impl.robot.time = 100
    run_service(area_callback_service_test_impl)


@pytest.mark.timeout(10)
def test_callback_end_timeout(area_callback_service_test_impl):
    """If a callback ends early via a timeout, make sure it actually ends."""

    def run_service(service):
        start_time = service.robot.time_sec()
        end_time = seconds_to_timestamp(start_time + 5)
        response = service.BeginCallback(area_callback_pb2.BeginCallbackRequest(end_time=end_time),
                                         None)
        handler = service.area_callback_region_handler
        assert handler
        assert response.command_id != 0
        assert handler.start_called
        command_id = response.command_id

        service.robot.time = start_time + 10
        # Wait for the callback to time out and set an error.
        # If this doesn't happen, we'll hit the pytest timeout.
        while not handler.update_response.HasField('error'):
            time.sleep(0.1)

        # Make a new update call and we should get back the correct error.
        end_time = seconds_to_timestamp(start_time + 15)
        response = service.UpdateCallback(
            area_callback_pb2.UpdateCallbackRequest(command_id=command_id, end_time=end_time), None)
        assert response.error.error == area_callback_pb2.UpdateCallbackResponse.Error.ERROR_TIMED_OUT

    run_service(area_callback_service_test_impl)
    area_callback_service_test_impl.robot.time = 100
    run_service(area_callback_service_test_impl)


def test_bad_handlers_init():
    """Test that calling blocking functions in init breaks"""
    mock_lease = MockLeaseClient(should_throw=False)
    mock_robot = MockRobot(mock_lease)
    conf = AreaCallbackServiceConfig("service-name", required_lease_resources=["body"])

    class BadHandlerInit(AreaCallbackRegionHandlerBase):
        """Calls the specified function in __init__()"""

        def __init__(self, config, robot, func_name):
            super().__init__(config, robot)
            getattr(self, func_name)()

    with pytest.raises(IncorrectUsage):
        BadHandlerInit(conf, mock_robot, 'block_until_control')
    with pytest.raises(IncorrectUsage):
        BadHandlerInit(conf, mock_robot, 'block_until_arrived_at_start')
    with pytest.raises(IncorrectUsage):
        BadHandlerInit(conf, mock_robot, 'block_until_arrived_at_end')


def test_bad_handlers_begin():
    """Test that calling blocking functions in begin() breaks"""
    mock_lease = MockLeaseClient(should_throw=False)
    mock_robot = MockRobot(mock_lease)
    conf = AreaCallbackServiceConfig("service-name", required_lease_resources=["body"])

    class BadHandlerBegin(AreaCallbackRegionHandlerBase):
        """Calls the specified function in begin()"""

        def __init__(self, config, robot, func_name):
            super().__init__(config, robot)
            self.func = getattr(self, func_name)

        def begin(self, request):
            self.func()
            return area_callback_pb2.BeginCallbackResponse.STATUS_OK

    req = area_callback_pb2.BeginCallbackRequest()
    handler = BadHandlerBegin(conf, mock_robot, 'block_until_control')
    with pytest.raises(IncorrectUsage):
        handler.begin(req)
    handler = BadHandlerBegin(conf, mock_robot, 'block_until_arrived_at_start')
    with pytest.raises(IncorrectUsage):
        handler.begin(req)
    handler = BadHandlerBegin(conf, mock_robot, 'block_until_arrived_at_end')
    with pytest.raises(IncorrectUsage):
        handler.begin(req)
