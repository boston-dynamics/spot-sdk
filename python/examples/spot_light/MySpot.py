# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import io

import cv2
import numpy

import bosdyn.client
import bosdyn.client.lease
import bosdyn.client.util
from bosdyn import geometry
from bosdyn.client.image import ImageClient
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient, blocking_stand, block_until_arm_arrives


class MySpot(object):
    """
    This is my spot for fun
    """

    def __init__(self):
        """
        Default C'tor
        """
        # Handle to the Boston Dynamics API SDK
        self._sdk = None
        # A handle to the spot robot
        self._robot = None

        self._gripper_open = False  # TODO read somehow

        # Provide users with a command client
        self.client = None
        # Provide users with access to the logger
        self.logger = None

        # A handle to the lease for the robot connected
        self._lease = None
        self._lease_client = None
        self._lease_keep_alive = None

    def __del__(self):
        """
        D'tor to clean up after ourself
        """
        # Nothing to do for now

    def connect(self, config):
        """
        Connect to a spot robot.

        @param[in]  config  The configuration to use when connecting
        """
        sdk_name = 'MySpot_sdk'

        # Create the SDK
        self._sdk = bosdyn.client.create_standard_sdk(sdk_name)

        # Use the SDK to create a robot
        self._robot = self._sdk.create_robot(config.hostname)
        bosdyn.client.util.authenticate(self._robot)

        assert self._prep_for_motion()
        self.client = self._robot.ensure_client(RobotCommandClient.default_service_name)

        bosdyn.client.util.setup_logging(config.verbose)
        self.logger = self._robot.logger

    def get_image(self):
        """
        Get an image from the front left camera
        """

        if self._robot is None:
            return 0

        # Get image data from robot
        image_client = self._robot.ensure_client(ImageClient.default_service_name)
        image_response = image_client.get_image_from_sources(['frontleft_fisheye_image'])
        # Convert the image data to an openCV image
        img_stream = io.BytesIO(image_response[0].shot.image.data)
        img = cv2.imdecode(numpy.frombuffer(img_stream.read(), numpy.uint8), 1)

        # Rotate the image so it alight better with the real world
        angle = 90
        rot_img = self._rotate_bound(img, angle)
        return rot_img

    def stand_up(self):
        """
        Ask Spot to stand up
        """
        if self._robot is None:
            return

        blocking_stand(self.client, timeout_sec=10)

    def sit_down(self):
        """
        Ask Spot to sit down
        """
        if self._robot is None:
            return

        cmd = RobotCommandBuilder.synchro_sit_command()
        self.client.robot_command(cmd)

    def stow_arm(self):
        """
        Ask Spot to sit down
        """
        if self._robot is None:
            return

        # Stow the arm
        # Build the stow command using RobotCommandBuilder
        stow = RobotCommandBuilder.arm_stow_command()

        # Issue the command via the RobotCommandClient
        stow_command_id = self.client.robot_command(stow)

        self.logger.info('Stow command issued.')
        block_until_arm_arrives(self.client, stow_command_id, 3.0)

    def _prep_for_motion(self):
        """
        Prepare the robot for motion

        @return  True if robot is ready for motion command; false otherwise
        """
        if self._robot is None:
            return False

        # Establish time sync with the robot
        self._robot.time_sync.wait_for_sync()

        # Verify the robot is not estopped
        assert not self._robot.is_estopped(), 'Robot is estopped. ' \
                                              'Please use an external E-Stop client, ' \
                                              'such as the estop SDK example, to configure E-Stop.'

        # Acquire a lease to indicate that we want to control the robot
        if self._lease_client is None:
            self._lease_client = self._robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
            self._lease = self._lease_client.take()
            self._lease_keep_alive = bosdyn.client.lease.LeaseKeepAlive(self._lease_client)

        # Power the motor on
        if not self._robot.is_powered_on():
            self._robot.power_on(timeout_sec=20)

        return self._robot.is_powered_on()

    def toggle_lease(self):
        """toggle lease acquisition. Initial state is acquired"""
        if self._lease_client is not None:
            if self._lease_keep_alive is None:
                self._lease_keep_alive = bosdyn.client.lease.LeaseKeepAlive(self._lease_client, must_acquire=True,
                                                                            return_at_exit=True)
                self.logger.info("Lease acquired")
            else:
                self._lease_keep_alive.shutdown()
                self._lease_keep_alive = None
                self.logger.warn("Lease released")

    def toggle_gripper(self):
        """open/close gripper. Initial state is assumed to be closed"""
        if self._gripper_open:
            cmd_id = self.client.robot_command(RobotCommandBuilder.claw_gripper_close_command())
        else:
            cmd_id = self.client.robot_command(RobotCommandBuilder.claw_gripper_open_command())
        self._gripper_open = not self._gripper_open

    def power_off(self):
        """
        Power off spot robot.
        """
        # Power the robot off. By specifying "cut_immediately=False", a safe power off command
        # is issued to the robot. This will attempt to sit the robot before powering off.
        self._robot.power_off(cut_immediately=False, timeout_sec=20)
        assert not self._robot.is_powered_on(), 'Robot power off failed.'
        self.logger.info('Robot safely powered off.')

        # TODO proper disconnect
        self._lease_client.return_lease(self._lease)
