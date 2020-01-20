# Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Simple image capture tutorial."""

import argparse
import sys

from bosdyn.api import image_pb2
import bosdyn.client
import bosdyn.client.util
from bosdyn.client.image import ImageClient

import cv2
import numpy as np

def main(argv):
    # Parse args
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument('--list', help='list image sources', action='store_true')
    parser.add_argument('--image-sources', help='Get image from source(s)', action='append')
    options = parser.parse_args(argv)

    # Create robot object with an image client.
    sdk = bosdyn.client.create_standard_sdk('image_capture')
    sdk.load_app_token(options.app_token)
    robot = sdk.create_robot(options.hostname)
    robot.authenticate(options.username, options.password)
    image_client = robot.ensure_client(ImageClient.default_service_name)

    # Optionally list image sources on robot.
    if options.list:
        image_sources = image_client.list_image_sources()
        print("Image sources:")
        for source in image_sources:
            print("\t" + source.name)

    # Optionally capture one or more images.
    if options.image_sources:
        # Capture and save images to disk
        image_responses = image_client.get_image_from_sources(options.image_sources)
        for image in image_responses:
            if image.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_DEPTH_U16:
                dtype = np.uint16
                extension = ".png"
            else:
                dtype = np.uint8
                extension = ".jpg"

            img = np.fromstring(image.shot.image.data, dtype=dtype)
            if image.shot.image.format == image_pb2.Image.FORMAT_RAW:
                img = img.reshape(image.shot.image.rows, image.shot.image.cols)
            else:
                img = cv2.imdecode(img, -1)

            cv2.imwrite(image.source.name + extension, img)
    return True


if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
