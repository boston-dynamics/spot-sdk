# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from bosdyn.api.alerts_pb2 import AlertData
from bosdyn.api.data_acquisition_pb2 import LiveDataResponse
from bosdyn.client.signals_helpers import (build_capability_live_data, build_live_data_response,
                                           build_simple_signal, get_data)

# Prepare test data.
test_signal_1 = build_simple_signal("Test Signal Name 1", 10.0, "%")
test_signal_2 = build_simple_signal("Test Signal Name 2", 20.0, "%", 30.0, 40.0)
test_signals = {"test_signal_1": test_signal_1, "test_signal_2": test_signal_2}


def test_building_live_data_response():
    # Build live data response using helpers.
    test_capability_live_data = build_capability_live_data(test_signals, "test")
    test_response = build_live_data_response([test_capability_live_data])

    # Confirm response is in expected format.
    assert len(test_response.live_data) == 1
    assert test_response.live_data[0].name == "test"
    assert test_response.live_data[0].status == LiveDataResponse.CapabilityLiveData.Status.STATUS_OK
    assert len(test_response.live_data[0].signals) == 2
    assert "bad_key" not in test_response.live_data[0].signals
    assert "test_signal_1" in test_response.live_data[0].signals
    response_signal_1 = test_response.live_data[0].signals["test_signal_1"]
    assert response_signal_1 == test_signal_1
    assert response_signal_1.signal_spec.info.name == "Test Signal Name 1"
    assert response_signal_1.signal_spec.sensor.units.name == "%"
    assert response_signal_1.signal_data.data.double == 10.0
    assert get_data(response_signal_1.signal_data) == 10.0
    assert "test_signal_2" in test_response.live_data[0].signals
    response_signal_2 = test_response.live_data[0].signals["test_signal_2"]
    assert response_signal_2 == test_signal_2
    assert response_signal_2.signal_spec.info.name == "Test Signal Name 2"
    assert response_signal_2.signal_spec.sensor.units.name == "%"
    assert response_signal_2.signal_data.data.double == 20.0
    assert len(response_signal_2.signal_spec.alerts) == 2
    max_warning_spec = response_signal_2.signal_spec.alerts[0]
    assert max_warning_spec.max == 30.0
    assert max_warning_spec.alert_data.severity == AlertData.SeverityLevel.SEVERITY_LEVEL_WARN
    max_critical_spec = response_signal_2.signal_spec.alerts[1]
    assert max_critical_spec.max == 40.0
    assert max_critical_spec.alert_data.severity == AlertData.SeverityLevel.SEVERITY_LEVEL_CRITICAL


