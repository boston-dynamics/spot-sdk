# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Use for testing ricoh_theta.py.

Before running this script, wirelessly connect your personal computer
to the ricoh theta camera and adjust the theta_ssid for your camera.

Example Usage:

python3 test_driver.py

"""

from ricoh_theta import Theta

# set client_mode=True to use client mode network settings
camera = Theta(theta_ssid='THETAYL00196843', client_mode=False)
camera.showState()

camera.takePicture()

# Below are some additional user functions for testing:
# camera.setMode(client_mode=False)
# camera.sleepMode(enabled=None, delay=180)
# camera.showState()
# camera.takePicture()
# camera.listFiles(1)
# camera.downloadLastImage(directory="")
# camera.downloadMissionImages(directory="")
# camera.previewLastImage()
# camera.connectToAP(ap_ssid=None, ap_sec="WPA/WPA2 PSK", ap_pw=None)
