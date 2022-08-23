# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Interactively set the focus region of the gripper camera."""

import argparse
import sys

import cv2
import numpy as np
from google.protobuf import wrappers_pb2

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import geometry_pb2, gripper_camera_param_pb2, image_pb2
from bosdyn.client.gripper_camera_param import GripperCameraParamClient
from bosdyn.client.image import ImageClient

g_image_click = None
g_image_display = None
g_mouse_pos = None

# Example that gets an image from the gripper camera and allows the user to click on a point
# in the image for the auto-focus to focus on.
#
# Also sets the auto-exposure to that position.


def main(argv):
    # Parse args
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)

    parser.add_argument('-e', '--exposure', action='store_true',
                        help='Set the exposure region of interest (ROI) instead of the focus.')
    parser.add_argument('-w', '--window-size', help='Set the ROI window size, valid options: [1-8]',
                        type=int)

    options = parser.parse_args(argv)

    if options.window_size:
        if options.window_size < 1 or options.window_size > 8:
            print('Error: window size must be between 1 and 8, inclusive.')
            sys.exit(1)

    sdk = bosdyn.client.create_standard_sdk('gripper_camera_focus_region')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    gripper_camera_param_client = robot.ensure_client(GripperCameraParamClient.default_service_name)

    image_client = robot.ensure_client(ImageClient.default_service_name)

    if options.exposure:
        image_title = 'Click to set Exposure'
    else:
        image_title = 'Click to Focus'
    cv2.namedWindow(image_title)
    cv2.setMouseCallback(image_title, cv_mouse_callback)

    while True:
        img = get_hand_color_image(image_client)

        # Show the image to the user and wait for them to click on a pixel
        print('Click on an area to select it. Press "q" to quit.')

        global g_image_click, g_image_display, g_mouse_pos
        g_image_display = img
        cv2.imshow(image_title, g_image_display)
        while g_image_click is None:
            img = get_hand_color_image(image_client)
            draw_lines(image_title, img, g_mouse_pos)
            g_image_display = img
            cv2.imshow(image_title, g_image_display)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == ord('Q'):
                # Quit
                print('"q" pressed, exiting.')
                exit(0)

        print('Clicked at (' + str(g_image_click[0]) + ', ' + str(g_image_click[1]) + ')')

        # Covert coordinate to percentage in image
        percent_x = g_image_click[0] / img.shape[1]
        percent_y = g_image_click[1] / img.shape[0]

        # Send a message asking for focus or exposure on that place.
        roi_percent = geometry_pb2.Vec2(x=percent_x, y=percent_y)

        if options.window_size:
            roi_size = options.window_size  # enum values match numbers
        else:
            roi_size = gripper_camera_param_pb2.RoiParameters.ROI_WINDOW_SIZE_1
        roi = gripper_camera_param_pb2.RoiParameters(roi_percentage_in_image=roi_percent,
                                                     window_size=roi_size)

        if not options.exposure:
            # Auto-focus must be enabled for focus ROI.
            focus_auto = wrappers_pb2.BoolValue(value=True)

            # Tell the camera firmware to draw a rectangle on the region.
            draw_focus_rectangle = wrappers_pb2.BoolValue(value=True)

            params = gripper_camera_param_pb2.GripperCameraParams(
                focus_roi=roi, focus_auto=focus_auto, draw_focus_roi_rectangle=draw_focus_rectangle)

        else:
            # Auto-exposure must be enabled for exposure ROI.
            exposure_auto = wrappers_pb2.BoolValue(value=True)

            # Sometimes the camera refocuses after setting the exposure, which can be
            # confusing if we just set a focus region, because it will draw a box around
            # the focus region, so we disable that drawing here.
            draw_focus_rectangle = wrappers_pb2.BoolValue(value=False)

            params = gripper_camera_param_pb2.GripperCameraParams(
                exposure_roi=roi,
                exposure_auto=exposure_auto,
                draw_focus_roi_rectangle=draw_focus_rectangle,
            )

        # Send the request
        request = gripper_camera_param_pb2.GripperCameraParamRequest(params=params)
        gripper_camera_param_client.set_camera_params(request)

        print('Sending request:')
        print(request)

        g_image_click = None

    return True


def get_hand_color_image(image_client):
    image_responses = image_client.get_image_from_sources(['hand_color_image'])
    if len(image_responses) != 1:
        print('Error: did not get exactly one image response.')
        sys.exit(1)

    resp = image_responses[0]

    # Display the image to the user
    image = image_responses[0]
    if image.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_DEPTH_U16:
        dtype = np.uint16
    else:
        dtype = np.uint8
    img = np.fromstring(image.shot.image.data, dtype=dtype)
    if image.shot.image.format == image_pb2.Image.FORMAT_RAW:
        img = img.reshape(image.shot.image.rows, image.shot.image.cols)
    else:
        img = cv2.imdecode(img, -1)

    return img


def cv_mouse_callback(event, x, y, flags, param):
    global g_image_click, g_image_display, g_mouse_pos
    clone = g_image_display.copy()
    if event == cv2.EVENT_LBUTTONUP:
        g_image_click = (x, y)
    else:
        # Draw some lines on the image.
        #print('mouse', x, y)
        g_mouse_pos = (x, y)


def draw_lines(image_title, img, mouse_pos):
    if mouse_pos is None:
        return
    x = mouse_pos[0]
    y = mouse_pos[1]
    color = (30, 30, 30)
    thickness = 2
    height = img.shape[0]
    width = img.shape[1]
    cv2.line(img, (0, y), (width, y), color, thickness)
    cv2.line(img, (x, 0), (x, height), color, thickness)
    cv2.imshow(image_title, img)


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
