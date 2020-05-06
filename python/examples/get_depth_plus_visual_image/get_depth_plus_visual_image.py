# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Simple image capture tutorial."""

import argparse
import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.image import ImageClient

import cv2
import numpy as np


def main(argv):
    # Parse args
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument('--camera', help='Camera to aquire image from.', default='frontleft',\
    choices=['frontleft', 'frontright', 'left', 'right', 'back'])
    options = parser.parse_args(argv)

    sources = [options.camera + '_depth_in_visual_frame', options.camera + '_fisheye_image']

    # Create robot object with an image client.
    sdk = bosdyn.client.create_standard_sdk('image_depth_plus_visual')
    sdk.load_app_token(options.app_token)
    robot = sdk.create_robot(options.hostname)
    robot.authenticate(options.username, options.password)
    image_client = robot.ensure_client(ImageClient.default_service_name)

    # Capture and save images to disk
    image_responses = image_client.get_image_from_sources(sources)

    # Image responses are in the same order as the requests.
    # Convert to opencv images.

    # Depth is a raw bytestream
    cv_depth = np.fromstring(image_responses[0].shot.image.data, dtype=np.uint16)
    cv_depth = cv_depth.reshape(image_responses[0].shot.image.rows,
                                image_responses[0].shot.image.cols)

    # Visual is a JPEG
    cv_visual = cv2.imdecode(np.fromstring(image_responses[1].shot.image.data, dtype=np.uint8), -1)

    # Convert the visual image from a single channel to RGB so we can add color
    visual_rgb = cv2.cvtColor(cv_visual, cv2.COLOR_GRAY2RGB)

    # Map depth ranges to color

    # cv2.applyColorMap() only supports 8-bit; convert from 16-bit to 8-bit and do scaling
    min_val = np.min(cv_depth)
    max_val = np.max(cv_depth)
    depth_range = max_val - min_val
    depth8 = (255.0 / depth_range * cv_depth - min_val).astype('uint8')
    depth8_rgb = cv2.cvtColor(depth8, cv2.COLOR_GRAY2RGB)
    depth_color = cv2.applyColorMap(depth8_rgb, cv2.COLORMAP_JET)

    # Add the two images together.
    out = cv2.addWeighted(visual_rgb, 0.5, depth_color, 0.5, 0)

    # Write the image out.
    filename = options.camera + ".jpg"
    cv2.imwrite(filename, out)

    return True


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
