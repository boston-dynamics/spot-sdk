# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from bosdyn.api import alerts_pb2, signals_pb2

# Define LTE signal quality specification
signal_quality_spec = signals_pb2.SignalSpec()
signal_quality_spec.info.name = "Signal quality"
signal_quality_spec.info.description = "LTE Signal Quality"
signal_quality_spec.info.order = 0
signal_quality_spec.sensor.resolution.value = 1
signal_quality_spec.sensor.units.name = "%"
signal_quality_alert = signals_pb2.AlertConditionSpec()
signal_quality_alert.min = 80.0
signal_quality_alert.alert_data.severity = alerts_pb2.AlertData.SeverityLevel.SEVERITY_LEVEL_WARN
signal_quality_spec.alerts.append(signal_quality_alert)

# Define SINR specification
sinr_spec = signals_pb2.SignalSpec()
sinr_spec.info.name = "SINR"
sinr_spec.info.description = "Signal to Interference plus Noise Ratio: comprehensive metric that measures strength of the wanted signal compared to the unwanted interference and noise."
sinr_spec.info.order = 1
sinr_spec.sensor.resolution.value = 0.1
sinr_spec.sensor.units.name = "dB"
sinr_alert = signals_pb2.AlertConditionSpec()
sinr_alert.min = 13.0
sinr_alert.alert_data.severity = alerts_pb2.AlertData.SeverityLevel.SEVERITY_LEVEL_WARN
sinr_spec.alerts.append(sinr_alert)

# Define RSRP specification
rsrp_spec = signals_pb2.SignalSpec()
rsrp_spec.info.name = "RSRP"
rsrp_spec.info.description = "Reference Signal Received Power: measures the power level of the serving cell's reference signals at the receiver. "
rsrp_spec.info.order = 2
rsrp_spec.sensor.resolution.value = 1
rsrp_spec.sensor.units.name = "dBm"
rsrp_alert = signals_pb2.AlertConditionSpec()
rsrp_alert.min = -90.0
rsrp_alert.alert_data.severity = alerts_pb2.AlertData.SeverityLevel.SEVERITY_LEVEL_WARN
rsrp_spec.alerts.append(rsrp_alert)

# Define RSRQ specification
rsrq_spec = signals_pb2.SignalSpec()
rsrq_spec.info.name = "SINR"
rsrq_spec.info.description = "Reference Signal Received Quality: measures the quality of the received reference signals."
rsrq_spec.info.order = 3
rsrq_spec.sensor.resolution.value = 1
rsrq_spec.sensor.units.name = "dB"
rsrq_alert = signals_pb2.AlertConditionSpec()
rsrq_alert.min = -15.0
rsrq_alert.alert_data.severity = alerts_pb2.AlertData.SeverityLevel.SEVERITY_LEVEL_WARN
rsrq_spec.alerts.append(rsrq_alert)

# Define signal ids (also data keys in our case).
SIGNAL_QUALITY_ID = "Signal Quality"
SINR_ID = "SINR"
RSRP_ID = "RSRP"
RSRQ_ID = "RSRQ"


def build_signals(data):
    """Build a dictionary of signals related to modem stats."""
    # Extract the values from the modem fetched data
    sQ = data['signalQuality']
    sinr = int(data['sinr']) / 12.5  # convert [0 250] scale into [0 20] for dB conversion
    rsrp = data['rsrp']
    rsrq = data['rsrq']

    sQ_signal = signals_pb2.Signal()
    sQ_signal.signal_spec.CopyFrom(signal_quality_spec)
    sQ_signal.signal_data.data.int = int(sQ)

    sinr_signal = signals_pb2.Signal()
    sinr_signal.signal_spec.CopyFrom(sinr_spec)
    sinr_signal.signal_data.data.double = sinr

    rsrp_signal = signals_pb2.Signal()
    rsrp_signal.signal_spec.CopyFrom(rsrp_spec)
    rsrp_signal.signal_data.data.int = int(rsrp)

    rsrq_signal = signals_pb2.Signal()
    rsrq_signal.signal_spec.CopyFrom(rsrq_spec)
    rsrq_signal.signal_data.data.int = int(rsrq)

    return {
        SIGNAL_QUALITY_ID: sQ_signal,
        SINR_ID: sinr_signal,
        RSRP_ID: rsrp_signal,
        RSRQ_ID: rsrq_signal
    }
