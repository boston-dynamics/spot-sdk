# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the Boston Dynamics API NetworkComputeBridgeWorkerServicer"""
import argparse
import io
import logging
import os
import sys
import threading
import time
from concurrent import futures
from multiprocessing import Queue
from timeit import default_timer as timer

import cv2
import grpc
import numpy as np
import tensorflow as tf
from google.protobuf import wrappers_pb2
from keras_retinanet import models
# import the necessary packages for ML
from keras_retinanet.utils.image import preprocess_image, resize_image
from PIL import Image
from scipy import ndimage

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import (image_pb2, network_compute_bridge_pb2,
                        network_compute_bridge_service_pb2_grpc, service_customization_pb2)
from bosdyn.client.directory import DirectoryClient, NonexistentServiceError
from bosdyn.client.directory_registration import (DirectoryRegistrationClient,
                                                  DirectoryRegistrationKeepAlive,
                                                  ServiceAlreadyExistsError)
from bosdyn.client.payload_registration import PayloadRegistrationClient

CONFIDENCE_KEY = "min_confidence"


class Resnet50Model:
    """ Simple class that allows us to load more than one tensorflow model at once. """

    @staticmethod
    def loadmodel(path):
        return models.load_model(path, backbone_name='resnet50')

    def __init__(self, path, labels_path):
        self.path = path
        self.model = self.loadmodel(path)

        # Make sure we tell tensor flow that this is a different model.
        self.graph = tf.compat.v1.get_default_graph()

        # Load the class label mappings
        if labels_path is None:
            self.labels = None
        else:
            # Load the class label mappings
            self.labels = open(labels_path).read().strip().split('\n')
            self.labels = {int(L.split(',')[1]): L.split(',')[0] for L in self.labels}

    def predict(self, X):
        """ Predict with this model. """
        return self.model.predict(X)


