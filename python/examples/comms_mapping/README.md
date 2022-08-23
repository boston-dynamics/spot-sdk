<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Comms image service

This service creates a virtual camera device that can be selected on the controller and displays a map of wifi signal strength.
This example will register itself as a payload, which will need to be authorized in the robot's admin console. The payload dimensions, location, and weight are small values.

# How to use

## Running locally:

```
pip install -r docker-requirements.txt
python3 comms_image_service.py [options] --host-ip <computer IP> <robotIP>
```

## When using a Docker image on CORE I/O:

Follow the instructions in this [document](../../../docs/payload/docker_containers.md) to create a docker image and an Extension for CORE I/O. Or, the docker image can be run locally on the command-line:

```
sudo docker run -it -p {PORT_NUM}:{PORT_NUM} --network host {comms_image_service} --port {PORT_NUM}
```

The same command can be run on the CORE I/O as an alternative to creating an Extension, after copying the docker image to the CORE I/O and loading it with the command `sudo docker load -i {IMAGE_FILE}`.
