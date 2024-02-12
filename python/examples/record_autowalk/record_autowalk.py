# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Record Autowalk"""

import argparse
import logging
import os
import sys
import time

import numpy as np
import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets

import bosdyn.api.basic_command_pb2 as basic_command_pb2
import bosdyn.api.mission
import bosdyn.api.power_pb2 as PowerServiceProto
import bosdyn.api.robot_state_pb2 as robot_state_proto
import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
import bosdyn.geometry as geometry
import bosdyn.mission.client
import bosdyn.util
from bosdyn.api import geometry_pb2, image_pb2, world_object_pb2
from bosdyn.api.autowalk import walks_pb2
from bosdyn.api.data_acquisition_pb2 import AcquireDataRequest, DataCapture, ImageSourceCapture
from bosdyn.api.graph_nav import graph_nav_pb2, recording_pb2
from bosdyn.api.mission import nodes_pb2
from bosdyn.client import ResponseError, RpcError
from bosdyn.client.async_tasks import AsyncPeriodicQuery, AsyncTasks
from bosdyn.client.docking import DockingClient, docking_pb2
from bosdyn.client.graph_nav import GraphNavClient
from bosdyn.client.lease import Error as LeaseBaseError
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.power import PowerClient
from bosdyn.client.recording import GraphNavRecordingServiceClient
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.world_object import WorldObjectClient
from bosdyn.util import now_sec, seconds_to_timestamp

LOGGER = logging.getLogger()

IMAGE_SOURCES = [
    'frontright_fisheye_image', 'frontleft_fisheye_image', 'right_fisheye_image',
    'back_fisheye_image', 'left_fisheye_image'
]
ASYNC_CAPTURE_RATE = 40  # milliseconds, 25 Hz
LINEAR_VELOCITY_DEFAULT = 0.6  # m/s
ANGULAR_VELOCITY_DEFAULT = 0.8  # rad/sec
COMMAND_DURATION_DEFAULT = 0.6  # seconds
SLIDER_MIDDLE_VALUE = 50
TRAVEL_MAX_DIST = 0.2  # meters
BLOCKED_PATH_WAIT_TIME = 5  # seconds
RETRY_COUNT_DEFAULT = 1
PROMPT_DURATION_DEFAULT = 60  # seconds
PROMPT_DURATION_DOCK = 600  # seconds
BATTERY_THRESHOLDS = (60.0, 10.0)  # battery percentages
POSE_INDEX, ROBOT_CAMERA_INDEX, DOCK_INDEX = range(3)
INITIAL_PANEL, RECORDED_PANEL, ACTION_PANEL, FINAL_PANEL = range(4)


def main():
    """Record autowalks with GUI"""

    # Configure logging
    bosdyn.client.util.setup_logging()

    # Process command-line arguments
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    args = parser.parse_args()

    # Initialize robot object
    robot = init_robot(args.hostname)
    assert not robot.is_estopped(), 'Robot is estopped. ' \
                                    'Please use an external E-Stop client, ' \
                                    'such as the estop SDK example, to configure E-Stop.'

    # Power on and get lease
    app = QtWidgets.QApplication(sys.argv)
    gui = AutowalkGUI(robot)
    gui.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    gui.show()
    app.exec_()

    return True


def init_robot(hostname):
    """Initialize robot object"""

    # Initialize SDK
    sdk = bosdyn.client.create_standard_sdk('RecordAutowalk', [bosdyn.mission.client.MissionClient])

    # Create robot object
    robot = sdk.create_robot(hostname)

    # Authenticate with robot
    bosdyn.client.util.authenticate(robot)

    # Establish time sync with the robot
    robot.time_sync.wait_for_sync()

    return robot


class AsyncRobotState(AsyncPeriodicQuery):
    """Grab robot state."""

    def __init__(self, robot_state_client):
        super(AsyncRobotState, self).__init__('robot_state', robot_state_client, LOGGER,
                                              period_sec=0.2)

    def _start_query(self):
        return self._client.get_robot_state_async()


class WindowWidget(QtWidgets.QWidget):
    """Window class to continuously check for key presses"""

    key_pressed = QtCore.pyqtSignal(str)

    def keyPressEvent(self, key_event):
        self.key_pressed.emit(key_event.text())


