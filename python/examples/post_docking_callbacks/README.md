<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Post Docking Callback Examples

The scripts in this folder allow you to upload files saved to DAQ during robot operation to various endpoints, with the target use case having the callback run when Spot docks at the end of an Autowalk mission.

## Install Packages
Run the below to install the necessary dependencies:
```
python3 -m pip install -r requirements.txt
```

## Configuration Requirements
For AWS, you must have your config file saved at `~/.aws/config` with format:
```
[default]
aws_access_key_id=KEY
aws_secret_access_key=KEY
```
If running on a CORE, you will need access to the internet or your local network.

## Run a Callback
Run the scripts by the following commands:
AWS:
```
python3 -m daq_upload_docking_callback --destination aws --bucket-name YOUR_BUCKET --host-ip HOST_COMPUTER_IP SPOT_IP
```
Note: You can either use a config file at `~/.aws/config` or use the `--aws-access-key` and `--aws-secret-key` arguments to have this service create the file.

GCP:
```
python3 -m daq_upload_docking_callback --destination gcp --key-filepath PATH_TO_KEY_JSON --bucket-name YOUR_BUCKET --host-ip HOST_COMPUTER_IP SPOT_IP
```
Local:
```
python3 -m daq_upload_docking_callback --destination local --destination-folder DESTINATION --host-ip HOST_COMPUTER_IP SPOT_IP
```
You can use the optional `--time-period` argument to adjust how far back the callback should look for files. If not specified, the callback will look for files starting from when the callback was initialized. After running once, the start time will be reset.

## Run a Callback using Docker

Please refer to this [document](../../../docs/payload/docker_containers.md) for general instructions on how to run software applications on computation payloads as docker containers.

You can find general instructions on how to build and use the docker image [here](../../../docs/payload/docker_containers.md#build-docker-images).

To build the Docker image, run:
```
sudo docker build -f Dockerfile  -t docking_callback .
sudo docker save docking_callback > docking_callback.tar
```

Note: For the AWS callback, you must copy your config file as `config` to this directory for `docker build` to work. You will then uncomment `COPY ./config ~/.aws/config` in Dockerfile. Alternatively, you can supply your keys by using the `--aws-access-key` and `--aws-secret-key` arguments.

Open Portainer (https://ROBOT_IP:21900), login, and navigate to "Images".

Click "Import", select your docking_callback.tar file, and upload.

Navigate to "Containers", click "Add Container", and fill out the following fields:
* "Name" = Name of the container. This should be set to a unique string that describes the container.
* "Image" = {IMAGE_NAME}:latest. {IMAGE_NAME} represents the image name used to build the docker image.
* Under the "Command & logging" tab in the container configuration page, add arguments depending on your configuration. On the CORE, the CORE_IP should be 192.168.50.5 and the ROBOT_IP should be 192.168.50.3.

    * AWS `--destination aws --bucket-name YOUR_BUCKET --host-ip HOST_COMPUTER_IP SPOT_IP`
    * GCP `--destination gcp --key-filepath PATH_TO_KEY_JSON --bucket-name YOUR_BUCKET --host-ip HOST_COMPUTER_IP SPOT_IP`
    * Local `--destination local --destination-folder DESTINATION --host-ip HOST_COMPUTER_IP SPOT_IP`
* Under the "Env" tab create `BOSDYN_CLIENT_USERNAME` and `BOSDYN_CLIENT_PASSWORD` variables with the login credentials for the robot.
* Under the "Network" tab in the container configuration page, set the "Network" field to `host` so ports are forwarded correctly between the host OS and the docker container.
* Under the "Restart policy" tab in the container configuration page, set the policy to "Unless stopped". This will allow the docker container to continue to keep running all the time (even after rebooting the spot core) unless it is manually stopped by a user in Portainer.

Click "Create". This will build your container. To verify that the callback registered, click logs and verify that you see the expected:
```
DATE TIME - INFO - Started the DaqDockingUploadServicer server.
DATE TIME - INFO - daq-docking-upload-callback service registered/updated.
DATE TIME - INFO - Starting directory registration loop for daq-docking-upload-callback
```
