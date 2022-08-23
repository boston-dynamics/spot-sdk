# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
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
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient, blocking_stand


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

        # A handle to the lease for the robot connected
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

        bosdyn.client.util.setup_logging(config.verbose)

        # Create the SDK
        self._sdk = bosdyn.client.create_standard_sdk(sdk_name)

        # Use the SDK to create a robot
        self._robot = self._sdk.create_robot(config.hostname)
        bosdyn.client.util.authenticate(self._robot)

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

        if self._prep_for_motion():
            command_client = self._robot.ensure_client(RobotCommandClient.default_service_name)
            blocking_stand(command_client, timeout_sec=10)

    def sit_down(self):
        """
        Ask Spot to sit down
        """
        if self._robot is None:
            return

        if self._prep_for_motion():
            command_client = self._robot.ensure_client(RobotCommandClient.default_service_name)
            cmd = RobotCommandBuilder.synchro_sit_command()
            command_client.robot_command(cmd)

    def orient(self, yaw=0.0, pitch=0.0, roll=0.0):
        """
        Ask Spot to orient its body (e.g. yaw, pitch, roll)

        @param[in]  yaw    Rotation about Z (+up/down) [rad]
        @param[in]  pitch  Rotation about Y (+left/right) [rad]
        @param[in]  roll   Rotation about X (+front/back) [rad]
        """

        if self._robot is None:
            return

        if self._prep_for_motion():
            rotation = geometry.EulerZXY(yaw=yaw, pitch=pitch, roll=roll)
            command_client = self._robot.ensure_client(RobotCommandClient.default_service_name)
            cmd = RobotCommandBuilder.synchro_stand_command(footprint_R_body=rotation)
            command_client.robot_command(cmd)

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
        assert not self._robot.is_estopped(), "Robot is estopped. " \
                                              "Please use an external E-Stop client, " \
                                              "such as the estop SDK example, to configure E-Stop."

        # Acquire a lease to indicate that we want to control the robot
        if self._lease_client is None:
            self._lease_client = self._robot.ensure_client(
                bosdyn.client.lease.LeaseClient.default_service_name)
            lease = self._lease_client.acquire()
            self._lease_keep_alive = bosdyn.client.lease.LeaseKeepAlive(self._lease_client)

        # Power the motor on
        if not self._robot.is_powered_on():
            self._robot.power_on(timeout_sec=20)

        return self._robot.is_powered_on()

    def _rotate_bound(self, image, angle):
        """
        Rotate the image without cutting portions of the image off
        From https://www.pyimagesearch.com/2017/01/02/rotate-images-correctly-with-opencv-and-python/

        @param[in]  image  The image to rotate
        @param[in]  angle  The angle [deg] to rotate the image by
        """

        # grab the dimensions of the image and then determine the
        # center
        (h, w) = image.shape[:2]
        (cX, cY) = (w // 2, h // 2)

        # grab the rotation matrix (applying the negative of the
        # angle to rotate clockwise), then grab the sine and cosine
        # (i.e., the rotation components of the matrix)
        M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
        cos = numpy.abs(M[0, 0])
        sin = numpy.abs(M[0, 1])

        # compute the new bounding dimensions of the image
        nW = int((h * sin) + (w * cos))
        nH = int((h * cos) + (w * sin))

        # adjust the rotation matrix to take into account translation
        M[0, 2] += (nW / 2) - cX
        M[1, 2] += (nH / 2) - cY

        # perform the actual rotation and return the image
        return cv2.warpAffine(image, M, (nW, nH))
