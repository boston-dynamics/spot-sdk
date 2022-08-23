# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the Boston Dynamics API"""
from __future__ import print_function

import argparse
import io
import multiprocessing
import os
import sys
import time
from multiprocessing import Process, Queue

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage
from tensorflow_object_detection import DetectorAPI

import bosdyn.client
import bosdyn.client.util
from bosdyn.api.image_pb2 import ImageSource
from bosdyn.client.image import ImageClient

# This is a multiprocessing.Queue for communication between the main process and the
# Tensorflow processes.
# Entries in this queue are in the format:
# {
#   'source': Name of the camera,
#   'raw_image_time': Time when the image was collected,
#   'capture_image_time': Time when the image was received by the main process,
#   'image': Actual image rotated
# }
RAW_IMAGES_QUEUE = Queue()

# This is a multiprocessing.Queue for communication between the Tensorflow processes and
# the display process.
# Entries in this queue are in the format:
# {
#   'source': Name of the camera,
#   'raw_image_time': Time when the image was collected,
#   'capture_image_time': Time when the image was received by the main process,
#   'processed_image_time': Time when the image was processed by a Tensorflow process,
#   'image': Actual image rotated and with boxes around the detections
# }
PROCESSED_IMAGES_QUEUE = Queue()


def inline_print(num_tabs, value):
    """Prints information in a specific format without new lines.

    Args:
        num_tabs: Number of tabs to print first.
        value: Value to print after the tabs.
    """

    #move cursor back to the start of the line
    print(chr(13), end="")
    print('\t' * num_tabs, end="")
    print(value, end="")


def start_tensorflow_processes(num_processes, model_path, detection_classes, detection_threshold,
                               max_processing_delay):
    """Starts Tensorflow processes in parallel.

    It does not keep track of the processes once they are started because they run indefinitely
    and are never joined back to the main process.

    Args:
        num_processes: Number of Tensorflow processes to start in parallel.
        model_path: Filepath to the Tensorflow model to use.
        detection_classes: List of detection classes to detect. Empty list means all classes
            in the model are detected.
        detection_threshold: Detection threshold to apply to all Tensorflow detections.
        max_processing_delay: Allowed delay before processing an incoming image.
    """

    for counter in range(num_processes):
        process = Process(
            target=process_images, args=(
                counter,
                model_path,
                detection_classes,
                detection_threshold,
                max_processing_delay,
            ))
        process.start()


def process_images(index, model_path, detection_classes, detection_threshold, max_processing_delay):
    """Starts Tensorflow and detects objects in the incoming images.

    Args:
        index: Process index used for displaying number of skips only.
        model_path: Filepath to the Tensorflow model to use.
        detection_classes: List of detection classes to detect. Empty list means all classes
            in the model are detected.
        detection_threshold: Detection threshold to apply to all Tensorflow detections.
        max_processing_delay: Allowed delay before processing an incoming image.
    """

    odapi = DetectorAPI(path_to_ckpt=model_path)
    num_processed_skips = 0

    while True:
        entry = RAW_IMAGES_QUEUE.get()
        inline_print(0, RAW_IMAGES_QUEUE.qsize())
        raw_time = entry['raw_image_time']
        if time.time() - raw_time > max_processing_delay:
            num_processed_skips = num_processed_skips + 1
            inline_print(20 + index, str(num_processed_skips))
            continue  # Skip image due to delay

        image = entry['image']
        boxes, scores, classes, _ = odapi.process_frame(image)

        for i in range(len(boxes)):
            # Empty detection classes means detect everything
            if not detection_classes or classes[i] in detection_classes:
                if scores[i] > detection_threshold:
                    box = boxes[i]
                    image = cv2.rectangle(image, (box[1], box[0]), (box[3], box[2]), (255, 0, 0), 2)
        out_entry = {
            'source': entry['source'],
            'raw_image_time': entry['raw_image_time'],
            'capture_image_time': entry['capture_image_time'],
            'processed_image_time': time.time(),
            'image': image
        }
        PROCESSED_IMAGES_QUEUE.put(out_entry)
        inline_print(3, PROCESSED_IMAGES_QUEUE.qsize())
        inline_print(9, str(out_entry['processed_image_time'] - out_entry['capture_image_time']))


def display_images(max_display_delay):
    """Asynchronously displays processed images in five separate windows, one per camera.

    Args:
        max_display_delay: Allowed delay before displaying an incoming image.
    """

    num_display_skips = 0
    while True:
        entry = PROCESSED_IMAGES_QUEUE.get()
        inline_print(3, PROCESSED_IMAGES_QUEUE.qsize())
        raw_time = entry['raw_image_time']
        if time.time() - raw_time > max_display_delay:
            num_display_skips = num_display_skips + 1
            inline_print(18, str(num_display_skips))
            continue  # Skip image due to delay

        img = entry['image']
        label = entry['source']
        cv2.imshow(label, img)
        cv2.waitKey(1)
        final_t = time.time()
        inline_print(12, str(final_t - entry['processed_image_time']))
        inline_print(15, str(final_t - raw_time))