class KerasExec():
    """ Thread that waits for data and runs the Keras model. """

    def __init__(self, options, model_extension):
        # This is a multiprocessing.Queue for communication between the main process and the
        # Tensorflow processes.
        self.in_queue = Queue()
        # This is a multiprocessing.Queue for communication between the Tensorflow processes and
        # the display process.
        self.out_queue = Queue()

        self.options = options
        self.model_extension = model_extension

    def run(self):
        run_models = {}
        for f in os.listdir(self.options.model_dir):
            if f in run_models:
                print(f'Warning: duplicate model name of "{f}", ignoring second model.')
                continue

            path = os.path.join(self.options.model_dir, f)
            if os.path.isfile(path) and path.endswith(self.model_extension):
                model_name = ''.join(f.rsplit(self.model_extension, 1))  # remove the extension

                # reverse replace the extension
                labels_file = '.csv'.join(f.rsplit(self.model_extension, 1))
                labels_path = os.path.join(self.options.model_dir, labels_file)

                if not os.path.isfile(labels_path):
                    labels_path = None
                run_models[model_name] = (Resnet50Model(path, labels_path))

        # Tensorflow prints out a bunch of stuff, so print out useful data here after a space.
        print('')
        print(f'Running on port: {self.options.port}')
        print('Loaded run_models:')
        for model_name in run_models:
            if run_models[model_name].labels is not None:
                labels_str = 'yes'
            else:
                labels_str = 'no'
            print(f'    {model_name} (loaded labels: {labels_str})')

        param_spec = create_custom_param_spec()
        while True:
            request = self.in_queue.get()

            if isinstance(request, network_compute_bridge_pb2.ListAvailableModelsRequest):
                out_proto = network_compute_bridge_pb2.ListAvailableModelsResponse()
                for model_name in run_models:
                    out_proto.models.data.append(
                        network_compute_bridge_pb2.ModelData(model_name=model_name,
                                                             custom_params=param_spec))
                    # To show available labels
                    #if run_models[model_name].labels is not None:
                    #    labels_msg = out_proto.labels.add()
                    #    labels_msg.model_name = model_name
                    #    for n in run_models[model_name].labels:
                    #        labels_msg.available_labels.append(run_models[model_name].labels[n])
                out_proto.status = network_compute_bridge_pb2.ListAvailableModelsStatus.LIST_AVAILABLE_MODELS_STATUS_SUCCESS
                self.out_queue.put(out_proto)
                continue
            else:
                out_proto = network_compute_bridge_pb2.NetworkComputeResponse()

            # Find the model
            if request.input_data.parameters.model_name not in run_models:
                print(
                    f'Cannot find model "{request.input_data.parameters.model_name}" in loaded run_models.'
                )
                self.out_queue.put(out_proto)
                continue

            # Got a request, run the model.
            self.run_model(request, run_models[request.input_data.parameters.model_name])

    def run_model(self, request, this_model):

        # Define the out proto
        out_proto = network_compute_bridge_pb2.WorkerComputeResponse()
        num_images = len(request.input_data.images)
        if num_images == 0:
            print("Error, worker needs one input image.")
            self.out_queue.put(out_proto)
            return
        if num_images > 1:
            print("Warning, worker accepts only one image, using first.")

        if request.input_data.images[0].shot.image.format == image_pb2.Image.FORMAT_RAW:
            pil_image = Image.open(io.BytesIO(request.input_data.images[0].shot.image.data))
            pil_image = ndimage.rotate(pil_image, 0)
            if request.input_data.images[
                    0].shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_GREYSCALE_U8:
                image = cv2.cvtColor(pil_image,
                                     cv2.COLOR_GRAY2RGB)  # Converted to RGB for Tensorflow
            elif request.input_data.images[
                    0].shot.image.pixel_format == image_pb2.Image.PIXEL_FORMAT_RGB_U8:
                # Already in the correct format
                image = pil_image
            else:
                print(
                    f'Error: image input in unsupported pixel format: {request.input_data.image.pixel_format}'
                )
                self.out_queue.put(out_proto)
                return
        elif request.input_data.images[0].shot.image.format == image_pb2.Image.FORMAT_JPEG:
            dtype = np.uint8
            jpg = np.frombuffer(request.input_data.images[0].shot.image.data, dtype=dtype)
            image = cv2.imdecode(jpg, -1)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            if len(image.shape) < 3:
                # Single channel image, convert to RGB.
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            print("Error, Image format is unsupported")
            self.out_queue.put(out_proto)
            return

        print('')
        print('Starting model eval...')
        # Run the model on the image
        keras_image = preprocess_image(image)
        (keras_image, scale) = resize_image(keras_image)
        keras_image = np.expand_dims(keras_image, axis=0)
        start = timer()
        boxes, scores, classes = this_model.predict(keras_image)
        end = timer()
        print(f'Model eval took {end - start} seconds')

        boxes /= scale

        # Package detections into the output proto
        num_objects = 0
        boxes = boxes[0]
        scores = scores[0]
        classes = classes[0]

        output = out_proto.output_images.get_or_create("detections")
        out_image = output.image_response
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 100]
        for i in range(len(boxes)):
            # Skip if not the Fire Extinguisher class
            if classes[i] != 7:
                continue

            label = this_model.labels[(classes[i])]
            box = boxes[i]
            score = scores[i]

            if score < request.input_data.parameters.custom_params.values[
                    CONFIDENCE_KEY].double_value.value:
                # scores are sorted so we can break
                break

            num_objects += 1

            print(f'Found object with label: "{label}" and score: {score}')
            print(f'Box is {box}')

            point1 = np.array([box[0], box[1]])
            point2 = np.array([box[0], box[3]])
            point3 = np.array([box[2], box[3]])
            point4 = np.array([box[2], box[1]])

            # Add data to the output proto.
            out_obj = output.object_in_image.add()
            out_obj.name = label

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

            polygon = np.array([point1, point2, point3, point4], np.int32)
            polygon = polygon.reshape((-1, 1, 2))
            cv2.polylines(image, [polygon], True, (0, 255, 0), 2)

            caption = f'{label}: {score:.3f}'
            left_x = min(point1[0], min(point2[0], min(point3[0], point4[0])))
            top_y = min(point1[1], min(point2[1], min(point3[1], point4[1])))
            cv2.putText(image, caption, (int(left_x), int(top_y)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 0), 2)

        print(f'Found {num_objects} object(s)')

        out_image.shot.image.data = cv2.imencode('.jpg', cv2.cvtColor(image, cv2.COLOR_RGB2BGR),
                                                 encode_param)[1].tobytes()
        out_image.shot.image.rows = image.shape[0]
        out_image.shot.image.cols = image.shape[1]
        out_image.shot.image.format = image_pb2.Image.FORMAT_JPEG
        out_image.shot.image.pixel_format = image_pb2.Image.PIXEL_FORMAT_RGB_U8

        # Pack all the outputs up and send them back.
        self.out_queue.put(out_proto)


class NetworkComputeBridgeWorkerServicer(
        network_compute_bridge_service_pb2_grpc.NetworkComputeBridgeWorkerServicer):
    """ Class that handles the incoming GRPC messages and dispatches them to a thread that
        services them.  Running directly in this callback doesn't work. """

    def __init__(self, thread_input_queue, thread_output_queue):
        super(NetworkComputeBridgeWorkerServicer, self).__init__()
        # Threading input and output queues.
        self.thread_input_queue = thread_input_queue
        self.thread_output_queue = thread_output_queue

    def WorkerCompute(self, request, context):
        # Transfer the request to the thread.
        self.thread_input_queue.put(request)
        # Blocking call, waiting for the thread to respond.
        out_proto = self.thread_output_queue.get()
        # Returning the proto will send it out over GRPC.
        return out_proto

    def ListAvailableModels(self, request, context):
        self.thread_input_queue.put(request)
        out_proto = self.thread_output_queue.get()
        return out_proto


