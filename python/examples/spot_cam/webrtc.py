# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import asyncio
import base64
import json
import logging
import sys
import threading

from aiortc import (
    RTCConfiguration,
    RTCPeerConnection,
    RTCSessionDescription,
    MediaStreamTrack,
)
import requests

from bosdyn.client.command_line import (Command, Subcommands)
from webrtc_client import WebRTCClient

logging.basicConfig(level=logging.DEBUG, filename='webrtc.log', filemode='a+')
STDERR = logging.getLogger('stderr')

class InterceptStdErr:
    _stderr = sys.stderr

    def __init__(self):
        pass

    def write(self, data):
        STDERR.error(data)

sys.stderr = InterceptStdErr()

class WebRTCCommands(Subcommands):
    """Commands related to the Spot CAM's WebRTC service"""

    NAME = 'webrtc'

    def __init__(self, subparsers, command_dict):
        super(WebRTCCommands, self).__init__(subparsers, command_dict, [
            WebRTCSaveCommand,
        ])


class WebRTCSaveCommand(Command):
    """Save webrtc stream as a sequence of images"""

    NAME = 'save'

    def __init__(self, subparsers, command_dict):
        super(WebRTCSaveCommand, self).__init__(subparsers, command_dict)
        self._parser.add_argument('track', default='video', const='video', nargs='?',
                                  choices=['video'])
        self._parser.add_argument('--sdp-filename', default='h264.sdp', help='File being streamed from WebRTC server')
        self._parser.add_argument('--sdp-port', default=31102, help='SDP port of WebRTC server')
        self._parser.add_argument('--cam-ssl-cert', default=None, help="Path to Spot CAM's client cert to verify against Spot CAM server")
        self._parser.add_argument('--dst-prefix', default='h264.sdp', help='Filename prefix to prepend to all output data')
        self._parser.add_argument('--count', type=int, default=1, help='Number of images to save.  0 is useful for streaming without saving.')

    def _run(self, robot, options):
        if not options.cam_ssl_cert:
          options.cam_ssl_cert = False

        shutdown_flag = threading.Event()
        webrtc_thread = threading.Thread(
            target=start_webrtc,
            args=[shutdown_flag, options],
            daemon=True
        )
        webrtc_thread.start()

        try:
            webrtc_thread.join()
            print('Successfully saved webrtc images to local directory.')
        except KeyboardInterrupt:
            shutdown_flag.set()
            webrtc_thread.join(timeout=3.0)

# WebRTC must be in its own thread with its own event loop.
def start_webrtc(shutdown_flag, options):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    config = RTCConfiguration(iceServers=[])
    client = WebRTCClient(options.hostname,
                          options.username,
                          options.password,
                          options.sdp_port,
                          options.sdp_filename,
                          options.cam_ssl_cert,
                          config)

    asyncio.gather(client.start(),
                   process_frame(client, options, shutdown_flag),
                   monitor_shutdown(shutdown_flag, client))
    loop.run_forever()

# Frame processing occurs; otherwise it waits.
async def process_frame(client, options, shutdown_flag):
    count = 0
    while asyncio.get_event_loop().is_running():
        try:
            frame = await client.video_frame_queue.get()

            if options.count == 0:
                continue

            frame.to_image().save(f'{options.dst_prefix}-{count}.jpg')
            count += 1
    
            if count >= options.count:
                break
        except:
            pass

    shutdown_flag.set()

# Flag must be monitored in a different coroutine and sleep to allow frame
# processing to occur.
async def monitor_shutdown(shutdown_flag, client):
    while not shutdown_flag.is_set():
        await asyncio.sleep(1.0)

    await client.pc.close()
    asyncio.get_event_loop().stop()
