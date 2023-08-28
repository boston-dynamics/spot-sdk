<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Network Compute Bridge

The network compute bridge allows you to off-load computation to another computer on the network. For example, you might want to offload a deep neural-network call to a server in the cloud.

Examples:

- `tensorflow_server.py`: Processes requests to run a Faster R-CNN TensorFlow model on Spot image data.

  - Registers a Network Compute Bridge Worker with the Spot directory service
  - Handles Network Compute queries and executes the TensorFlow model on the image or image source input
  - Can be easily reconfigured to run other TensorFlow object detection models

- `identify_object.py`: Requests identification on an image using a TensorFlow model.

  - Client requests an image source, such as `frontleft_fisheye_image`
  - Robot takes image, rotates it to align with the horizon and sends it to a server running `tensorflow_server.py`.
  - Results are returned to the client. If depth data is available inside the bounding box, the robot adds depth to the result.

- [Fire Extinguisher Server](./fire_extinguisher_server/README.md): Example of a network compute bridge server for detecting fire extinguishers that uses Keras Retinanet instead of TensorFlow.

- `simple_alert_server.py`: Registers a Network Compute Bridge alert-generating worker server and triggers a Data Acquisition request to generate captures with the alert.

## System Diagram

![System Diagram](../../../docs/concepts/network_compute_bridge_diagram.png)

## Installation

### Server

These examples require the bosdyn API and client to be installed, and must be run using python3.

The `tensorflow_server.py` example requires TensorFlow to be installed. You can install its
dependencies via:

```
python3 -m pip install -r requirements_server.txt
```

TensorFlow can use the GPU for better performance but installation of NVIDIA drivers and CUDA is outside the scope of the document. There are many tutorials available such as [this one](https://www.pyimagesearch.com/2019/01/30/ubuntu-18-04-install-tensorflow-and-keras-for-deep-learning/).

### Client

The client example (`identify_object.py`) does not require TensorFlow:

```
python3 -m pip install -r requirements_client.txt
```

## Execution

To run this example, first launch the server and direct it to your Spot:

```
python3 tensorflow_server.py -d <MODEL DIRECTORY> <ROBOT ADDRESS>
```

- `USERNAME` and `PASSWORD` are your user credentials for your Spot.
- `MODEL DIRECTORY` is the path to the directory containing the TensorFlow model to be hosted.
- `ROBOT ADDRESS` is the IP address or hostname of your Spot.

An example model directory can be obtained here: `https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/tf1_detection_zoo.md`. As an example, use the `frozen_inference_graph.pb` file from the `faster_rcnn_inception_v2_coco` model to detect people in the camera images.

To associate numeric labels with names, the user may optionally provide a CSV file in the model directory with a matching file name, e.g. `frozen_inference_graph.csv`, with the following format:

```
apples,1
oranges,2
```

Where `1` and `2` are possible label outputs for detections from the TensorFlow model and `apples` and `oranges` are their respective semantic names. The `tensorflow_server.py` example output indicates if a CSV has been loaded to associate label values with names.

An example CSV file for the Faster R-CNN model described above is included in this directory as `frozen_inference_graph.csv`.

After launching `tensorflow_server.py`, the user may post requests to it using the `identify_object.py` client example. To run this example with the above example server and model, run:

```
python3 identify_object.py --service <SERVICE_NAME>  --model <MODEL_NAME> <ROBOT_IP>

For example:

python3 identify_object.py --service tensorflow-server --confidence 0.5 --model frozen_inference_graph --image-source frontleft_fisheye_image <ROBOT_IP>
```

Note, the `USERNAME` and `PASSWORD` are your user credentials for your Spot.

## Simple Alert Server Execution

To run the `simple_alert_server.py` example:

```
python3 simple_alert_server.py <ROBOT ADDRESS>
```

Optionally, pass `-p <PORT>` to the command above to specify the port used by the server. This command generates a zip file with the captures from an acquisition request. The zip file contains two copies of an image captured from the robot back camera, and a `metadata.json` file that contains `alert_data`:`simple-alert-server_alert_model_alert_output` key with the alert values.

## Robot-independent Execution

To run this example without a robot in the pipeline, first launch the server with the "-r" flag:

```
python3 tensorflow_server.py -r -d <MODEL DIRECTORY>
```

After launching `tensorflow_server.py`, the user may post requests to it using the `identify_object_without_robot.py` client example. To run this example with the above example server and model, run:

```
python3 identify_object_without_robot.py --model <MODEL_NAME> --server <SERVER_IP:PORT> --confidence 0.5 --model frozen_inference_graph

For example:

python3 identify_object_without_robot.py --server localhost:50051 --confidence 0.5 --model frozen_inference_graph --input-image-dir ~/Download/images/ -v
```

Example output:

```
    Got 2 objects.
    name: "obj1_label_person"
    image_properties {
        coordinates {
        vertexes {
            x: 1146.0
            y: 27.0
        }
    --- cut ---
```

## Docker Execution

This example contains the configuration files to run the python scripts described above also in Docker containers. The docker containers accept the same arguments described above. For example, to run the server docker container and the client docker container, follow the steps below with the correct values for the <> variables:

```
sudo docker build -t ncb_server -f Dockerfile.server .
sudo docker run -it --network=host --env BOSDYN_CLIENT_USERNAME --env BOSDYN_CLIENT_PASSWORD -v <MODEL_DIRECTORY>:/model_dir/ ncb_server --model-dir /model_dir/ <ROBOT_IP>


sudo docker build -t ncb_client -f Dockerfile.client .
sudo docker run -it --network=host --env BOSDYN_CLIENT_USERNAME --env BOSDYN_CLIENT_PASSWORD ncb_client --service tensorflow-server --confidence 0.5 --model frozen_inference_graph --image-source frontleft_fisheye_image <ROBOT_IP>
```

When running `ncb_server` on CORE I/O, or another compute payload with GPU, pass the flag `--gpus all` to the `docker run` command to take advantage of the GPU.

## Troubleshooting

- Ensure that your firewall is allowing traffic on the specified port (default: 50051).
