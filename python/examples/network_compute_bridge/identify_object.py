# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from __future__ import print_function

import argparse
import math
import sys
import time

import cv2
import numpy as np
from google.protobuf import wrappers_pb2

import bosdyn.client
import bosdyn.client.util
from bosdyn import geometry
from bosdyn.api import geometry_pb2 as geo
from bosdyn.api import (image_pb2, network_compute_bridge_pb2, network_compute_bridge_service_pb2,
                        network_compute_bridge_service_pb2_grpc, trajectory_pb2)
from bosdyn.api.image_pb2 import ImageSource
from bosdyn.api.spot import robot_command_pb2 as spot_command_pb2
from bosdyn.client.common import BaseClient, common_header_errors
from bosdyn.client.estop import EstopClient, EstopEndpoint, EstopKeepAlive
from bosdyn.client.image import ImageClient
from bosdyn.client.lease import LeaseClient, LeaseKeepAlive
from bosdyn.client.math_helpers import Quat
from bosdyn.client.network_compute_bridge_client import NetworkComputeBridgeClient
from bosdyn.client.robot_command import RobotCommandBuilder, RobotCommandClient, blocking_stand
from bosdyn.client.robot_state import RobotStateClient
from bosdyn.client.world_object import (WorldObjectClient, make_add_world_object_req,
                                        make_change_world_object_req, make_delete_world_object_req)


def get_all_network_compute_services(directory_client):
    dir_list = directory_client.list()
    out = []

    for service in dir_list:
        if service.type == "bosdyn.api.NetworkComputeBridgeWorker":
            out.append(service.name)

    return out


