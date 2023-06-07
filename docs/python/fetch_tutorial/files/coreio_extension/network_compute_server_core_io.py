# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import io
import os
import sys
import time
import logging

import cv2
from PIL import Image
import numpy as np

from bosdyn.api import network_compute_bridge_service_pb2_grpc
from bosdyn.api import network_compute_bridge_pb2
from bosdyn.api import image_pb2
from bosdyn.api import header_pb2
import bosdyn.client
import bosdyn.client.util
import grpc
from concurrent import futures
import tensorflow as tf

import queue
import threading
from google.protobuf import wrappers_pb2
from object_detection.utils import label_map_util

kServiceAuthority = "fetch-tutorial-worker.spot.robot"


class TensorFlowObjectDetectionModel:
    def __init__(self, model_path, label_path):
        self.detect_fn = tf.saved_model.load(model_path)
        self.category_index = label_map_util.create_category_index_from_labelmap(label_path, use_display_name=True)
        self.name = os.path.basename(os.path.dirname(model_path))

    def predict(self, image):
        input_tensor = tf.convert_to_tensor(image)
        input_tensor = input_tensor[tf.newaxis, ...]
        detections = self.detect_fn(input_tensor)

        return detections

def process_thread(args, request_queue, response_queue):
    # Load the model(s)
    models = {}
    for model in args.model:
        this_model = TensorFlowObjectDetectionModel(model[0], model[1])
        models[this_model.name] = this_model

    print('')
    print('Service ' + args.name + ' running on port: ' + str(args.port))

    print('Loaded models:')
    for model_name in models:
        print('    ' + model_name)

    while True:
        request = request_queue.get()

        if isinstance(request, network_compute_bridge_pb2.ListAvailableModelsRequest):
            out_proto = network_compute_bridge_pb2.ListAvailableModelsResponse()
            for model_name in models:
                out_proto.models.data.append(network_compute_bridge_pb2.ModelData(model_name=model_name))
            response_queue.put(out_proto)
            continue
        else:
            out_proto = network_compute_bridge_pb2.NetworkComputeResponse()

        # Find the model
        if request.input_data.model_name not in models:
            err_str = 'Cannot find model "' + request.input_data.model_name + '" in loaded models.'
            print(err_str)

             # Set the error in the header.
            out_proto.header.error.code = header_pb2.CommonError.CODE_INVALID_REQUEST
            out_proto.header.error.message = err_str
            response_queue.put(out_proto)
            continue

        model = models[request.input_data.model_name]

        # Unpack the incoming image.
        if request.input_data.image.format == image_pb2.Image.FORMAT_RAW:
            pil_image = Image.open(io.BytesIO(request.input_data.image.data))
            if request.input_data.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8:
                # If the input image is grayscale, convert it to RGB.
                image = cv2.cvtColor(pil_image, cv2.COLOR_GRAY2RGB)

            elif request.input_data.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_RGB_U8:
                # Already an RGB image.
                image = pil_image

            else:
                print('Error: image input in unsupported pixel format: ', request.input_data.image.pixel_format)
                response_queue.put(out_proto)
                continue

        elif request.input_data.image.format == image_pb2.Image.FORMAT_JPEG:
            dtype = np.uint8
            jpg = np.frombuffer(request.input_data.image.data, dtype=dtype)
            image = cv2.imdecode(jpg, -1)

            if len(image.shape) < 3:
                # If the input image is grayscale, convert it to RGB.
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

        image_width = image.shape[0]
        image_height = image.shape[1]

        detections = model.predict(image)

        num_objects = 0

        # All outputs are batches of tensors.
        # Convert to numpy arrays, and take index [0] to remove the batch dimension.
        # We're only interested in the first num_detections.
        num_detections = int(detections.pop('num_detections'))
        detections = {key: value[0, :num_detections].numpy()
                       for key, value in detections.items()}

        boxes = detections['detection_boxes']
        classes = detections['detection_classes']
        scores = detections['detection_scores']


        for i in range(boxes.shape[0]):
            if scores[i] < request.input_data.min_confidence:
                continue

            box = tuple(boxes[i].tolist())

            # Boxes come in with normalized coordinates.  Convert to pixel values.
            box = [box[0] * image_width, box[1] * image_height, box[2] * image_width, box[3] * image_height]

            score = scores[i]

            if classes[i] in model.category_index.keys():
                label = model.category_index[classes[i]]['name']
            else:
                label = 'N/A'

            num_objects += 1

            print('Found object with label: "' + label + '" and score: ' + str(score))


            point1 = np.array([box[1], box[0]])
            point2 = np.array([box[3], box[0]])
            point3 = np.array([box[3], box[2]])
            point4 = np.array([box[1], box[2]])

            # Add data to the output proto.
            out_obj = out_proto.object_in_image.add()
            out_obj.name = "obj" + str(num_objects) + "_label_" + label

            vertex1 = out_obj.image_properties.coordinates.vertexes.add()
            vertex1.x = point1[0]
            vertex1.y = point1[1]

            vertex2 = out_obj.image_properties.coordinates.vertexes.add()
            vertex2.x = point2[0]
            vertex2.y = point2[1]

            vertex3 = out_obj.image_properties.coordinates.vertexes.add()
            vertex3.x = point3[0]
            vertex3.y = point3[1]

            vertex4 = out_obj.image_properties.coordinates.vertexes.add()
            vertex4.x = point4[0]
            vertex4.y = point4[1]

            # Pack the confidence value.
            confidence = wrappers_pb2.FloatValue(value=score)
            out_obj.additional_properties.Pack(confidence)

            if not args.no_debug:
                polygon = np.array([point1, point2, point3, point4], np.int32)
                polygon = polygon.reshape((-1, 1, 2))
                cv2.polylines(image, [polygon], True, (0, 255, 0), 2)

                caption = "{}: {:.3f}".format(label, score)
                left_x = min(point1[0], min(point2[0], min(point3[0], point4[0])))
                top_y = min(point1[1], min(point2[1], min(point3[1], point4[1])))
                cv2.putText(image, caption, (int(left_x), int(top_y)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 255, 0), 2)

        print('Found ' + str(num_objects) + ' object(s)')

        if not args.no_debug:
            debug_image_filename = 'network_compute_server_output.jpg'
            cv2.imwrite(debug_image_filename, image)
            print('Wrote debug image output to: "' + debug_image_filename + '"')

        response_queue.put(out_proto)


