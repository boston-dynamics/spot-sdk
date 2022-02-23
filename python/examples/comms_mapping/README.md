<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Comms image service
This service creates a virtual camera device that can be selected on the controller and displays a map of wifi signal strength.
This example will register itself as a payload, which will need to be authorized in the robot's admin console.  The payload dimensions, location, and weight are small values.

# How to use

## Running locally:

```
pip install -r docker-requirements.txt
python3 comms_image_service.py [options] --host-ip <computer IP> <robotIP>
```

## When using a Docker image on CORE:
* Build using included Dockerfile then save to a .tar
* Upload image tarfile using Portainer on CORE and create a new container from the image
* Under "Network ports configuration", expose a port number (e.g. 7223)
* Set the restart policy to "Always Unless Stopped"
* In the "Advanced container settings", put `--port {PORT_NUM}`

#### From the command line (alternate method):
```
sudo docker run -it -p {PORT_NUM}:{PORT_NUM} {comms_image_service} --port {PORT_NUM}
```
