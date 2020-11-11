<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# API Example - Comms Testing
This example demonstrates how to use the SDK to perform comms testing.
This is meant to be run on a Spot CORE during an Autowalk mission.

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

On the Spot CORE running the client:
Run:
```
python3 client.py --username USER --password PASSWORD 192.168.50.3 --protocol tcp --server-port 5201 --server-hostname 127.0.0.1
```

### Running with Docker
Alternatively, this example can be run with Docker. To do so, just build and run the image.
If you are building on a separate machine, you'll also need to import the image to the CORE.

Build the image:
```
sudo docker build -t comms_test .
```

Run the image:
```
sudo docker run comms_test --username USER --password PASSWORD 192.168.50.3 --protocol tcp --server-port 5201 --server-hostname 127.0.0.1
```