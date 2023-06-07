# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Tutorial to show how to use the service customization with the Network Compute API

This example server handles requests to run a Tensorflow model on image
services registered with Spot. The server is configured to run the
Faster R-CNN network but can be reconfigured to run other object
detection networks by modifying the tensor names to match your model's input
and output layer names. Please see the README.md for information on how to
acquire the Faster R-CNN model file that can be used to demonstrate this example.

Clients can specify a region of interest and confidence value in the image recieved 
by the network compute bridge worker. The region of interest tells the model where
to look for object matches. The confidence value tells the model the confidence 
threshold for an object match.
"""

import argparse
import io
import logging
import math
import multiprocessing
import os
import queue
import socket
import sys
import threading
import time
from concurrent import futures
from multiprocessing import Lock, Process, Queue
from timeit import default_timer as timer

import cv2
import grpc
# import the necessary packages for ML
import numpy
import numpy as np
import tensorflow as tf
from google.protobuf import any_pb2, wrappers_pb2
from PIL import Image
from scipy import ndimage

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import (header_pb2, image_pb2, network_compute_bridge_pb2,
                        network_compute_bridge_service_pb2, network_compute_bridge_service_pb2_grpc,
                        service_customization_pb2, world_object_pb2)
from bosdyn.api.image_pb2 import ImageSource
from bosdyn.client.image import ImageClient
from bosdyn.client.service_customization_helpers import create_value_validator

# This is a multiprocessing.Queue for communication between the main process and the
# Tensorflow processes.
REQUEST_QUEUE = Queue()

# This is a multiprocessing.Queue for communication between the Tensorflow processes and
# the display process.
RESPONSE_QUEUE = Queue()

TOGGLE_KEY = "roi_toggle"
TOGGLE_OFF_KEY = "off"
TOGGLE_ON_KEY = "on"
ROI_KEY = "roi"
CONFIDENCE_KEY = "confidence"


class TensorflowModel:
    """ Wraps a tensorflow model in a way that allows online switching between models."""

    def __init__(self, path, labels_path):
        self.path = path

        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.compat.v1.GraphDef()
            with tf.io.gfile.GFile(self.path, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

        # Make sure we tell tensor flow that this is a different model.
        self.default_graph = self.detection_graph.as_default()
        self.sess = tf.compat.v1.Session(graph=self.detection_graph)

        # Definite input and output Tensors for detection_graph
        self.image_tensor = self.detection_graph.get_tensor_by_name('image_tensor:0')
        # Each box represents a part of the image where a particular object was detected.
        self.detection_boxes = self.detection_graph.get_tensor_by_name('detection_boxes:0')
        # Each score represent how level of confidence for each of the objects.
        # Score is shown on the result image, together with the class label.
        self.detection_scores = self.detection_graph.get_tensor_by_name('detection_scores:0')
        self.detection_classes = self.detection_graph.get_tensor_by_name('detection_classes:0')
        self.num_detections = self.detection_graph.get_tensor_by_name('num_detections:0')

        if labels_path is None:
            self.labels = None
        else:
            # Load the class label mappings
            self.labels = open(labels_path).read().strip().split('\n')
            self.labels = {int(L.split(',')[1]): L.split(',')[0] for L in self.labels}

    def predict(self, image):
        """ Predict with this model. """
        with self.detection_graph.as_default():
            # Expand dimensions since the trained_model expects images to have shape: [1, None, None, 3]
            image_np_expanded = np.expand_dims(image, axis=0)
            # Actual detection.
            (boxes, scores, classes, num) = self.sess.run([
                self.detection_boxes, self.detection_scores, self.detection_classes,
                self.num_detections
            ], feed_dict={self.image_tensor: image_np_expanded})

            im_height, im_width, _ = image.shape
            boxes_list = [None for i in range(boxes.shape[1])]
            for i in range(boxes.shape[1]):
                boxes_list[i] = (int(boxes[0, i, 0] * im_height), int(boxes[0, i, 1] * im_width),
                                 int(boxes[0, i, 2] * im_height), int(boxes[0, i, 3] * im_width))

            if self.labels is not None:
                labels_out = [self.labels[int(x)] for x in classes[0].tolist()]
            else:
                labels_out = classes[0].tolist()

            return boxes_list, scores[0].tolist(), labels_out, int(num[0])


def start_tensorflow_processes(options, model_extension):
    """Starts Tensorflow processes in parallel.

    It does not keep track of the processes once they are started because they run indefinitely
    and are never joined back to the main process.
    """

    process = Process(target=process_images, args=([options, model_extension]))
    process.start()


def create_custom_param_spec():
    """Creates the custom parameter specification for the NCB worker.
    """
    param_spec = service_customization_pb2.DictParam.Spec()

    # Create one of param with options "On" and "Off".
    # "On" enables region of interest param.
    oneof_dict_childspec = param_spec.specs.get_or_create(TOGGLE_KEY)
    oneof_dict_childspec.ui_info.display_name = "Region Of Interest Toggle"
    oneof_dict_childspec.ui_info.description = "Turn on/off region of interest. If off model will look for object matches in entire image."
    oneof_spec = oneof_dict_childspec.spec.one_of_spec
    oneof_spec.specs.get_or_create(TOGGLE_OFF_KEY)
    oneof_spec.default_key = TOGGLE_OFF_KEY

    # Create region of interest param.
    roi_dict_childspec = oneof_spec.specs.get_or_create(TOGGLE_ON_KEY).spec.specs.get_or_create(
        ROI_KEY)
    roi_dict_childspec.ui_info.display_name = "Region Of Interest"
    roi_dict_childspec.ui_info.description = "Network compute bridge worker will look for object matches in specified region."
    roi_spec = roi_dict_childspec.spec.roi_spec
    roi_spec.allows_rectangle = True

    # Create double param to specify minimum confidence to return an object.
    double_dict_childspec = param_spec.specs.get_or_create(CONFIDENCE_KEY)
    double_dict_childspec.ui_info.display_name = "Confidence"
    double_dict_childspec.ui_info.description = "Minimum confidence to return an object."
    double_spec = double_dict_childspec.spec.double_spec
    double_spec.default_value.value = 0.5
    double_spec.min_value.value = 0
    double_spec.max_value.value = 1

    return param_spec


def process_images(options, model_extension):
    """Starts Tensorflow and detects objects in the incoming images.
    """
    models = {}
    for f in os.listdir(options.model_dir):
        if f in models:
            print(f'Warning: duplicate model name of "{f}", ignoring second model.')
            continue

        path = os.path.join(options.model_dir, f)
        if os.path.isfile(path) and path.endswith(model_extension):
            model_name = ''.join(f.rsplit(model_extension, 1))  # remove the extension

            # reverse replace the extension
            labels_file = '.csv'.join(f.rsplit(model_extension, 1))
            labels_path = os.path.join(options.model_dir, labels_file)

            if not os.path.isfile(labels_path):
                labels_path = None
            models[model_name] = (TensorflowModel(path, labels_path))

    # Tensorflow prints out a bunch of stuff, so print out useful data here after a space.
    print('')
    print(f'Running on port: {options.port}')
    print('Loaded models:')
    for model_name in models:
        if models[model_name].labels is not None:
            labels_str = 'yes'
        else:
            labels_str = 'no'
        print(f'    {model_name} (loaded labels: {labels_str})')

    # Create an validate custom parameter specification.
    param_spec = create_custom_param_spec()
    param_validator = create_value_validator(param_spec)

    while True:
        request = REQUEST_QUEUE.get()

        # Handle ListAvailableModel requests.
        if isinstance(request, network_compute_bridge_pb2.ListAvailableModelsRequest):
            out_proto = network_compute_bridge_pb2.ListAvailableModelsResponse()
            for f in models:
                out_proto.models.data.append(
                    network_compute_bridge_pb2.ModelData(model_name=f, custom_params=param_spec))
            RESPONSE_QUEUE.put(out_proto)
            continue

        # Handle WorkerCompute requests.
        else:
            out_proto = network_compute_bridge_pb2.WorkerComputeResponse()

        # Validate custom parameters.
        param_error = param_validator(request.input_data.parameters.custom_params)
        if param_error:
            out_proto.status = network_compute_bridge_pb2.NETWORK_COMPUTE_STATUS_CUSTOM_PARAMS_ERROR
            out_proto.custom_param_error.CopyFrom(param_error)
            for message in param_error.error_message:
                err_str = "\n" + err_str + message
            print(f'Custom parameter validation failed: {err_str}')
            RESPONSE_QUEUE.put(out_proto)
            continue

        # Find the model
        if request.input_data.parameters.model_name not in models:
            err_str = f'Cannot find model "{request.input_data.parameters.model_name}" in loaded models.'
            print(err_str)

            # Set the error in the header.
            out_proto.header.error.code = header_pb2.CommonError.CODE_INVALID_REQUEST
            out_proto.header.error.message = err_str
            RESPONSE_QUEUE.put(out_proto)
            continue

        model = models[request.input_data.parameters.model_name]

        # Loop through images in request.
        image_num = 0
        for image in request.input_data.images:
            image_num += 1
            image_key = f'Image_{image_num}'
            image_proto = image.shot.image
            if image_proto.format == image_pb2.Image.FORMAT_RAW:
                pil_image = Image.open(io.BytesIO(image_proto.data))
                pil_image = ndimage.rotate(pil_image, 0)
                if image_proto.pixel_format == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8:
                    model_image = cv2.cvtColor(
                        pil_image, cv2.COLOR_GRAY2RGB)  # Converted to RGB for Tensorflow
                elif image_proto.pixel_format == image_pb2.Image.PIXEL_FORMAT_RGB_U8:
                    # Already in the correct format
                    model_image = pil_image
                else:
                    err_str = f'Error: image input in unsupported pixel format: {image_proto.pixel_format}'
                    print(err_str)

                    # Set the error in the header.
                    out_proto.header.error.code = header_pb2.CommonError.CODE_INVALID_REQUEST
                    out_proto.header.error.message = err_str
                    RESPONSE_QUEUE.put(out_proto)
                    continue
            elif image_proto.format == image_pb2.Image.FORMAT_JPEG:
                dtype = np.uint8
                jpg = np.frombuffer(image_proto.data, dtype=dtype)
                model_image = cv2.imdecode(jpg, -1)

                if len(model_image.shape) < 3:
                    # Single channel image, convert to RGB.
                    model_image = cv2.cvtColor(model_image, cv2.COLOR_GRAY2RGB)

            # Check if request specifies region of interest.
            roi_toggle = request.input_data.parameters.custom_params.values.get(TOGGLE_KEY)
            if roi_toggle is not None and roi_toggle.one_of_value.key == TOGGLE_ON_KEY:
                roi_param = roi_toggle.one_of_value.values.get(TOGGLE_ON_KEY).values.get(
                    ROI_KEY).roi_value

                # Ensure image dimensions are consistent.
                if roi_param.image_cols != image_proto.cols or roi_param.image_rows != image_proto.rows:
                    err_str = "Image dimensions of capture does not match image dimensions specified in region of interest parameter."
                    out_proto.custom_param_error.error_messages.append(err_str)
                    out_proto.custom_param_error.status = service_customization_pb2.CustomParamError.STATUS_INVALID_VALUE
                    print(err_str)
                    RESPONSE_QUEUE.put(out_proto)
                    continue

                # Crop image to region of interest
                rectangle = roi_param.area.rectangle
                model_image_cropped = model_image[rectangle.y:rectangle.y + rectangle.rows,
                                                  rectangle.x:rectangle.x + rectangle.cols]

                # Function to convert pixel in cropped image to pixel in uncropped image
                convert_pixel = lambda x, y: (x + rectangle.x, y + rectangle.y)

            # If region of interest is turned off, use uncropped image.
            else:
                model_image_cropped = model_image
                convert_pixel = lambda x, y: (x, y)

            boxes, scores, classes, _ = model.predict(model_image_cropped)

            num_objects = 0

            for i in range(len(boxes)):

                label = str(classes[i])
                box = boxes[i]
                score = scores[i]

                # Enforce minimum confidence value from request.
                min_confidence = request.input_data.parameters.custom_params.values.get(
                    CONFIDENCE_KEY).double_value.value
                if score < min_confidence:
                    break
                num_objects += 1
                print(f'Found object with label: "{label}" and score: {score}')

                # Get pixel coordinates of box corners in uncropped image.
                point1 = np.array(convert_pixel(box[1], box[0]))
                point2 = np.array(convert_pixel(box[3], box[0]))
                point3 = np.array(convert_pixel(box[3], box[2]))
                point4 = np.array(convert_pixel(box[1], box[2]))

                # Add data to the output proto.
                out_obj = out_proto.output_images.get_or_create(image_key).object_in_image.add()
                out_obj.name = f'obj {num_objects}_label_{label}'

                def add_vertex(point):
                    vertex = out_obj.image_properties.coordinates.vertexes.add()
                    vertex.x = point[0]
                    vertex.y = point[1]

                add_vertex(point1)
                add_vertex(point2)
                add_vertex(point3)
                add_vertex(point4)

                # Pack the confidence value.
                confidence = wrappers_pb2.FloatValue(value=score)
                out_obj.additional_properties.Pack(confidence)

                # Draw box on image.
                polygon = np.array([point1, point2, point3, point4], np.int32)
                polygon = polygon.reshape((-1, 1, 2))
                cv2.polylines(model_image, [polygon], True, (0, 255, 0), 2)
                caption = f'{label}: {score:.3f}'
                left_x = min(point1[0], min(point2[0], min(point3[0], point4[0])))
                top_y = min(point1[1], min(point2[1], min(point3[1], point4[1])))
                cv2.putText(model_image, caption, (int(left_x), int(top_y)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Add image to response
            out_img = out_proto.output_images.get_or_create(image_key).image_response
            out_img.status = image_pb2.ImageResponse.STATUS_OK
            out_img.custom_param_error.status = service_customization_pb2.CustomParamError.STATUS_OK
            out_img.source.CopyFrom(image.source)
            out_img.shot.CopyFrom(image.shot)
            if image_proto.format == image_pb2.Image.FORMAT_RAW:
                out_img.shot.image.data = np.ndarray.tobytes(model_image)
            elif image_proto.format == image_pb2.Image.FORMAT_JPEG or image_proto.format == image_pb2.Image.FORMAT_UNKNOWN:
                out_img.shot.image.data = cv2.imencode('.jpg', model_image)[1].tobytes()
            else:
                # Unsupported format.
                print(
                    f'Image format {image_pb2.Image.Format.Name(image_proto.format)} is unsupported.'
                )

            print(f'Found {num_objects} object(s)')
        RESPONSE_QUEUE.put(out_proto)


class NetworkComputeBridgeWorkerServicer(
        network_compute_bridge_service_pb2_grpc.NetworkComputeBridgeWorkerServicer):

    def __init__(self, thread_input_queue, thread_output_queue):
        super(NetworkComputeBridgeWorkerServicer, self).__init__()

        self.thread_input_queue = thread_input_queue
        self.thread_output_queue = thread_output_queue
        self._lock = Lock()

    def WorkerCompute(self, request, context):
        with self._lock:
            self.thread_input_queue.put(request)
            out_proto = self.thread_output_queue.get()
        return out_proto

    def ListAvailableModels(self, request, context):
        with self._lock:
            self.thread_input_queue.put(request)
            out_proto = self.thread_output_queue.get()
        return out_proto


def register_with_robot(options):
    """ Registers this worker with the robot's Directory."""
    ip = bosdyn.client.common.get_self_ip(options.hostname)
    print(f'Detected IP address as: {ip}')
    kServiceName = 'tensorflow-server'
    kServiceAuthority = 'tensorflow-worker.spot.robot'

    sdk = bosdyn.client.create_standard_sdk('tensorflow_server')

    robot = sdk.create_robot(options.hostname)

    # Authenticate robot before being able to use it
    bosdyn.client.util.authenticate(robot)

    directory_client = robot.ensure_client(
        bosdyn.client.directory.DirectoryClient.default_service_name)
    directory_registration_client = robot.ensure_client(
        bosdyn.client.directory_registration.DirectoryRegistrationClient.default_service_name)

    # Check to see if a service is already registered with our name
    services = directory_client.list()
    for s in services:
        if s.name == kServiceName:
            print(f'WARNING: existing service with name, "{kServiceName}", removing it.')
            directory_registration_client.unregister(kServiceName)
            break

    # Register service
    print(f'Attempting to register {ip}:{options.port} onto {options.hostname} directory...')
    directory_registration_client.register(kServiceName, 'bosdyn.api.NetworkComputeBridgeWorker',
                                           kServiceAuthority, ip, int(options.port))


