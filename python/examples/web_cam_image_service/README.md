<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Image Service for a Web Cam

This example implements the standard Boston Dynamics API image service and communicates to common web cameras using OpenCV. The example will run the web cam image service locally and register it with the robot's directory service using the payload service registration procedure. The web cam image service is an implementation of the GRPC image service, which has the ListImageSources RPC and the GetImage RPC. The service can encode information from the OpenCV camera connection into a protobuf message.

This example will register the service from a payload, which could be the CORE I/O or a different external computer; therefore, it will require knowing the guid, secret, and IP address of the computer the service will be running off of. See the [self registration payloads example](../self_registration/README.md) for a higher level overview of how to set up and register a payload, as well as how to register a simple announcing service.

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

This example takes two different IP addresses as arguments. The `--host-ip` argument describes the IP address for the computer that will be running the web cam image service. A helper exists to try to determine the correct IP address. This command must be run on the same computer that will be running the web cam image service:

```
python3 -m bosdyn.client {ROBOT_IP} self-ip
```

The other IP address is the traditional robot hostname ("ROBOT_IP") argument, which describes the IP address of the robot hosting the directory service.

When launching the web cam image service, the different device names should be provided. All of these sources should be queryable from the web cam image service using OpenCV. They can be specified individually by using the argument `--device-name`, and appending multiple of the argument to specify each camera source. For example, `--device-name CAMERA1 --device-name CAMERA2`. By default, the device "0" will be used, which represents the device at index 0 and will connect to the first connected video device found for each operating system. A user can provide either an index to a specific camera device, or the file path to describe the USB location of the camera. Each device will be listed by the service as an image source using the final part of the device name after the last "/" in a filepath (e.g. "/dev/video0" will result in an image source name "video0", device index "0" will also have image source name "video0"). Note for linux, by default the camera devices connected will have a filepath formatted as `/dev/videoXXX` where "XXX" is the index of the camera. However, on Windows the default locations are more difficult to determine, so providing the index number as the device name is preferred.

Since the example runs off of a payload computer, it requires a GUID (uniquely generated payload specifier) and secret (private string associated with a payload) for a _registered_ and _authorized_ payload computer as arguments when launching the example. This "payload" can represent any type of computer capable of hosting the web cam image service. See documentation on [configuration of payload software](../../../docs/payload/configuring_payload_software.md#Configuring-and-authorizing-payloads) for more information.

A port number for the image service can be specified using the `--port` argument. It is possible to bypass the port argument and allow a random port number to be selected, but it is discouraged since restarts may result in unexpected changes to a services listening port. This port number will be used with the host-ip ("PAYLOAD_IP") to fully specify where the image service is running. This port number must be open and cannot be blocked by a local firewall, otherwise the web cam image service will be unreachable from the robot and the directory registration service.

There is an optional string argument `--codec` to specify a four character video codec describing the camera's compression/decompression software. The video codec code is operating system dependent. For example, on a Windows computer, the video codec is commonly 'DIVX', and on a linux computer, the video codec is commonly 'MJPG'. Note, the video codec does not necessarily need to be specified as OpenCV's default selection will typically work for most web cams, however if you are seeing OpenCV errors when the image service tries to capture an image, then try specifying the video codec for your camera. An example error of this type is:

```
[ WARN:0] global /io/opencv/modules/videoio/src/cap_v4l.cpp (998) tryIoctl VIDEOIO(V4L2:/dev/video1): select() timeout.
```

This error was fixed for a linux experiment by providing the video codec argument as `--codec mjpg`.

There are optional arguments to change the camera's resolution if it is possible. The arguments `--res-width` and `--res-height` can adjust the image resolution for all captures completed by the service. If the input resolution is not achievable by the camera, the nearest/most similar resolution will be chosen and used. If no resolution is provided, the image service will use the camera's defaults.

Lastly, the command line argument `--show-debug-info` will allow a user to live-view the OpenCV output of the web cam video capture on their local computer. Only use this flag for debug purposes, as it will likely slow down the main example operation and reduce the performance of the image service.

## Debugging Tips

Here are a couple suggestions for debugging the web cam image service:

- Ensure the camera is powered on and plugged in.
- Check that your web cam is working separate from the api connections. For linux, the program `Cheese` allows you to stream from the camera. Run `cheese /dev/video0` (or the name of your cameras USB location) to verify the image appears.
- Use the command line argument `--show-debug-info` which will display the openCV capture output before encoded it into the image service protobuf message. If the image is unable to show here, then the device name is likely incorrect or unreachable.
- Check that the image service appears in the directory using the command line tool: `python3 -m bosdyn.client {ROBOT_IP} dir list`
- Use the [image service tester program](../tester_programs/README.md) to ensure the service can successfully be communicated with and that each RPC will complete correctly.
- When all tests pass for the image service tester program, check that the tablet is detecting the web cam image service by looking in the camera sources drop down menu (top-left of the status bar) and then check that the images are appearing by selecting the "Web Cam" camera source.

## Run the Web Cam Image Service using Docker

Please refer to this [document](../../../docs/payload/docker_containers.md) for general instructions on how to run software applications on computation payloads as docker containers.

Follow the instructions on how to build and use the docker image from [this section](../../../docs/payload/docker_containers.md#build-docker-images) on. The docker container with the application in this example needs the following modifications from the general instructions:

- The application arguments needed to run the Web Cam application in this example are `--host-ip HOST_COMPUTER_IP --guid GUID --secret SECRET --port PORT_NUMBER ROBOT_IP --device-name DEVICE_NAME`
- In the `Runtime & Resources` tab in the `Portainer` container configuration page , click `add device` and specify the camera's communication port (e.g. `/dev/video0`) in both the `host` field as well as the `container` field before deploying the container.
- If running the docker container locally, the device needs to be mapped from the container to your local computer in a similar manner to how it is configured on portainer. The `docker run` command needs the additional argument `--device=/dev/video0:/dev/video0`, which is mapping the host location to the container location with `/dev/video0` as an example.
