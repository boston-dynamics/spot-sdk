<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Machine Learning Bridge and External Compute

Spot provides capabilities to perform **computation off-board** and easily integrate it into your API programs.  For example, you might want to run a deep-learning-based bounding box detector to identify a ball that you want to command the robot to pick up.

The `network_compute_bridge` API can help you by coordinating the networking between various components and adding pre- and post-processing to your image calls, capturing and rotating images for you as needed.  The tablet application has a built-in capability to view the output of bounding-box detectors online while driving (`Menu > Utilities > ML Model Viewer`).

## Example Concept

You have trained a model to detect tennis balls.  You want to build a script to walk to every tennis ball in an area.  Because your tennis ball detector is computationally expensive, you decide to have a big server running on the same WiFi network as Spot to do the computation.

Here's how you might set that up:

1. Large server is running in a server room, on the same WiFi network as Spot.
2. Your client laptop has a script that queries the `Network Compute Bridge` to:
    - capture an image
    - run the tennis ball detector on that image
    - return results to the script
3. With the results, your script commands the robot to walk to a tennis ball.

## Components of the system

1. Spot robot
2. Server running computation
    - mounted on Spot or externally networked
3. Client computer
    - robot tablet
    - external computer
    - same computer as is running the server

![Network compute bridge diagram](network_compute_bridge_diagram.png)

## Discovering Servers and Models

- Computation servers register with Spot's [Directory](developing_api_services.md#robot-directory).
- Clients can use the directory to look up available servers (see: [listing services](../python/understanding_spot_programming.md#listing-services)).
- Servers should implement the `ListAvailableModels` RPC to inform clients of their available computation.


## Example Clients and Servers

Examples are found in the [network compute bridge examples](../../python/examples/network_compute_bridge/README.md) folder.

## Pre- and Post-Processing

If you are working with images, you can:

1. Ask the robot to capture an image
2. Send an already-captured image for computation


If you choose (1), you can optionally have the robot rotate the image to align the horizontal.  This is particularly useful for the robot's built-in cameras that are not all mounted horizontally.  Many ML detectors are biased towards horizontally-captured images, so this is a good way to improve your results.

If you use the rotation functions, the robot will:

1. Capture image
2. Rotate the image to the horizontal
3. Send to the external server
4. Receive the bounding-box results and un-rotate the boxes so they line up with the original image
5. Send you the original image with the corresponding bounding boxes.


### RPC Definitions: `NetworkComputeBridge` and `NetworkComputeBridgeWorker`

- `NetworkComputeBridge` is the API interface between your **API client** and the **robot**.
- `NetworkComputeBridgeWorker` is the API interface between the **robot** and a **compute server**



## Other Data

The API provides an `Any` field in the proto to allow you to pack arbitrary input and output data.  This field allows you to perform external computation on any data.  However, the tablet application will not be able to interpret this custom data.