class SpotImageCapture:
    """Captures images from Spot cameras periodically.

    Attributes:
        rotation_angles: Rotation angle for each of the 5 Spot cameras.
        robot: Instance of the Spot robot.
        image_client: Instance of the image client from the robot  to use for capturing images.
        source_list: List of all visual camera labels, skipping the depth ones.
    """

    def __init__(self):
        self.rotation_angles = {
            'back_fisheye_image': 0,
            'frontleft_fisheye_image': -78,
            'frontright_fisheye_image': -102,
            'left_fisheye_image': 0,
            'right_fisheye_image': 180
        }

        # These robot-related fields will be initialized in initializeNoControl method
        self.robot = None
        self.image_client = None
        self.source_list = []

    def initialize_sdk_no_motor_control(self, address):
        """Initializes the SDK and the robot without motor control.

        Args:
            address: IP address of the robot.
            username: Username for authenticating with robot.
            password: Password for authenticating with robot.
        """

        sdk = bosdyn.client.create_standard_sdk('quickstart-spot')

        # Create robot and authenticate
        self.robot = sdk.create_robot(address)
        bosdyn.client.util.authenticate(self.robot)
        self.robot.time_sync.wait_for_sync()

        self.image_client = self.robot.ensure_client(ImageClient.default_service_name)
        # We are using only the visual images
        sources = self.image_client.list_image_sources()
        for source in sources:
            if source.image_type == ImageSource.IMAGE_TYPE_VISUAL:
                self.source_list.append(source.name)

    def capture_images(self, sleep_between_capture):
        """ Captures an image from a specific camera.

        Args:
            sleep_between_capture: Duration to sleep between captures.
        """
        while True:
            images_response = self.image_client.get_image_from_sources(self.source_list)
            for image_response in images_response:
                source = image_response.source.name
                acquisition_time = image_response.shot.acquisition_time
                image_time = acquisition_time.seconds + acquisition_time.nanos / pow(10, 9)

                image = Image.open(io.BytesIO(image_response.shot.image.data))
                source = image_response.source.name
                image = ndimage.rotate(image, self.rotation_angles[source])
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)  # Converted to RGB for Tensorflow
                entry = {
                    'source': source,
                    'raw_image_time': image_time,
                    'capture_image_time': time.time(),
                    'image': image
                }
                RAW_IMAGES_QUEUE.put(entry)
                inline_print(0, RAW_IMAGES_QUEUE.qsize())
                inline_print(6, str(entry['capture_image_time'] - entry['raw_image_time']))
            time.sleep(sleep_between_capture)


def main(argv):
    """Command line interface.

    Args:
        argv: List of command-line arguments passed to the program.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True,
                        help="Local file path to the Tensorflow model")
    parser.add_argument("--number-tensorflow-processes", default=7, type=int,
                        help="Number of Tensorflow processes to run in parallel")
    parser.add_argument("--detection-threshold", default=0.7, type=float,
                        help="Detection threshold to use for Tensorflow detections")
    parser.add_argument(
        "--sleep-between-capture", default=0.0, type=float,
        help="Seconds to sleep between each image capture loop iteration, which captures " +
        "an image from all cameras")
    parser.add_argument(
        "--detection-classes", help="Comma-separated list of detection classes " +
        "included in the Tensorflow model; Default is to use all classes in the model")
    parser.add_argument(
        "--max-processing-delay", default=4.0, type=float,
        help="Maximum allowed delay for processing an image; " +
        "any image older than this value will be skipped")
    parser.add_argument(
        "--max-display-delay", default=5.0, type=float,
        help="Maximum allowed delay for displaying an image; " +
        "any image older than this value will be skipped")

    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args(argv)
    try:
        detection_classes = []
        if options.detection_classes:
            # Convert comma-separated detection classes to a list of integers
            detection_classes = list(map(int, list(options.detection_classes.split(","))))

        # Make sure the model path is a valid file
        if options.model_path is None or \
        not os.path.exists(options.model_path) or \
        not os.path.isfile(options.model_path):
            print("ERROR, could not find model file " + str(options.model_path))
            sys.exit(1)

        image_capture = SpotImageCapture()
        image_capture.initialize_sdk_no_motor_control(options.hostname)

        # Start Tensorflow processes
        start_tensorflow_processes(options.number_tensorflow_processes, options.model_path,
                                   detection_classes, options.detection_threshold,
                                   options.max_processing_delay)

        # Start Display process
        process = Process(target=display_images, args=(options.max_display_delay,))
        process.start()

        #sleep to give the Tensorflow processes time to initialize
        time.sleep(5)
        print("\n\n\nRAW_IMAGES_QUEUE\tPROCESSED_IMAGES_QUEUE\tNetwork_Delay\t\
            Processing_Delay\tDisplay_Delay\t\tTotal_Delay\t\tDisplay_Skips\tProcessing_Skips")
        # Start the ingestion of images from the Spot in this main process
        image_capture.capture_images(options.sleep_between_capture)

        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.error("Spot Tensorflow Detector threw an exception: %s", exc)
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
