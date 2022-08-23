# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
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
import signal
import sys
import time
from multiprocessing import Barrier, Process, Queue, Value
from queue import Empty, Full
from threading import BrokenBarrierError, Thread

import cv2
import numpy as np
from PIL import Image
from scipy import ndimage
from tensorflow_object_detection import DetectorAPI

import bosdyn.client
import bosdyn.client.util
from bosdyn import geometry
from bosdyn.api import geometry_pb2 as geo
from bosdyn.api import image_pb2, trajectory_pb2
from bosdyn.api.image_pb2 import ImageSource
from bosdyn.api.spot import robot_command_pb2 as spot_command_pb2
from bosdyn.client.async_tasks import AsyncPeriodicQuery, AsyncTasks
from bosdyn.client.frame_helpers import (GROUND_PLANE_FRAME_NAME, VISION_FRAME_NAME, get_a_tform_b,
                                         get_vision_tform_body)
from bosdyn.client.image import ImageClient
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.math_helpers import Quat, SE3Pose
from bosdyn.client.robot_command import (CommandFailedError, CommandTimedOutError,
                                         RobotCommandBuilder, RobotCommandClient, blocking_stand)
from bosdyn.client.robot_state import RobotStateClient

LOGGER = bosdyn.client.util.get_logger()

SHUTDOWN_FLAG = Value('i', 0)

# Don't let the queues get too backed up
QUEUE_MAXSIZE = 10

# This is a multiprocessing.Queue for communication between the main process and the
# Tensorflow processes.
# Entries in this queue are in the format:

# {
#     'source': Name of the camera,
#     'world_tform_cam': transform from VO to camera,
#     'world_tform_gpe':  transform from VO to ground plane,
#     'raw_image_time': Time when the image was collected,
#     'cv_image': The decoded image,
#     'visual_dims': (cols, rows),
#     'depth_image': depth image proto,
#     'system_cap_time': Time when the image was received by the main process,
#     'image_queued_time': Time when the image was done preprocessing and queued
# }
RAW_IMAGES_QUEUE = Queue(QUEUE_MAXSIZE)

# This is a multiprocessing.Queue for communication between the Tensorflow processes and
# the bbox print process. This is meant for running in a containerized environment with no access
# to an X display
# Entries in this queue have the following fields in addition to those in :
# {
#   'processed_image_start_time':  Time when the image was received by the TF process,
#   'processed_image_end_time':  Time when the image was processing for bounding boxes
#   'boxes': list of detected bounding boxes for the processed image
#   'classes': classes of objects,
#   'scores': confidence scores,
# }
PROCESSED_BOXES_QUEUE = Queue(QUEUE_MAXSIZE)

# Barrier for waiting on Tensorflow processes to start, initialized in main()
TENSORFLOW_PROCESS_BARRIER = None

COCO_CLASS_DICT = {
    1: 'person',
    2: 'bicycle',
    3: 'car',
    4: 'motorcycle',
    5: 'airplane',
    6: 'bus',
    7: 'train',
    8: 'truck',
    9: 'boat',
    10: 'trafficlight',
    11: 'firehydrant',
    13: 'stopsign',
    14: 'parkingmeter',
    15: 'bench',
    16: 'bird',
    17: 'cat',
    18: 'dog',
    19: 'horse',
    20: 'sheep',
    21: 'cow',
    22: 'elephant',
    23: 'bear',
    24: 'zebra',
    25: 'giraffe',
    27: 'backpack',
    28: 'umbrella',
    31: 'handbag',
    32: 'tie',
    33: 'suitcase',
    34: 'frisbee',
    35: 'skis',
    36: 'snowboard',
    37: 'sportsball',
    38: 'kite',
    39: 'baseballbat',
    40: 'baseballglove',
    41: 'skateboard',
    42: 'surfboard',
    43: 'tennisracket',
    44: 'bottle',
    46: 'wineglass',
    47: 'cup',
    48: 'fork',
    49: 'knife',
    50: 'spoon',
    51: 'bowl',
    52: 'banana',
    53: 'apple',
    54: 'sandwich',
    55: 'orange',
    56: 'broccoli',
    57: 'carrot',
    58: 'hotdog',
    59: 'pizza',
    60: 'donut',
    61: 'cake',
    62: 'chair',
    63: 'couch',
    64: 'pottedplant',
    65: 'bed',
    67: 'diningtable',
    70: 'toilet',
    72: 'tv',
    73: 'laptop',
    74: 'mouse',
    75: 'remote',
    76: 'keyboard',
    77: 'cellphone',
    78: 'microwave',
    79: 'oven',
    80: 'toaster',
    81: 'sink',
    82: 'refrigerator',
    84: 'book',
    85: 'clock',
    86: 'vase',
    87: 'scissors',
    88: 'teddybear',
    89: 'hairdrier',
    90: 'toothbrush'
}

