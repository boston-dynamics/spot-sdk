<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Comms Testing

This example demonstrates how to use the SDK to perform comms testing.
This is meant to be run on a CORE I/O during an Autowalk mission.

## Setup Dependencies

This example needs to be run with python3, and have the Spot SDK installed. See the requirements.txt file for a list of dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Running the Example

To run the example:

On the server computer. Note that the server computer should not be associated with controls for the robot. The networks tests may behave in a way that limits controls communications to the robot.:
Setup:

```
sudo apt update
sudo apt install iperf3
```

Running:

```
iperf3 -s
```

On the CORE I/O running the client (from the CORE I/O, ROBOT_IP will always be 192.168.50.3):
Run:

```
python3 client.py ROBOT_IP --server-hostname SERVER_IP
```

Specifying a UDP test:

```
python3 client.py ROBOT_IP --protocol udp --server-hostname SERVER_IP
```

Specifying a different iperf3 server port:

```
python3 client.py ROBOT_IP --server-port 1234 --server-hostname SERVER_IP
```

Running the test without running an Autowalk mission:

```
python3 client.py ROBOT_IP --server-hostname SERVER_IP --run-without-mission
```

### Running with Docker

Alternatively, this example can be run with Docker. To do so, just build and run the image.
If you are building on a separate machine, you'll also need to import the image to the CORE I/O, or package it as a Spot Extension.

Build and saved the image for CORE I/O:

```
sudo docker build -t comms_test:l4t --platform linux/arm64 .
sudo docker save comms_test:l4t | pigz > comms_test_l4t.tgz
```

Copy the image file to the CORE I/O and load it with the command:

```
sudo docker load -i comms_test_l4t.tgz
```

Run the image:

```
sudo docker run -it -v $(pwd):/comms_out/ --network host comms_test:l4t ROBOT_IP --server-hostname SERVER_IP
```

which will ask for username/password, or pass the environment variables `--env BOSDYN_CLIENT_USERNAME --env BOSDYN_CLIENT_PASSWORD` to the command above.

The argument `-v $(pwd):/comms_out/` allows the Docker container to save files to the current directory, so the resulting csv output file will be in the directory you just ran from. For different configurations of the comms test, see above.
