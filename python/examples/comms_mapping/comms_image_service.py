# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).
"""Register and run an Image Service for the output of a comms data on Spot."""

import io
import logging
import sys
import threading
import time

import cv2
import numpy as np
import requests
import six
import urllib3

import bosdyn.api.geometry_pb2 as geometry_protos
import bosdyn.api.payload_pb2 as payload_protos
import bosdyn.client.util
import bosdyn.util
from bosdyn.api import (header_pb2, image_pb2, image_service_pb2, image_service_pb2_grpc,
                        payload_registration_pb2, service_fault_pb2)
from bosdyn.client.async_tasks import AsyncPeriodicQuery, AsyncTasks
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive)
from bosdyn.client.fault import FaultClient, ServiceFaultDoesNotExistError
from bosdyn.client.frame_helpers import get_odom_tform_body
from bosdyn.client.math_helpers import SE3Pose
from bosdyn.client.payload_registration import PayloadAlreadyExistsError, PayloadRegistrationClient
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.util import GrpcServiceRunner, populate_response_header, setup_logging

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import matplotlib as mpl

mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import cm as CM

# payload and service details
DIRECTORY_NAME = 'comms-image-service'
AUTHORITY = 'comms'
SOURCE_NAME = 'wifimap'
RESET_SOURCE_NAME = 'reset'
SERVICE_TYPE = 'bosdyn.api.ImageService'
GUID = 'ad17feb4-c23c-4bbc-90f3-2be50a4f9929'
SECRET = 'curlyfriesarebetter'
MAJOR_VERSION = 1
MINOR_VERSION = 0
PATCH_LEVEL = 0

# thresholds
TRAVEL_THRESH = 0.15
# RSSI thresholds based on https://www.netspotapp.com/what-is-rssi-level.html
NO_SIGNAL = -100
VERY_POOR_RSSI_THRESH = -80
POOR_RSSI_THRESH = -70
WARN_RSSI_THRESH = -60
GOOD_RSSI_THRESH = -50

# SNR thresholds based on https://www.increasebroadbandspeed.co.uk/what-is-a-good-signal-level-or-signal-to-noise-ratio-snr-for-wi-fi
VERY_POOR_SNR_THRESH = 20
POOR_SNR_THRESH = 25
WARN_SNR_THRESH = 35
GOOD_SNR_THRESH = 40

# misc constants
IMG_SHAPE = (720, 1280, 3)
WHITE_COLOR = (255, 255, 255)
RED_COLOR = (0, 0, 255)
GREEN_COLOR = (0, 255, 0)
YELLOW_COLOR = (0, 211, 255)

_LOGGER = logging.getLogger(__name__)


class AsyncRobotState(AsyncPeriodicQuery):
    """Grab robot state."""

    def __init__(self, robot_state_client):
        super(AsyncRobotState, self).__init__("robot_state", robot_state_client, _LOGGER,
                                              period_sec=0.2)

    def _start_query(self):
        return self._client.get_robot_state_async()


