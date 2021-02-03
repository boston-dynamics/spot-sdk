# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the Boston Dynamics API to detect and follow an object"""
from __future__ import print_function

import argparse
import io
import json
import math
import os
import statistics
import sys
import time
from multiprocessing import Barrier, Process, Queue
from queue import Full
from threading import BrokenBarrierError, Thread

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage

import bosdyn.client
import bosdyn.client.util
from bosdyn import geometry
from bosdyn.api import geometry_pb2 as geo
from bosdyn.api import image_pb2, trajectory_pb2
from bosdyn.api.image_pb2 import ImageSource
from bosdyn.api.spot import robot_command_pb2 as spot_command_pb2
from bosdyn.client.async_tasks import AsyncPeriodicQuery, AsyncTasks
from bosdyn.client.frame_helpers import *
from bosdyn.client.image import ImageClient
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.math_helpers import Quat, SE3Pose
from bosdyn.client.robot_command import (RobotCommandBuilder, RobotCommandClient,
                                        blocking_stand, CommandFailedError, CommandTimedOutError)
from bosdyn.client.robot_state import RobotStateClient
from tensorflow_object_detection import DetectorAPI

LOGGER = bosdyn.client.util.get_logger()

# Don't let the queues get too backed up
QUEUE_MAXSIZE = 10

# This is a multiprocessing.Queue for communication between the main process and the
# Tensorflow processes.
# Entries in this queue are in the format:
# {
#   'source': Name of the camera,
#   'raw_image_time': Time when the image was collected,
#   'capture_image_time': Time when the image was received by the main process,
#   vision_'image': Actual image rotated
# }
RAW_IMAGES_QUEUE = Queue(QUEUE_MAXSIZE)

# This is a multiprocessing.Queue for communication between the Tensorflow processes and
# the bbox print process. This is meant for running in a containerized environment with no access
# to an X display
# Entries in this queue are in the format:
# {
#   'source': Name of the camera,
#   'raw_image_time': Time when the image was collected,
#   'capture_image_time': Time when the image was received by the main process,
#   'processed_image_time': Time when the image was processed by a Tensorflow process,
#   'boxes': list of detected bounding boxes for the processed image
# }
PROCESSED_BOXES_QUEUE = Queue(QUEUE_MAXSIZE)

# Barrier for waiting on Tensorflow processes to start, initialized in main()
TENSORFLOW_PROCESS_BARRIER = None

COCO_CLASS_DICT = {1:'person',2:'bicycle',3:'car',4:'motorcycle',5:'airplane',6:'bus',7:'train',
                   8:'truck',9:'boat',10:'trafficlight',11:'firehydrant',13:'stopsign',
                   14:'parkingmeter',15:'bench',16:'bird',17:'cat',18:'dog',19:'horse',20:'sheep',
                   21:'cow',22:'elephant',23:'bear',24:'zebra',25:'giraffe',27:'backpack',
                   28:'umbrella',31:'handbag',32:'tie',33:'suitcase',34:'frisbee',35:'skis',
                   36:'snowboard',37:'sportsball',38:'kite',39:'baseballbat',40:'baseballglove',
                   41:'skateboard',42:'surfboard',43:'tennisracket',44:'bottle',46:'wineglass',
                   47:'cup',48:'fork',49:'knife',50:'spoon',51:'bowl',52:'banana',53:'apple',
                   54:'sandwich',55:'orange',56:'broccoli',57:'carrot',58:'hotdog',59:'pizza',
                   60:'donut',61:'cake',62:'chair',63:'couch',64:'pottedplant',65:'bed',
                   67:'diningtable',70:'toilet',72:'tv',73:'laptop',74:'mouse',75:'remote',
                   76:'keyboard',77:'cellphone',78:'microwave',79:'oven',80:'toaster',81:'sink',
                   82:'refrigerator',84:'book',85:'clock',86:'vase',87:'scissors',88:'teddybear',
                   89:'hairdrier',90:'toothbrush'}

# Mapping from visual to depth data
VISUAL_SOURCE_TO_DEPTH_MAP_SOURCE = {
    'frontleft_fisheye_image': 'frontleft_depth_in_visual_frame',
    'frontright_fisheye_image': 'frontright_depth_in_visual_frame'}
ROTATION_ANGLES = {
    'back_fisheye_image': 0,
    'frontleft_fisheye_image': -78,
    'frontright_fisheye_image': -102,
    'left_fisheye_image': 0,
    'right_fisheye_image': 180
}

