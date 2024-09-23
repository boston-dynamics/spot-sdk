# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Setup a Ublox F9R for use with the GPS Listener extension. Configures the output rate to be 2Hz and
enables the GGA, GST, and ZDA NMEA messages.

Requires the following pip dep:
    pyubx2>=1.2.43
"""

from pyubx2 import SET_LAYER_BBR, SET_LAYER_FLASH, SET_LAYER_RAM, TXN_NONE, UBXMessage
from serial import Serial

F9R_DEV = '/dev/ublox_f9r'
F9R_BAUD = 38400
TIMEOUT = 3  # seconds

if __name__ == "__main__":
    layers = SET_LAYER_RAM | SET_LAYER_BBR | SET_LAYER_FLASH
    transaction = TXN_NONE
    cfgData = [
        # Output data at 2 Hz (every 500ms).
        ("CFG_RATE_MEAS", 500),
        # Enable GGA, GST, and ZDA messages.
        ("CFG_MSGOUT_NMEA_ID_GGA_USB", 1),
        ("CFG_MSGOUT_NMEA_ID_GST_USB", 1),
        ("CFG_MSGOUT_NMEA_ID_ZDA_USB", 1),
        # Disable the default enabled messages.
        ("CFG_MSGOUT_NMEA_ID_GSA_USB", 0),
        ("CFG_MSGOUT_NMEA_ID_VTG_USB", 0),
        ("CFG_MSGOUT_NMEA_ID_GSV_USB", 0),
        ("CFG_MSGOUT_NMEA_ID_GLL_USB", 0),
        ("CFG_MSGOUT_NMEA_ID_RMC_USB", 0),
        # Disable sensor fusion, use GNSS only.
        ("CFG-SFCORE-USE_SF", 0),
    ]
    msg = UBXMessage.config_set(layers, transaction, cfgData)
    with Serial(F9R_DEV, F9R_BAUD, timeout=TIMEOUT) as stream:
        stream.write(msg.serialize())