class CommsImageServicer(image_service_pb2_grpc.ImageServiceServicer):
    """GRPC service to provide access to multiple different image sources. The service can list the
    available image (device) sources and query each source for image data."""

    def __init__(self, bosdyn_sdk_robot, service_name, options, logger=None):
        super(CommsImageServicer, self).__init__()

        self.logger = logger or _LOGGER

        # Create a robot instance.
        self.bosdyn_sdk_robot = bosdyn_sdk_robot

        # Get a timesync endpoint from the robot instance such that the image timestamps can be
        # reported in the robot's time.
        self.bosdyn_sdk_robot.time_sync.wait_for_sync()

        # Initialize the frame renderer
        self.comms_image_renderer = CommsMapImageRenderer(options.testmode, options)

        # Service name this servicer is associated with in the robot directory.
        self.service_name = service_name

        # Fault client to report service faults
        self.fault_client = self.bosdyn_sdk_robot.ensure_client(FaultClient.default_service_name)

        # Map tracking the image source name to the protobuf message representing that source.
        # key: device_name (str), value: image_pb2.ImageSource
        self.image_sources = {}

        # Map tracking the image source name to the ImageCaptureThread running in the background.
        # key: device_name (str), value: VideoCapture thread
        self.image_name_to_video = {}

        # Set the different ImageSource protos and ImageCaptureThread for each image source name
        # provided on initialization.
        source_name = SOURCE_NAME
        image_source_proto = self.make_image_source(source_name)
        reset_image_source_proto = self.make_image_source(RESET_SOURCE_NAME)

        self.image_name_to_video[source_name] = self.comms_image_renderer

        self.image_sources[source_name] = image_source_proto
        self.image_sources[RESET_SOURCE_NAME] = reset_image_source_proto

        # Default value for JPEG image quality, in case one is not provided in the GetImage request.
        self.default_jpeg_quality = 85

    def ListImageSources(self, request, context):
        """Obtain the list of ImageSources for this given service.

        Args:
            request (image_pb2.ListImageSourcesRequest): The list images request.
            context (GRPC ClientContext): tracks internal grpc statuses and information.

        Returns:
            A list of all image sources known to this image service. Note, there could be multiple image
            services registered with the robot's directory service that can have different image sources.
        """
        response = image_pb2.ListImageSourcesResponse()
        for source in self.image_sources.values():
            response.image_sources.add().CopyFrom(source)
        populate_response_header(response, request)
        return response

    def GetImage(self, request, context):
        """The image service's GetImage implementation that gets the latest image capture from
        all the image sources specified in the request.

        Args:
            request (image_pb2.GetImageRequest): The image request, which specifies the image sources to
                                                 query, and other format parameters.
            context (GRPC ClientContext): tracks internal grpc statuses and information.

        Returns:
            The ImageSource and Image data for the last captured image from each image source name
            specified in the request.
        """
        response = image_pb2.GetImageResponse()
        for img_req in request.image_requests:

            # reset the comms map
            if img_req.image_source_name == RESET_SOURCE_NAME:
                _LOGGER.info("Resetting comms data")
                self.comms_image_renderer.reset()
                continue

            img_resp = response.image_responses.add()
            src_name = img_req.image_source_name
            img_resp.source.name = src_name
            capture_instance = self.image_name_to_video[src_name]
            img_resp.shot.capture_params.CopyFrom(image_pb2.CaptureParameters())
            frame, img_time = capture_instance.get_frame()
            if frame is None or img_time is None:
                response.header.error.code = header_pb2.CommonError.CODE_INTERNAL_SERVER_ERROR
                response.header.error.message = 'Failed to capture an image from {} on the server.'.format(
                    src_name)
                return response

            # Convert the image capture time from the local clock time into the robot's time. Then set it as
            # the acquisition timestamp for the image data.
            img_resp.shot.acquisition_time.CopyFrom(
                self.bosdyn_sdk_robot.time_sync.robot_timestamp_from_local_secs(img_time))
            img_resp.shot.image.rows = int(frame.shape[0])
            img_resp.shot.image.cols = int(frame.shape[1])

            # Determine the pixel format for the data.
            if frame.shape[2] == 3:
                # RGB image.
                img_resp.shot.image.pixel_format = image_pb2.Image.PIXEL_FORMAT_RGB_U8
            elif frame.shape[2] == 1:
                # Greyscale image.
                img_resp.shot.image.pixel_format = image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8
            elif frame.shape[2] == 4:
                # RGBA image.
                img_resp.shot.image.pixel_format = image_pb2.Image.PIXEL_FORMAT_RGBA_U8
            else:
                # The number of pixel channels did not match any of the known formats.
                img_resp.shot.image.pixel_format = image_pb2.Image.PIXEL_FORMAT_UNKNOWN

            # Note, we are currently not setting any information for the transform snapshot or the frame
            # name for an image sensor since this information can't be determined with openCV.

            # Set the image data.
            if img_req.image_format == image_pb2.Image.FORMAT_RAW:
                img_resp.shot.image.data = np.ndarray.tobytes(frame)
                img_resp.shot.image.format = image_pb2.Image.FORMAT_RAW
            elif img_req.image_format == image_pb2.Image.FORMAT_JPEG:
                quality = self.default_jpeg_quality
                if img_req.quality_percent > 0 and img_req.quality_percent <= 100:
                    quality = img_req.quality_percent
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
                img_resp.shot.image.data = cv2.imencode('.jpg', frame, encode_param)[1].tostring()
                img_resp.shot.image.format = image_pb2.Image.FORMAT_JPEG
            else:
                quality = self.default_jpeg_quality
                if img_req.quality_percent > 0 and img_req.quality_percent <= 100:
                    quality = img_req.quality_percent
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                img_resp.shot.image.data = cv2.imencode('.jpg', frame, encode_param)[1].tostring()
                img_resp.shot.image.format = image_pb2.Image.FORMAT_JPEG

            # Set that we successfully got the image.
            if img_resp.status == image_pb2.ImageResponse.STATUS_UNKNOWN:
                img_resp.status = image_pb2.ImageResponse.STATUS_OK

        # No header error codes, so set the response header as CODE_OK.
        populate_response_header(response, request)
        # Limit frame rate to 1 FPS
        time.sleep(1)
        return response

    @staticmethod
    def make_image_source(source_name):
        """Create an instance of the image_pb2.ImageSource and a VideoCapture for that image source.
        Args:
            source_name(str): The image source name that should be described.

        Returns:
            An ImageSource with the cols, rows, and image type populated, in addition to an OpenCV VideoCapture
            instance which can be used to query the image source for images.
        """
        source = image_pb2.ImageSource()
        source.name = source_name
        source.cols = 720
        source.rows = 1280
        source.image_type = image_pb2.ImageSource.IMAGE_TYPE_VISUAL
        return source


