<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Spot Tensorflow Object Detection

The Spot Tensorflow Detector example collects images from the 5 Spot cameras and performs object
detection using Tensorflow. It accepts any Tensorflow model, and it allows the user to specify a
subset of detection classes included in the model. It performs this set of operations for a
predefined number of iterations, blocking for a predefined amount of time between each iteration.
The output of each iteration is a plot of the original 5 images collected from the cameras and
another set of those 5 images with boxes around the detections reported by the Tensorflow model.

The program is organized as three sets of Python processes communicating with the Spot robot. The
process diagram is shown below. The main process communicates with the Spot robot over GRPC and
constantly receives images.These images are pushed into the RAW_IMAGES_QUEUE and read by the
Tensorflow processes.Those processes detect objects in the images, draw the bounding boxes around
the detections, and push those processed images into the PROCESSED_IMAGES_QUEUE. The Display
process then pulls images from the PROCESSED_IMAGES_QUEUE and displays them to the screen.

<img src="documentation/process_diagram.png" alt="Process Diagram" style="width:250px;"/>

## User Guide

### Installation

For your best learning experience, please use the [Quickstart Guide](../../../docs/python/quickstart.md)
found in the SDK's docs/python directory. That will help you get your Python programming
environment setup properly.

To install this example on Ubuntu 18.04, follow these instructions:

- Create virtual environment as described in this
  [Quickstart Guide virtualenv section](../../../docs/python/quickstart.md#manage-multiple-python-environments)
- Install dependencies: `python3 -m pip install -r requirements.txt`
- Run the example using instructions in the next section
- To exit the virtual environment, run `deactivate`

### Execution

This example follows the common pattern for expected arguments. It needs the common arguments used to configure the SDK and connect to a Spot:

- hostname passed as the last argument
- username and password should be set in the environment variables `BOSDYN_CLIENT_USERNAME` and `BOSDYN_CLIENT_PASSWORD`.

On top of those arguments, it also needs the following arguments:

- --model-path (required) argument that specifies the path of the Tensorflow model (a file in .pb format)
- --detection-classes (optional) argument that specifies a comma-separated list of detection classes to use from the Tensorflow model; not specifying this argument means that all classes in the model will be detected
- --detection-threshold (optional) argument that specifies the threshold to use to consider the Tensorflow detections as real detections; defaults to 0.7
- --number-tensorflow-processes (optional) argument that specifies the number of Tensorflow processes to start; defaults to 7
- --sleep-between-capture (optional) argument that specifies the amount to sleep in seconds between each image capture iteration; defaults to 0.0
- --max-processing-delay (optional) argument that specifies max delay in seconds allowed for each image before being processed; images with greater latency will not be processed. Setting this to a larger value can help the model run faster.
- --max-display-delay (optional) argument that specifies max delay in seconds allowed for each image before being displayed; images with greater latency will not be displayed. Setting this to a larger value can help the model run faster.

```
python3 spot_tensorflow_detector.py --model-path <path_to_pb> ROBOT_IP
```

The program generates two sets of output:

- A set of 5 image windows with live images from the five cameras with boxes around the Tensorflow detections.
- A command line log in the format: `RAW_IMAGES_QUEUE PROCESSED_IMAGES_QUEUE Network_Delay Processing_Delay Display_Delay Total_Delay Display_Skips Processing_Skips`

The value of all those parameters is updated asynchronously. The parameters are: - RAW_IMAGES_QUEUE: The size of the queue holding raw images; main process adds raw images in this queue and the Tensorflow processes get images from this queue - PROCESSED_IMAGES_QUEUE: The size of the queue holding processes images; Tensorflow processes add processed images in this queue and the Display process gets images from this queue - Network_Delay: Delay in seconds between when the image is captured in the robot and the time it is received by this program - Processing_Delay: Amount of time in seconds it takes a Tensorflow processor to process the image - Display_Delay: Amount of time in seconds it takes to show the processed image - Total_Delay: Total delay in seconds between when the image is captured in the robot and the time it is shown on the screen - Display_Skips: Total number of images skipped from being displayed due to latency - Processing_Skips: Total number of images skipped from being processed in each Tensorflow process due to latency

The value for RAW_IMAGES_QUEUE increases rapidly in the beginning of the program, but it should decrease back to 0 in a few minutes. Based on the hardware where the program is running, increasing the value passed to the argument `--number-tensorflow-processes` reduces the size of this queue more quickly. Increasing the value of the argument `--sleep-between-capture` also reduces the size of this queue, but this option also reduces the real-time visualization of the environment around the Spot robot.

As an example, the `faster_rcnn_inception_v2_coco` Tensorflow model pre-trained on COCO dataset can be obtained [here](http://download.tensorflow.org/models/object_detection/faster_rcnn_inception_v2_coco_2018_01_28.tar.gz). Run the example with `--model-path` pointing to the `frozen_inference_graph.pb` file in that model and with `--detection-classes` argument set to `1` to detect people in the camera images. That model is not supported on Windows or MacOS.