def _update_thread(async_task):
    while True:
        async_task.update()
        time.sleep(0.01)

class AsyncImage(AsyncPeriodicQuery):
    """Grab image."""

    def __init__(self, image_client, image_sources):
        # Period is set to be about 15 FPS
        super(AsyncImage, self).__init__('images', image_client, LOGGER,
                                         period_sec=0.067)
        self.image_sources = image_sources

    def _start_query(self):
        return self._client.get_image_from_sources_async(self.image_sources)

class AsyncRobotState(AsyncPeriodicQuery):
    """Grab robot state."""

    def __init__(self, robot_state_client):
        # period is set to be about the same rate as detections on the CORE AI
        super(AsyncRobotState, self).__init__('robot_state', robot_state_client, LOGGER,
                                              period_sec=0.02)

    def _start_query(self):
        return self._client.get_robot_state_async()

def get_source_list(image_client):
    """Gets a list of image sources and filters based on config dictionary

    Args:
        image_client: Instantiated image client
    """

    # We are using only the visual images with their corresponding depth sensors
    sources = image_client.list_image_sources()
    source_list = []
    for source in sources:
        if source.image_type == ImageSource.IMAGE_TYPE_VISUAL:
            # only append if sensor has corresponding depth sensor
            if source.name in VISUAL_SOURCE_TO_DEPTH_MAP_SOURCE:
                source_list.append(source.name)
                source_list.append(VISUAL_SOURCE_TO_DEPTH_MAP_SOURCE[source.name])
    return source_list

def capture_images(image_task, sleep_between_capture):
    """ Captures images and places them on the queue

    Args:
        image_task (AsyncImage): Async task that provides the images response to use
        sleep_between_capture (float): Time to sleep between each image capture
    """
    while True:
        images_response = image_task.proto
        if not images_response:
            continue
        depth_responses = {img.source.name: img for img in images_response
                           if img.source.image_type == ImageSource.IMAGE_TYPE_DEPTH}
        entry = {}
        for image_response in images_response:
            if image_response.source.image_type == ImageSource.IMAGE_TYPE_VISUAL:
                source = image_response.source.name
                depth_source = VISUAL_SOURCE_TO_DEPTH_MAP_SOURCE[source]
                depth_image = depth_responses[depth_source]

                acquisition_time = image_response.shot.acquisition_time
                image_time = acquisition_time.seconds + acquisition_time.nanos * 1e-9

                try:
                    image = Image.open(io.BytesIO(image_response.shot.image.data))
                    source = image_response.source.name

                    image = ndimage.rotate(image, ROTATION_ANGLES[source])
                    # image = ndimage.rotate(image, 0)
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)  # Converted to RGB for TF
                    tform_snapshot = image_response.shot.transforms_snapshot
                    frame_name = image_response.shot.frame_name_image_sensor
                    world_tform_cam = get_a_tform_b(tform_snapshot,
                                                    VISION_FRAME_NAME,
                                                    frame_name)
                    entry[source] = {
                        'source': source,
                        'world_tform_cam': world_tform_cam,
                        'raw_image_time': image_time,
                        'capture_image_time': time.time(),
                        'cv_image': image,
                        'visual_image': image_response,
                        'depth_image': depth_image,
                        'system_cap_time': time.time()
                    }
                except Exception as exc: # pylint: disable=broad-except
                    print(f'Exception occurred during image capture {exc}')
        try:
            RAW_IMAGES_QUEUE.put_nowait(entry)
        except Full as exc:
            print(f'RAW_IMAGES_QUEUE is full: {exc}')
        time.sleep(sleep_between_capture)

def start_tensorflow_processes(num_processes, model_path, detection_class, detection_threshold,
                               max_processing_delay):
    """Starts Tensorflow processes in parallel.

    It does not keep track of the processes once they are started because they run indefinitely
    and are never joined back to the main process.

    Args:
        num_processes (int): Number of Tensorflow processes to start in parallel.
        model_path (str): Filepath to the Tensorflow model to use.
        detection_class (int): Detection class to detect
        detection_threshold (float): Detection threshold to apply to all Tensorflow detections.
        max_processing_delay (float): Allowed delay before processing an incoming image.
    """

    for counter in range(num_processes):
        process = Process(target=process_images, args=(
            model_path,
            detection_class,
            detection_threshold,
            max_processing_delay,
        ))
        process.start()


