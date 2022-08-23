<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Interacting with a Ricoh Theta Camera

Since the 2.1.0 release, we have provided a **new** Ricoh Theta example for developers to learn how to create a standard Boston Dynamics API image service that communicates with the Ricoh Theta camera.

This example assumes you are using the default settings of a Ricoh Theta camera and mounted/registered CORE I/O.

## Required Items

- CORE I/O
- Ricoh Theta V or Z1
- Personal Computer

## Installation Steps

The following installation steps assume you:

- have read the Ricoh Theta online manual and understand client mode operation
- have the latest spot-sdk downloaded & installed on your PC
- familiar with SSH and using a Command Line Interface (CLI)

### Install Packages on PC

Navigate via the CLI on your PC to the python examples [ricoh_theta](https://github.com/boston-dynamics/spot-sdk/tree/master/python/examples/ricoh_theta) directory and review the requirements.txt document for this example before continuing. Several python packages will need to be installed along with the standard SDK:

```
python3 -m pip install -r requirements.txt
```

### Test Ricoh Theta

A `test_driver.py` script has been included which will show the state of the camera and take a picture.

The `SSID` field within the script must be updated to match your camera's theta_ssid. Additionally, before running the example driver, you must be wirelessly connected to the Ricoh Theta camera from the computer you intend to run this example. Note that the Ricoh Theta's wireless network may not appear or be available when the camera is plugged into a computer through its USB port. For a Ricoh Theta Z, check the OLED display for the WiFi icon to confirm the network is broadcasting. For a Ricoh Theta V, the wireless indicator should be lit up blue if in access point mode.

The script is currently configured for direct mode IP settings for running on your PC. Edit the python script as desired to enable/disable different functions of the Ricoh Theta camera driver.

```
python3 test_driver.py
```

### Connect Ricoh Theta to Spot

Perform the following steps on your PC to set up Ricoh Theta client mode, which means the Ricoh Theta will be connected to a different network (in this case, Spot's WiFI) instead of broadcasting its own network (which is the direct mode). The python script below is required for this example to set the static ip, which the App does not allow.

1. Enable wireless connection on the Ricoh Theta and connect your PC to the Ricoh Theta via WiFi.
1. Run `ricoh_client_mode.py` on your PC via the CLI. Replace the capitalized letters in the command below with your Ricoh Theta SSID **with the .OSC removed from the end**, Spot's WiFi SSID, and Spot's WiFi password. The `disable-sleep-mode` will disable the Ricoh Theta's automatic sleep with inactivity mode. Note, this can also be done through the Ricoh Theta's phone application, in which case this argument does not need to be provided when running the client mode script.

   ```
   python ricoh_client_mode.py --theta-ssid THETAYL00196843 --wifi-ssid WIFI_SSID --wifi-password WIFI_PASSWORD --disable-sleep-mode
   ```

   If all goes well, you should see a positive response that shows the new static ip:

   ```
   Response Below:
   {
     "name": "camera._setAccessPoint",
     "state": "done"
   }
   New static ip: 192.168.80.110
   ```

   The above script will specify the access point settings for Ricoh Theta client mode and a static ip address.

   For Developers: As an _additional_ option, you can configure the ip settings by editing the `__init__` function directly in `ricoh_theta.py` or when creating the Theta() object. These settings are featured below and have been tested on the CORE I/O.

   ```python
   def __init__(..., static_ip="192.168.80.110", subnet_mask="255.255.255.0", default_gateway="192.168.80.1"):
   ```

1. Enable client mode on your Ricoh Theta (press the wireless button on the camera) and confirm connection with Spot's access point. The wireless indicator should stop blinking and become solid green in client mode for Ricoh Theta V. On a Ricoh Theta Z, on the OLED display screen of the camera, there will be a 'CL' icon next to the wireless indicator. **Often a Ricoh Theta power cycle is required.** Note, the new static IP for the Ricoh Theta in client mode will be persistent across reboots of the camera.

## Run Image Service

The image service script creates a standard Boston Dynamics API image service that communicates with the Ricoh Theta camera.

To launch the GRPC image service from a registered payload computer (such as the CORE I/O), authenticate the robot connection using the payload's authentication, and ultimately register the service with the directory **with the service name 'ricoh-theta-image-service'**, issue the following command:

```
python3 ricoh_theta_image_service.py --theta-ssid THETA_SSID --theta-client --host-ip HOST_COMPUTER_IP --guid GUID --secret SECRET --port PORT_NUMBER ROBOT_IP
```

This example takes two different IP addresses as arguments. The `--host-ip` argument describes the IP address for the computer that will be running the web cam image service. A helper exists to try to determine the correct IP address. This command must be run on the same computer that will be running the ricoh theta image service:

```
python3 -m bosdyn.client {ROBOT_IP} self-ip
```

The other IP address is the traditional robot hostname ("ROBOT_IP") argument, which describes the IP address of the robot hosting the directory service.

Since the example is created to run off of a payload computer, it requires the input arguments `--guid` (uniquely generated payload specifier) and `--secret` (private string associated with a payload) for the registered payload computer that will be running the Ricoh Theta image service. For the CORE I/O, this information by default will be located in the file `/opt/payload_credentials/payload_guid_and_secret`. Note, you can run the Ricoh Theta image service locally on your PC by registering it as a weightless payload using [the payloads example](../payloads/README.md) and creating a GUID and secret for your computer. See documentation on [configuration of payload software](../../../docs/payload/configuring_payload_software.md#Configuring-and-authorizing-payloads) for more information.

If the `--theta-client` argument is provided, the Ricoh Theta will be connected to in client mode. Otherwise, it will default to a direct-ip mode connection, requiring the computer running the image service script to be wirelessly connected to the Ricoh Theta's WiFi. If using the Ricoh Theta in client mode, make sure that the `ricoh_client_mode.py` script has been run to create a connection to Spot's WiFi with the correct static ip.

The `--theta-ssid` argument is used to pass the SSID for the Ricoh Theta camera that will take the images and **should have the .OSC removed**. This will be set as the image source name for the service. Additionally, if the password for the Ricoh Theta is different from the default password of the camera, this can be provided using the `--theta-password` argument.

The Ricoh Theta image service will default to only attempting to capture an image from the Ricoh Theta camera when requested with a GetImage gRPC call. To have the Ricoh Theta attempt to continuously capture images, pass the command line argument `--capture-continuously`. This will cause the image service to create a background thread and attempt to query the ricoh theta at a high rate. Note, the Ricoh Theta images are very high resolution and the stitching process to go from the fisheye image to the processed image is time-consuming, so sometimes the continuous captures will drain the camera's battery quickly or overwhelm the camera processors.

The `--live-stream` argument can be provided to use a quicker image capturing method. This will create a stream that reads from the live preview results, which can then use a different, lower quality image stitching algorithm that allows a faster, live stream return of images.

**Note:** using the arguments `--live-stream` and `--capture-continuously` are recommended for the best results when working with the ricoh theta through the tablet in teleop.

Lastly, a port number for the image service can be specified using the `--port` argument. It is possible to bypass the port argument and allow a random port number to be selected, but it is discouraged since restarts may result in unexpected changes to a service listening on the old port. This port number will be used with the host-ip (HOST_COMPUTER_IP) to fully specify where the image service is running. This port number must be open and cannot be blocked by a local firewall, otherwise the ricoh-theta image service will be unreachable from the robot and the directory registration service.

### Ricoh Theta Image Service Configuration

The Ricoh Theta image service is configured to prevent directory registration if communication cannot be established with the Ricoh Theta camera. This means the image service will not show up in the directory listing, the data acquisition service's known captures, or the tablet's set of available camera sources.

Additionally, the service will throw [Service Faults](../../../docs/concepts/faults.md) for both failure to communicate at start up with the camera and also if a capture attempt fails for a different reason than networking. These faults will be visible in the robot state, and will show warning indicators on the tablet.

Note, the Ricoh Theta image requests can be slow due to the time it takes to stitch the two fisheye images together on the camera.

### Debugging Tips

Here are a couple suggestions for debugging the Ricoh Theta image service:

- Check that the Ricoh Theta is configured properly. If running the image service locally, the Ricoh Theta can be in direct-ip mode and the local computer can connect to the Ricoh Theta's network. If running on the CORE I/O or a different spot payload computer, the Ricoh Theta should be in client mode. For the Ricoh Theta V, the wireless indicator should be solid green; for the Ricoh Theta Z, the OLED display will have a 'CL' icon near the wireless indicator. It may help to just rerun the `ricoh_client_mode.py` script to fully ensure that it is setup for communicating on Spot's network.
- Check that the image service appears in the directory using the command line tool: `python3 -m bosdyn.client {ROBOT_IP} dir list`
- Use the [image service tester program](../tester_programs/README.md) to ensure the service can successfully be communicated with and that each RPC will complete correctly.
- When all tests pass for the image service tester program, check that the tablet is detecting the Ricoh Theta image service by looking in the camera sources drop down menu (top-left of the status bar) and then check that the images are appearing by selecting the Ricoh Theta.
- Check the camera's current capture mode. If you are seeing the following error: `takePicture failed due to: Command executed is currently disabled` then either change the mode to picture mode, or pass the `--live-stream` argument when starting the service.

## Run the Ricoh Theta Image Service using Docker

Please refer to this [document](../../../docs/payload/docker_containers.md) for general instructions on how to run software applications on computation payloads as docker containers.

Follow the instructions on how to build and use the docker image from [this section](../../../docs/payload/docker_containers.md#build-docker-images). The application arguments needed to run the Ricoh Theta application in this example are `--theta-ssid THETA_SSID --theta-client --host-ip HOST_COMPUTER_IP --guid GUID --secret SECRET --port PORT_NUMBER ROBOT_IP`.

**Reminder:** the Ricoh Theta needs to be in client mode when running the image service on a payload computer. Follow the initial instructions above to setup client mode.

## Developer Comments

For Ricoh Theta API Documentation, visit [https://api.ricoh/products/theta-api/](https://api.ricoh/products/theta-api/).