def run_service(bosdyn_sdk_robot, port, service_name, options, logger=None):
    # Proto service specific function used to attach a servicer to a server.
    add_servicer_to_server_fn = image_service_pb2_grpc.add_ImageServiceServicer_to_server

    # Instance of the servicer to be run.
    service_servicer = CommsImageServicer(bosdyn_sdk_robot, service_name, options, logger=logger)
    return GrpcServiceRunner(service_servicer, add_servicer_to_server_fn, port, logger=logger)


def add_web_cam_arguments(parser):
    parser.add_argument(
        '--device-name',
        help=('Image source to query. If none are passed, it will default to the first available '
              'source.'), action='append', required=False, default=[SOURCE_NAME])


def self_register_payload(robot, config):
    payload_registration_client = robot.ensure_client(
        PayloadRegistrationClient.default_service_name)

    payload = define_payload(GUID, config.name, config.description)

    # Register the payload and authenticate
    robot.register_payload_and_authenticate(payload, SECRET)
    _LOGGER.info('Payload has been authorized by admin.')

    return True


def define_payload(guid, name, description):
    """Return an arbitrary bosdyn.api.Payload object."""

    # Populate the fields from hardcoded values
    payload = payload_protos.Payload()
    payload.GUID = guid
    payload.name = name
    payload.version.major_version = MAJOR_VERSION
    payload.version.minor_version = MINOR_VERSION
    payload.version.patch_level = PATCH_LEVEL

    payload.description = description

    # Specify other top level fields with sample values.
    payload.label_prefix.append('comms')

    return payload


class FakeWifi():
    """Returns fake data for testing
    """

    def __init__(self):
        self.data = {
            "beacons_received": 22705,
            "rx_signal_dbm": -36,
            "tx_bits_per_second": 117000000,
            "mac_address": "f0:af:85:c5:f9:f6",
            "tx_packets": 78985,
            "expected_bits_per_second": 42388000,
            "tx_bytes": 62443534,
            "tx_failed": 0,
            "rx_signal_avg_dbm": -30,
            "rx_bytes": 28656529,
            "tx_retries": 3234,
            "rx_beacon_signal_avg_dbm": 226,
            "rx_bits_per_second": 130000000,
            "beacon_loss_count": 0,
            "connected_time": "2350s",
            "rx_packets": 118013
        }

    def get_latest_data(self):
        self.data['rx_signal_dbm'] = self.data['rx_signal_dbm'] + 0.1
        return self.data


