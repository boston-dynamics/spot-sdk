<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Image Service for a Web Cam

This example implements the standard Boston Dynamics API image service and communicates to common web cameras using OpenCV. The example will run the web cam image service locally and register it with the robot's directory service using the payload service registration procedure. The web cam image service is an implementation of the GRPC image service, which has the ListImageSources RPC and the GetImage RPC. The service can encode information from the OpenCV camera connection into a protobuf message.

This example will register the service from a payload, which could be the Spot CORE or a different external computer; therefore, it will require knowing the guid, secret, and IP address of the computer the service will be running off of. See the [self registration payloads example](../self_registration/README.md) for a higher level overview of how to setup and register a payload, as well as how to register a simple announcing service.

## Prerequisites

This example requires bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Example Execution

This example will run the web cam image service locally and register it with the robot's directory service using a directory keep alive. After running the example clients will be able to send requests to this service through the robot.

(NOTE: the example may need to be run with `sudo` to enable access to the web cam.)

To run the web cam image service from this directory, issue the command:

```
python3 web_cam_image_service.py --guid {PAYLOAD_GUID} --secret {SECRET} --host-ip {PAYLOAD_IP} --port {PORT} {ROBOT_IP} --device-name {CAMERA}
```
The example can be safely exited by issuing a SIGINT (Ctrl + C) to the caller.

This example takes two different IP addresses: the `--host-ip` argument describes the IP address for the computer that will be running the web cam image service, and the `hostname` ("ROBOT_IP") argument describes the IP address of the robot hosting the directory service.

When launching the web cam image service, the different device names should be provided. All of these sources should be queryable from the web cam image service using OpenCV. They can be specified individually by using the argument `--device-name`, and appending multiple of the argument to specify each camera source. For example, `--device-name CAMERA1 --device-name CAMERA2`. By default, the device "/dev/video0" will be used, which will connect to the first connected webcam for a linux computer.  Each device will be listed by the service as an image source using the final part of the device name (e.g. "/dev/video0" will result in an image source name "video0").

Since the example runs off of a payload computer, it requires a GUID (uniquely generated payload specifier) and secret (private string associated with a payload) for a *registered* and *authorized* payload computer as arguments when launching the example. This "payload" can represent any type of computer capable of hosting the web cam image service. See documentation on [configuration of payload software](../../../docs/payload/configuring_payload_software.md#Configuring-and-authorizing-payloads) for more information.

Lastly, a port number for the image service can be specified using the `--port` argument, however the script will choose a random default port number if nothing is provided. This port number will be used with the host-ip ("PAYLOAD_IP") to fully specify where the image service is running. This port number must be open and cannot be blocked by a local firewall, otherwise the web cam image service will be unreachable from the robot and the directory registration service.

## Querying the Web Cam Image Service

To validate the web cam image service is working, the [`get_image` example](../get_image/README.md) has an argument `--image-service` which can be used to specify the service name of the web cam service: `'web-cam-service'`. This example can be used to list the different image sources or request and save an image from a specified image source. By default, this example will try to query the standard image service on-robot that communicates with the robot's built-in cameras, but can be redirected to any implementation of the API image service using the `--image-service` argument.

Since the web cam image service is registered with the robot's directory service, the get_image example can be run from any computer and just needs an API connection to the robot to be able to access the web cam image service and its images.

### Run the Web Cam Image Service using Docker

With docker installed and setup, the web cam image service can be created into a docker container, saved as a tar file, and then run on the Spot CORE using Portainer.

The docker file, which will run the web cam image service, can be built and saved to a tar file using the following comamnds:
```
sudo docker build -t web_cam_image_service .
sudo docker save web_cam_image_service > web_cam_image_service.tar
```

The dockerfile can now be run locally or run directly on the Spot CORE.

#### Run On Local Computer

To run locally, your computer must be registered as a weightless payload (and authorized on the admin console web server for the robot). This can be done using the [payloads example](../payloads/README.md), which registers the payload with the name 'Client Registered Payload Ex #1' and a default GUID and secret.

To start the dockerfile and the web cam image service, run:
```
sudo docker run -it --device=/dev/video0:/dev/video0 --network=host web_cam_image_service --guid 78b076a2-b4ba-491d-a099-738928c4410c --secret secret --host-ip HOST_IP ROBOT_IP --device-name /dev/video0
```
** Note, the HOST_IP must be your computer's IP address, and the ROBOT_IP should be the robot's IP address or hostname. Additionally, the device name `/dev/video0` should match the location of your USB web cam and may need to be updated.

#### Run On Spot CORE

To run the dockerfile and web cam image service on the Spot CORE, first ensure that you have a 2.1 release on the Spot CORE. This can be checked by ssh-ing onto the Spot CORE and running `cat /etc/spotcore-release`.

If it is not up to date, upgrade to the latest Spot CORE release following the instructions to upgrade: https://support.bostondynamics.com/s/article/How-to-update-Spot-CORE-software.

Once the Spot CORE is updated, the docker file can be deployed using Portainer. Upload the `web_cam_image_service.tar` as an "Image" on Portainer. If the upload fails, try changing the permissions of the tar file using the command:
```
sudo chmod a+r web_cam_image_service.tar
```
Once the upload completes, go to the "Containers" tab in Portainer and add a container. Set the follow fields:
```
"Name" = web_cam_image_service
"Image" = web_cam_image_service:latest
"Publish all exposednetwork ports to random host ports" = True
```

Under the "Command & logging" tab in the container configuration page, add all of the arguments in the "Command" field. Specifically, these arguments:
```
--host-ip HOST_COMPUTER_IP --guid GUID --secret SECRET ROBOT_IP
```
** Make sure the `HOST_COMPUTER_IP` matches the Spot CORE's IP (by default, this is 192.168.50.5), and `ROBOT_IP` matches the robot IP from the perspective of the Spot CORE (by default, this is 192.168.50.3).

Under the "Network" tab in the container configuration page, set the "Network" field to host.

In the "Runtime & Resources" tab in the container configuration page, click `add device` and specify `/dev/video0` in both the `host` field as well as the `container` field.

Under the "Restart policy" tab in the container configuration page, set the policy to "Unless stopped". This will allow the docker container to continue to keep running all the time (even after rebooting the spot core) unless it is manually stopped by a user in Portainer.

Once all the necessary fields are configured, select "Deploy the container" to run the web cam image service using the docker container on Spot CORE.