def process_images(model_path, detection_class, detection_threshold, max_processing_delay):
    """Starts Tensorflow and detects objects in the incoming images.

    Args:
        model_path (str): Filepath to the Tensorflow model to use.
        detection_class (int): Detection class to detect
        detection_threshold (float): Detection threshold to apply to all Tensorflow detections.
        max_processing_delay (float): Allowed delay before processing an incoming image.
    """

    odapi = DetectorAPI(path_to_ckpt=model_path)
    num_processed_skips = 0

    if TENSORFLOW_PROCESS_BARRIER is None:
        return

    try:
        TENSORFLOW_PROCESS_BARRIER.wait()
    except BrokenBarrierError as exc:
        print(f'Error waiting for Tensorflow processes to initialize: {exc}')
        return False

    while True:
        entry = RAW_IMAGES_QUEUE.get()
        for _, capture in entry.items():
            if time.time() - capture['raw_image_time'] > max_processing_delay:
                num_processed_skips += 1
                continue  # Skip image due to delay

            image = capture['cv_image']
            # process_start = time.time()
            boxes, scores, classes, _ = odapi.process_frame(image)
            # process_end = time.time()
            confident_boxes = []
            confident_object_classes = []
            confident_scores = []
            if len(boxes) == 0:
                continue
            for box, score, box_class in sorted(zip(boxes, scores, classes),
                                                key=lambda x: x[1],
                                                reverse=True):
                # if score > detection_threshold:
                if score > detection_threshold and box_class == detection_class:
                    confident_boxes.append(box)
                    confident_object_classes.append(COCO_CLASS_DICT[box_class])
                    confident_scores.append(score)
                    image = cv2.rectangle(image, (box[1], box[0]), (box[3], box[2]), (255, 0, 0), 2)

            capture['processed_image_time'] = time.time()
            capture['boxes'] = confident_boxes
            capture['classes'] = confident_object_classes
            capture['scores'] = confident_scores
            capture['cv_image'] = image
        try:
            PROCESSED_BOXES_QUEUE.put_nowait(entry)
        except Full as exc:
            print(f'PROCESSED_BOXES_QUEUE is full: {exc}')

def get_go_to(world_tform_object, robot_state, mobility_params, dist_margin=1.2):
    """Gets trajectory command to a goal location

    Args:
        world_tform_object (SE3Pose): Transform from vision frame to target object
        robot_state (RobotState): Current robot state
        mobility_params (MobilityParams): Mobility parameters
        dist_margin (float): Distance margin to target
    """
    vo_tform_robot = get_vision_tform_body(robot_state.kinematic_state.transforms_snapshot)
    delta_ewrt_vo = np.array(
        [world_tform_object.x - vo_tform_robot.x, world_tform_object.y - vo_tform_robot.y, 0])
    norm = np.linalg.norm(delta_ewrt_vo)
    if norm == 0:
        return None
    delta_ewrt_vo_norm = delta_ewrt_vo / norm
    heading = _get_heading(delta_ewrt_vo_norm)
    vo_tform_goal = np.array([
        world_tform_object.x - delta_ewrt_vo_norm[0] * dist_margin,
        world_tform_object.y - delta_ewrt_vo_norm[1] * dist_margin
    ])
    tag_cmd = RobotCommandBuilder.trajectory_command(
                goal_x=vo_tform_goal[0], goal_y=vo_tform_goal[1], goal_heading=heading,
                frame_name=VISION_FRAME_NAME, params=mobility_params)
    return tag_cmd

def _get_heading(xhat):
    zhat = [0.0, 0.0, 1.0]
    yhat = np.cross(zhat, xhat)
    mat = np.array([xhat, yhat, zhat]).transpose()
    return Quat.from_matrix(mat).to_yaw()


def set_default_body_control():
    """Set default body control params to current body position"""
    footprint_R_body = geometry.EulerZXY()
    position = geo.Vec3(x=0.0, y=0.0, z=0.0)
    rotation = footprint_R_body.to_quaternion()
    pose = geo.SE3Pose(position=position, rotation=rotation)
    point = trajectory_pb2.SE3TrajectoryPoint(pose=pose)
    traj = trajectory_pb2.SE3Trajectory(points=[point])
    return spot_command_pb2.BodyControlParams(base_offset_rt_footprint=traj)


