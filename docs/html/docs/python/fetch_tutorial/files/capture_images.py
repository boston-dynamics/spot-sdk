# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import sys
import os
import bosdyn.client
import bosdyn.client.util
from bosdyn.client.image import ImageClient
import cv2
import numpy as np
import time

def main(argv):
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('--image-source', help='Get image from source(s)', default='frontleft_fisheye_image')
    parser.add_argument('--folder', help='Path to write images to', default='')
    options = parser.parse_args(argv)

    # Create robot object with an image client.
    sdk = bosdyn.client.create_standard_sdk('image_capture')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.sync_with_directory()
    robot.time_sync.wait_for_sync()

    image_client = robot.ensure_client(ImageClient.default_service_name)

    # Make sure the folder exists.
    if not os.path.exists(options.folder):
        print('Error: output folder does not exist: ' + options.folder)
        return

    counter = 0

    while True:
        # We want to capture from one camera at a time.

        # Capture and save images to disk
        image_responses = image_client.get_image_from_sources([options.image_source])

        dtype = np.uint8

        img = np.frombuffer(image_responses[0].shot.image.data, dtype=dtype)
        img = cv2.imdecode(img, -1)

        # Approximately rotate the image to level.
        if image_responses[0].source.name[0:5] == "front":
            img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

        elif image_responses[0].source.name[0:5] == "right":
            img = cv2.rotate(img, cv2.ROTATE_180)

        # Don't overwrite an existing image
        while True:
            image_saved_path = os.path.join(options.folder, image_responses[0].source.name + '_{:0>4d}'.format(counter) + '.jpg')
            counter += 1

            if not os.path.exists(image_saved_path):
                break

        cv2.imwrite(image_saved_path, img)

        print('Wrote: ' + image_saved_path)

        # Wait for some time so we can drive the robot to a new position.
        time.sleep(0.7)


    return True

if __name__ == "__main__":
    if not main(sys.argv[1:]):
        sys.exit(1)
