<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

<script type="text/javascript" src="video_play_at_scroll.js"></script>
<link rel="stylesheet" type="text/css" href="tutorial.css">
<link href="prism.css" rel="stylesheet" />
<script src="prism.js"></script>

[<< Previous Page](daq3.md)
|
[Next Page >>](daq5.md)

---

# Part 4: Deploying to the CORE I/O

In this part of the tutorial, you will:

- Build docker images for the image service and data plugin.
- Run and test the docker images.
- Configure the docker images to run with `docker-compose`.
- Deploy the docker images to the robot's CORE I/O payload.

The instructions included use the CORE I/O payload, but docker images can be deployed to many different kinds of payload computers.

## Packaging the services for deployment

The previous sections described how to test the [image service](daq2.md) or the [data acquisition plugin](daq3.md) on your laptop. The next step is to package the services for deployment. The suggested approach is to package everything as Docker containers and run them on a SpotCORE payload attached to the robot.

### Creating Docker images

A variety of Spot SDK examples include a `Dockerfile` file with instructions to package the example as a docker image. An example `Dockerfile` for the web_cam_image_service and battery_service examples are shown below.

#### Creating web_cam_image_service Docker image

The file contains instructions to start from the `python:3.7-slim` image with an additional command to install a few necessary system packages.

```docker
FROM python:3.7-slim

# Requirements for opencv to work.
RUN apt-get update && apt-get install -y libsm6 libglib2.0-0 libxrender1 libxext6
```

It then uses the `docker-requirements.txt` file to install all the wheels necessary to run the example. We recommend keeping a separate `requirements.txt` file that specifies the range of dependencies that you require, and then use `pip freeze` to lock those dependencies into a `docker-requirements.txt` file so that the docker builds are repeatable with known versions.

```docker
COPY docker-requirements.txt .
RUN python3 -m pip install -r docker-requirements.txt
```

Finally, it copies the rest of the files into the image and sets `web_cam_image_service.py` as the entrypoint when starting docker containers from this image. We also provide some default arguments designed for running on the CORE I/O. These can be overridden for local testing, but make deployment to a payload computer.

```
COPY . /app
WORKDIR /app

ENTRYPOINT ["python3", "/app/web_cam_image_service.py"]
# Default arguments for running on the CORE I/O
CMD [ "192.168.50.3", "--host-ip=192.168.50.5", "--payload-credentials-file=/creds/payload_guid_and_secret"]
```

To build the docker image for the architecture of the computer being used, run the commands:

```sh
docker build --tag web_cam_image_service .
docker save web_cam_image_service | pigz > web_cam_image_service.tgz
```

This will build the image and create a file to upload to the robot.
The above commands assume that your user is in the `docker` group. If not, you may need to run them with `sudo`.