class AutowalkGUI(QtWidgets.QMainWindow):
    """GUI for recording autowalk"""

    def __init__(self, robot):
        super(QtWidgets.QMainWindow, self).__init__()
        self._robot = robot
        self._robot_id = self._robot.get_id()
        self._lease_keepalive = None
        self.walk = self._init_walk()
        self.directory = os.getcwd()

        # Initialize clients
        self._lease_client = robot.ensure_client(LeaseClient.default_service_name)
        self._power_client = robot.ensure_client(PowerClient.default_service_name)
        self._robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
        self._robot_command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        self._graph_nav_client = robot.ensure_client(GraphNavClient.default_service_name)
        # Clear graph to ensure only the data recorded using this example gets packaged into map
        self._graph_nav_client.clear_graph()
        self._recording_client = robot.ensure_client(
            GraphNavRecordingServiceClient.default_service_name)
        self._world_object_client = robot.ensure_client(WorldObjectClient.default_service_name)
        self._docking_client = robot.ensure_client(DockingClient.default_service_name)

        # Initialize async tasks
        self._robot_state_task = AsyncRobotState(self._robot_state_client)
        self._async_tasks = AsyncTasks([self._robot_state_task])
        self._async_tasks.update()

        # Timer for grabbing robot states
        self.timer = QtCore.QTimer(self)
        self.timer.setTimerType(QtCore.Qt.PreciseTimer)
        self.timer.timeout.connect(self._update_tasks)
        self.timer.start(ASYNC_CAPTURE_RATE)

        # Default starting speed values for the robot
        self.linear_velocity = LINEAR_VELOCITY_DEFAULT
        self.angular_velocity = ANGULAR_VELOCITY_DEFAULT
        self.command_duration = COMMAND_DURATION_DEFAULT

        # Experimentally determined default starting values for pitch, roll, yaw, and height
        self.euler_angles = geometry.EulerZXY()
        self.robot_height = 0

        self.resumed_recording = False
        self.elements = []
        self.fiducial_objects = []
        self.dock = None
        self.dock_and_end_recording = False

        self.command_to_function = {
            27: self._quit_program,
            ord('P'): self._toggle_power,
            ord('v'): self._sit,
            ord('f'): self._stand,
            ord('w'): self._move_forward,
            ord('s'): self._move_backward,
            ord('a'): self._strafe_left,
            ord('d'): self._strafe_right,
            ord('q'): self._turn_left,
            ord('e'): self._turn_right,
            ord('L'): self._toggle_lease
        }

        self.command_descriptions = [
            '[ESC]  Quit Program', '[P]  Toggle Power', '[L]  Toggle Lease', '[v]  Sit',
            '[f]  Stand', '[w]  Move Forward', '[s]  Move Backward', '[a]  Strafe Left',
            '[d]  Strafe Right', '[q]  Turn Left', '[e]  Turn Right'
        ]

        self.format_GUI()

    def format_GUI(self):
        """Create and format GUI window"""

        # Main window widget
        window_widget = WindowWidget()
        window_widget.setFocusPolicy(QtCore.Qt.StrongFocus)
        window_widget.key_pressed.connect(self._drive_command)
        self.window_layout = QtWidgets.QVBoxLayout()
        window_widget.setLayout(self.window_layout)
        self.setCentralWidget(window_widget)

        # Add main panels for recording autowalk
        self.format_top_panel()
        self.format_left_panel()
        self.format_right_panel()

        content_widget = QtWidgets.QWidget()
        content_widget_layout = QtWidgets.QHBoxLayout()
        content_widget.setLayout(content_widget_layout)
        content_widget_layout.addWidget(self.left_panel_widget)
        content_widget_layout.addStretch()
        content_widget_layout.addWidget(self.right_panel_widget)

        self.window_layout.addWidget(self.top_panel_widget)
        self.window_layout.addWidget(content_widget)

        # Signal connections for buttons, sliders, and combo boxes
        self.action_combobox.activated.connect(self.change_action_panel)
        self.record_button.clicked.connect(self._toggle_record)
        self.save_autowalk_button.clicked.connect(self._save_autowalk)
        self.linear_velocity_slider.valueChanged.connect(self._change_linear_velocity)
        self.angular_velocity_slider.valueChanged.connect(self._change_angular_velocity)
        self.command_duration_slider.valueChanged.connect(self._change_command_duration)
        self.pose_pitch_slider.sliderReleased.connect(self._change_pose)
        self.pose_roll_slider.sliderReleased.connect(self._change_pose)
        self.pose_yaw_slider.sliderReleased.connect(self._change_pose)
        self.pose_height_slider.sliderReleased.connect(self._change_pose)
        self.pose_duration_slider.valueChanged.connect(self._change_pose_duration)
        self.rcam_pitch_slider.sliderReleased.connect(self._change_pose)
        self.rcam_roll_slider.sliderReleased.connect(self._change_pose)
        self.rcam_yaw_slider.sliderReleased.connect(self._change_pose)
        self.rcam_height_slider.sliderReleased.connect(self._change_pose)
        self.save_action_button.clicked.connect(self._save_action)
        self.cancel_action_button.clicked.connect(self._cancel_action)
        self.add_action_button.clicked.connect(self._add_action)
        self.directory_button.clicked.connect(self._choose_directory)
        self.cancel_autowalk_button.clicked.connect(self._reset_walk)
        self.docks_list.itemClicked.connect(self.choose_dock)

        self.setWindowTitle('Record Autowalk')

    def format_top_panel(self):
        self.top_panel_widget = QtWidgets.QWidget()
        self.top_panel_layout = QtWidgets.QHBoxLayout()
        self.top_panel_widget.setLayout(self.top_panel_layout)

        self.power_label = QtWidgets.QLabel('Powered off', self, alignment=QtCore.Qt.AlignCenter)
        self.power_label.setStyleSheet('color: red')
        self.lease_label = QtWidgets.QLabel('Unleased', self, alignment=QtCore.Qt.AlignCenter)
        self.lease_label.setStyleSheet('color: red')
        self.directions_label = QtWidgets.QLabel(
            'Set up and move robot to desired starting position', self)
        self.directions_label.setAlignment(QtCore.Qt.AlignCenter)
        self.record_button = QtWidgets.QPushButton('Start Recording', self)
        self.record_button.setStyleSheet('background-color: green')

        self.top_panel_layout.addWidget(self.lease_label)
        self.top_panel_layout.addWidget(self.power_label)
        self.top_panel_layout.addStretch()
        self.top_panel_layout.addWidget(self.directions_label)
        self.top_panel_layout.addStretch()
        self.top_panel_layout.addWidget(self.record_button)

    def format_left_panel(self):
        """ Creates left panel widget with available actions, statuses, and speed controls"""
        self.left_panel_widget = QtWidgets.QWidget()
        self.left_panel_layout = QtWidgets.QVBoxLayout()
        self.left_panel_widget.setLayout(self.left_panel_layout)

        self.actions_label_widget = QtWidgets.QLabel(self)
        self.actions_label_widget.setText('Robot Commands')
        self.actions_label_widget.setAlignment(QtCore.Qt.AlignCenter)
        self.actions_list_widget = QtWidgets.QListWidget(self)
        for description in self.command_descriptions:
            QtWidgets.QListWidgetItem(description, self.actions_list_widget)

        self.linear_velocity_label = QtWidgets.QLabel(f'Speed: {self.linear_velocity:.2f} m/s',
                                                      self)
        self.angular_velocity_label = QtWidgets.QLabel(
            f'Turning speed: {self.angular_velocity:.2f} rad/s', self)
        self.command_duration_label = QtWidgets.QLabel(
            f'Sensitivity: {self.command_duration:.2f} s', self)
        self.linear_velocity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.linear_velocity_slider.setValue(SLIDER_MIDDLE_VALUE)
        self.angular_velocity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.angular_velocity_slider.setValue(SLIDER_MIDDLE_VALUE)
        self.command_duration_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.command_duration_slider.setValue(SLIDER_MIDDLE_VALUE)

        self.left_panel_layout.addWidget(self.actions_label_widget)
        self.left_panel_layout.addWidget(self.actions_list_widget)
        self.left_panel_layout.addWidget(self.linear_velocity_label)
        self.left_panel_layout.addWidget(self.linear_velocity_slider)
        self.left_panel_layout.addWidget(self.angular_velocity_label)
        self.left_panel_layout.addWidget(self.angular_velocity_slider)
        self.left_panel_layout.addWidget(self.command_duration_label)
        self.left_panel_layout.addWidget(self.command_duration_slider)

    def format_right_panel(self):
        """Creates right panel with autowalk actions and save menu"""
        self.right_panel_widget = QtWidgets.QWidget()
        self.right_panel_layout = QtWidgets.QVBoxLayout()
        self.right_panel_widget.setLayout(self.right_panel_layout)
        self.right_panel_stacked_widget = QtWidgets.QStackedWidget()

        # Initial panel with welcome message
        self.initial_panel = QtWidgets.QWidget()
        self.initial_panel_layout = QtWidgets.QVBoxLayout()
        self.initial_panel.setLayout(self.initial_panel_layout)
        self.welcome_message = QtWidgets.QLabel(
            '''Welcome to the Record Autowalk GUI.\n\nMake sure to remove the E-Stop, acquire a lease, and power on the robot.\n\nPosition the robot with a fiducial in view before starting the recording.''',
            self)
        self.welcome_message.setAlignment(QtCore.Qt.AlignTop)
        self.welcome_message.setWordWrap(True)
        self.initial_panel_layout.addWidget(self.welcome_message)

        # Panel with summary of recorded actions
        self.recorded_panel = QtWidgets.QWidget()
        self.recorded_panel_layout = QtWidgets.QVBoxLayout()
        self.recorded_panel.setLayout(self.recorded_panel_layout)
        self.recorded_label = QtWidgets.QLabel('Currently Saved Actions', self)
        self.recorded_list = QtWidgets.QListWidget(self)
        self.add_action_button = QtWidgets.QPushButton('Add Action', self)
        self.recorded_panel_layout.addWidget(self.recorded_label)
        self.recorded_panel_layout.addWidget(self.recorded_list)
        self.recorded_panel_layout.addWidget(self.add_action_button)

        # Action Panels
        self.action_panel = QtWidgets.QWidget()
        self.action_panel_layout = QtWidgets.QVBoxLayout()
        self.action_panel.setLayout(self.action_panel_layout)

        self.action_combobox = QtWidgets.QComboBox(self)
        self.action_combobox.addItems(['Pose', 'Robot Camera', 'Dock and End Recording'])

        self.format_pose_panel()

        self.format_rcam_panel()

        self.format_docking_panel()

        # Stacking Panels
        self.stack_widget = QtWidgets.QStackedWidget()
        self.stack_widget.addWidget(self.pose_panel)
        self.stack_widget.addWidget(self.rcam_panel)
        self.stack_widget.addWidget(self.docking_panel)

        self.save_action_button = QtWidgets.QPushButton('Save Action', self)
        self.cancel_action_button = QtWidgets.QPushButton('Cancel Action', self)

        self.action_panel_layout.addWidget(self.action_combobox)
        self.action_panel_layout.addWidget(self.stack_widget)
        self.action_panel_layout.addWidget(self.save_action_button)
        self.action_panel_layout.addWidget(self.cancel_action_button)

        # Final Panel
        self.final_panel = QtWidgets.QWidget()
        self.final_panel_layout = QtWidgets.QVBoxLayout()
        self.final_panel.setLayout(self.final_panel_layout)

        self.autowalk_name_label = QtWidgets.QLabel('Autowalk Name:', self)
        self.autowalk_name_line = QtWidgets.QLineEdit()
        self.directory_button = QtWidgets.QPushButton('Choose Directory', self)
        self.save_autowalk_button = QtWidgets.QPushButton('Save Autowalk', self)
        self.cancel_autowalk_button = QtWidgets.QPushButton('Cancel', self)
        self.final_panel_layout.addWidget(self.autowalk_name_label)
        self.final_panel_layout.addWidget(self.autowalk_name_line)
        self.final_panel_layout.addWidget(self.directory_button)
        self.final_panel_layout.addStretch()
        self.final_panel_layout.addWidget(self.save_autowalk_button)
        self.final_panel_layout.addWidget(self.cancel_autowalk_button)

        self.right_panel_stacked_widget.addWidget(self.initial_panel)
        self.right_panel_stacked_widget.addWidget(self.recorded_panel)
        self.right_panel_stacked_widget.addWidget(self.action_panel)
        self.right_panel_stacked_widget.addWidget(self.final_panel)

        self.right_panel_layout.addWidget(self.right_panel_stacked_widget)

    def format_pose_panel(self):
        """Creates pose panel for widgets associated with creating pose action"""
        self.pose_panel = QtWidgets.QWidget()
        self.pose_panel_layout = QtWidgets.QVBoxLayout()
        self.pose_panel.setLayout(self.pose_panel_layout)

        self.pose_name_label = QtWidgets.QLabel('Pose Name', self)
        self.pose_name_line = QtWidgets.QLineEdit()
        self.pose_pitch_label = QtWidgets.QLabel('Pitch', self)
        self.pose_pitch_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.pose_pitch_slider.setValue(SLIDER_MIDDLE_VALUE)
        self.pose_roll_label = QtWidgets.QLabel('Roll', self)
        self.pose_roll_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.pose_roll_slider.setValue(SLIDER_MIDDLE_VALUE)
        self.pose_yaw_label = QtWidgets.QLabel('Yaw', self)
        self.pose_yaw_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.pose_yaw_slider.setValue(SLIDER_MIDDLE_VALUE)
        self.pose_height_label = QtWidgets.QLabel('Height', self)
        self.pose_height_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.pose_height_slider.setValue(SLIDER_MIDDLE_VALUE)
        self.pose_duration_label = QtWidgets.QLabel('Pose Duration: 5 s', self)
        self.pose_duration_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.pose_duration_slider.setValue(SLIDER_MIDDLE_VALUE)
        self.pose_panel_layout.addWidget(self.pose_name_label)
        self.pose_panel_layout.addWidget(self.pose_name_line)
        self.pose_panel_layout.addWidget(self.pose_pitch_label)
        self.pose_panel_layout.addWidget(self.pose_pitch_slider)
        self.pose_panel_layout.addWidget(self.pose_roll_label)
        self.pose_panel_layout.addWidget(self.pose_roll_slider)
        self.pose_panel_layout.addWidget(self.pose_yaw_label)
        self.pose_panel_layout.addWidget(self.pose_yaw_slider)
        self.pose_panel_layout.addWidget(self.pose_height_label)
        self.pose_panel_layout.addWidget(self.pose_height_slider)
        self.pose_panel_layout.addWidget(self.pose_duration_label)
        self.pose_panel_layout.addWidget(self.pose_duration_slider)
        self.pose_panel_layout.addStretch()

    def format_rcam_panel(self):
        """Creates robot camera panel for widgets associated with creating a robot camera action"""
        self.rcam_panel = QtWidgets.QWidget()
        self.rcam_layout = QtWidgets.QVBoxLayout()
        self.rcam_panel.setLayout(self.rcam_layout)

        self.rcam_label = QtWidgets.QLabel(self)
        self.rcam_label.setText('Picture name:')
        self.rcam_line = QtWidgets.QLineEdit()
        self.rcam_pitch_label = QtWidgets.QLabel('Pitch', self)
        self.rcam_pitch_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.rcam_pitch_slider.setValue(SLIDER_MIDDLE_VALUE)
        self.rcam_roll_label = QtWidgets.QLabel('Roll', self)
        self.rcam_roll_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.rcam_roll_slider.setValue(SLIDER_MIDDLE_VALUE)
        self.rcam_yaw_label = QtWidgets.QLabel('Yaw', self)
        self.rcam_yaw_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.rcam_yaw_slider.setValue(SLIDER_MIDDLE_VALUE)
        self.rcam_height_label = QtWidgets.QLabel('Height', self)
        self.rcam_height_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.rcam_height_slider.setValue(SLIDER_MIDDLE_VALUE)
        self.rcam_layout.addWidget(self.rcam_label)
        self.rcam_layout.addWidget(self.rcam_line)
        self.rcam_layout.addWidget(self.rcam_pitch_label)
        self.rcam_layout.addWidget(self.rcam_pitch_slider)
        self.rcam_layout.addWidget(self.rcam_roll_label)
        self.rcam_layout.addWidget(self.rcam_roll_slider)
        self.rcam_layout.addWidget(self.rcam_yaw_label)
        self.rcam_layout.addWidget(self.rcam_yaw_slider)
        self.rcam_layout.addWidget(self.rcam_height_label)
        self.rcam_layout.addWidget(self.rcam_height_slider)
        self.rcam_layout.addStretch()

    def format_docking_panel(self):
        """Creates docking panel for widgets associated with creating a docking action"""
        self.docking_panel = QtWidgets.QWidget()
        self.docking_layout = QtWidgets.QVBoxLayout()
        self.docking_panel.setLayout(self.docking_layout)

        self.docks_list = QtWidgets.QListWidget(self)
        self.docking_layout.addWidget(self.docks_list)
        self.docking_layout.addStretch()

    def _init_walk(self):
        """Initialize walk object"""

        walk = walks_pb2.Walk()
        walk.global_parameters.self_right_attempts = RETRY_COUNT_DEFAULT
        walk.playback_mode.once.SetInParent()
        return walk

    def _update_tasks(self):
        """Updates asynchronous robot state captures"""
        self._async_tasks.update()

    def _create_element(self, name, waypoint, isAction=True):
        """Creates default autowalk Element object, populating everything except Action and ActionWrapper"""
        QtWidgets.QListWidgetItem(name, self.recorded_list)
        element = walks_pb2.Element()
        element.name = name
        element.target.navigate_to.destination_waypoint_id = waypoint.id
        element.target.navigate_to.travel_params.max_distance = TRAVEL_MAX_DIST
        element.target.navigate_to.travel_params.feature_quality_tolerance = graph_nav_pb2.TravelParams.FeatureQualityTolerance.TOLERANCE_IGNORE_POOR_FEATURE_QUALITY
        element.target.navigate_to.travel_params.blocked_path_wait_time.seconds = BLOCKED_PATH_WAIT_TIME
        element.target_failure_behavior.retry_count = RETRY_COUNT_DEFAULT
        element.target_failure_behavior.prompt_duration.seconds = PROMPT_DURATION_DEFAULT
        element.target_failure_behavior.proceed_if_able.SetInParent()
        if isAction:
            element.action_failure_behavior.retry_count = RETRY_COUNT_DEFAULT
            element.action_failure_behavior.prompt_duration.seconds = PROMPT_DURATION_DEFAULT
            element.action_failure_behavior.proceed_if_able.SetInParent()
        element.battery_monitor.battery_start_threshold = BATTERY_THRESHOLDS[0]
        element.battery_monitor.battery_stop_threshold = BATTERY_THRESHOLDS[1]
        return element

    def _save_action(self):
        """Save autowalk action by modifying walk object"""
        # Create waypoint at action location
        waypoint_response = self._recording_client.create_waypoint()

        element = walks_pb2.Element()
        if self.action_combobox.currentIndex() == POSE_INDEX:
            element = self._create_element(self.pose_name_line.text().strip(),
                                           waypoint_response.created_waypoint)
            element.action.sleep.duration.seconds = int(
                self.pose_duration_slider.value() / 10)  # Creates range of 0-9 seconds
            element.action_wrapper.robot_body_pose.target_tform_body.position.SetInParent()
            element.action_wrapper.robot_body_pose.target_tform_body.rotation.CopyFrom(
                self.euler_angles.to_quaternion())
            position = geometry_pb2.Vec3()
            position.z = self.robot_height
            element.action_wrapper.robot_body_pose.target_tform_body.position.CopyFrom(position)

        elif self.action_combobox.currentIndex() == ROBOT_CAMERA_INDEX:
            action_name = self.rcam_line.text().strip()
            element = self._create_element(action_name, waypoint_response.created_waypoint)
            daq = AcquireDataRequest()
            daq.action_id.action_name = action_name
            for img_source in IMAGE_SOURCES:
                img_request = ImageSourceCapture()
                img_request.image_service = 'image'
                img_request.image_source = img_source
                img_request.pixel_format = image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8
                daq.acquisition_requests.image_captures.append(img_request)

            data_capture_types = [
                'robot-id', 'robot-state', 'detected-objects', 'detailed-position-data',
                'basic-position-data'
            ]
            for data_type in data_capture_types:
                data_request = DataCapture()
                data_request.name = data_type
                daq.acquisition_requests.data_captures.append(data_request)
            element.action.data_acquisition.acquire_data_request.CopyFrom(daq)
            element.action.data_acquisition.completion_behavior = nodes_pb2.DataAcquisition.COMPLETE_AFTER_SAVED

            element.action_wrapper.robot_body_pose.target_tform_body.position.SetInParent()
            element.action_wrapper.robot_body_pose.target_tform_body.rotation.CopyFrom(
                self.euler_angles.to_quaternion())
            position = geometry_pb2.Vec3()
            position.z = self.robot_height
            element.action_wrapper.robot_body_pose.target_tform_body.position.CopyFrom(position)

        elif self.action_combobox.currentIndex() == DOCK_INDEX:
            if not self.dock:
                return
            end_dock = walks_pb2.Dock()
            end_dock.dock_id = self.dock

            # Create waypoint at prep pose before docking
            dock_prep_waypoint = self._recording_client.create_waypoint()
            dock_target = walks_pb2.Target()
            dock_target.navigate_to.destination_waypoint_id = dock_prep_waypoint.created_waypoint.id
            dock_target.navigate_to.travel_params.max_distance = TRAVEL_MAX_DIST
            dock_target.navigate_to.travel_params.feature_quality_tolerance = graph_nav_pb2.TravelParams.FeatureQualityTolerance.TOLERANCE_IGNORE_POOR_FEATURE_QUALITY
            dock_target.navigate_to.travel_params.blocked_path_wait_time.seconds = BLOCKED_PATH_WAIT_TIME
            end_dock.target_prep_pose.CopyFrom(dock_target)

            # Try to dock the robot
            timeout = 30
            converter = self._robot.time_sync.get_robot_time_converter()
            start_time = converter.robot_seconds_from_local_seconds(now_sec())
            cmd_end_time = start_time + timeout

            self._docking_client.docking_command_full(
                self.dock, self._robot.time_sync.endpoint.clock_identifier,
                seconds_to_timestamp(cmd_end_time), docking_pb2.PREP_POSE_SKIP_POSE)

            # Create last waypoint on top of dock
            dock_waypoint = self._recording_client.create_waypoint()
            end_dock.docked_waypoint_id = dock_waypoint.created_waypoint.id
            end_dock.prompt_duration.seconds = PROMPT_DURATION_DOCK
            self.walk.docks.append(end_dock)

            self.right_panel_stacked_widget.setCurrentIndex(RECORDED_PANEL)
            self.dock_and_end_recording = True
            QtWidgets.QListWidgetItem('Dock and Finish', self.recorded_list)
            return

        self.elements.append(element)
        self.right_panel_stacked_widget.setCurrentIndex(RECORDED_PANEL)

    def _save_autowalk(self):
        """Save autowalk in directory"""
        if not self.dock_and_end_recording:
            # Creates end waypoint and action if the last action is not docking
            self._toggle_record()
            waypoint_response = self._recording_client.create_waypoint()
            end_element = self._create_element('End Recording', waypoint_response.created_waypoint,
                                               isAction=False)
            self.elements.append(end_element)
            self._toggle_record()

        walk_name = self.autowalk_name_line.text().strip()
        self.walk.mission_name = walk_name

        # Creates walk directory and saves autowalk in format
        walk_directory = os.path.join(self.directory, f'{walk_name}.walk')
        directory_copy_number = 0
        while os.path.isdir(walk_directory):
            # Appends (number) to folder name if folder with existing name exists
            directory_copy_number += 1
            walk_directory = os.path.join(self.directory,
                                          walk_name + f'{walk_name}({directory_copy_number}).walk')
        self._graph_nav_client.write_graph_and_snapshots(walk_directory)
        self.walk.elements.extend(self.elements)
        mission_directory = os.path.join(walk_directory, 'missions')
        os.mkdir(mission_directory)
        with open(os.path.join(mission_directory, 'autogenerated.walk'), 'wb') as autowalk_file:
            autowalk_file.write(self.walk.SerializeToString())

        self._reset_walk()

    def _reset_walk(self):
        """Resets walk parameters and GUI"""
        self.right_panel_stacked_widget.setCurrentIndex(INITIAL_PANEL)
        self.walk = self._init_walk()
        self.directions_label.setText('Set up and move robot to desired starting position')
        self.record_button.setText('Start Recording')
        self.recorded_list.clear()
        self.resumed_recording = False
        self.dock_and_end_recording = False
        self._graph_nav_client.clear_graph()

    def _drive_command(self, key):
        """Maps keyboard input to robot commands"""
        if key and ord(key) in self.command_to_function:
            cmd_function = self.command_to_function[ord(key)]
            cmd_function()

    def change_action_panel(self, index):
        """Looks for fiducials before opening docking panel"""
        self.stack_widget.setCurrentIndex(index)
        if index == DOCK_INDEX:
            # Get all fiducial objects (an object of a specific type).
            self.docks_list.clear()
            request_fiducials = [world_object_pb2.WORLD_OBJECT_DOCK]
            self.fiducial_objects = self._world_object_client.list_world_objects(
                object_type=request_fiducials).world_objects
            for fiducial in self.fiducial_objects:
                QtWidgets.QListWidgetItem(str(fiducial.dock_properties.dock_id), self.docks_list)

    def choose_dock(self, item):
        """Initializes dock selection"""
        self.dock = int(item.text())

    def _change_pose(self):
        if self.stack_widget.currentIndex() == POSE_INDEX:
            pitch = np.radians(self.pose_pitch_slider.value() - SLIDER_MIDDLE_VALUE)
            roll = np.radians(self.pose_roll_slider.value() - SLIDER_MIDDLE_VALUE)
            yaw = np.radians(self.pose_yaw_slider.value() - SLIDER_MIDDLE_VALUE)
            self.robot_height = (
                self.pose_height_slider.value() - SLIDER_MIDDLE_VALUE
            ) * 0.003 - 0.15  # Maps to range (-0.15,0.15) meters from normal height
        else:
            pitch = np.radians(self.rcam_pitch_slider.value() - SLIDER_MIDDLE_VALUE)
            roll = np.radians(self.rcam_roll_slider.value() - SLIDER_MIDDLE_VALUE)
            yaw = np.radians(self.rcam_yaw_slider.value() - SLIDER_MIDDLE_VALUE)
            self.robot_height = (
                self.rcam_height_slider.value() - SLIDER_MIDDLE_VALUE
            ) * 0.003 - 0.15  # Maps to range (-0.15,0.15) meters from normal height
        self.euler_angles = geometry.EulerZXY(yaw=yaw, roll=roll, pitch=pitch)
        self._pose_command()

    def _change_pose_duration(self):
        val = int(
            self.pose_duration_slider.value() / 10)  # Creates a range between 0 and 10 seconds
        self.pose_duration_label.setText(f'Pose Duration: {val} s')

    def _change_linear_velocity(self, value):
        self.linear_velocity = value / 100  # Creates a range between 0 and 1 m/s
        self.linear_velocity_label.setText(f'Speed: {self.linear_velocity:.2f} m/s')

    def _change_angular_velocity(self, value):
        self.angular_velocity = value / 100  # Creates a range between 0 and 1 rad/s
        self.angular_velocity_label.setText(f'Turning speed: {self.angular_velocity:.2f} rad/s')

    def _change_command_duration(self, value):
        self.command_duration = value / 100  # Creates a range between 0 and 1 seconds
        self.command_duration_label.setText(f'Sensitivity: {self.command_duration:.2f} s')

    @property
    def robot_state(self):
        """Get latest robot state proto."""
        return self._robot_state_task.proto

    def _try_grpc(self, desc, thunk):
        try:
            return thunk()
        except (ResponseError, RpcError, LeaseBaseError) as err:
            print(f'Failed {desc}: {err}')
            return None

    def _try_grpc_async(self, desc, thunk):

        def on_future_done(fut):
            try:
                fut.result()
            except (ResponseError, RpcError, LeaseBaseError) as err:
                print(f'Failed {desc}: {err}')
                return None

        future = thunk()
        future.add_done_callback(on_future_done)

    def _choose_directory(self):
        """Opens directory selection dialog"""
        self.directory = str(QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Directory'))

    def _add_action(self):
        """Opens action selection panel"""
        self.right_panel_stacked_widget.setCurrentIndex(ACTION_PANEL)

    def _cancel_action(self):
        """Goes back to action summary panel"""
        self.right_panel_stacked_widget.setCurrentIndex(RECORDED_PANEL)

    def _quit_program(self):
        """Settles robot before exiting"""
        if self._lease_keepalive:
            self._lease_keepalive.shutdown()
        self.close()

    def _toggle_record(self):
        """toggle recording on/off. Initial state is OFF"""
        if self._recording_client is not None:
            recording_status = self._recording_client.get_record_status()

            if not recording_status.is_recording:
                # Start recording map
                start_recording_response = self._recording_client.start_recording_full()
                if start_recording_response.status != recording_pb2.StartRecordingResponse.STATUS_OK:
                    print(f'Error starting recording (status = {start_recording_response.status}).')
                    return False
                else:
                    self.record_button.setText('Stop Recording')
                    self.record_button.setStyleSheet('background-color: red')
                    self.right_panel_stacked_widget.setCurrentIndex(RECORDED_PANEL)
                    self.directions_label.setText('Create and record actions for Autowalk')
                    if not self.resumed_recording:
                        del self.walk.elements[:]
                        start_element = self._create_element(
                            'Start', start_recording_response.created_waypoint, isAction=False)
                        self.elements.append(start_element)

            else:
                # Stop recording map
                while True:
                    try:
                        # For some reason it doesn't work the first time, no matter what
                        stop_status = self._recording_client.stop_recording()
                        if stop_status != recording_pb2.StopRecordingResponse.STATUS_NOT_READY_YET:
                            break
                    except bosdyn.client.recording.NotReadyYetError:
                        time.sleep(0.1)

                if stop_status != recording_pb2.StopRecordingResponse.STATUS_OK:
                    print(f'Error stopping recording (status = {stop_status}).')
                    return False

                self.resumed_recording = True
                self.record_button.setText('Resume Recording')
                self.record_button.setStyleSheet('background-color: orange')
                self.right_panel_stacked_widget.setCurrentIndex(FINAL_PANEL)
                self.directions_label.setText('Review and save Autowalk')

    def _toggle_lease(self):
        """toggle lease acquisition. Initial state is acquired"""
        if self._lease_client is not None:
            if self._lease_keepalive is None:
                self._lease_keepalive = LeaseKeepAlive(self._lease_client, must_acquire=True,
                                                       return_at_exit=True)
                self.lease_label.setText('Leased')
                self.lease_label.setStyleSheet('color: green')
            else:
                self._lease_keepalive.shutdown()
                self._lease_keepalive = None
                self.lease_label.setText('Unleased')
                self.lease_label.setStyleSheet('color: red')

    def _toggle_power(self):
        """toggle motor power. Initial state is OFF"""
        power_state = self._power_state()
        if power_state is None:
            self.power_label.setText('Unknown')
            return
        if power_state == robot_state_proto.PowerState.STATE_OFF:
            self._try_grpc_async('powering-on', self._request_power_on)
            self.power_label.setText('Powered On')
            self.power_label.setStyleSheet('color: blue')

        else:
            self._try_grpc('powering-off', self._safe_power_off)
            self.power_label.setText('Powered Off')
            self.power_label.setStyleSheet('color: red')

    # Robot command implementations
    def _start_robot_command(self, desc, command_proto, end_time_secs=None):

        def _start_command():
            self._robot_command_client.robot_command(command=command_proto,
                                                     end_time_secs=end_time_secs)

        self._try_grpc(desc, _start_command)

    def _self_right(self):
        self._start_robot_command('self_right', RobotCommandBuilder.selfright_command())

    def _battery_change_pose(self):
        self._start_robot_command(
            'battery_change_pose',
            RobotCommandBuilder.battery_change_pose_command(
                dir_hint=basic_command_pb2.BatteryChangePoseCommand.Request.HINT_RIGHT))

    def _sit(self):
        self._start_robot_command('sit', RobotCommandBuilder.synchro_sit_command())

    def _stand(self):
        self._start_robot_command('stand', RobotCommandBuilder.synchro_stand_command())

    def _move_forward(self):
        self._velocity_cmd_helper('move_forward', v_x=self.linear_velocity)

    def _move_backward(self):
        self._velocity_cmd_helper('move_backward', v_x=-self.linear_velocity)

    def _strafe_left(self):
        self._velocity_cmd_helper('strafe_left', v_y=self.linear_velocity)

    def _strafe_right(self):
        self._velocity_cmd_helper('strafe_right', v_y=-self.linear_velocity)

    def _turn_left(self):
        self._velocity_cmd_helper('turn_left', v_rot=self.angular_velocity)

    def _turn_right(self):
        self._velocity_cmd_helper('turn_right', v_rot=-self.angular_velocity)

    def _stop(self):
        self._start_robot_command('stop', RobotCommandBuilder.stop_command())

    def _velocity_cmd_helper(self, desc='', v_x=0.0, v_y=0.0, v_rot=0.0):
        self._start_robot_command(
            desc, RobotCommandBuilder.synchro_velocity_command(v_x=v_x, v_y=v_y, v_rot=v_rot),
            end_time_secs=time.time() + self.command_duration)

    def _pose_command(self):
        self._start_robot_command(
            '',
            RobotCommandBuilder.synchro_trajectory_command_in_body_frame(
                0, 0, 0, self._robot.get_frame_tree_snapshot(),
                params=RobotCommandBuilder.mobility_params(body_height=self.robot_height,
                                                           footprint_R_body=self.euler_angles),
                body_height=self.robot_height), end_time_secs=time.time() + 1)

    def _request_power_on(self):
        request = PowerServiceProto.PowerCommandRequest.REQUEST_ON
        return self._power_client.power_command_async(request)

    def _safe_power_off(self):
        self._start_robot_command('safe_power_off', RobotCommandBuilder.safe_power_off_command())

    def _power_state(self):
        state = self.robot_state
        if not state:
            return None
        return state.power_state.motor_power_state


if __name__ == '__main__':
    main()