# Mapping from visual to depth data
VISUAL_SOURCE_TO_DEPTH_MAP_SOURCE = {
    'frontleft_fisheye_image': 'frontleft_depth_in_visual_frame',
    'frontright_fisheye_image': 'frontright_depth_in_visual_frame'
}
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
        super(AsyncImage, self).__init__('images', image_client, LOGGER, period_sec=0.067)
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
    while not SHUTDOWN_FLAG.value:
        get_im_resp = image_task.proto
        start_time = time.time()
        if not get_im_resp:
            continue
        depth_responses = {
            img.source.name: img
            for img in get_im_resp
            if img.source.image_type == ImageSource.IMAGE_TYPE_DEPTH
        }
        entry = {}
        for im_resp in get_im_resp:
            if im_resp.source.image_type == ImageSource.IMAGE_TYPE_VISUAL:
                source = im_resp.source.name
                depth_source = VISUAL_SOURCE_TO_DEPTH_MAP_SOURCE[source]
                depth_image = depth_responses[depth_source]

                acquisition_time = im_resp.shot.acquisition_time
                image_time = acquisition_time.seconds + acquisition_time.nanos * 1e-9

                try:
                    image = Image.open(io.BytesIO(im_resp.shot.image.data))
                    source = im_resp.source.name

                    image = ndimage.rotate(image, ROTATION_ANGLES[source])
                    if im_resp.shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8:
                        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)  # Converted to RGB for TF
                    tform_snapshot = im_resp.shot.transforms_snapshot
                    frame_name = im_resp.shot.frame_name_image_sensor
                    world_tform_cam = get_a_tform_b(tform_snapshot, VISION_FRAME_NAME, frame_name)
                    world_tform_gpe = get_a_tform_b(tform_snapshot, VISION_FRAME_NAME,
                                                    GROUND_PLANE_FRAME_NAME)
                    entry[source] = {
                        'source': source,
                        'world_tform_cam': world_tform_cam,
                        'world_tform_gpe': world_tform_gpe,
                        'raw_image_time': image_time,
                        'cv_image': image,
                        'visual_dims': (im_resp.shot.image.cols, im_resp.shot.image.rows),
                        'depth_image': depth_image,
                        'system_cap_time': start_time,
                        'image_queued_time': time.time()
                    }
                except Exception as exc:  # pylint: disable=broad-except
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
    processes = []
    for _ in range(num_processes):
        process = Process(
            target=process_images, args=(
                model_path,
                detection_class,
                detection_threshold,
                max_processing_delay,
            ), daemon=True)
        process.start()
        processes.append(process)
    return processes


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

    while not SHUTDOWN_FLAG.value:
        try:
            entry = RAW_IMAGES_QUEUE.get_nowait()
        except Empty:
            time.sleep(0.1)
            continue
        for _, capture in entry.items():
            start_time = time.time()
            processing_delay = time.time() - capture['raw_image_time']
            if processing_delay > max_processing_delay:
                num_processed_skips += 1
                print(f'skipped image because it took {processing_delay}')
                continue  # Skip image due to delay

            image = capture['cv_image']
            boxes, scores, classes, _ = odapi.process_frame(image)
            confident_boxes = []
            confident_object_classes = []
            confident_scores = []
            if len(boxes) == 0:
                print('no detections founds')
                continue
            for box, score, box_class in sorted(zip(boxes, scores, classes), key=lambda x: x[1],
                                                reverse=True):
                if score > detection_threshold and box_class == detection_class:
                    confident_boxes.append(box)
                    confident_object_classes.append(COCO_CLASS_DICT[box_class])
                    confident_scores.append(score)
                    image = cv2.rectangle(image, (box[1], box[0]), (box[3], box[2]), (255, 0, 0), 2)

            capture['processed_image_start_time'] = start_time
            capture['processed_image_end_time'] = time.time()
            capture['boxes'] = confident_boxes
            capture['classes'] = confident_object_classes
            capture['scores'] = confident_scores
            capture['cv_image'] = image
        try:
            PROCESSED_BOXES_QUEUE.put_nowait(entry)
        except Full as exc:
            print(f'PROCESSED_BOXES_QUEUE is full: {exc}')
    print('tf process ending')
    return True