def get_mobility_params():
    """Gets mobility parameters for following"""
    vel_desired = .75
    speed_limit = geo.SE2VelocityLimit(
        max_vel=geo.SE2Velocity(linear=geo.Vec2(x=vel_desired, y=vel_desired), angular=.25))
    body_control = set_default_body_control()
    mobility_params = spot_command_pb2.MobilityParams(vel_limit=speed_limit, obstacle_params=None,
                                                      body_control=body_control,
                                                      locomotion_hint=spot_command_pb2.HINT_TROT)
    return mobility_params

def get_distance_to_closest_object_depth(x_min, x_max, y_min, y_max,
                                         depth_scale, raw_depth_image,
                                         histogram_bin_size=0.20,
                                         minimum_number_of_points=100,
                                         max_distance=4.0):
    """Make a histogram of distances to points in the cloud and take the closest distance with
    enough points.

    Args:
        origin (tuple): Origin to rotate the point around
        x_min (int): minimum x coordinate (column) of object to find
        x_max (int): maximum x coordinate (column) of object to find
        y_min (int): minimum y coordinate (row) of object to find
        y_max (int): maximum y coordinate (row) of object to find
        depth_scale (float): depth scale of the image to convert from sensor value to meters
        raw_depth_image (np.array): matrix of depth pixels
        histogram_bin_size (float): size of each bin of distances
        minimum_number_of_points (int): minimum number of points before returning depth
        max_distance (float): maximum distance to object in meters
    """
    num_bins = math.ceil(max_distance / histogram_bin_size)
    depths = []

    for row in range(y_min, y_max):
        for col in range(x_min, x_max):
            raw_depth = raw_depth_image[row][col]
            if raw_depth != 0 and raw_depth is not None:
                depth = raw_depth / depth_scale
                depths.append(depth)

    hist, hist_edges = np.histogram(depths, bins=num_bins, range=(0,max_distance))

    edges_zipped = zip(hist_edges[:-1], hist_edges[1:])
    # Iterate over the histogram and return the first distance with enough points.
    for entry, edges in zip(hist, edges_zipped):
        if entry > minimum_number_of_points:
            return statistics.mean([d for d in depths if d > edges[0] and d > edges[1]])

    return max_distance

