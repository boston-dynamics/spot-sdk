# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Set the gripper camera parameter settings from the robot."""

import argparse
import sys
import time

import get_gripper_camera_params
from google.protobuf import wrappers_pb2

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import gripper_camera_param_pb2, header_pb2
from bosdyn.client.gripper_camera_param import GripperCameraParamClient


def main(argv):
    # Parse args
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)

    parser.add_argument(
        '--resolution',
        choices=['640x480', '1280x720', '1920x1080', '3840x2160', '4096x2160',
                 '4208x3120'], help='Resolution of the camera')
    parser.add_argument('--brightness', type=float, help='Brightness value, 0.0 - 1.0')
    parser.add_argument('--contrast', type=float, help='Contrast value, 0.0 - 1.0')
    parser.add_argument('--saturation', type=float, help='Saturation value, 0.0 - 1.0')
    parser.add_argument('--gain', type=float, help='Gain value, 0.0 - 1.0')
    parser.add_argument('--exposure', type=float, help='Exposure value, 0.0 - 1.0')
    parser.add_argument('--manual-focus', type=float, help='Manual focus value , 0.0 - 1.0')
    parser.add_argument('--auto-exposure', choices=['on', 'off'],
                        help='Enable/disable auto-exposure')
    parser.add_argument('--auto-focus', choices=['on', 'off'], help='Enable/disable auto-focus')
    parser.add_argument(
        '--hdr-mode', choices=['off', 'auto', 'manual1', 'manual2', 'manual3', 'manual4'], help=
        'On-camera high dynamic range (HDR) setting.  manual1-4 modes enable HDR with 1 the minimum HDR setting and 4 the maximum'
    )
    parser.add_argument('--led-mode', choices=['off', 'torch'],
                        help='LED mode. "torch": On all the time.')
    parser.add_argument('--led-torch-brightness', type=float,
                        help='LED brightness value when on all the time, 0.0 - 1.0')

    options = parser.parse_args(argv)

    sdk = bosdyn.client.create_standard_sdk('gripper_camera_params')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    gripper_camera_param_client = robot.ensure_client(GripperCameraParamClient.default_service_name)

    # Camera resolution
    camera_mode = None
    if options.resolution is not None:
        if options.resolution == '640x480':
            camera_mode = gripper_camera_param_pb2.GripperCameraParams.MODE_640_480_120FPS_UYVY
        elif options.resolution == '1280x720':
            camera_mode = gripper_camera_param_pb2.GripperCameraParams.MODE_1280_720_60FPS_UYVY
        elif options.resolution == '1920x1080':
            camera_mode = gripper_camera_param_pb2.GripperCameraParams.MODE_1920_1080_60FPS_MJPG
        elif options.resolution == '3840x2160':
            camera_mode = gripper_camera_param_pb2.GripperCameraParams.MODE_3840_2160_30FPS_MJPG
        elif options.resolution == '4096x2160':
            camera_mode = gripper_camera_param_pb2.GripperCameraParams.MODE_4096_2160_30FPS_MJPG
        elif options.resolution == '4208x3120':
            camera_mode = gripper_camera_param_pb2.GripperCameraParams.MODE_4208_3120_20FPS_MJPG

    # Other settings
    brightness = None
    if options.brightness is not None:
        brightness = wrappers_pb2.FloatValue(value=options.brightness)

    contrast = None
    if options.contrast is not None:
        contrast = wrappers_pb2.FloatValue(value=options.contrast)

    saturation = None
    if options.saturation is not None:
        saturation = wrappers_pb2.FloatValue(value=options.saturation)

    gain = None
    if options.gain is not None:
        gain = wrappers_pb2.FloatValue(value=options.gain)

    if options.manual_focus is not None and options.auto_focus and options.auto_focus == 'on':
        print('Error: cannot specify both a manual focus value and enable auto-focus.')
        sys.exit(1)

    manual_focus = None
    auto_focus = None
    if options.manual_focus:
        manual_focus = wrappers_pb2.FloatValue(value=options.manual_focus)
        auto_focus = wrappers_pb2.BoolValue(value=False)

    if options.auto_focus is not None:
        auto_focus_enabled = options.auto_focus == 'on'
        auto_focus = wrappers_pb2.BoolValue(value=auto_focus_enabled)

    if options.exposure is not None and options.auto_exposure and options.auto_exposure == 'on':
        print('Error: cannot specify both a manual exposure value and enable auto-exposure.')
        sys.exit(1)

    exposure = None
    auto_exposure = None
    if options.exposure is not None:
        exposure = wrappers_pb2.FloatValue(value=options.exposure)
        auto_exposure = wrappers_pb2.BoolValue(value=False)

    if options.auto_exposure:
        auto_exposure_enabled = options.auto_exposure == 'on'
        auto_exposure = wrappers_pb2.BoolValue(value=auto_exposure_enabled)

    hdr = None
    if options.hdr_mode is not None:
        if options.hdr_mode == 'off':
            hdr = gripper_camera_param_pb2.HDR_OFF
        elif options.hdr_mode == 'auto':
            hdr = gripper_camera_param_pb2.HDR_AUTO
        elif options.hdr_mode == 'manual1':
            hdr = gripper_camera_param_pb2.HDR_MANUAL_1
        elif options.hdr_mode == 'manual2':
            hdr = gripper_camera_param_pb2.HDR_MANUAL_2
        elif options.hdr_mode == 'manual3':
            hdr = gripper_camera_param_pb2.HDR_MANUAL_3
        elif options.hdr_mode == 'manual4':
            hdr = gripper_camera_param_pb2.HDR_MANUAL_4

    led_mode = None
    if options.led_mode is not None:
        if options.led_mode == 'off':
            led_mode = gripper_camera_param_pb2.GripperCameraParams.LED_MODE_OFF
        elif options.led_mode == 'torch':
            led_mode = gripper_camera_param_pb2.GripperCameraParams.LED_MODE_TORCH

    led_torch_brightness = None
    if options.led_torch_brightness is not None:
        led_torch_brightness = wrappers_pb2.FloatValue(value=options.led_torch_brightness)

    params = gripper_camera_param_pb2.GripperCameraParams(
        camera_mode=camera_mode, brightness=brightness, contrast=contrast, gain=gain,
        saturation=saturation, focus_absolute=manual_focus, focus_auto=auto_focus,
        exposure_absolute=exposure, exposure_auto=auto_exposure, hdr=hdr, led_mode=led_mode,
        led_torch_brightness=led_torch_brightness)

    request = gripper_camera_param_pb2.GripperCameraParamRequest(params=params)

    # Send the request
    response = gripper_camera_param_client.set_camera_params(request)
    print('Sent request.')

    if response.header.error and response.header.error.code != header_pb2.CommonError.CODE_OK:
        print('Got an error:')
        print(response.header.error)

    print('Now querying robot for current settings.')

    # Send a request for the current gripper camera parameters
    time.sleep(3)
    request = gripper_camera_param_pb2.GripperCameraGetParamRequest()
    response = gripper_camera_param_client.get_camera_params(request)
    return get_gripper_camera_params.print_response_from_robot(response)


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