class NetworkComputeBridgeWorkerServicer(
        network_compute_bridge_service_pb2_grpc.NetworkComputeBridgeWorkerServicer):

    def __init__(self, thread_input_queue, thread_output_queue):
        super(NetworkComputeBridgeWorkerServicer, self).__init__()

        self.thread_input_queue = thread_input_queue
        self.thread_output_queue = thread_output_queue

    def NetworkCompute(self, request, context):
        print('Got NetworkCompute request')
        self.thread_input_queue.put(request)
        out_proto = self.thread_output_queue.get()
        return out_proto

    def ListAvailableModels(self, request, context):
        print('Got ListAvailableModels request')
        self.thread_input_queue.put(request)
        out_proto = self.thread_output_queue.get()
        return out_proto


def register_with_robot(options):
    """ Registers this worker with the robot's Directory."""
    ip = bosdyn.client.common.get_self_ip(options.hostname)
    print('Detected IP address as: ' + ip)

    sdk = bosdyn.client.create_standard_sdk("tensorflow_server")

    robot = sdk.create_robot(options.hostname)

    # Authenticate robot before being able to use it
    if options.payload_credentials_file:
        robot.authenticate_from_payload_credentials(
            *bosdyn.client.util.get_guid_and_secret(options))
    else:
        bosdyn.client.util.authenticate(robot)

    directory_client = robot.ensure_client(
        bosdyn.client.directory.DirectoryClient.default_service_name)
    directory_registration_client = robot.ensure_client(
        bosdyn.client.directory_registration.DirectoryRegistrationClient.default_service_name)

    # Check to see if a service is already registered with our name
    services = directory_client.list()
    for s in services:
        if s.name == options.name:
            print("WARNING: existing service with name, \"" + options.name + "\", removing it.")
            directory_registration_client.unregister(options.name)
            break

    # Register service
    print('Attempting to register ' + ip + ':' + options.port + ' onto ' + options.hostname + ' directory...')
    directory_registration_client.register(options.name, "bosdyn.api.NetworkComputeBridgeWorker", kServiceAuthority, ip, int(options.port))



def main(argv):
    default_port = '50051'

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--model', help='[MODEL_DIR] [LABELS_FILE.pbtxt]: Path to a model\'s directory and path to its labels .pbtxt file', action='append', nargs=2, required=True)
    parser.add_argument('-p', '--port', help='Server\'s port number, default: ' + default_port,
                        default=default_port)
    parser.add_argument('-d', '--no-debug', help='Disable writing debug images.', action='store_true')
    parser.add_argument('-n', '--name', help='Service name', default='fetch-server')
    bosdyn.client.util.add_payload_credentials_arguments(parser, required=False)
    bosdyn.client.util.add_base_arguments(parser)

    options = parser.parse_args(argv)

    print(options.model)

    for model in options.model:
        if not os.path.isdir(model[0]):
            print('Error: model directory (' + model[0] + ') not found or is not a directory.')
            sys.exit(1)

    # Perform registration.
    register_with_robot(options)

    # Thread-safe queues for communication between the GRPC endpoint and the ML thread.
    request_queue = queue.Queue()
    response_queue = queue.Queue()

    # Start server thread
    thread = threading.Thread(target=process_thread, args=([options, request_queue, response_queue]))
    thread.start()

    # Set up GRPC endpoint
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    network_compute_bridge_service_pb2_grpc.add_NetworkComputeBridgeWorkerServicer_to_server(
        NetworkComputeBridgeWorkerServicer(request_queue, response_queue), server)
    server.add_insecure_port('[::]:' + options.port)
    server.start()

    print('Running...')
    thread.join()

    return True

if __name__ == '__main__':
    logging.basicConfig()
    if not main(sys.argv[1:]):
        sys.exit(1)
