# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import asyncio
import base64
import requests

from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    MediaStreamTrack,
)


class SpotCAMMediaStreamTrack(MediaStreamTrack):

    def __init__(self, track, queue):
        super().__init__()

        self.track = track
        self.queue = queue

    async def recv(self):
        frame = await self.track.recv()
        await self.queue.put(frame)

        return frame


class WebRTCClient:

    def __init__(self, hostname, username, password, sdp_port, sdp_filename, cam_ssl_cert,
                 rtc_config, media_recorder=None, recorder_type=None):
        self.pc = RTCPeerConnection(configuration=rtc_config)

        self.video_frame_queue = asyncio.Queue()
        self.audio_frame_queue = asyncio.Queue()

        self.hostname = hostname
        self.username = username
        self.password = password
        self.sdp_port = sdp_port
        self.media_recorder = media_recorder
        self.recorder_type = recorder_type
        self.sdp_filename = sdp_filename
        self.cam_ssl_cert = cam_ssl_cert

    def get_bearer_token(self, mock=False):
        if mock:
            return 'token'
        payload = {'username': self.username, 'password': self.password}
        response = requests.post(f'https://{self.hostname}/accounts/jwt/generate/', verify=False,
                                 data=payload, timeout=1)
        token = response.content.decode('utf-8')
        return token

    def get_sdp_offer_from_spot_cam(self, token):

        # then made the sdp request with the token
        headers = {'Authorization': f'Bearer {token}'}
        server_url = f'https://{self.hostname}:{self.sdp_port}/{self.sdp_filename}'
        response = requests.get(server_url, verify=self.cam_ssl_cert, headers=headers)
        result = response.json()
        return result['id'], base64.b64decode(result['sdp']).decode()

    def send_sdp_answer_to_spot_cam(self, token, offer_id, sdp_answer):
        headers = {'Authorization': f'Bearer {token}'}
        server_url = f'https://{self.hostname}:{self.sdp_port}/{self.sdp_filename}'

        payload = {'id': offer_id, 'sdp': base64.b64encode(sdp_answer).decode('utf8')}
        r = requests.post(server_url, verify=self.cam_ssl_cert, json=payload, headers=headers)
        if r.status_code != 200:
            raise ValueError(r)

    async def start(self):
        # first get a token
        try:
            token = self.get_bearer_token()
        except:
            token = self.get_bearer_token(mock=True)

        offer_id, sdp_offer = self.get_sdp_offer_from_spot_cam(token)

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
                self.send_sdp_answer_to_spot_cam(token, offer_id,
                                                 self.pc.localDescription.sdp.encode())

        @self.pc.on('track')
        def _on_track(track):
            print(f'Received track: {track.kind}')

            if self.media_recorder:
                if track.kind == self.recorder_type:
                    self.media_recorder.addTrack(track)

            if track.kind == 'video':
                video_track = SpotCAMMediaStreamTrack(track, self.video_frame_queue)
                video_track.kind = 'video'
                self.pc.addTrack(video_track)

        desc = RTCSessionDescription(sdp_offer, 'offer')
        await self.pc.setRemoteDescription(desc)

        sdp_answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(sdp_answer)
