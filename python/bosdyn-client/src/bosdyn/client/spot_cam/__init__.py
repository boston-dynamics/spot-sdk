# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from . import audio
from . import compositor
from . import health
from . import lighting
from . import media_log
from . import network
from . import power
from . import ptz
from . import streamquality
from . import version

CLIENTS = [
    audio.AudioClient,
    compositor.CompositorClient,
    health.HealthClient,
    lighting.LightingClient,
    media_log.MediaLogClient,
    network.NetworkClient,
    power.PowerClient,
    ptz.PtzClient,
    streamquality.StreamQualityClient,
    version.VersionClient
]

def register_all_service_clients(sdk):
    for client in CLIENTS:
        sdk.register_service_client(client)
