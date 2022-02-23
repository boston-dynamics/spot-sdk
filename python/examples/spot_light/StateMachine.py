# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import cv2
import numpy


class StateMachine(object):
    """
    This is the base state machine class to manipulate Spot
    """

    def __init__(self, name, robot):
        """
        Default C'tor

        @param[in]  name   The name of this state machine
        @param[in]  robot  The handle to the robot
        """
        # Enable / disable flag
        self.enable = False
        # The next state that follows this one
        self.next_state = None

        # Current index within this state machine
        self._state_idx = 0
        # Name of this state
        self._name = name
        # The handle to the robot
        self._robot = robot
        # The list of sub state functions to execute
        self._state_funcs = []
        # Count for light detection
        self._light_count = 0

    def __del__(self):
        """
        D'tor to clean up after ourself
        """
        # Nothing to do for now

    def exe(self):
        """
        Execute the state machine
        """
        # If we're not currently enabled, reset ourself
        if not self.enable:
            self._state_idx = 0
            return

        # Execute our states
        if self._state_idx < len(self._state_funcs):
            self._state_funcs[self._state_idx]()
        else:
            # Turn ourself off
            self.enable = False
            # Switch on the next state if we have one
            if self.next_state is not None:
                self.next_state.enable = True

    def _state_init(self):
        """
        Initial state
        """
        print('See Spot {}.'.format(self._name))
        self._state_idx = self._state_idx + 1

    def _state_look_for_light(self):
        """
        Grab an image from one of the forward looking camera and look for a saturated spot near center
        """

        try:
            # Get an image from the robot
            img = self._robot.get_image()

            # Crop the image to our ROI
            roi = self._crop_img(img)

            # Detect a blob
            light_found, roi_with_keypoints, _ = self._detect_blob(roi)

            if light_found and self._light_count > 50:
                self._state_idx = self._state_idx + 1
                self._light_count = 0
                cv2.imwrite('test_{}.png'.format(self._name.lower()), img)

            self._light_count = self._light_count + 1
            cv2.imshow('', roi_with_keypoints)
            cv2.waitKey(10)
        except TypeError as err:
            print(err)

    def _detect_blob(self, img, min_area=2500):
        """
        Detect largest blob in the given image with area greater than the given minimum

        @param[in]  img       The image to analysis
        @param[in]  min_area  The minimum area to look for [pixel^2]

        @return  True if area found, Image with blob marked, centroid of the blob found
        """

        # Note:  Did not use SimpleBlobDetector because it didn't seem to like irregular shapes

        # Binarize the image
        grey_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        ret, bin_img = cv2.threshold(grey_img, 250, 255, cv2.THRESH_BINARY)

        # Noise removal
        kernel = numpy.ones((3, 3), numpy.uint8)
        filt_img = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel, iterations=2)

        # Finding sure foreground area
        dist_transform = cv2.distanceTransform(filt_img, cv2.DIST_L2, 5)
        ret, sure_fg = cv2.threshold(dist_transform, 0.25 * dist_transform.max(), 255, 0)
        sure_fg = numpy.uint8(sure_fg)

        # CC analysis
        connectivity = 8
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            sure_fg, connectivity, cv2.CV_32S)

        area_found = False
        blob_center = [0, 0]
        img_with_keypoints = img.copy()

        # See if we found more than the background (background is always at 0)
        if num_labels > 1:
            # Find the largest area
            largest_label_idx = numpy.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1
            # Make sure the blob is big enough
            if stats[largest_label_idx, cv2.CC_STAT_AREA] > min_area:
                area_found = True
                img_with_keypoints[labels == largest_label_idx] = [0, 0, 255]
                blob_center = centroids[largest_label_idx]

        return area_found, img_with_keypoints, blob_center

    def _crop_img(self, img):
        """
        Crop the given image to the ROI

        @param[in]  img  The image to crop

        @return  The cropped image
        """
        # Find the center of the image
        img_height, img_width, img_channels = img.shape
        img_center_x = img_width // 2
        img_center_y = img_height // 2

        # The ROI is at the center of the image with half the width and height
        x1 = int(img_center_x * 0.5)
        x2 = x1 + img_center_x
        y1 = int(img_center_y * 0.5)
        y2 = y1 + img_center_y

        # Crop it to the ROI
        roi = img[y1:y2, x1:x2]

        return roi


#===================================================================================================


