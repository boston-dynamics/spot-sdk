# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import asyncio
import base64
import json
import requests
import threading

from aiortc import (
    RTCConfiguration,
    RTCPeerConnection,
    RTCSessionDescription,
    MediaStreamTrack,
)

from bosdyn.client.command_line import (Command, Subcommands)

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
        self._parser.add_argument('--filename', default='h264.sdp', help='File being streamed from WebRTC server')
        self._parser.add_argument('--sdp-port', default=31102, help='SDP port of WebRTC server')
        self._parser.add_argument('--cam-ssl-cert', default=None, help="Path to Spot CAM's client cert to verify against Spot CAM server")
        self._parser.add_argument('--dst-prefix', default='h264.sdp', help='Filename prefix to prepend to all output data')
        self._parser.add_argument('--count', type=int, default=1, help='Number of images to save')

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
        except KeyboardInterrupt:
            shutdown_flag.set()
            webrtc_thread.join(timeout=3.0)

# WebRTC must be in its own thread with its own event loop.
def start_webrtc(shutdown_flag, options):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    config = RTCConfiguration(iceServers=[])
    client = SpotCAMWebRTCClient(options, config)

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

def get_sdp_offer_from_spot_cam(options):
    server_url = f'https://{options.hostname}:{options.sdp_port}/{options.filename}'
    r = requests.get(server_url, verify=options.cam_ssl_cert)
    result = r.json()
    return result['id'], base64.b64decode(result['sdp']).decode()

def send_sdp_answer_to_spot_cam(options, offer_id, sdp_answer):
    server_url = f'https://{options.hostname}:{options.sdp_port}/{options.filename}'

    payload = {'id': offer_id, 'sdp': base64.b64encode(sdp_answer).decode('utf8')}
    r = requests.post(server_url, verify=options.cam_ssl_cert, json=payload)
    if r.status_code != 200:
        raise ValueError(r)

class SpotCAMMediaStreamTrack(MediaStreamTrack):
    def __init__(self, track, queue):
        super().__init__()

        self.track = track
        self.queue = queue

    async def recv(self):
        frame = await self.track.recv()

        await self.queue.put(frame)

        return frame

class SpotCAMWebRTCClient:
    def __init__(self, options, rtc_config):
        self.pc = RTCPeerConnection(configuration=rtc_config)

        self.video_frame_queue = asyncio.Queue()
        self.audio_frame_queue = asyncio.Queue()

        self.options = options

    async def start(self):
        #offer_id = None
        offer_id, sdp_offer = get_sdp_offer_from_spot_cam(self.options)

        @self.pc.on('icegatheringstatechange')
        def _on_ice_gathering_state_change():
            print(f'ICE gathering state changed to {self.pc.iceGatheringState}')

        @self.pc.on('signalingstatechange')
        def _on_signaling_state_change():
            print(f'Signaling state changed to: {self.pc.signalingState}')

        @self.pc.on('icecandidate')
        def _on_ice_candidate(event):
            print(f'Received candidate: {event.candidate}')

        @self.pc.on('iceconnectionstatechange')
        async def _on_ice_connection_state_change():
            print(f'ICE connection state changed to: {self.pc.iceConnectionState}')

            if self.pc.iceConnectionState == 'checking':
                send_sdp_answer_to_spot_cam(self.options, offer_id, self.pc.localDescription.sdp.encode())

        @self.pc.on('track')
        def _on_track(track):
            print(f'Received track: {track.kind}')

            if track.kind == 'video':
                video_track = SpotCAMMediaStreamTrack(track, self.video_frame_queue)
                video_track.kind = 'video'
                self.pc.addTrack(video_track)
            elif track.kind == 'audio':
                audio_track = SpotCAMMediaStreamTrack(track, self.audio_frame_queue)
                audio_track.kind = 'audio'
                self.pc.addTrack(audio_track)

        desc = RTCSessionDescription(sdp_offer, 'offer')
        await self.pc.setRemoteDescription(desc)

        sdp_answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(sdp_answer)