def rotate_about_origin_degrees(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    Args:
        origin (tuple): Origin to rotate the point around
        point (tuple): Point to rotate
        angle (float): Angle in degrees
    """
    return rotate_about_origin(origin, point, math.radians(angle))

def rotate_about_origin(origin, point, angle):
    """
    Rotate a point counterclockwise by a given angle around a given origin.

    Args:
        origin (tuple): Origin to rotate the point around
        point (tuple): Point to rotate
        angle (float): Angle in radians
    """
    orig_x, orig_y = origin
    pnt_x, pnt_y = point

    ret_x = orig_x + math.cos(angle) * (pnt_x - orig_x) - math.sin(angle) * (pnt_y - orig_y)
    ret_y = orig_y + math.sin(angle) * (pnt_x - orig_x) + math.cos(angle) * (pnt_y - orig_y)
    return int(ret_x), int(ret_y)

def get_object_position(world_tform_cam,
                        visual_image, depth_image,
                        bounding_box, rotation_angle):
    """
    Extract the bounding box, then find the mode in that region.

    Args:
        world_tform_cam (SE3Pose): SE3 transform from world to camera frame
        visual_image (ImageResponse): From a visual camera
        depth_image (ImageResponse): From a depth camera corresponding to the visual_image
        bounding_box (list): Bounding box from tensorflow
        rotation_angle (float): Angle (in degrees) to rotate depth image to match cam image rotation
    """

    # Make sure there are two images.
    if visual_image is None or depth_image is None:
        # Fail.
        return

    # Rotate bounding box back to original frame
    points = [(bounding_box[1], bounding_box[0]),
              (bounding_box[3], bounding_box[0]),
              (bounding_box[3], bounding_box[2]),
              (bounding_box[1], bounding_box[2])]

    origin = (visual_image.shot.image.cols / 2, visual_image.shot.image.rows / 2)

    points_rot = [rotate_about_origin_degrees(origin, point, rotation_angle) for point in points]

    # Get the bounding box corners.
    y_min = max(0, min([point[1] for point in points_rot]))
    x_min = max(0, min([point[0] for point in points_rot]))
    y_max = min(visual_image.shot.image.rows, max([point[1] for point in points_rot]))
    x_max = min(visual_image.shot.image.cols, max([point[0] for point in points_rot]))

    # Check that the bounding box is valid.
    if (x_min < 0 or y_min < 0 or x_max > visual_image.shot.image.cols or
            y_max > visual_image.shot.image.rows):
        print(f'Bounding box is invalid: ({x_min}, {y_min}) | ({x_max}, {y_max})')
        print(f'Bounds: ({visual_image.shot.image.cols}, {visual_image.shot.image.rows})')
        return

    # Unpack the images.
    try:
        if depth_image.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_DEPTH_U16:
            dtype = np.uint16
        else:
            dtype = np.uint8
        img = np.fromstring(depth_image.shot.image.data, dtype=dtype)
        if depth_image.shot.image.format == image_pb2.Image.FORMAT_RAW:
            img = img.reshape(depth_image.shot.image.rows, depth_image.shot.image.cols)
        else:
            img = cv2.imdecode(img, -1)
        depth_image_pixels = img

        # Get the depth data from the region in the bounding box.
        depth = get_distance_to_closest_object_depth(x_min, x_max, y_min, y_max,
                                                     depth_image.source.depth_scale,
                                                     depth_image_pixels)

        if depth >= 4.0:
            # Not enough depth data.
            print('Not enough depth data.')
            return False

        # Calculate the transform to the center point of the object using camera intrinsics
        # and depth calculated earlier in the function
        focal_x = depth_image.source.pinhole.intrinsics.focal_length.x
        principal_x = depth_image.source.pinhole.intrinsics.principal_point.x

        focal_y = depth_image.source.pinhole.intrinsics.focal_length.y
        principal_y = depth_image.source.pinhole.intrinsics.principal_point.y

        center_x = round((x_max - x_min) / 2.0 + x_min)
        center_y = round((y_max - y_min) / 2.0 + y_min)

        tform_x = depth * (center_x - principal_x) / focal_x
        tform_y = depth * (center_y - principal_y) / focal_y
        tform_z = depth
        obj_tform_camera = SE3Pose(tform_x, tform_y, tform_z, Quat())

        return world_tform_cam * obj_tform_camera
    except Exception as exc: # pylint: disable=broad-except
        print(f'Error getting object position: {exc}')
        return

def _check_model_path(model_path):
    if model_path is None or \
    not os.path.exists(model_path) or \
    not os.path.isfile(model_path):
        print("ERROR, could not find model file " + str(model_path))
        return False
    return True

def _check_and_load_json_classes(config_path):
    if os.path.isfile(config_path):
        with open(config_path) as json_classes:
            global COCO_CLASS_DICT # pylint: disable=global-statement
            COCO_CLASS_DICT = json.load(json_classes)

def _find_highest_conf_source(processed_boxes_entry):
    highest_conf_source = None
    max_score = 0
    for key, capture in processed_boxes_entry.items():
        if 'scores' in capture.keys():
            if len(capture['scores']) > 0 and capture['scores'][0] > max_score:
                highest_conf_source = key
                max_score = capture['scores'][0]
    return highest_conf_source

def main(argv):
    """Command line interface.

    Args:
        argv: List of command-line arguments passed to the program.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True,
                        help="Local file path to the Tensorflow model, example pre-trained models \
                            can be found at \
                            https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md")
    parser.add_argument("--classes", default='/classes.json', type=str,
                        help="File containing json mapping of object class IDs to class names")
    parser.add_argument("--number-tensorflow-processes", default=1, type=int,
                        help="Number of Tensorflow processes to run in parallel")
    parser.add_argument("--detection-threshold", default=0.7, type=float,
                        help="Detection threshold to use for Tensorflow detections")
    parser.add_argument(
        "--sleep-between-capture", default=1.0, type=float,
        help="Seconds to sleep between each image capture loop iteration, which captures " +
        "an image from all cameras")
    parser.add_argument(
        "--detection-class", default=1, type=int, help="Detection classes to use in the" +
        "Tensorflow model; Default is to use 1, which is a person in the Coco dataset")
    parser.add_argument("--max-processing-delay", default=7.0, type=float,
                        help="Maximum allowed delay for processing an image; " +
                        "any image older than this value will be skipped")

    bosdyn.client.util.add_common_arguments(parser)
    options = parser.parse_args(argv)
    try:
        # Make sure the model path is a valid file
        if not _check_model_path(options.model_path):
            return False

        # Check for classes json file, otherwise use the COCO class dictionary
        _check_and_load_json_classes(options.classes)

        global TENSORFLOW_PROCESS_BARRIER # pylint: disable=global-statement
        TENSORFLOW_PROCESS_BARRIER = Barrier(options.number_tensorflow_processes + 1)
        # Start Tensorflow processes
        start_tensorflow_processes(options.number_tensorflow_processes, options.model_path,
                                   options.detection_class, options.detection_threshold,
                                   options.max_processing_delay)

        # sleep to give the Tensorflow processes time to initialize
        try:
            TENSORFLOW_PROCESS_BARRIER.wait()
        except BrokenBarrierError as exc:
            print(f'Error waiting for Tensorflow processes to initialize: {exc}')
            return False
        # Start the API related things

        # Create robot object with a world object client
        sdk = bosdyn.client.create_standard_sdk('SpotFollowClient')
        robot = sdk.create_robot(options.hostname)
        robot.authenticate(options.username, options.password)
        #Time sync is necessary so that time-based filter requests can be converted
        robot.time_sync.wait_for_sync()

        # Verify the robot is not estopped and that an external application has registered and holds
        # an estop endpoint.
        assert not robot.is_estopped(), "Robot is estopped. Please use an external E-Stop client," \
                                        " such as the estop SDK example, to configure E-Stop."

        # Create the sdk clients
        robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
        robot_command_client = robot.ensure_client(RobotCommandClient.default_service_name)
        lease_client = robot.ensure_client(LeaseClient.default_service_name)
        image_client = robot.ensure_client(ImageClient.default_service_name)
        source_list = get_source_list(image_client)
        image_task = AsyncImage(image_client, source_list)
        robot_state_task = AsyncRobotState(robot_state_client)
        task_list = [image_task, robot_state_task]
        _async_tasks = AsyncTasks(task_list)
        print('Detect and follow client connected.')

        lease = lease_client.acquire()
        lease_keep = LeaseKeepAlive(lease_client)
        # Power on the robot and stand it up
        resp = robot.power_on()
        try:
            blocking_stand(robot_command_client)
        except CommandFailedError as exc:
            print(f'Error ({exc}) occurred while trying to stand. Check robot surroundings.')
            return False
        except CommandTimedOutError as exc:
            print(f'Stand command timed out: {exc}')
            return False
        print('Robot powered on and standing.')
        params_set = get_mobility_params()

        # This thread starts the async tasks for image and robot state retrieval
        update_thread = Thread(target=_update_thread, args=[_async_tasks])
        update_thread.daemon = True
        update_thread.start()
        # Wait for the first responses.
        while any(task.proto is None for task in task_list):
            time.sleep(0.1)

        # Start image capture process
        image_capture_thread = Thread(target=capture_images,
                                      args=(image_task, options.sleep_between_capture,))
        image_capture_thread.start()
        while True:
            # This comes from the tensorflow processes and limits the rate of this loop
            entry = PROCESSED_BOXES_QUEUE.get()
            # find the highest confidence bounding box
            highest_conf_source = _find_highest_conf_source(entry)
            if highest_conf_source is None:
                # no boxes or scores found
                continue
            capture_to_use = entry[highest_conf_source]
            raw_time = capture_to_use['raw_image_time']
            time_gap = time.time() - raw_time
            if time_gap > options.max_processing_delay:
                continue  # Skip image due to delay

            # Find the transform to highest confidence object using the depth sensor
            world_tform_object = get_object_position(capture_to_use['world_tform_cam'],
                                                     capture_to_use['visual_image'],
                                                     capture_to_use['depth_image'],
                                                     capture_to_use['boxes'][0],
                                                     ROTATION_ANGLES[capture_to_use['source']])

            # get_object_position can fail if there is insufficient depth sensor information
            if not world_tform_object:
                continue

            scores = capture_to_use['scores']
            print(f'Transform for object with confidence {scores[0]}: {world_tform_object}')
            print(f'Process latency: {time.time() - capture_to_use["system_cap_time"]}')
            tag_cmd = get_go_to(world_tform_object,
                                robot_state_task.proto,
                                params_set)
            end_time = 15.0
            if tag_cmd is not None:
                robot_command_client.robot_command(lease=None, command=tag_cmd,
                                                   end_time_secs=time.time() + end_time)

        # Shutdown lease keep-alive and return lease gracefully.
        lease_keep.shutdown()
        lease_client.return_lease(lease)

        return True
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error("Spot Tensorflow Detector threw an exception: %s", exc)
        # Shutdown lease keep-alive and return lease gracefully.
        lease_keep.shutdown()
        lease_client.return_lease(lease)
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
