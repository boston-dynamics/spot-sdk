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

If running on a CORE I/O, you will need access to the internet or your local network.

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
sudo docker save docking_callback | pigz > docking_callback.tar.gz
```

To build the Docker image for an arm64 platform (e.g. CORE I/O), run:

```
# Prerequisites
# Install the pigz and qemu packages
sudo apt-get install qemu binfmt-support qemu-user-static pigz
# This step will execute the registering scripts
sudo docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Builds the image
sudo docker build -f Dockerfile.arm64  -t docking_callback:arm64 .
# Exports the image, uses pigz
sudo docker save docking_callback:arm64 | pigz > docking_callback_arm64.tar.gz
```

Note: For the AWS callback, you must copy your config file as `config` to this directory for `docker build` to work. You will then uncomment `COPY ./config ~/.aws/config` in Dockerfile. Alternatively, you can supply your keys by using the `--aws-access-key` and `--aws-secret-key` arguments.

This example also provides a script for building the callback service into a Spot Extension.
This script requires the same prerequisites as listed above for building a docker image for CORE I/O.
Additionally, this script requires that the current user be added to the `docker` user group.
If this is not the case, the script needs to be run with root privileges.

```
./create_extension.sh
```

The output file will be called aws_docking_callback_arm64.spx and can be uploaded to a CORE I/O.
