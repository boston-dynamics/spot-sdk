<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# CORE I/O OpenVPN Extension Documentation

This section describes how to develop and deploy a CORE I/O extension to run an OpenVPN client.

## Before Starting

Please read [CORE I/O Documentation](coreio_documentation.md) and [Running Custom Applications with Spot](docker_containers.md) before continuing.

## dockerfile

Create the following dockerfile to build the container for our extension.

```sh
FROM arm64v8/alpine

RUN apk update
RUN apk add openvpn
RUN mkdir -p /dev/net; mknod /dev/net/tun c 10 200; chmod 600 /dev/net/tun

COPY kickoff.sh /app/
WORKDIR /app
ENTRYPOINT ["/app/kickoff.sh"]
```

The line `RUN mkdir -p /dev/net; mknod /dev/net/tun c 10 200; chmod 600 /dev/net/tun` is specific for OpenVPN and creates a device file for the network interface with the right name and permissions set.

## docker-compose.yml

Create the following docker-compose file to start the container for our extension.

```sh
version: "3.5"
services:
  openvpn_client:
    image: openvpn_client
    network_mode: host
    restart: unless-stopped
    cap_add:
      - NET_ADMIN
    devices:
      - /dev/net/tun:/dev/net/tun
    volumes:
      # Mount /persist/openvpn/ for the .ovpn cred file
      - /persist/openvpn/:/persist/openvpn/
```

The important settings being configured here are

- `network_mode: host`

which will map the CORE I/Os host networking to the container and

- `volumes: - /persist/openvpn/:/persist/openvpn/`

which will mount the OpenVPN credentials file into our container.

## kickoff.sh

Create the following file as our entry point into the container. The primary function being performed here is to start the OpenVPN client and provide debugging to the console should something fail unexpectedly.

```sh
#!/bin/sh

echo "Kicking OpenVPN client extension"
openvpn /persist/openvpn/*.ovpn
echo "We've crashed or could not locate the .ovpn file under /persist/openvpn/"
echo "Please scp the .ovpn file to /persist/openvpn/*.ovpn and try again"
```

### Create or include the following files for our extension

- manifest.json

```sh
{
  "description": "OpenVPN Client",
  "version": "3.2.0",
  "icon": "icon.png",
  "images": ["openvpn_client.tar.gz"]
}
```

- icon.png

Include an image as the extension icon. Name the image icon.png. This will act as the icon for our extension. This parameter is optional.

## Build The Extension

If building on a host system architecture that is not ARM64 based the following will need to be run before continuing.

```sh
sudo apt-get install qemu binfmt-support qemu-user-static
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

Installing and running qemu will allow us to build ARM binaries on an x86 machine without needing a cross compiler.

### Run the following from the folder containing all of the above files to build and output the OpenVPN extension

```sh
#!/bin/bash -e

SCRIPT=${BASH_SOURCE[0]}
SCRIPT_PATH="$(dirname "$SCRIPT")"
cd $SCRIPT_PATH

# Builds the image
docker build -t openvpn_client -f Dockerfile .

# Exports the image, uses pigz
docker save openvpn_client | pigz > openvpn_client.tar.gz

tar -cvzf openvpn_client.spx \
    openvpn_client.tar.gz \
    manifest.json \
    docker-compose.yml \
    icon.png

# Cleanup intermediate image
rm openvpn_client.tar.gz
```

## Running the Extension

The output file will be called openvpn_client.spx and can be uploaded to a CORE I/O. See [extension documention](docker_containers#install-extension-using-web-portal) for directions on uploading extension to the CORE I/O using the web portal.
**The cred.ovpn file must be provided by the user and placed under /persist/openvpn/\*.ovpn to work.**

To copy over the cred file to the robot over ethernet or wifi run the following.

```sh
scp -P 20022 ${your_cred_file.ovpn} spot@${spots_ip}:~/
ssh -p 20022 spot@${spots_ip}
sudo mkdir -p /persist/openvpn/
sudo cp ~/${your_cred_file.ovpn} /persist/openvpn/
```