def main(argv):
    """An example using the API to list and get specific objects."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('-i', '--image-source', help='Image source on the robot to use.')
    parser.add_argument(
        '-q', '--image-source-service', help=
        'Image *service* for the image source to use.  Defaults to the main image service if not provided.',
        default='')
    parser.add_argument('-s', '--service',
                        help='Service name of external machine learning server in the directory.',
                        required=False)
    parser.add_argument('-m', '--model', help='Model file on the server')
    parser.add_argument('-c', '--confidence', help='Minimum confidence to return an object.',
                        default=0.5, type=float)
    parser.add_argument('-j', '--input-image',
                        help='Path to an image to use instead of an image source.')
    parser.add_argument(
        '-l', '--model-list',
        help='List all available network compute servers and their provided models.',
        action='store_true')
    parser.add_argument('-r', '--disable-rotation',
                        help='Disable rotation of images (to align with horizontal)',
                        action='store_true')
    options = parser.parse_args(argv)

    if options.image_source is not None and options.input_image is not None:
        print('Error: cannot provide both an input image and an image source.')
        sys.exit(1)

    if options.model_list and (options.image_source is not None or options.input_image is not None):
        print('Error: cannot list models with input image source or input image.')
        sys.exit(1)

    if options.image_source is None and options.input_image is None and options.model_list == False:
        default_image_source = 'frontleft_fisheye_image'
        print('No image source provided so defaulting to "' + default_image_source + '".')
        options.image_source = default_image_source

    # Create robot object with a world object client
    sdk = bosdyn.client.create_standard_sdk('IdentifyObjectClient')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    #Time sync is necessary so that time-based filter requests can be converted
    robot.time_sync.wait_for_sync()

    #Create the network compute client
    network_compute_client = robot.ensure_client(NetworkComputeBridgeClient.default_service_name)

    directory_client = robot.ensure_client(
        bosdyn.client.directory.DirectoryClient.default_service_name)

    robot_state_client = robot.ensure_client(RobotStateClient.default_service_name)
    robot_command_client = robot.ensure_client(RobotCommandClient.default_service_name)
    robot.time_sync.wait_for_sync()

    if options.model_list:
        server_service_names = get_all_network_compute_services(directory_client)

        print('Found ' + str(len(server_service_names)) +
              ' available service(s).  Listing their models:')
        print('------------------------------------')

        for service in server_service_names:
            print('    ' + service)
            server_data = network_compute_bridge_pb2.NetworkComputeServerConfiguration(
                service_name=service)
            list_req = network_compute_bridge_pb2.ListAvailableModelsRequest(
                server_config=server_data)
            response = network_compute_client.list_available_models_command(list_req)

            if response.header.error.message:
                print('        Error message: {}'.format(response.header.error.message))
            else:
                for model in response.available_models:
                    print('        ' + model)
        sys.exit(0)

    # A service name must be provided if not doing a directory list.
    if options.service is None or len(options.service) == 0:
        print('Error: --service must be provided for operations other than --model-list')
        sys.exit(1)

    server_data = network_compute_bridge_pb2.NetworkComputeServerConfiguration(
        service_name=options.service)

    if options.image_source is not None:
        if options.model is None:
            print('Error: you must provide a model.')
            sys.exit(1)

        img_source_and_service = network_compute_bridge_pb2.ImageSourceAndService(
            image_source=options.image_source, image_service=options.image_source_service)

        input_data = network_compute_bridge_pb2.NetworkComputeInputData(
            image_source_and_service=img_source_and_service, model_name=options.model,
            min_confidence=options.confidence)
    else:
        # Read the input image.
        image_in = cv2.imread(options.input_image)
        if image_in is None:
            print('Error: failed to read "' + options.input_image + '".  Does the file exist?')
            sys.exit(1)

        rgb = cv2.cvtColor(image_in, cv2.COLOR_BGR2RGB)

        success, im_buffer = cv2.imencode(".jpg", rgb)

        if not success:
            print('Error: failed to encode input image as a jpg.  Abort.')
            sys.exit(1)

        height = image_in.shape[0]
        width = image_in.shape[1]

        image_proto = image_pb2.Image(format=image_pb2.Image.FORMAT_JPEG, cols=width, rows=height,
                                      data=im_buffer.tobytes(),
                                      pixel_format=image_pb2.Image.PIXEL_FORMAT_RGB_U8)

        input_data = network_compute_bridge_pb2.NetworkComputeInputData(
            image=image_proto, model_name=options.model, min_confidence=options.confidence)

    if options.disable_rotation:
        input_data.rotate_image = network_compute_bridge_pb2.NetworkComputeInputData.ROTATE_IMAGE_NO_ROTATION
    else:
        input_data.rotate_image = network_compute_bridge_pb2.NetworkComputeInputData.ROTATE_IMAGE_ALIGN_HORIZONTAL

    process_img_req = network_compute_bridge_pb2.NetworkComputeRequest(
        input_data=input_data, server_config=server_data)

    response = network_compute_client.network_compute_bridge_command(process_img_req)

    if len(response.object_in_image) <= 0:
        print('No objects found')
    else:
        print('Got ' + str(len(response.object_in_image)) + ' objects.')

    if options.image_source is not None:
        # We asked for an image to be taken, so the return proto should have an image in it.
        dtype = np.uint8
        img = np.frombuffer(response.image_response.shot.image.data, dtype=dtype)
        if response.image_response.shot.image.format == image_pb2.Image.FORMAT_RAW:
            img = img.reshape(response.image_response.shot.image.rows,
                              response.image_response.shot.image.cols)
        else:
            img = cv2.imdecode(img, -1)
    else:
        # To save bandwidth, the network_compute_bridge service won't re-send us back our own
        # image.
        img = image_in

    # The image always comes back in the raw orientation.  Rotate it to horizontal so that we can
    # visualize it the same as it was processed.
    img, rotmat = rotate_image_nocrop(img, response.image_rotation_angle)

    # Convert to color for nicer drawing
    if len(img.shape) < 3:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    # Draw bounding boxes in the image for all the detections.
    for obj in response.object_in_image:
        print(obj)
        conf_msg = wrappers_pb2.FloatValue()
        obj.additional_properties.Unpack(conf_msg)
        confidence = conf_msg.value

        polygon = []
        min_x = float('inf')
        min_y = float('inf')
        for v in obj.image_properties.coordinates.vertexes:
            # If we are rotating the output image, make sure to rotate the bounding box points
            # as well
            x, y = rotate_point(v.x, v.y, rotmat)
            polygon.append([x, y])
            min_x = min(min_x, x)
            min_y = min(min_y, y)

        polygon = np.array(polygon, np.int32)
        polygon = polygon.reshape((-1, 1, 2))
        cv2.polylines(img, [polygon], True, (0, 255, 0), 2)

        caption = "{} {:.3f}".format(obj.name, confidence)
        cv2.putText(img, caption, (int(min_x), int(min_y)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 255, 0), 2)

    cv2.imwrite('identify_object_output.jpg', img)


def rotate_image_nocrop(img, rotation_rad):
    """ Rotate an image without cropping (instead adding black space) """
    h = img.shape[0]
    w = img.shape[1]
    cX = w / 2
    cY = h / 2

    rotmat = cv2.getRotationMatrix2D((cX, cY), math.degrees(rotation_rad), 1.0)

    cos_d = abs(rotmat[0][0])
    sin_d = abs(rotmat[0][1])

    # Compute the new bounding dimensions
    nW = int((h * sin_d) + (w * cos_d))
    nH = int((h * cos_d) + (w * sin_d))

    # Adjust the rotation matrix to account for translation
    rotmat[0][2] += (nW / 2.0) - cX
    rotmat[1][2] += (nH / 2.0) - cY

    img = cv2.warpAffine(img, rotmat, (nW, nH))

    return img, rotmat


def rotate_point(x, y, rotmat):
    """ Apply a rotation matrix to a point """
    src = np.array([[[x, y]]])
    out = cv2.transform(src, rotmat)
    return out[0][0]


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
