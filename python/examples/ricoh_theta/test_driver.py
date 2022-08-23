# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
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

# UPDATE ME!! This should be the SSID for the Ricoh Theta that is attempting to be queried.
SSID = 'THETAYN14103427'

# set client_mode=True to use client mode network settings
camera = Theta(theta_ssid=SSID, client_mode=False, show_state_at_init=False)
camera.showState()
camera.takePicture()
camera.downloadLastImage()

gen = camera.yieldLivePreview()
jpg = next(gen)
with open("ricoh_theta_live_preview.jpg", 'wb') as f:
    f.write(jpg)
gen.close()

# Below are some additional user functions for testing:
# camera.setMode(client_mode=False)
# camera.sleepMode(enabled=None, delay=180)
# camera.showState()
# camera.takePicture()
# camera.listFiles(1)
# camera.downloadLastImage(directory="")
# camera.previewLastImage()
# camera.connectToAP(ap_ssid=None, ap_sec="WPA/WPA2 PSK", ap_pw=None)
# camera.getCaptureParameters()
# camera.getFileFormat()
# camera.getLastImage()