def get_go_to(world_tform_object, robot_state, mobility_params, dist_margin=0.5):
    """Gets trajectory command to a goal location

    Args:
        world_tform_object (SE3Pose): Transform from vision frame to target object
        robot_state (RobotState): Current robot state
        mobility_params (MobilityParams): Mobility parameters
        dist_margin (float): Distance margin to target
    """
    vo_tform_robot = get_vision_tform_body(robot_state.kinematic_state.transforms_snapshot)
    print(f"robot pos: {vo_tform_robot}")
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
    tag_cmd = RobotCommandBuilder.trajectory_command(goal_x=vo_tform_goal[0],
                                                     goal_y=vo_tform_goal[1], goal_heading=heading,
                                                     frame_name=VISION_FRAME_NAME,
                                                     params=mobility_params)
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


def depth_to_xyz(depth, pixel_x, pixel_y, focal_length, principal_point):
    """Calculate the transform to point in image using camera intrinsics and depth"""
    x = depth * (pixel_x - principal_point.x) / focal_length.x
    y = depth * (pixel_y - principal_point.y) / focal_length.y
    z = depth
    return x, y, z


def remove_ground_from_depth_image(raw_depth_image, focal_length, principal_point, world_tform_cam,
                                   world_tform_gpe, ground_tolerance=0.04):
    """ Simple ground plane removal algorithm. Uses ground height
        and does simple z distance filtering.

    Args:
        raw_depth_image (np.array): Depth image
        focal_length (Vec2): Focal length of camera that produced the depth image
        principal_point (Vec2): Principal point of camera that produced the depth image
        world_tform_cam (SE3Pose): Transform from VO to camera frame
        world_tform_gpe (SE3Pose): Transform from VO to GPE frame
        ground_tolerance (float): Distance in meters to add to the ground plane
    """
    new_depth_image = raw_depth_image

    # same functions as depth_to_xyz, but converted to np functions
    indices = np.indices(raw_depth_image.shape)
    xs = raw_depth_image * (indices[1] - principal_point.x) / focal_length.x
    ys = raw_depth_image * (indices[0] - principal_point.y) / focal_length.y
    zs = raw_depth_image

    # create xyz point cloud
    camera_tform_points = np.stack([xs, ys, zs], axis=2)
    # points in VO frame
    world_tform_points = world_tform_cam.transform_cloud(camera_tform_points)
    # array of booleans where True means the point was below the ground plane plus tolerance
    world_tform_points_mask = (world_tform_gpe.z - world_tform_points[:, :, 2]) < ground_tolerance
    # remove data below ground plane
    new_depth_image[world_tform_points_mask] = 0
    return new_depth_image