class WifiStatsRetriever():
    """Retrieves data from robot data buffer
    """

    def __init__(self, robot):
        self.robot = robot
        self.data = {
            "beacons_received": 0,
            "rx_signal_dbm": 0,
            "tx_bits_per_second": 0,
            "mac_address": "",
            "tx_packets": 0,
            "expected_bits_per_second": 0,
            "tx_bytes": 0,
            "tx_failed": 0,
            "rx_signal_avg_dbm": 0,
            "rx_bytes": 0,
            "tx_retries": 0,
            "rx_beacon_signal_avg_dbm": 0,
            "rx_bits_per_second": 0,
            "beacon_loss_count": 0,
            "connected_time": 0,
            "rx_packets": 0,
        }

        self.token_str = self.get_token()
        self.previous_time_retrieved = None

        self.update_thread = threading.Thread(target=self.update)
        self.update_thread.daemon = True
        self.update_thread.start()

    def get_token(self):
        payload_registration_client = self.robot.ensure_client(
            PayloadRegistrationClient.default_service_name)

        # grab token for later use
        token = payload_registration_client.get_payload_auth_token(GUID, SECRET)
        return token

    def update(self):
        while True:
            self.retrieve_from_robot()
            time.sleep(1)

    def retrieve_from_robot(self):
        """ Retrieves data from robot data buffer, equivalent to calling:
        curl -O -J -k -H "Authorization: Bearer $(cat token_file)" \
            https://robot/v1/data-buffer/messages/?type=bosdyn.api.WifiStats&from_sec=X&to_sec=Y
        """
        headers = {"Authorization": f"Bearer {self.token_str}"}
        # maintain times in robot time
        current_time = int(time.time())
        robot_time = self.robot.time_sync.robot_timestamp_from_local_secs(current_time)
        current_time = robot_time.ToSeconds()
        # get last 5 seconds on the first iteration
        if self.previous_time_retrieved is None:
            self.previous_time_retrieved = current_time - 5
        payload = {'from_sec': self.previous_time_retrieved, 'to_sec': current_time}
        wifi_stats_url = f'https://{self.robot.address}/v1/data-buffer/messages/?type=bosdyn.api.WifiStats'
        resp = requests.get(wifi_stats_url, headers=headers, params=payload, verify=False)

        if resp.status_code == 401:
            self.token_str = self.get_token()
        elif resp.status_code == 200:
            try:
                data = resp.json()['messages'][0]['message']['devices'][0]['associations'][0]
                self.data.update(data)
                self.previous_time_retrieved = current_time
            except (KeyError, IndexError) as exc:
                pass
        else:
            _LOGGER.warning('Unexpected error encountered when retrieving wifi data')

    def get_latest_data(self):
        return self.data


class RajantStatsRetriever():
    """Retrieves data from robot data buffer
    """

    def __init__(self, robot):
        self.robot = robot
        self.data = {
            "beacons_received": 0,
            "rx_signal_dbm": 0,
            "tx_bits_per_second": 0,
            "mac_address": "",
            "tx_packets": 0,
            "expected_bits_per_second": 0,
            "tx_bytes": 0,
            "tx_failed": 0,
            "rx_signal_avg_dbm": 0,
            "rx_bytes": 0,
            "tx_retries": 0,
            "rx_beacon_signal_avg_dbm": 0,
            "rx_bits_per_second": 0,
            "beacon_loss_count": 0,
            "connected_time": 0,
            "rx_packets": 0,
        }

        self.token_str = self.get_token()
        self.previous_time_retrieved = None

        self.update_thread = threading.Thread(target=self.update)
        self.update_thread.daemon = True
        self.update_thread.start()

    def update(self):
        while True:
            self.retrieve_from_robot()
            time.sleep(1)

    def retrieve_from_robot(self):
        """ Retrieves data from robot data buffer, equivalent to calling:
        curl -O -J -k -H "Authorization: Bearer $(cat token_file)" \
            https://robot/v1/data-buffer/messages/?type=bosdyn.api.WifiStats&from_sec=X&to_sec=Y
        """
        headers = {"Authorization": f"Bearer {self.token_str}"}
        # maintain times in robot time
        current_time = int(time.time())
        robot_time = self.robot.time_sync.robot_timestamp_from_local_secs(current_time)
        current_time = robot_time.ToSeconds()
        # get last 5 seconds on the first iteration
        if self.previous_time_retrieved is None:
            self.previous_time_retrieved = current_time - 5
        payload = {'from_sec': self.previous_time_retrieved, 'to_sec': current_time}
        rajant_stats_url = f'https://{self.robot.address}/v1/data-buffer/messages/?type=blue.perception.RajantProto'
        resp = requests.get(rajant_stats_url, headers=headers, params=payload, verify=False)

        if resp.status_code == 401:
            self.token_str = self.get_token()
        elif resp.status_code == 200:
            try:
                data = resp.json()['messages'][0]['message']  # ['devices'][0]['associations'][0]
                # map some of the Rajant stats to the wifi proto
                self.data["beacons_received"] = len(data["peers"])
                # find peer with max rssi
                max_peer_wlan = None
                snrs = []
                for peer in data["peers"]:
                    if "wlan0" in peer:
                        if not max_peer_wlan:
                            max_peer_wlan = peer["wlan0"]
                        elif peer["wlan0"]["snr"] > max_peer_wlan["snr"]:
                            max_peer_wlan = peer["wlan0"]
                    if "wlan1" in peer:
                        if not max_peer_wlan:
                            max_peer_wlan = peer["wlan1"]
                        elif peer["wlan1"]["snr"] > max_peer_wlan["snr"]:
                            max_peer_wlan = peer["wlan1"]
                self.data["rx_signal_dbm"] = max_peer_wlan["snr"]
                self.data["rx_beacon_signal_avg_dbm"] = max_peer_wlan["snr"]
                self.data["expected_bits_per_second"] = max_peer_wlan["rate"] * 1e7
                self.data.update(data)
                self.previous_time_retrieved = current_time
            except (KeyError, IndexError) as exc:
                pass
        else:
            _LOGGER.warning('Unexpected error encountered when retrieving wifi data')

    def get_latest_data(self):
        return self.data


