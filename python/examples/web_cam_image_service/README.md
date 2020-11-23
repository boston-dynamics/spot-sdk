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

In addition to the pip-installable requirements, the web cam example requires OpenCV, which must be installed separately following instructions from OpenCV. Alternatively, the example provides a Dockerfile which can be used to run the example and has a base docker image with OpenCV already installed.

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

Lastly, a port number for the image service can be specified using the `--port` argument. It is possible to bypass the port argument and allow a random port number to be selected, but it is discouraged since restarts may result in unexpected changes to a services listening port. This port number will be used with the host-ip ("PAYLOAD_IP") to fully specify where the image service is running. This port number must be open and cannot be blocked by a local firewall, otherwise the web cam image service will be unreachable from the robot and the directory registration service.

## Querying the Web Cam Image Service

To validate the web cam image service is working, the [`get_image` example](../get_image/README.md) has an argument `--image-service` which can be used to specify the service name of the web cam service: `'web-cam-service'`. This example can be used to list the different image sources or request and save an image from a specified image source. By default, this example will try to query the standard image service on-robot that communicates with the robot's built-in cameras, but can be redirected to any implementation of the API image service using the `--image-service` argument.

Since the web cam image service is registered with the robot's directory service, the get_image example can be run from any computer and just needs an API connection to the robot to be able to access the web cam image service and its images.

### Debugging Tips

Here are a couple suggestions for debugging the web cam image service:

- Check that your web cam is working separate from the api connections. For linux, the program `Cheese` allows you to stream from the camera. Run `cheese /dev/video0` (or the name of your cameras USB location) to verify the image appears.
- Check that the image service appears in the directory using the command line tool: `python3 -m bosdyn.client --username {USER} --password {PWD} {ROBOT_IP} dir list`
- Check that no faults appear from the image service using the command line tool: `python3 -m bosdyn.client --username {USER} --password {PWD} {ROBOT_IP} fault watch`
- Check for any error spew in the terminal where the image service is running while attempting to make requests to the service. If the image service is running as a docker container with Portainer, check the logs page on the web cam service's container for any error spew.
- Check that the image service responds with a complete list of its image sources using the command line tool: `python3 -m bosdyn.client --username {USER} --password {PWD} {ROBOT_IP} image list-sources --service-name web-cam-service`
- Check that retrieving and saving each image is successful, and opening the saved image reveals the correct/expected image.
    - For source names that are plain strings (with no special characters like "/"), use the command line tool: `python3 -m bosdyn.client --username {USER} --password {PWD} {ROBOT_IP} image get-image SRC_NAME --service-name web-cam-service`
    - For complicated source names, use the `get_image.py` example from the `get_image/` directory. This example will convert the source name when saving the image file to a "saveable" string: `python3 get_image.py --image-service web-cam-service --image-source {IMG_SRC}  --username {USER} --password {PWD} {ROBOT_IP}`
- Check that the tablet is detecting the web cam image service by looking in the camera sources drop down menu (top-left of the status bar) and then check that the images are appearing by selecting the Web Cam.

## Run the Web Cam Image Service using Docker

Please refer to this [document](../../../docs/payload/docker_containers.md) for general instructions on how to run software applications on computation payloads as docker containers.

Follow the instructions on how to build and use the docker image from [this section](../../../docs/payload/docker_containers.md#build-docker-images) on. The docker container with the application in this example needs the following modifications from the general instructions:
* The application arguments needed to run the Web Cam application in this example are `--host-ip HOST_COMPUTER_IP --guid GUID --secret SECRET --port PORT_NUMBER ROBOT_IP --device-name DEVICE_NAME`
* In the `Runtime & Resources` tab in the `Portainer` container configuration page , click `add device` and specify the camera's communication port (e.g. `/dev/video0`) in both the `host` field as well as the `container` field before deploying the container.
* If running the docker container locally, the device needs to be mapped from the container to your local computer in a similar manner to how it is configured on portainer. The `docker run` command needs the additional argument `--device=/dev/video0:/dev/video0`, which is mapping the host location to the container location with `/dev/video0` as an example.