def get_distance_to_closest_object_depth(x_min, x_max, y_min, y_max, depth_scale, raw_depth_image,
                                         histogram_bin_size=0.50, minimum_number_of_points=10,
                                         max_distance=8.0):
    """Make a histogram of distances to points in the cloud and take the closest distance with
    enough points.

    Args:
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

    # get a sub-rectangle of the bounding box out of the whole image, then flatten
    obj_depths = (raw_depth_image[y_min:y_max, x_min:x_max]).flatten()
    obj_depths = obj_depths / depth_scale
    obj_depths = obj_depths[obj_depths != 0]

    hist, hist_edges = np.histogram(obj_depths, bins=num_bins, range=(0, max_distance))

    edges_zipped = zip(hist_edges[:-1], hist_edges[1:])
    # Iterate over the histogram and return the first distance with enough points.
    for entry, edges in zip(hist, edges_zipped):
        if entry > minimum_number_of_points:
            filtered_depths = obj_depths[(obj_depths > edges[0]) & (obj_depths < edges[1])]
            if len(filtered_depths) == 0:
                continue
            return np.mean(filtered_depths)

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


def get_object_position(world_tform_cam, world_tform_gpe, visual_dims, depth_image, bounding_box,
                        rotation_angle):
    """
    Extract the bounding box, then find the mode in that region.

    Args:
        world_tform_cam (SE3Pose): SE3 transform from world to camera frame
        visual_dims (Tuple): (cols, rows) tuple from the visual image
        depth_image (ImageResponse): From a depth camera corresponding to the visual_image
        bounding_box (list): Bounding box from tensorflow
        rotation_angle (float): Angle (in degrees) to rotate depth image to match cam image rotation
    """

    # Make sure there are two images.
    if visual_dims is None or depth_image is None:
        # Fail.
        return

    # Rotate bounding box back to original frame
    points = [(bounding_box[1], bounding_box[0]), (bounding_box[3], bounding_box[0]),
              (bounding_box[3], bounding_box[2]), (bounding_box[1], bounding_box[2])]

    origin = (visual_dims[0] / 2, visual_dims[1] / 2)

    points_rot = [rotate_about_origin_degrees(origin, point, rotation_angle) for point in points]

    # Get the bounding box corners.
    y_min = max(0, min([point[1] for point in points_rot]))
    x_min = max(0, min([point[0] for point in points_rot]))
    y_max = min(visual_dims[1], max([point[1] for point in points_rot]))
    x_max = min(visual_dims[0], max([point[0] for point in points_rot]))

    # Check that the bounding box is valid.
    if (x_min < 0 or y_min < 0 or x_max > visual_dims[0] or y_max > visual_dims[1]):
        print(f'Bounding box is invalid: ({x_min}, {y_min}) | ({x_max}, {y_max})')
        print(f'Bounds: ({visual_dims[0]}, {visual_dims[1]})')
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
        depth_image_pixels = remove_ground_from_depth_image(
            depth_image_pixels, depth_image.source.pinhole.intrinsics.focal_length,
            depth_image.source.pinhole.intrinsics.principal_point, world_tform_cam, world_tform_gpe)
        # Get the depth data from the region in the bounding box.
        max_distance = 8.0
        depth = get_distance_to_closest_object_depth(x_min, x_max, y_min, y_max,
                                                     depth_image.source.depth_scale,
                                                     depth_image_pixels, max_distance=max_distance)

        if depth >= max_distance:
            # Not enough depth data.
            print('Not enough depth data.')
            return False
        else:
            print(f"distance to object: {depth}")

        center_x = round((x_max - x_min) / 2.0 + x_min)
        center_y = round((y_max - y_min) / 2.0 + y_min)

        tform_x, tform_y, tform_z = depth_to_xyz(
            depth, center_x, center_y, depth_image.source.pinhole.intrinsics.focal_length,
            depth_image.source.pinhole.intrinsics.principal_point)
        camera_tform_obj = SE3Pose(tform_x, tform_y, tform_z, Quat())

        return world_tform_cam * camera_tform_obj
    except Exception as exc:  # pylint: disable=broad-except
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
            global COCO_CLASS_DICT  # pylint: disable=global-statement
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


def signal_handler(signal, frame):
    print('Interrupt caught, shutting down')
    SHUTDOWN_FLAG.value = 1


def main(argv):
    """Command line interface.

    Args:
        argv: List of command-line arguments passed to the program.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-path", default="/model.pb", help=
        ("Local file path to the Tensorflow model, example pre-trained models can be found at "
         "https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/tf1_detection_zoo.md"
        ))
    parser.add_argument("--classes", default='/classes.json', type=str,
                        help="File containing json mapping of object class IDs to class names")
    parser.add_argument("--number-tensorflow-processes", default=1, type=int,
                        help="Number of Tensorflow processes to run in parallel")
    parser.add_argument("--detection-threshold", default=0.7, type=float,
                        help="Detection threshold to use for Tensorflow detections")
    parser.add_argument(
        "--sleep-between-capture", default=0.2, type=float,
        help=("Seconds to sleep between each image capture loop iteration, which captures "
              "an image from all cameras"))
    parser.add_argument(
        "--detection-class", default=1, type=int,
        help=("Detection classes to use in the Tensorflow model."
              "Default is to use 1, which is a person in the Coco dataset"))
    parser.add_argument(
        "--max-processing-delay", default=7.0, type=float,
        help=("Maximum allowed delay for processing an image. "
              "Any image older than this value will be skipped"))
    parser.add_argument("--test-mode", action='store_true',
                        help="Run application in test mode, don't execute commands")

    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args(argv)
    signal.signal(signal.SIGINT, signal_handler)
    try:
        # Make sure the model path is a valid file
        if not _check_model_path(options.model_path):
            return False

        # Check for classes json file, otherwise use the COCO class dictionary
        _check_and_load_json_classes(options.classes)

        global TENSORFLOW_PROCESS_BARRIER  # pylint: disable=global-statement
        TENSORFLOW_PROCESS_BARRIER = Barrier(options.number_tensorflow_processes + 1)
        # Start Tensorflow processes
        tf_processes = start_tensorflow_processes(options.number_tensorflow_processes,
                                                  options.model_path, options.detection_class,
                                                  options.detection_threshold,
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
        bosdyn.client.util.authenticate(robot)
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

        lease = lease_client.take()
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
        image_capture_thread = Process(target=capture_images,
                                       args=(image_task, options.sleep_between_capture),
                                       daemon=True)
        image_capture_thread.start()
        while not SHUTDOWN_FLAG.value:
            # This comes from the tensorflow processes and limits the rate of this loop
            try:
                entry = PROCESSED_BOXES_QUEUE.get_nowait()
            except Empty:
                continue
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
            get_object_position_start = time.time()
            robot_state = robot_state_task.proto
            world_tform_gpe = get_a_tform_b(robot_state.kinematic_state.transforms_snapshot,
                                            VISION_FRAME_NAME, GROUND_PLANE_FRAME_NAME)
            world_tform_object = get_object_position(
                capture_to_use['world_tform_cam'], world_tform_gpe, capture_to_use['visual_dims'],
                capture_to_use['depth_image'], capture_to_use['boxes'][0],
                ROTATION_ANGLES[capture_to_use['source']])
            get_object_position_end = time.time()
            print(f"system_cap_time: {capture_to_use['system_cap_time']}, "
                  f"image_queued_time: {capture_to_use['image_queued_time']}, "
                  f"processed_image_start_time: {capture_to_use['processed_image_start_time']}, "
                  f"processed_image_end_time: {capture_to_use['processed_image_end_time']}, "
                  f"get_object_position_start_time: {get_object_position_start}, "
                  f"get_object_position_end_time: {get_object_position_end}, ")

            # get_object_position can fail if there is insufficient depth sensor information
            if not world_tform_object:
                continue

            scores = capture_to_use['scores']
            print(f'Position of object with confidence {scores[0]}: {world_tform_object}')
            print(f'Process latency: {time.time() - capture_to_use["system_cap_time"]}')
            tag_cmd = get_go_to(world_tform_object, robot_state, params_set)
            end_time = 15.0
            if tag_cmd is not None:
                if not options.test_mode:
                    print("executing command")
                    robot_command_client.robot_command(lease=None, command=tag_cmd,
                                                       end_time_secs=time.time() + end_time)
                else:
                    print("Running in test mode, skipping command.")

        # Shutdown lease keep-alive and return lease gracefully.
        lease_keep.shutdown()
        lease_client.return_lease(lease)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error("Spot Tensorflow Detector threw an exception: %s", exc)
        # Shutdown lease keep-alive and return lease gracefully.
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
