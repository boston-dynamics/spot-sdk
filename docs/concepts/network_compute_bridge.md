<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Machine Learning Bridge and External Compute

Spot provides capabilities to perform **computation off-board** and easily integrate it into your API programs. For example, you might want to run a deep-learning-based bounding box detector to identify a ball that you want to command the robot to pick up. The `Network Compute Bridge` functionality in the system can help you by coordinating the networking between various components and capturing images for you as needed. The tablet application has a built-in capability to view the output images from the detectors online.

## Components of the system

The diagram below shows the diagram of `Network Compute Bridge` functionality.

![Network compute bridge diagram](network_compute_bridge_diagram.png)

Users implement `Compute Server` applications as `NetworkComputeBridgeWorker` RPC services and register them with Spot's [Directory](developing_api_services.md#robot-directory). These workers can run on an onboard compute payload, such as the CORE I/O, or any server networked with the Spot system. The `NetworkComputeBridge` service running on the robot periodically checks for new workers and queries them for available model names through the `ListAvailableModels`. API clients, such as the tablet application or any application that uses the Spot SDK, communicate with the `NetworkComputeBridge` service on the robot through the `NetworkCompute` RPC to process any set of images with any available models in registered in the system.

## Example Concept

You have trained a model to detect tennis balls. You want to build a script to walk to every tennis ball in an area. Because your tennis ball detector is computationally expensive, you decide to have a big server running on the same WiFi network as Spot to do the computation.

Here is how you might set that up:

1. Large server is running in a server room, on the same WiFi network as Spot, or a compute payload attached to Spot, such as the CORE I/O.
2. Your client laptop has a script that calls the `Network Compute Bridge` service to:
   - capture an image
   - run the tennis ball detector on that image
   - return results to the script
3. With the results, your script commands the robot to walk to a tennis ball.

## Example Clients and Servers

Examples are found in the [network compute bridge examples](../../python/examples/network_compute_bridge/README.md) folder.

### RPC Definitions: `NetworkComputeBridge` and `NetworkComputeBridgeWorker`

- `NetworkComputeBridge` is the API interface between your **API client** and the **robot**.
- `NetworkComputeBridgeWorker` is the API interface between the **robot** and a **compute server**

External applications do not communicate directly with the worker services. They always communicate through the `NetworkComputeBridge` service and API interface.

The workers return any processed data through the `output_images` and `other_data` fields in `WorkerComputeResponse` message. Those pieces of information are then forwarded through the `NetworkComputeResponse` message to the main client.

## Parameterization

Does your service require inputs or parameters? Do you want controls or widgets for those parameters to show up on the SpotApp android application or on Scout? Please refer to [this document](service_customization.md) to learn how to add parameters to a network compute bridge worker.