class CommsMapImageRenderer():

    def __init__(self, testmode, options):
        # Instantiate robot for use in getting state
        try:
            self.robot = sdk.create_robot(options.hostname)
            self.robot.authenticate_from_payload_credentials(GUID, SECRET)
            self.robot_state_client = self.robot.ensure_client(
                RobotStateClient.default_service_name)
            self._robot_state_task = AsyncRobotState(self.robot_state_client)
        except Exception as e:
            _LOGGER.error("Unable to create robot state client: {}".format(e))
            sys.exit(-1)

        self._task_list = [self._robot_state_task]
        self._async_tasks = AsyncTasks(self._task_list)

        self.update_thread = threading.Thread(target=self.update_async_thread,
                                              args=[self._async_tasks])
        self.update_thread.daemon = True

        self.frame = np.zeros(IMG_SHAPE, dtype=np.uint8)
        self.unit = None
        if testmode == 'true':
            self.unit = FakeWifi()
        else:
            self.unit = WifiStatsRetriever(self.robot)
            self.cm_map = self.comms_colormaps()
            self.cm, self.norm_bins = self.cm_map['rssi']
            if options.rajant:
                self.unit = RajantStatsRetriever(self.robot)
                self.cm, self.norm_bins = self.cm_map['snr']

        # for storing the matplotlib image
        self.img_lock = threading.Lock()
        self.plot_img_buffer = io.BytesIO()
        self.last_good_map = None

        self.FPS = 1
        self.SLEEP_TIME = int(1 / self.FPS)

        # Start frame update thread
        self.thread = threading.Thread(target=self.update, args=())
        self.thread.daemon = True

        # Start the map builder thread
        self.map_thread = threading.Thread(target=self.update_map, args=())
        self.map_thread.daemon = True

        # Datasets for mapping comms data as the robot moves
        self.data_lock = threading.Lock()
        self.rssi_list = []
        self.map_x = []
        self.map_y = []

        # Font setup for adding text to the CV image
        self.text_render_font = cv2.FONT_HERSHEY_SIMPLEX
        self.text_render_size = 0.5  # fontScale
        self.text_render_top_frame = 500  # Location above frame bottom
        self.text_render_line_increment_y = 35  # line height
        self.text_render_left_margin = 12  # location from left side
        self.text_render_thickness = 1
        _LOGGER.info("CommsMapImageRenderer object init complete")

        # start all the threads
        self.update_thread.start()
        self.thread.start()
        self.map_thread.start()

    def reset(self):
        with self.data_lock:
            self.rssi_list = []
            self.map_x = []
            self.map_y = []

    def update_async_thread(self, async_task):
        while True:
            async_task.update()
            time.sleep(0.1)

    def update_map_data(self, rx_signal_dbm):
        if rx_signal_dbm is None:
            return
        # Remove small drift variations based on 0.015m threshold
        def traveled(loc):
            if loc is None:
                return False
            if len(self.map_x) == 0:
                return (True)
            point1 = np.array((self.map_x[-1], self.map_y[-1]))
            point2 = np.array((loc.x, loc.y))
            return np.linalg.norm(point1 - point2) > TRAVEL_THRESH

        loc = self.get_robot_loc()
        if loc is None:
            return
        idx = len(self.map_x)

        if traveled(loc):
            with self.data_lock:
                self.map_x.append(loc.x)
                self.map_y.append(loc.y)
                self.rssi_list.append(rx_signal_dbm)
            _LOGGER.debug(f"{self.rssi_list}")

    def update_map(self):
        while True:
            self.draw_comms_map()
            time.sleep(self.SLEEP_TIME)

    def comms_colormaps(self):
        colors = [
            (.96, .32, .23),  # Red light red
            (1.0, .48, .33),  # Salmon-ish
            (.96, .63, .27),  # Orange
            (1.0, .84, .23),  # Dehydrated Yellow
            (1.0, 1.0, .28),  # Lemon Yellow
            (.22, .73, .29)  # Artificial Green
        ]
        n_bins_ranges = [
            NO_SIGNAL - 10, NO_SIGNAL, VERY_POOR_RSSI_THRESH, POOR_RSSI_THRESH, WARN_RSSI_THRESH,
            GOOD_RSSI_THRESH, 0
        ]
        n_bin = len(n_bins_ranges) - 1
        cmap_name = 'comms_cm'
        cm = mpl.colors.LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bin)
        norm_bins = mpl.colors.BoundaryNorm(n_bins_ranges, len(n_bins_ranges))

        colors_snr = [
            (.96, .32, .23),  # Red light red
            (1.0, .48, .33),  # Salmon-ish
            (.96, .63, .27),  # Orange
            (1.0, .84, .23),  # Dehydrated Yellow
            (.22, .73, .29)  # Artificial Green
        ]
        n_bins_ranges_snr = [
            VERY_POOR_SNR_THRESH - 10, VERY_POOR_SNR_THRESH, POOR_SNR_THRESH, WARN_SNR_THRESH,
            GOOD_SNR_THRESH, 100
        ]
        n_bin_snr = len(n_bins_ranges_snr) - 1
        cmap_name = 'comms_cm_snr'
        cm_snr = mpl.colors.LinearSegmentedColormap.from_list(cmap_name, colors_snr, N=n_bin_snr)
        norm_bins_snr = mpl.colors.BoundaryNorm(n_bins_ranges_snr, len(n_bins_ranges_snr))
        cm_dict = {"rssi": (cm, norm_bins), "snr": (cm_snr, norm_bins_snr)}
        return cm_dict

    def draw_comms_map(self):
        fig, ax = plt.subplots(figsize=(7.5, 6.7))
        with self.data_lock:
            sc = ax.scatter(
                self.map_x,
                self.map_y,
                c=self.rssi_list,
                s=20,
                cmap=self.cm,  # CM.RdYlGn,
                alpha=1,
                norm=self.norm_bins
                #edgecolor='grey'
            )
        ax.axis('equal')
        ax.set_facecolor('k')
        ax.set_title('Comms Plot (dBm)')
        ax.set_xlabel('X-Position (m)')
        ax.set_ylabel('Y-Position (m)')
        cbar = fig.colorbar(sc)

        with self.img_lock:
            self.plot_img_buffer = io.BytesIO()
            plt.savefig(self.plot_img_buffer, format='jpg')
        plt.close('all')

    def get_robot_loc(self):
        if self._robot_state_task.proto:
            odom_tform_body = get_odom_tform_body(
                self._robot_state_task.proto.kinematic_state.transforms_snapshot).to_proto()
            helper_se3 = SE3Pose.from_obj(odom_tform_body)
            return helper_se3

    # Render the sensor readings onto the frame for display on the controller via the image service
    def put_results(self):
        # Get latest data
        comms_data = self.unit.get_latest_data()

        # Set the text color appropriately for any alert or error statuses
        def db_color(db):
            if db is None:
                return WHITE_COLOR
            elif db < POOR_RSSI_THRESH:
                return RED_COLOR
            elif db < WARN_RSSI_THRESH:
                return YELLOW_COLOR
            else:
                return GREEN_COLOR

        # Update the frame
        self.frame = np.zeros(IMG_SHAPE, dtype=np.uint8)

        # Load the rendered matplotlib comms scatter plot into the frame
        try:
            with self.img_lock:
                self.plot_img_buffer.seek(0)
                file_bytes = np.asarray(bytearray(self.plot_img_buffer.read()), dtype=np.uint8)
            comms_map = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            self.last_good_map = comms_map
        except Exception as e:
            _LOGGER.warning("Error encountered decoding plot image, using last good figure")
            if self.last_good_map is not None:
                comms_map = self.last_good_map
            else:
                comms_map = np.zeros((670, 750, 3), dtype=np.uint8)

        try:
            x_offset = 500
            y_offset = 20
            self.frame[y_offset:y_offset + comms_map.shape[0],
                       x_offset:x_offset + comms_map.shape[1]] = comms_map
        except Exception as e:
            _LOGGER.error("Unable to place comms survey map in frame: {}".format(e))
            cv2.putText(self.frame, "Map not ready", (500, 300), self.text_render_font, 1.2,
                        (0, 0, 255), 2)
            pass

        # Add all lines for display here with key of "Label: " and value of information to display
        text_struct = {
            "Rx Signal (dBm): ": comms_data['rx_signal_dbm'],
            "Expected Throughput (kbps): ": int(comms_data['expected_bits_per_second']) / 1000,
            "Rx Signal Avg (dBm): ": comms_data['rx_signal_avg_dbm']
        }

        # Loop through all fields to display and render them consecutively on the cv2 image
        textline = self.text_render_top_frame
        for field_label in text_struct.keys():
            data_string = text_struct[field_label]
            if "dBm" in field_label:
                textcolor = db_color(data_string)
            else:
                textcolor = WHITE_COLOR
            try:
                cv2.putText(self.frame, field_label + str(data_string),
                            (self.text_render_left_margin, self.frame.shape[0] - textline),
                            self.text_render_font, self.text_render_size, textcolor,
                            self.text_render_thickness)
            except Exception as e:
                _LOGGER.error("Couldn't add line for {} because: {}".format(field_label, e))
            textline = textline - self.text_render_line_increment_y

        return True

    def update(self):
        while True:
            self.put_results()
            # Update the map image with the most recent location and exposure rate every 4.9 seconds
            comms_data = self.unit.get_latest_data()
            dbm = comms_data['rx_signal_dbm']
            _LOGGER.debug(f"dBm: {dbm}")
            self.update_map_data(dbm)
            time.sleep(self.SLEEP_TIME)

    def get_frame(self):
        tnow = time.time()
        frame = self.frame
        return frame, tnow


