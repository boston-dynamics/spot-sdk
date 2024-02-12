# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
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


def main():
    # Parse args
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)

    options = parser.parse_args()

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
        print_line('Brightness', f'{params.brightness.value:.2f}')
        print_line('Contrast', f'{params.contrast.value:.2f}')
        print_line('Saturation', f'{params.saturation.value:.2f}')
        print_line('Gain', f'{params.gain.value:.2f}')

        if params.HasField('focus_auto') and params.focus_auto.value is True:
            print_line('Focus', 'auto')
        else:
            print_line('Focus', 'manual')

        if params.HasField('focus_absolute'):
            print_line('Focus', f'value ({params.focus_absolute.value:.2f})')

        if params.HasField('exposure_absolute'):
            print_line('Exposure', f'manual ({params.exposure_absolute.value:.2f})')
        else:
            print_line('Exposure', 'auto')

        if not params.HasField('exposure_roi'):
            print_line('Exposure ROI', 'unset')
        else:
            exposure_roi_percentage_x = params.exposure_roi.roi_percentage_in_image.x
            exposure_roi_percentage_y = params.exposure_roi.roi_percentage_in_image.y
            roi_window_size = gripper_camera_param_pb2.RoiParameters.RoiWindowSize.Name(
                params.exposure_roi.window_size)
            print_line(
                'Exposure ROI',
                f'({exposure_roi_percentage_x:.2f}, {exposure_roi_percentage_y:.2f}) '
                f'window size: {roi_window_size}')

        print_line('Draw focus ROI', str(params.draw_focus_roi_rectangle.value))

        if params.hdr == gripper_camera_param_pb2.HDR_UNKNOWN:
            print_line('HDR', 'HDR_OFF')
        else:
            print_line('HDR', gripper_camera_param_pb2.HdrParameters.Name(params.hdr))

        if not params.HasField('focus_roi'):
            print_line('Focus ROI', 'unset')
        else:
            focus_roi_percentage_x = params.focus_roi.roi_percentage_in_image.x
            focus_roi_percentage_y = params.focus_roi.roi_percentage_in_image.y
            roi_window_size = gripper_camera_param_pb2.RoiParameters.RoiWindowSize.Name(
                params.focus_roi.window_size)

            print_line(
                'Focus ROI', f'({focus_roi_percentage_x:.2f}, {focus_roi_percentage_y:.2f}) '
                f'window size: {roi_window_size}')

        if params.led_mode == gripper_camera_param_pb2.GripperCameraParams.LED_MODE_UNKNOWN:
            print_line('LED mode', 'LED_MODE_OFF')
        else:
            print_line('LED mode',
                       gripper_camera_param_pb2.GripperCameraParams.LedMode.Name(params.led_mode))

        if not params.HasField('led_torch_brightness'):
            print_line('LED torch brightness', 'unset')
        else:
            print_line('LED torch brightness', f'{params.led_torch_brightness.value:.2f}')

        if not params.HasField('gamma'):
            print_line('gamma', 'unset')
        else:
            print_line('gamma', f'{params.gamma.value:.2f}')

        if not params.HasField('sharpness'):
            print_line('sharpness', 'unset')
        else:
            print_line('sharpness', f'{params.sharpness.value:.2f}')

        if not params.HasField('white_balance_temperature') and not params.HasField(
                'white_balance_temperature_auto'):
            print_line('white_balance_temperature', 'unset')
        elif params.HasField('white_balance_temperature'):
            print_line('white_balance_temperature',
                       f'manual ({params.white_balance_temperature.value:.2f})')
        elif params.HasField('white_balance_temperature_auto'):
            print_line('white_balance_temperature', 'auto')

    return True


def print_line(label, value):
    print(f'{label} {"".rjust(35 - len(label), ".")} {value}')


def mode_to_resolution_str(mode):
    if mode == gripper_camera_param_pb2.GripperCameraParams.MODE_640_480:
        return '640x480'
    elif mode == gripper_camera_param_pb2.GripperCameraParams.MODE_1280_720:
        return '1280x720'
    elif mode == gripper_camera_param_pb2.GripperCameraParams.MODE_1920_1080:
        return '1920x1080'
    elif mode == gripper_camera_param_pb2.GripperCameraParams.MODE_3840_2160:
        return '3840x2160'
    elif mode == gripper_camera_param_pb2.GripperCameraParams.MODE_4096_2160:
        return '4096x2160'
    elif mode == gripper_camera_param_pb2.GripperCameraParams.MODE_4208_3120:
        return '4208x3120'
    return str(mode)


if __name__ == '__main__':
    if not main():
        sys.exit(1)
