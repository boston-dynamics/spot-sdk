<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Ricoh Theta
In the 2.1.0 release, we have provided a **new** Ricoh Theta example for developers to learn how to create a standard Boston Dynamics API image service that communicates with the Ricoh Theta camera.

This example assumes you are using the default settings of a Ricoh Theta camera and mounted/registered Spot CORE.

## Required Items
- Spot CORE
- Ricoh Theta V or Z1
- Personal Computer

## Installation Steps
The following installation steps assume you:
- have read the Ricoh Theta online manual and understand client mode operation
- have the latest spot-sdk downloaded & installed on your PC
- familiar with SSH and using a Command Line Interface (CLI)

### Install Packages on PC
Navigate via the CLI on your PC to the ricoh_theta directory and review the requirements.txt document for this example before continuing. Several python packages will need to be installed along with the standard SDK:

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
Perform the following steps on your PC to setup Ricoh Theta client mode, which means the Ricoh Theta will be connected to a different network (in this case, Spot's WiFI) instead of broadcasting its own network (which is the direct mode). The python script below is required for this example to set the static ip, which the App does not allow.

1. Enable wireless connection on the Ricoh Theta and connect your PC to the Ricoh Theta via WiFi.
1. Run `ricoh_client_mode.py` on your PC via the CLI. Replace the capitilized letters in the command below with your Ricoh Theta SSID **with the .OSC removed from the end**, Spot's WiFi SSID, and Spot's WiFi password.
    ```
    python ricoh_client_mode.py --theta-ssid THETAYL00196843 --wifi-ssid WIFI_SSID --wifi-password WIFI_PASSWORD
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

    For Developers: As an _additional_ option, you can configure the ip settings by editing the `__init__` function directly in `ricoh_theta.py` or when creating the Theta() object. These settings are featured below and have been tested on the Spot CORE.
    ```python
    def __init__(..., static_ip="192.168.80.110", subnet_mask="255.255.255.0", default_gateway="192.168.80.1"):
    ```

1. Enable client mode on your Ricoh Theta (press the wireless button on the camera) and confirm connection with Spot's access point. The wireless indicator should stop blinking and become solid green in client mode for Ricoh Theta V. On a Ricoh Theta Z, on the OLED display screen of the camera, there will be a 'CL' icon next to the wireless indicator. **Often a Ricoh Theta power cycle is required.** Note, the new static IP for the Ricoh Theta in client mode will be persistent across reboots of the camera.


## Run Image Service

The image service script creates a standard Boston Dyanmics API image service that communicates with the Ricoh Theta camera.

To launch the GRPC image service from a registered payload computer (such as the Spot CORE), authenticate the robot connection using the payload's authentication, and ultimately register the service with the directory **with the service name 'ricoh-theta-image-service'**, issue the following command:
```
python3 ricoh_theta_image_service.py --theta-ssid THETA_SSID --theta-client --host-ip HOST_COMPUTER_IP --guid GUID --secret SECRET ROBOT_IP
```

The `hostname` ("ROBOT_IP") argument should be the IP address of the robot which is hosting the directory service. The `--host-ip` argument is the IP address for the computer running the script. For example, in the example where we run the image service on the Spot CORE, the default IP address of 192.168.50.5 can be provided for the `--host-ip` argument.

Since the example is created to run off of a payload computer, it requires the input arguments `--guid` (uniquely generated payload specifier) and `--secret` (private string associated with a payload) for the registered payload computer that will be running the Ricoh Theta image service. For the Spot CORE, this information by default will be located in the file `/opt/payload_credentials/payload_guid_and_secret`. Note, you can run the Ricoh Theta image service locally on your PC by registering it as a weightless payload using [the payloads example](../payloads/README.md) and creating a GUID and secret for your computer. See documentation on [configuration of payload software](../../../docs/payload/configuring_payload_software.md#Configuring-and-authorizing-payloads) for more information.

If the `--theta-client` argument is provided, the Ricoh Theta will be connected to in client mode. Otherwise, it will default to a direct-ip mode connection, requiring the computer running the image service script to be wirelessly connected to the Ricoh Theta's WiFi. If using the Ricoh Theta in client mode, make sure that the `ricoh_client_mode.py` script has been run to create a connection to Spot's WiFi with the correct static ip.

The `--theta-ssid` argument is used to pass the SSID for the Ricoh Theta camera that will take the images and **should have the .OSC removed**. This will be set as the image source name for the service. Additionally, if the password for the Ricoh Theta is different from the default password of the camera, this can be provided using the `--theta-password` argument.

Lastly, a port number for the image service can be specified using the `--port` argument, however the script will choose a random default port number if nothing is provided. This port number will be used with the host-ip (HOST_COMPUTER_IP) to fully specify where the image service is running. This port number must be open and cannot be blocked by a local firewall, otherwise the ricoh-theta image service will be unreachable from the robot and the directory registration service.

### Querying the Ricoh Theta Image Service

To validate the ricoh-theta image service is working, the [`get_image` example](../get_image/README.md) has an argument `--image-service` which can be used to specify the service name of the Ricoh Theta service: `'ricoh-theta-image-service'`. This example can be used to list the different image sources or request and save an image from a specified image source. By default, this example will try to query the standard image service on-robot that communicates with the robot's built-in cameras, but can be redirected to any implementation of the API image service using the `--image-service` argument.

Since the ricoh-theta service is registered with the robot's directory service, the get_image example can be run from any computer and just needs an API SDK connection to the robot to be able to access the ricoh-theta service and its images.

### Run the Ricoh Theta Image Service using Docker

With docker installed and setup, the Ricoh Theta image service can be created into a docker container, saved as a tar file, and then run on the Spot CORE using Portainer.

The docker file, which will run the Ricoh Theta image service, can be built and saved to a tar file using the following commands:
```
sudo docker build -t ricoh_theta_image_service .
sudo docker save ricoh_theta_image_service > ricoh_theta_image_service.tar
```

The dockerfile can now be run locally or run directly on the Spot CORE.

#### Run On Local Computer

To run locally, your computer must be registered as a weightless payload (and authorized on the admin console web server for the robot). This can be done using the [payloads example](../payloads/README.md), which registers the payload with the name 'Client Registered Payload Ex #1' and a default GUID and secret.

To start the dockerfile and the Ricoh Theta image service, run:
```
sudo docker run -it --network=host ricoh_theta_image_service --theta-ssid THETA_SSID --theta-client --host-ip HOST_COMPUTER_IP --guid GUID --secret SECRET ROBOT_IP
```
** Note, all the arguments are the same as when running the python script `ricoh_theta_image_service.py`.

#### Run On Spot CORE
To run the dockerfile and Ricoh Theta image service on the Spot CORE, first ensure that you have a 2.1 release on the Spot CORE. This can be checked by ssh-ing onto the Spot CORE and running `cat /etc/spotcore-release`.

If it is not up to date, upgrade to the latest Spot CORE release following the instructions to upgrade: https://support.bostondynamics.com/s/article/How-to-update-Spot-CORE-software.

Once the Spot CORE is updated, the docker file can be deployed using Portainer. Upload the `ricoh_theta_image_service.tar` as an "Image" on Portainer. If the upload fails, try changing the permissions of the tar file using the command:
```
sudo chmod a+r ricoh_theta_image_service.tar
```
Once the upload completes, go to the "Containers" tab in Portainer and add a container. Set the follow fields:
```
"Name" = ricoh_theta_image_service
"Image" = ricoh_theta_image_service:latest
"Publish all exposed network ports to random host ports" = True
```

Under the "Command & logging" tab in the container configuration page, add all of the arguments in the "Command" field. Specifically, these arguments:
```
--theta-ssid THETA_SSID --theta-client --host-ip HOST_COMPUTER_IP --guid GUID --secret SECRET ROBOT_IP
```
** Make sure the `HOST_COMPUTER_IP` matches the Spot CORE's IP (by default, this is 192.168.50.5 for the rear-mounted Spot CORE), `ROBOT_IP` matches the robot IP from the perspective of the Spot CORE (by default, this is 192.168.50.3), and that `THETA_SSID` has the .OSC removed.

Under the "Network" tab in the container configuration page, set the "Network" field to "host".

Under the "Restart policy" tab in the container configuration page, set the policy to "Unless stopped". This will allow the docker container to continue to keep running all the time (even after rebooting the spot core) unless it is manually stopped by a user in Portainer.

Once all the necessary fields are configured, select "Deploy the container" to run the Ricoh Theta image service using the docker container on Spot CORE.

## Developer Comments
For Ricoh Theta API Documentation, visit [https://api.ricoh/products/theta-api/](https://api.ricoh/products/theta-api/)
