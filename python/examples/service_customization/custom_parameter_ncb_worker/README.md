<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Network Compute Bridge

The network compute bridge allows you to off-load computation to another computer on the network. For example, you might want to offload a deep neural-network call to a server in the cloud. This example is mostly a copy of the [Tensorflow Network Compute Bridge Example](../../network_compute_bridge/README.md). However in this example, clients can specify a region of interest and confidence value in the image recieved by the network compute bridge worker. The region of interest tells the model where to look for object matches. The confidence value tells the model the confidence threshold for an object match. There is no example client for the server. Please use the Spot app as the example client.

Examples:

- `tensorflow_server.py`: Processes requests to run a Faster R-CNN TensorFlow model on Spot image data.

  - Registers a Network Compute Bridge Worker with the Spot directory service
  - Handles Network Compute queries and executes the TensorFlow model on the image or image source input
  - Can be easily reconfigured to run other TensorFlow object detection models

## System Diagram

![System Diagram](../../../../docs/concepts/network_compute_bridge_diagram.png)

## Installation

This example require the bosdyn API and client to be installed, and must be run using python3.

The `tensorflow_server.py` example requires TensorFlow to be installed. You can install its
dependencies via:

```
For non-GPU installations:

python3 -m pip install -r requirements_server_cpu.txt

For CUDA / NVIDIA GPU installations:

python3 -m pip install -r requirements_server_gpu.txt
```

Installation of NVIDIA drivers and CUDA is outside the scope of the document. There are
many tutorials available such as [this one](https://www.pyimagesearch.com/2019/01/30/ubuntu-18-04-install-tensorflow-and-keras-for-deep-learning/).

## Execution

To run this example, first launch the server and direct it to your Spot:

```
python3 tensorflow_server.py -d <MODEL DIRECTORY> <ROBOT ADDRESS>
```

- `USERNAME` and `PASSWORD` are your user credentials for your Spot.
- `MODEL DIRECTORY` is the path to the directory containing the TensorFlow model to be hosted.
- `ROBOT ADDRESS` is the IP address or hostname of your Spot.

An example model directory can be obtained here: `https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/tf1_detection_zoo.md`. As an example, use the `frozen_inference_graph.pb` file from the `faster_rcnn_inception_v2_coco` model to detect people in the camera images.

To associate numeric labels with names, the user may optionally provide a CSV file in the model directory with a matching file name, e.g. frozen_inference_graph.csv, with the following format:

```
apples,1
oranges,2
```

Where `1` and `2` are possible label outputs for detections from the TensorFlow model and `apples` and `oranges` are their respective semantic names. The tensorflow_server.py example output indicates if a CSV has been loaded to associate label values with names.

An example CSV file for the Faster R-CNN model described above is included in this directory as `frozen_inference_graph.csv`.

## Docker Execution

This example contains the configuration files to run the python scripts described above also in Docker containers. The docker containers accept the same arguments described above. For example, to run the server docker container and the client docker container, follow the steps below with the correct values for the <> variables:

```
Create a .env file that specifies username and password with the following variables.
BOSDYN_CLIENT_USERNAME={username}
BOSDYN_CLIENT_PASSWORD={password}

sudo docker build -t ncb_server -f Dockerfile.server .
sudo docker run -it --network=host --env-file .env -v <MODEL_DIRECTORY>:/model_dir/ ncb_server --model-dir /model_dir/ <ROBOT_IP>
```

When running ncb_server on CORE I/O, or another compute payload with GPU, pass the flag `--gpus all` to the `docker run` command to take advantage of the GPU.

## Controling Custom Parameters in Spot App

There is no example client for the server. It is easiest to use the Spot app as the example client. To do so:

1. Connect the tablet to a robot that has the tensorflow server registered.
2. In Hamburger Menu > Settings > Actions, select the "Create New Action" at the bottom of the menu.
3. Start with an empty inspection.
4. Add the tensorflow network compute bridge worker.
5. Add "Robot Cameras - Right" as input image.
6. Save action.
7. Select red plus button on drive screen.
8. Select newly made action.
9. Aim camera.
10. Configure custom parameters. Press double arrow at bottom of screen to switch between input and output image view.

## Troubleshooting

- Ensure that your firewall is allowing traffic on the specified port (default: 50051).