if __name__ == '__main__':
    # Define all arguments used by this service.
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_service_hosting_arguments(parser)
    add_web_cam_arguments(parser)

    # Setup payload self-registration details
    parser.add_argument("--name", type=str, help="Name of the payload.", default="CommsMapper")
    parser.add_argument("--description", type=str, help="Description of the payload.",
                        default="Comms mapping tool")
    parser.add_argument('--rajant', default=False, action='store_true')
    parser.add_argument('--testmode',
                        help="Run in 'test mode' without using real comms data, return fake values",
                        default='false')

    # base and service port arguments with CORE defaults
    parser.add_argument('--hostname', default='192.168.50.3', help='Hostname or address of robot,'
                        ' e.g. "192.168.50.3"')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print debug-level messages')
    parser.add_argument(
        '--host-ip', default='192.168.50.5',
        help='Hostname or address the service can be reached at. e.g. "192.168.50.5"')

    # Arguments parsing finished
    options = parser.parse_args()

    # Setup logging to use either INFO level or DEBUG level.
    setup_logging(options.verbose)

    # Create and authenticate a bosdyn robot object. Authenticate with the payload credentials
    # once the payload is confirmed defined and authorized in the admin console
    sdk = bosdyn.client.create_standard_sdk("CommsMapper")
    robot = sdk.create_robot(options.hostname)
    self_register_payload(robot, options)

    # Create a service runner to start and maintain the service on background thread.
    service_runner = run_service(robot, options.port, DIRECTORY_NAME, options, logger=_LOGGER)

    # Use a keep alive to register the service with the robot directory.
    dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
    keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client, logger=_LOGGER)
    keep_alive.start(DIRECTORY_NAME, SERVICE_TYPE, AUTHORITY, options.host_ip, service_runner.port)

    # Attach the keep alive to the service runner and run until a SIGINT is received.
    with keep_alive:
        service_runner.run_until_interrupt()
