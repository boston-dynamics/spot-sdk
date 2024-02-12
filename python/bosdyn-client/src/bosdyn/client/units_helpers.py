# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Helpers for working with units.proto."""

from bosdyn.api import units_pb2

TEMPERATURE_NAMES = {
    units_pb2.TEMPERATURE_KELVIN: "K",
    units_pb2.TEMPERATURE_CELSIUS: "°C",
    units_pb2.TEMPERATURE_FAHRENHEIT: "°F"
}

PRESSURE_NAMES = {
    units_pb2.PRESSURE_PSI: "psi",
    units_pb2.PRESSURE_KPA: "kPa",
    units_pb2.PRESSURE_BAR: "bar"
}


def units_to_string(units: units_pb2.Units):
    """Gets the units in string form to use for display. Ex: TEMPERATURE_KELVIN = "K"

    Args:
        units(Units): Populate units message.

    Returns:
        String
    """
    if units.HasField("temp"):
        return TEMPERATURE_NAMES.get(units.temp, "")
    if units.HasField("press"):
        return PRESSURE_NAMES.get(units.press, "")
    if units.HasField("name"):
        return units.name
    return ""