def create_custom_param_spec():
    """Creates the custom parameter specification for the NCB worker.
    """
    param_spec = service_customization_pb2.DictParam.Spec()

    # Create double param to specify minimum confidence to return an object.
    double_dict_childspec = param_spec.specs.get_or_create(CONFIDENCE_KEY)
    double_dict_childspec.ui_info.display_name = "Min_Confidence"
    double_dict_childspec.ui_info.description = "Minimum confidence to return a detection."
    double_spec = double_dict_childspec.spec.double_spec
    double_spec.default_value.value = 0.4
    double_spec.min_value.value = 0
    double_spec.max_value.value = 1
    return param_spec


def register_with_robot(options):
    """ Registers this worker with the robot's Directory."""
    ip = bosdyn.client.common.get_self_ip(options.hostname)
    print(f'Detected IP address as: {ip}')
    kServiceName = 'fire-extinguisher-server'
    kServiceTypeName = 'bosdyn.api.NetworkComputeBridgeWorker'
    kServiceAuthority = 'fire-extinguisher-worker.spot.robot'

    sdk = bosdyn.client.create_standard_sdk('retinanet-server')

    robot = sdk.create_robot(options.hostname)

    # Authenticate robot before being able to use it
    if options.guid or options.secret or options.payload_credentials_file:
        robot.authenticate_from_payload_credentials(
            *bosdyn.client.util.get_guid_and_secret(options))
    else:
        bosdyn.client.util.authenticate(robot)

    directory_client = robot.ensure_client(DirectoryClient.default_service_name)
    directory_registration_client = robot.ensure_client(
        bosdyn.client.directory_registration.DirectoryRegistrationClient.default_service_name)

    # Create a keep_alive to reset and maintain registration of service.
    keep_alive = DirectoryRegistrationKeepAlive(directory_registration_client)
    keep_alive.start(kServiceName, kServiceTypeName, kServiceAuthority, ip, int(options.port))

    # List all services. Success if above test service is shown.
    try:
        registered_service = directory_client.get_entry(kServiceName)
    except NonexistentServiceError as exc:
        print(f'\nSelf-registered service not found. Failure: {exc}')
        return False

    print('\nService registration confirmed. Self-registration was a success.')
    return True


def main():
    """
    Command line interface.
    """

    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()

    default_port = '50051'
    model_extension = '.h5'

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--model-dir', help=
        'Directory of pre-trained models and (optionally) associated label files.\nExample directory contents: my_model.pb, my_classes.csv, my_model2.pb, my_classes2.csv.  CSV label format is: object,1<new line>thing,2',
        required=True)
    parser.add_argument('-p', '--port', help=f'Server\'s port number, default: {default_port}',
                        default=default_port)
    parser.add_argument(
        '-r', '--no-registration', help=
        'Don\'t register with the robot\'s directory. This is useful for cloud applications where we can\'t reach into every robot directly. Instead use another program to register this server.',
        action='store_true')
    bosdyn.client.util.add_payload_credentials_arguments(parser, required=False)
    parser.add_argument('hostname', nargs='?', help='Hostname or address of robot,'
                        ' e.g. "beta25-p" or "192.168.80.3"')
    options = parser.parse_args()

    # Either we need a hostname to talk to the robot or the --no-registration argument.
    if not options.no_registration and (options.hostname is None or len(options.hostname) < 1):
        print('Error: must either provide a robot hostname or the --no-registration argument.')
        sys.exit(1)

    if options.no_registration and (options.hostname is not None and len(options.hostname) > 0):
        print('Error: cannot provide both a robot hostname and the --no-registration argument.')
        sys.exit(1)

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

    if not options.no_registration:
        register_with_robot(options)

    # Limit memory allocation so this program does not allocate 7GB of memory on CORE I/O.
    gpu_options = tf.compat.v1.GPUOptions(allow_growth=True)
    sess = tf.compat.v1.Session(config=tf.compat.v1.ConfigProto(gpu_options=gpu_options))
    tf.compat.v1.keras.backend.set_session(sess)

    # Start the model eval thread.
    keras_exec = KerasExec(options, model_extension)
    model_thread = threading.Thread(target=keras_exec.run)
    print('Starting Model Thread')
    model_thread.start()

    # Start the GRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    network_compute_bridge_service_pb2_grpc.add_NetworkComputeBridgeWorkerServicer_to_server(
        NetworkComputeBridgeWorkerServicer(keras_exec.in_queue, keras_exec.out_queue), server)
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
    if not main():
        sys.exit(1)
