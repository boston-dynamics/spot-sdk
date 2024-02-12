# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Tutorial to show how to use the Boston Dynamics Network Compute API

This example starts a simple NCB server that returns a NetworkComputeResponse
with AlertData specified. It then calls into the DAQ to invoke the server and
write the response. Finally, this downloads the DAQ data.
"""

import argparse
import logging
import sys
import time
from concurrent import futures

import grpc
from google.protobuf.json_format import MessageToDict as _MessageToDict

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import (alerts_pb2, data_acquisition_pb2, image_pb2, network_compute_bridge_pb2,
                        network_compute_bridge_service_pb2_grpc)
from bosdyn.client.data_acquisition_helpers import (acquire_and_process_request, download_data_REST,
                                                    make_time_query_params)

kServiceName = 'simple-alert-server'
kServiceAuthority = 'simple-alert-worker.spot.robot'
kModelName = 'alert_model'


def MessageToDict(message):
    return _MessageToDict(message, including_default_value_fields=True,
                          preserving_proto_field_name=True)


class SimpleNetworkComputeBridgeWorkerServicer(
        network_compute_bridge_service_pb2_grpc.NetworkComputeBridgeWorkerServicer):

    def __init__(self):
        super(SimpleNetworkComputeBridgeWorkerServicer, self).__init__()

    def WorkerCompute(self, request, context):
        # Create a simple response including AlertData
        out_proto = network_compute_bridge_pb2.WorkerComputeResponse()
        out_img = out_proto.output_images.get_or_create("output")
        # Use the input image as the output image.
        out_img.image_response.shot.CopyFrom(request.input_data.images[0].shot)
        out_img.alert_data.CopyFrom(
            alerts_pb2.AlertData(title='NCB Test Alert',
                                 severity=alerts_pb2.AlertData.SEVERITY_LEVEL_ERROR,
                                 source=kServiceName))
        return out_proto

    def ListAvailableModels(self, request, context):
        # List our dummy model name
        out_proto = network_compute_bridge_pb2.ListAvailableModelsResponse()
        out_proto.models.data.append(network_compute_bridge_pb2.ModelData(model_name=kModelName))
        return out_proto


def register_with_robot(options):
    """ Registers this worker with the robot's Directory."""
    ip = bosdyn.client.common.get_self_ip(options.hostname)
    print(f'Detected IP address as: {ip}')

    sdk = bosdyn.client.create_standard_sdk('simple_alert_server')

    robot = sdk.create_robot(options.hostname)

    # Authenticate robot before being able to use it
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()

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
    print('Service registration complete')

    return robot


def main():
    """Command line interface."""

    default_port = '50051'

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', help=f'Server\'s port number, default: {default_port}',
                        default=default_port)
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()

    if options.hostname is None or len(options.hostname) < 1:
        print('Error: must provide a robot hostname.')
        sys.exit(1)

    robot = register_with_robot(options)

    # Start the server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    network_compute_bridge_service_pb2_grpc.add_NetworkComputeBridgeWorkerServicer_to_server(
        SimpleNetworkComputeBridgeWorkerServicer(), server)
    server.add_insecure_port(f'[::]:{options.port}')
    server.start()

    print('Waiting for capability to register in the system. This may take a few minutes ...')
    data_acq_client = robot.ensure_client(
        bosdyn.client.data_acquisition.DataAcquisitionClient.default_service_name)
    while True:
        print('.', end='')
        sys.stdout.flush()
        if kServiceName in [
                source.server_config.service_name
                for source in data_acq_client.get_service_info().network_compute_sources
        ]:
            break
        time.sleep(2)

    # Get the start time so we can download all data from this example.
    start_time_secs = time.time()
    now = robot.time_sync.robot_timestamp_from_local_secs(time.time())
    group_name = f'SimpleAlertServer_{now.ToJsonString().replace(":", "-")}'

    # Create acquisition request list with a network compute request.
    acquisition_requests = data_acquisition_pb2.AcquisitionRequestList()
    ncb_request = acquisition_requests.network_compute_captures.add()
    ncb_request.server_config.service_name = kServiceName
    ncb_request.input_data_bridge.parameters.model_name = kModelName
    ncb_request.input_data_bridge.image_sources_and_services.append(
        network_compute_bridge_pb2.ImageSourceAndService(image_service='image',
                                                         image_source='back_fisheye_image'))

    print('Sending acquire request')
    # Send the requests to the DAQ server
    acquire_and_process_request(data_acq_client, acquisition_requests, group_name, 'NCBCapture')

    # Get the end time, download all the data from the example, and save to ./REST.
    end_time_secs = time.time()
    query_params = make_time_query_params(start_time_secs, end_time_secs, robot)
    download_data_REST(query_params, options.hostname, robot.user_token, destination_folder='.')
    print('Full list of captures downloaded in zip file.')

    # List images and alert data stored in the DAQ from this call
    data_acq_store_client = robot.ensure_client(
        bosdyn.client.data_acquisition_store.DataAcquisitionStoreClient.default_service_name)
    images = data_acq_store_client.list_stored_images(query_params)

    for idx, image in enumerate(images):
        print(f'Stored image[{idx}]', MessageToDict(image))

    alerts = data_acq_store_client.list_stored_alertdata(query_params)

    for idx, alert in enumerate(alerts):
        print(f'Stored alert[{idx}]', MessageToDict(alert))

    return True


if __name__ == '__main__':
    logging.basicConfig()
    if not main():
        sys.exit(1)
