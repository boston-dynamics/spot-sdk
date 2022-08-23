# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from . import (audio, compositor, health, lighting, media_log, network, power, ptz, streamquality,
               version)


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
