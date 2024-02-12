# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Helpers for working with DAQ plugins and signals.proto."""
from bosdyn.api.alerts_pb2 import AlertData
from bosdyn.api.data_acquisition_pb2 import LiveDataResponse
from bosdyn.api.signals_pb2 import AlertConditionSpec, Signal, SignalData, SignalSpec
from bosdyn.client.units_helpers import units_to_string


def build_max_alert_spec(value: float, severity: AlertData.SeverityLevel) -> AlertConditionSpec:
    """Builds a max AlertConditionSpec.

    Args:
        value(float): Max threshold.
        severity(str): Severity of alert.
    Returns:
        AlertConditionSpec
    """
    alert = AlertConditionSpec()
    alert.max = value
    alert.alert_data.severity = severity
    return alert


def build_simple_signal(name: str, value: float, units: str, max_warning: float = None,
                        max_critical: float = None) -> Signal:
    """Builds a simple signal with a float value, string units, and optional max alerts.

    Args:
        name(str): Name of the signal.
        value(float): Signal data value.
        units(str): Simple units.
        max_warning(float): Max warning threshold.
        max_critical(float): Max critical threshold.
    Returns:
        Signal
    """
    # Bundle spec/data together as a signal.
    signal = Signal()

    # Setup signal specification.
    signal_spec = signal.signal_spec
    signal_spec.info.name = name
    signal_spec.sensor.units.name = units
    if max_warning:
        alert_spec_1 = build_max_alert_spec(max_warning,
                                            AlertData.SeverityLevel.SEVERITY_LEVEL_WARN)
        signal_spec.alerts.append(alert_spec_1)
    if max_critical:
        alert_spec_2 = build_max_alert_spec(max_critical,
                                            AlertData.SeverityLevel.SEVERITY_LEVEL_CRITICAL)
        signal_spec.alerts.append(alert_spec_2)

    # Add value to signal data.
    signal.signal_data.data.double = value

    return signal


def build_capability_live_data(signals: dict,
                               capability_name: str) -> LiveDataResponse.CapabilityLiveData:
    """Takes a dictionary of signals and copies them into a CapabilityLiveData message.

    Args:
        signals(dict[str, Signal]): A dictionary of signal id to Signal.
        capability_name(str): The capability name.
    Returns:
        CapabilityLiveData
    """
    capability_live_data = LiveDataResponse.CapabilityLiveData()
    capability_live_data.name = capability_name
    capability_live_data.status = LiveDataResponse.CapabilityLiveData.Status.STATUS_OK
    for signal_id, signal in signals.items():
        capability_live_data.signals[signal_id].CopyFrom(signal)
    return capability_live_data


def build_live_data_response(live_data_capabilities: list) -> LiveDataResponse:
    """Takes a list of CapabilityLiveData and adds them to a LiveDataResponse.

    Args:
        live_data_capabilities(list[LiveDataResponse.CapabilityLiveData]): A list of CapabilityLiveData.
    Returns:
        LiveDataResponse
    """
    response = LiveDataResponse()
    response.live_data.extend(live_data_capabilities)
    return response


def get_data(signal_data: SignalData):
    """Checks type of SignalData and returns the value.

    Args:
        signal_data(SignalData): Signal data.
    Returns:
        The data value.
    """
    return getattr(signal_data.data, signal_data.data.WhichOneof('value'), None)


