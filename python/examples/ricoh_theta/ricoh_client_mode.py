# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Configures a ricoh theta camera for client mode.

Before running this script, wirelessly connect your personal computer
to the ricoh theta camera. This script will specify the client mode settings using
the default parameters specified in the ricoh_theta.py script. Once complete, click
the wireless button on the ricoh theta to enable client mode.

Example Usage:

python3 ricoh_client_mode.py --theta-ssid THETAYL00196843 --wifi-ssid WIFI_SSID --wifi-password WIFI_PASSWORD

"""

import argparse
import sys

from ricoh_theta import Theta


def connect(options):
    """Uses the ricoh_theta.py script to connect to an access point"""
    camera = Theta(theta_ssid=options.theta_ssid, theta_pw=options.theta_password,
                   client_mode=False, show_state_at_init=True)
    camera.connectToAP(ap_ssid=options.wifi_ssid, ap_pw=options.wifi_password,
                       ap_sec=options.security)
    if options.disable_sleep_mode:
        camera.sleepMode(enabled=False)


def main(argv):
    """Collects command line arguments to enable client mode"""
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--theta-ssid', default=None, required=True, help='ricoh theta ssid')
    parser.add_argument('--theta-password', default=None,
                        help='ricoh theta password (leave empty to use default password)')
    parser.add_argument('--wifi-ssid', help='WiFi network SSID/name for desired access point',
                        required=True)
    parser.add_argument('--wifi-password', help='WiFi network password', required=True)
    parser.add_argument('--security', default='WPA/WPA2 PSK',
                        help='WiFi security type: "none", "WEP", "WPA/WPA2 PSK"')
    parser.add_argument('--disable-sleep-mode', action='store_true',
                        help='Disables the Ricoh theta from automatically sleeping.')
    options = parser.parse_args(argv)

    connect(options)


if __name__ == '__main__':
    main(sys.argv[1:])