def main(argv):
    """Command line interface.

    Args:
        argv: List of command-line arguments passed to the program.
    """

    default_port = '50051'
    model_extension = '.pb'

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--model-dir', help=
        'Directory of pre-trained models and (optionally) associated label files.\nExample directory contents: my_model.pb, my_classes.csv, my_model2.pb, my_classes2.csv.  CSV label format is: object,1<new line>thing,2',
        required=True)
    parser.add_argument('-p', '--port', help=f'Server\'s port number, default: {default_port}',
                        default=default_port)
    parser.add_argument('--username', help='User name of account to get credentials for.')
    parser.add_argument('--password', help='Password to get credentials for.')
    parser.add_argument('hostname', nargs='?', help='Hostname or address of robot,'
                        ' e.g. "beta25-p" or "192.168.80.3"')

    options = parser.parse_args(argv)

    if not os.path.isdir(options.model_dir):
        print(f'Error: model directory ({options.model_dir}) not found or is not a directory.')
        sys.exit(1)

    # Make sure there is at least one file ending in .pb in the directory.
    found_model = False
    for f in os.listdir(options.model_dir):
        path = os.path.join(options.model_dir, f)
        if os.path.isfile(path) and path.endswith(model_extension):
            found_model = True
            break

    if not found_model:
        print(
            f'Error: model directory must contain at least one model file with extension {model_extension}.  Found:'
        )
        for f in os.listdir(options.model_dir):
            print(f'    {f}')
        sys.exit(1)

    register_with_robot(options)

    # Start Tensorflow processes
    start_tensorflow_processes(options, model_extension)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    network_compute_bridge_service_pb2_grpc.add_NetworkComputeBridgeWorkerServicer_to_server(
        NetworkComputeBridgeWorkerServicer(REQUEST_QUEUE, RESPONSE_QUEUE), server)
    server.add_insecure_port(f'[::]:{options.port}')
    server.start()

    print('Running...')
    while True:
        print('.', end='')
        sys.stdout.flush()
        time.sleep(2)

    return True


if __name__ == '__main__':
    logging.basicConfig()
    if not main(sys.argv[1:]):
        sys.exit(1)
