# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Setup a Bynav C2 M2X for use with the GPS Listener extension. Configures the output rate to be 2Hz
and enables the GGA, GST, and ZDA NMEA messages.
"""

from serial import Serial

C2_M2X_DEV = "/dev/bynav_c2_m2x1"
C2_M2X_BAUD = 115200
TIMEOUT = 3  # seconds

if __name__ == "__main__":
    NMEA_CONFIG_FMT = "log com3 {} ontime 0.5\n"
    CONFIG_CMDS = [
        # Disable all output.
        "unlogall com3\n",
        # Set the RTK type to Rover.
        "rtktype rover\n",
        # Configure the NMEA GGA GST and ZDA messages to output at 2Hz.
        NMEA_CONFIG_FMT.format("gpgga"),
        NMEA_CONFIG_FMT.format("gpgst"),
        NMEA_CONFIG_FMT.format("gpzda"),
        # Save the configuration to flash.
        "saveconfig\n",
    ]
    with Serial(C2_M2X_DEV, C2_M2X_BAUD, timeout=TIMEOUT) as stream:
        for config_cmd in CONFIG_CMDS:
            stream.write(bytes(config_cmd, "utf-8"))
