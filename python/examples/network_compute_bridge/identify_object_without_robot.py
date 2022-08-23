# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import multiprocessing as mp
import os
import sys
import time

import cv2
import grpc
import numpy as np
from google.protobuf import wrappers_pb2

from bosdyn.api import (image_pb2, network_compute_bridge_pb2, network_compute_bridge_service_pb2,
                        network_compute_bridge_service_pb2_grpc)


def append_str_to_filename(filename, string):
    return "{0}_{2}{1}".format(*os.path.splitext(filename) + (string,))


def _send_request(server, image_path, model, confidence, verbose=False):
    start = time.time()

    channel = grpc.insecure_channel(server)
    stub = network_compute_bridge_service_pb2_grpc.NetworkComputeBridgeWorkerStub(channel)
    server_data = network_compute_bridge_pb2.NetworkComputeServerConfiguration(service_name='test')
    # Read the input image.
    image_in = cv2.imread(image_path)
    if image_in is None:
        print('Error: failed to read "' + image_path + '".  Does the file exist?')
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

    input_data = network_compute_bridge_pb2.NetworkComputeInputData(image=image_proto,
                                                                    model_name=model,
                                                                    min_confidence=confidence)

    process_img_req = network_compute_bridge_pb2.NetworkComputeRequest(
        input_data=input_data, server_config=server_data)

    response = stub.NetworkCompute(process_img_req)
    end = time.time()
    latency = end - start
    print(f'latency: {latency * 1000} ms')

    if verbose:
        if len(response.object_in_image) <= 0:
            print('No objects found')
        else:
            print('Got ' + str(len(response.object_in_image)) + ' objects.')

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
                polygon.append([v.x, v.y])
                min_x = min(min_x, v.x)
                min_y = min(min_y, v.y)

            polygon = np.array(polygon, np.int32)
            polygon = polygon.reshape((-1, 1, 2))
            cv2.polylines(image_in, [polygon], True, (0, 255, 0), 2)

            caption = "{} {:.3f}".format(obj.name, confidence)
            cv2.putText(image_in, caption, (int(min_x), int(min_y)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 0), 2)

        cv2.imwrite(append_str_to_filename(image_path, 'detections'), image_in)
    return latency


def main(argv):
    """An example using the API to list and get specific objects."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', help='IP address of external machine learning server.',
                        required=True)
    parser.add_argument('-m', '--model', help='Model file on the server', default='coco_inference')
    parser.add_argument('-c', '--confidence', help='Minimum confidence to return an object.',
                        default=0.7, type=float)
    parser.add_argument('-j', '--input-image-dir', help='Path to a directory of images.')
    parser.add_argument('-n', '--num-runs', help='Number of runs of the image directory to perform',
                        default=1, type=int)
    parser.add_argument('-l', '--model-list', help='List of models to be used.',
                        action='store_true')
    parser.add_argument('-v', '--verbose', help='Print verbose output', action='store_true')
    options = parser.parse_args(argv)

    if options.input_image_dir is None and not options.model_list:
        print('Error: must provide an input image.')
        sys.exit(1)

    if options.model_list and options.input_image_dir is not None:
        print('Error: cannot list models with input image.')
        sys.exit(1)

    if options.model_list:
        channel = grpc.insecure_channel(options.server)
        stub = network_compute_bridge_service_pb2_grpc.NetworkComputeBridgeWorkerStub(channel)
        server_data = network_compute_bridge_pb2.NetworkComputeServerConfiguration(
            service_name='test')
        list_req = network_compute_bridge_pb2.ListAvailableModelsRequest(server_config=server_data)
        response = stub.ListAvailableModels(list_req)

        print('Available models on server at ' + options.server + ' are:')
        for model in response.available_models:
            print('    ' + model)
        sys.exit(0)

    image_paths = []
    for entry in os.scandir(options.input_image_dir):
        if (entry.path.endswith(".jpg") or entry.path.endswith(".png")) and entry.is_file():
            image_paths.append(entry.path)

    image_paths = image_paths * options.num_runs

    start_time = time.perf_counter()
    with mp.Pool() as p:
        latencies = p.starmap(
            _send_request,
            [(options.server, path, options.model, options.confidence, options.verbose)
             for path in image_paths])
        latency_sum = sum(latencies)
        count = len(latencies)

    end_time = time.perf_counter()
    total_time = end_time - start_time
    print(f'Total time: {total_time} seconds.')
    avg_latency = latency_sum / count
    print(f'avg latency: {avg_latency * 1000} ms, fps: {count / total_time} fps')


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