class StateMachineSit(StateMachine):
    """
    Sit state.  In this state spot will sit and wait until it sees the light.
    """

    def __init__(self, robot):
        """
        Default C'tor

        @param[in]  robot  The handle to the robot
        """
        super(StateMachineSit, self).__init__('Sit', robot)

        # Line up our states
        self._state_funcs = [self._state_init, self._state_sit, self._state_look_for_light]

    def _state_sit(self):
        """
        Command the robot to sit
        """
        print('Spot is going to {}.'.format(self._name.lower()))
        self._robot.sit_down()
        self._state_idx = self._state_idx + 1

        print("\n Shine a light in Spot's front left camera for Spot to stand.\n")


#===================================================================================================


class StateMachineStand(StateMachine):
    """
    Stand state.  In this state spot will stand and wait until it sees the light.
    """

    def __init__(self, robot):
        """
        Default C'tor

        @param[in]  robot  The handle to the robot
        """
        super(StateMachineStand, self).__init__('Stand', robot)

        # Line up our states
        self._state_funcs = [self._state_init, self._state_stand, self._state_look_for_light]

    def _state_stand(self):
        """
        Command the robot to stand
        """
        print('Spot is going to {}.'.format(self._name.lower()))
        self._robot.stand_up()
        self._state_idx = self._state_idx + 1

        print(
            "\n Shine a light in Spot's front left camera, and Spot will tilt to follow the light.\n"
        )


#===================================================================================================


class StateMachineFollow(StateMachine):
    """
    Follow state.  In this state spot will rotate its body to follow the light.
    """

    def __init__(self, robot):
        """
        Default C'tor

        @param[in]  robot  The handle to the robot
        """
        from simple_pid import PID

        super(StateMachineFollow, self).__init__('Follow', robot)

        # The initial pointing position
        self._init_pt = None
        # Our PID controller
        self._pitch_pid = PID(0.5, 0.5, 0, setpoint=0)
        self._yaw_pid = PID(0.5, 0.5, 0, setpoint=0)

        # Line up our states
        self._state_funcs = [self._state_init, self._state_follow]

    def _state_follow(self):
        """
        Spot will position its body to follow the light
        """
        from simple_pid import PID

        try:
            # Get an image from the robot
            img = self._robot.get_image()

            # Find the center of the image
            img_height, img_width, _ = img.shape
            img_center_x = img_width // 2
            img_center_y = img_height // 2

            # The ROI is at the center of the image with half the width and height
            # The following crops the corner where is the plastic reflects the cmd light
            x1 = 0
            x2 = int(0.8 * img_width)
            y1 = 0
            y2 = int(0.8 * img_height)

            # Crop it to the ROI
            roi = img[y1:y2, x1:x2]

            # Detect a blob
            light_found, img_with_keypoints, pt = self._detect_blob(roi, 3500)

            # Check to see if we see a blob
            if not light_found:

                # If we have an initial point that mean we were following
                # and now the light is gone, so we'll stop
                if self._init_pt is not None and self._light_count > 50:
                    self._state_idx = self._state_idx + 1
                    self._init_pt = None
                    self._light_count = 0

                self._light_count = self._light_count + 1
                cv2.imshow('', roi)
                cv2.waitKey(5)
                return

            # Save the initial point if we don't have one yet
            if self._init_pt is None:
                self._init_pt = pt

            # Mark the 2 points for visualization
            cv2.drawMarker(img_with_keypoints, tuple(map(int, pt)), (255, 0, 0))
            cv2.drawMarker(img_with_keypoints, tuple(map(int, self._init_pt)), (0, 255, 0))

            # Maximum angle range is +/- 0.5 [rad]
            MAX_ANGLE = 0.50
            self._pitch_pid.output_limits = (-MAX_ANGLE, MAX_ANGLE)

            # Figure out how much to yaw and pitch
            adj = numpy.divide(numpy.subtract(self._init_pt, pt), self._init_pt) * MAX_ANGLE
            yaw_cmd = self._yaw_pid(-adj[0])
            pitch_cmd = self._pitch_pid(adj[1])

            # Add text to show adjustment value
            font = cv2.FONT_HERSHEY_SIMPLEX
            bottom_left = (25, 25)
            scale = 0.5
            color = (0, 255, 0)
            lineType = 1
            disp_text = 'Yaw: {}     Pitch: {}'.format(adj[0], pitch_cmd)
            cv2.putText(img_with_keypoints, disp_text, bottom_left, font, scale, color, lineType)

            cv2.imshow('', img_with_keypoints)
            cv2.waitKey(5)

            self._robot.orient(yaw_cmd, pitch_cmd, 0)
            test = 0

        except TypeError as err:
            print(err)
