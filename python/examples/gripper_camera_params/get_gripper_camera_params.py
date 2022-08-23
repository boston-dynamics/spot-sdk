# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Get the current gripper camera parameter settings from the robot."""

import argparse
import sys

from google.protobuf import wrappers_pb2

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import gripper_camera_param_pb2, header_pb2
from bosdyn.client.gripper_camera_param import GripperCameraParamClient


def main(argv):
    # Parse args
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)

    options = parser.parse_args(argv)

    # Create robot object
    sdk = bosdyn.client.create_standard_sdk('get_gripper_camera_params')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    gripper_camera_param_client = robot.ensure_client(GripperCameraParamClient.default_service_name)

    request = gripper_camera_param_pb2.GripperCameraGetParamRequest()

    # Send the request
    response = gripper_camera_param_client.get_camera_params(request)

    return print_response_from_robot(response)


def print_response_from_robot(response):
    if response.header.error and response.header.error.code != header_pb2.CommonError.CODE_OK:
        print('Got an error:')
        print(response.header.error)
    else:
        params = response.params

        print_line('Resolution', mode_to_resolution_str(params.camera_mode))
        print_line('Brightness', '{:.2f}'.format((params.brightness.value)))
        print_line('Contrast', '{:.2f}'.format(params.contrast.value))
        print_line('Saturation', '{:.2f}'.format(params.saturation.value))
        print_line('Gain', '{:.2f}'.format(params.gain.value))

        if params.HasField('focus_absolute'):
            print_line('Focus', 'manual (' + '{:.2f}'.format(params.focus_absolute.value) + ')')
        else:
            print_line('Focus', 'auto')

        if params.HasField('exposure_absolute'):
            print_line('Exposure',
                       'manual (' + '{:.2f}'.format(params.exposure_absolute.value) + ')')
        else:
            print_line('Exposure', 'auto')

        if not params.HasField('exposure_roi'):
            print_line('Exposure ROI', 'unset')
        else:
            print_line(
                'Exposure ROI',
                '(' + '{:.2f}, {:.2f}'.format(params.exposure_roi.roi_percentage_in_image.x,
                                              params.exposure_roi.roi_percentage_in_image.y) +
                ') window size: ' + gripper_camera_param_pb2.RoiParameters.RoiWindowSize.Name(
                    params.exposure_roi.window_size))

        print_line('Draw focus ROI', str(params.draw_focus_roi_rectangle.value))

        if params.hdr == gripper_camera_param_pb2.HDR_UNKNOWN:
            print_line('HDR', 'HDR_OFF')
        else:
            print_line('HDR', gripper_camera_param_pb2.HdrParameters.Name(params.hdr))

        if not params.HasField('focus_roi'):
            print_line('Focus ROI', 'unset')
        else:
            print_line(
                'Focus ROI',
                '(' + '{:.2f}, {:.2f}'.format(params.focus_roi.roi_percentage_in_image.x,
                                              params.focus_roi.roi_percentage_in_image.y) +
                ') window size: ' + gripper_camera_param_pb2.RoiParameters.RoiWindowSize.Name(
                    params.focus_roi.window_size))

        if params.led_mode == gripper_camera_param_pb2.GripperCameraParams.LED_MODE_UNKNOWN:
            print_line('LED mode', 'LED_MODE_OFF')
        else:
            print_line('LED mode',
                       gripper_camera_param_pb2.GripperCameraParams.LedMode.Name(params.led_mode))

        if not params.HasField('led_torch_brightness'):
            print_line('LED torch brightness', 'unset')
        else:
            print_line('LED torch brightness', '{:.2f}'.format(params.led_torch_brightness.value))

    return True


def print_line(label, value):
    print(label + ' ' + ''.rjust(35 - len(label), '.') + ' ' + value)


def mode_to_resolution_str(mode):
    if mode == gripper_camera_param_pb2.GripperCameraParams.MODE_640_480_120FPS_UYVY:
        return '640x480'
    elif mode == gripper_camera_param_pb2.GripperCameraParams.MODE_1280_720_60FPS_UYVY:
        return '1280x720'
    elif mode == gripper_camera_param_pb2.GripperCameraParams.MODE_1920_1080_60FPS_MJPG:
        return '1920x1080'
    elif mode == gripper_camera_param_pb2.GripperCameraParams.MODE_3840_2160_30FPS_MJPG:
        return '3840x2160'
    elif mode == gripper_camera_param_pb2.GripperCameraParams.MODE_4096_2160_30FPS_MJPG:
        return '4096x2160'
    elif mode == gripper_camera_param_pb2.GripperCameraParams.MODE_4208_3120_20FPS_MJPG:
        return '4208x3120'
    return str(mode)


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
