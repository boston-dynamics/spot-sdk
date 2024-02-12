# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Data Acquisition plugin for saving a file to the robot.
"""
import argparse
import asyncio
import logging
import os
import pathlib
import sys

from aiortc import RTCConfiguration
from aiortc.contrib.media import MediaRecorder
from webrtc_client import WebRTCClient

import bosdyn.client.util
from bosdyn.api import data_acquisition_pb2, data_acquisition_plugin_service_pb2_grpc
from bosdyn.client.data_acquisition_plugin_service import Capability, DataAcquisitionPluginService
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.server_util import GrpcServiceRunner
from bosdyn.client.util import setup_logging

_LOGGER = logging.getLogger(__name__)
STDERR = logging.getLogger("stderr")

DIRECTORY_NAME = "data-acquisition-save-video-plugin"
AUTHORITY = "data-acquisition-save-video-plugin"
CHANNEL_NAME = "data"

TRACK_PARAM_NAME = "Track"
TRACK_PARAM_NAME_VIDEO = "video"
TRACK_PARAM_NAME_AUDIO = "audio"

# Constants related to timeout on recording.
PAUSE_NAME = "Time"
PAUSE_DURATION = 5.0  # Default time to record (in seconds).
PAUSE_TIMEOUT = 30.0  # Maximum time to record (seconds).

RETRIES = 2


class VideoAdapter:
    """Basic plugin for taking videos from rtc stream"""

    def __init__(self, sdk_robot, hostname):
        self.client = sdk_robot.ensure_client(RobotStateClient.default_service_name)
        self._file_data = None
        self._file_extension = None
        self.data = None
        self.robot = sdk_robot
        self.cam_ssl_cert = None
        self.hostname = hostname

    # Call the record command but do it recursively incase the file is not made
    def record(self, file_prefix, file_path, ttime, track, retries, sdp_port=31102):
        # Suppress all exceptions and log them instead.
        sys.stderr = InterceptStdErr()
        if not self.cam_ssl_cert:
            self.cam_ssl_cert = False

        recorder = MediaRecorder(file_path)

        asyncio.run(
            record_webrtc(
                recorder,
                track,
                self.robot.user_token,
                self.cam_ssl_cert,
                ttime,
                self.hostname,
                sdp_port,
                file_prefix,
            ))

        # Read the data from the file created
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                self._file_data = f.read()
            os.remove(file_path)
        elif retries > 0:
            print("File not found")
            self.record(file_prefix, file_path, ttime, track, retries - 1)

    def get_video_data(self, request, store_helper):
        """Save the file data to the data store."""
        file_prefix = "h264.sdp"

        # Pull the custom parameters from the request
        params = request.acquisition_requests.data_captures[0].custom_params.values
        track = params.get(TRACK_PARAM_NAME).string_value.value
        video_time = params.get(PAUSE_NAME).double_value.value

        # Create the file path based on track type
        if track == "video":
            sdp_filename = f"{file_prefix}.mp4"
        else:
            sdp_filename = f"{file_prefix}.wav"
        self.record(file_prefix, sdp_filename, video_time, track, RETRIES)

        self._file_extension = pathlib.Path(sdp_filename).suffix
        data_id = data_acquisition_pb2.DataIdentifier(action_id=request.action_id,
                                                      channel=CHANNEL_NAME)
        store_helper.store_data(self._file_data, data_id, file_extension=self._file_extension)
        store_helper.state.set_status(data_acquisition_pb2.GetStatusResponse.STATUS_SAVING)


def make_service(robot, hostname):
    capability = Capability(
        name="data",
        description="Loading Data from RTC Stream",
        channel_name=CHANNEL_NAME,
    )

    # Custom parameters on UI
    custom_params = capability.custom_params

    track_params = custom_params.specs[TRACK_PARAM_NAME].spec.string_spec
    track_params.default_value = TRACK_PARAM_NAME_VIDEO
    track_params.editable = False
    track_params.options.extend([TRACK_PARAM_NAME_VIDEO, TRACK_PARAM_NAME_AUDIO])

    duration_params = custom_params.specs[PAUSE_NAME].spec.double_spec
    duration_params.default_value.value = PAUSE_DURATION
    duration_params.min_value.value = PAUSE_DURATION
    duration_params.max_value.value = PAUSE_TIMEOUT

    adapter = VideoAdapter(robot, hostname)
    return DataAcquisitionPluginService(robot, [capability], adapter.get_video_data)


def run_service(bosdyn_sdk_robot, port, hostname, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = (
        data_acquisition_plugin_service_pb2_grpc.add_DataAcquisitionPluginServiceServicer_to_server)

    # Instance of the servicer to be run.
    service_servicer = make_service(bosdyn_sdk_robot, hostname)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


# WebRTC must be in its own thread with its own event loop.
async def record_webrtc(recorder, track, token, cam_ssl_cert, video_time, hostname, sdp_port,
                        sdp_filename):
    config = RTCConfiguration(iceServers=[])
    client = WebRTCClient(
        hostname,
        sdp_port,
        sdp_filename,
        cam_ssl_cert,
        token,
        config,
        media_recorder=recorder,
        recorder_type=track,
    )
    await client.start()

    # wait for connection to be established before recording
    while client.pc.iceConnectionState != "completed":
        await asyncio.sleep(0.1)

    # start recording
    await recorder.start()
    try:
        await asyncio.sleep(video_time)
    except KeyboardInterrupt:
        pass
    finally:
        # close everything
        await client.pc.close()
        await recorder.stop()


class InterceptStdErr:
    """Intercept all exceptions and print them to StdErr without interrupting."""

    _stderr = sys.stderr

    def __init__(self):
        pass

    def write(self, data):
        STDERR.error(data)


def main():
    # Define all arguments used by this service.
    import argparse

    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    bosdyn.client.util.add_payload_credentials_arguments(parser)
    bosdyn.client.util.add_service_endpoint_arguments(parser)
    options = parser.parse_args()

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object.
    sdk = bosdyn.client.create_standard_sdk("VideoPlugin")
    robot = sdk.create_robot(options.hostname)
    robot.authenticate_from_payload_credentials(*bosdyn.client.util.get_guid_and_secret(options))

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options.port, options.hostname)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(
        DIRECTORY_NAME,
        DataAcquisitionPluginService.service_type,
        AUTHORITY,
        options.host_ip,
        service_runner.port,
    )

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()


if __name__ == '__main__':
    main()