An example `docker_requirements.txt` for [the web cam image service](https://github.com/boston-dynamics/spot-sdk/blob/master/python/examples/web_cam_image_service/docker-requirements.txt) and [a point cloud data acquisition plugin](https://github.com/boston-dynamics/spot-sdk/blob/master/python/examples/data_acquisition_service/pointcloud_plugin/docker-requirements.txt) can be found in the examples directory. The main difference is the OpenCV dependency in image services.

#### Creating battery_service Docker image

Instructions above can also be used to create the docker image for the `battery_service`, called `battery_service.tgx`. The main difference is the `ENTRYPOINT` set to the battery_service.py file and different docker-requirements.txt file.

## Testing Docker container locally

Now that we have a docker images, the next step is to test the docker image locally on your laptop. The Spot SDK documentation contains instructions how to do that [here](../../payload/docker_containers.md#test-docker-images-locally).

Specifically, to test the image service and the data acquisition plugin docker images, you would run the following, if connected to the robot’s wifi:

```sh
export DEVICE_PATH=/dev/video0
export WEBCAM_PORT=5000
export BATTERY_PORT=5050
docker run --device=$DEVICE_PATH --network=host web_cam_image_service $ROBOT_IP --payload-credentials-file $CRED_FILE --host-ip $SELF_IP --port $WEBCAM_PORT --device-name $DEVICE_PATH
docker run --network=host battery_service $ROBOT_IP --payload-credentials-file $CRED_FILE --host-ip $SELF_IP --port $BATTERY_PORT
```

You will need to ensure that `$WEBCAM_PORT` and `$BATTERY_PORT` are accessible on your computer and not blocked by any firewall or networking rules.

## Create Spot Extension and Install it on CORE I/O

Once you have tested and verified that the docker containers work correctly on your laptop, it is time to recreate the docker images for the `arm64` CORE I/O architecture and install them as an Extension. The Spot SDK documentation contains instructions how to do that [here](../../payload/docker_containers.md#manage-payload-software-in-core-i-o).

### Recreate Docker Images for ARM64 Architecture

If you are using a development machine with an `x86` architecture, you need to run a few more steps to be able to create `arm64` docker images that can run on CORE I/O. Please follow the instructions in the SDK documentation [here](../../payload/docker_containers.md#build-docker-images). After installing the additional dependecies listed in that part of the documentation, you simply need to pass `--platform linux/arm64` to the `docker build` command you used earlier in order to create `arm64` docker images.

### Create docker-compose.yml File

Next, you need to create a docker-compose.yml file that contains instructions how to start the two docker images. The content of the file are shown below:

```
services:
  web_cam_image_service:
    image: web_cam_image_service
    platform: linux
    network_mode: host
    restart: unless-stopped
    devices:
      - ${ORIG_VIDEO_DEV}:/dev/video99
    volumes:
      /creds/:/opt/payload_credentials/
    command: --device-name 99 --port 5000
  battery_service:
    image: battery_service
    platform: linux
    network_mode: host
    restart: unless-stopped
    volumes:
      /creds/:/opt/payload_credentials/
    command: --port 5050
```

In this configuration, we use ports 5000 and 5050 that you used earlier for testing. The command fields for the two docker services in the file specify the additiona parameters to append to the `CMD` field specified in the `Dockerfile` files. The `web_cam_image_service` contains the additional field `devices`, which is described in more details in the section below.

### Create Udev Rules Files for Web Cam application

The python script in the `web_cam_image_service` docker container pulls images from a web cam USB device. That device name is generated when the device is plugged in and it is usually `/dev/video0` when it is the first USB device plugged in (the `0` count increases afterwards). But, with that device name not being deterministic by default, we do not want to regenerate the `web_cam_image_service` docker image every time the web cam is mounted with a different device name. To solve this issue, we will add udev rules in the Extension that are automatically installed by the Extesion manager installed on the CORE I/O.

The way we will structure the udev rule is as follows:

1. Add udev rule file that adds a symlink `video99` and runs a script `setup_device_name.sh` when a USB device with the information `SUBSYSTEM=="video4linux", SUBSYSTEMS=="usb", ATTR{name}=="PC-LM1E Camera: PC-LM1E Camera"` is plugged in. This allows us to have a symlink `/dev/video99` that is always going to be present when our particular USB web cam is plugged in. You will probably need to update the `ATTR{name}` for your web cam.

`1-sdk.camera.rules` file

```
SUBSYSTEM=="video4linux", SUBSYSTEMS=="usb", ATTR{name}=="PC-LM1E Camera: PC-LM1E Camera", SYMLINK+="video99", RUN+="/data/.extensions/daq_tutorial/setup_device_name.sh"
```

2. Unfortunately, symlinks cannot be mounted in docker containers so we need to tell docker which original device name `/dev/video99` points to and mount that as a device in the docker container. We implement that logic in the `setup_device_name.sh` script that is specified in the udev rule:

`setup_device_name.sh` file

```
#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
orig_device=$(readlink -f /dev/video99 | sed 's/\//\\\//g')
sed "s/@ORIG_VIDEO_DEV/$orig_device/" $SCRIPT_DIR/.env.tpl > $SCRIPT_DIR/.env
```

The script finds the original device name that is symlinked to `/dev/video99` and it sets that value in the `.env` file with the environment variable name `ORIG_VIDEO_DEV`. It does that replacing a value in the template file we are also including `.env.tp`

`.env.tpl` file

```
ORIG_VIDEO_DEV=@ORIG_VIDEO_DEV
```

Then, the `docker-compose.yml` file mounts the original device name specified in the docker environment variable `ORIG_VIDEO_DEV` as device `/dev/video99` in the docker container, which is also passed as the `--device-name` to the python script. This method allows us create an Extension for this tutorial that works with any device name given to the USB web cam when it is plugged in.

### Create manifest.json File

The last step is to create a `manifest.json` file with the Extension information. The contents of the file are shown below:

```
{
    "description": "DAQ Tutorial",
    "version": "3.2.0",
    "udev_rules": "1-sdk.camera.rules",
    "images": ["web_cam_image_service.tgz", "battery_service.tgz"]
}
```

### Create Extension and Install It on CORE I/O

Creating an Extension is very simple once we have the files created in the section above. Simply copy the files `battery_service.tgz`, `web_cam_image_service.tgz`, `manifest.json`, `docker-compose.yml`, `1-sdk.camera.rules`, `setup_device_name.sh`, `.env.tpl` in a folder and create the Extension, which is a zipped tar file, with the command `tar zcfv daq_tutorial.spx * .env.tpl`. Then, follow these steps to install the Extension `daq_tutorial.spx` in the CORE I/O:

1. Plug in USB web cam. This will execute the udev rule included in the Extension and create `/dev/video99` symlink and the `.env` file.
2. Install Extension by drag-and-dropping it in the "Upload New Extension" section in the Extensions tab of the CORE I/O web portal. This process is also described in the SDK documentation section [here](../../payload/docker_containers.md#install-extension). The udev rules in the Extension will be automatically triggered when the Extension is installed.

On other types of computational payloads, users can copy the docker images to the payload, load them and run `docker-compose` commands manually to start/stop/monitor the containers.

## Confirming deployment

Click on the logs icon of the installed Extension to verify that they are running correctly or to debug any errors that occur. Common problems at this stage are often typos in the volume configuration or command arguments.

Now that the containers are deployed to the robot, use the tester programs again to verify that they are operating and responding correctly.

```sh
# In examples/tester_programs
$ python3 image_service_tester.py $ROBOT_IP --service-name web-cam-service --check-data-acquisition

$ python3 plugin_tester.py $ROBOT_IP --service-name data-acquisition-battery
```

## Head over to [Part 5: Collecting Data](daq5.md) >>

[<< Previous Page](daq3.md)
|
[Next Page >>](daq5.md)
