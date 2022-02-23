<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Fire Extinguisher Detector Server

This is an example of a network compute bridge server. It is similar to tensorflow_server.py, but uses Keras Retinanet instead of TensorFlow. The provided model specifically detects fire extinguishers 


## Build and Export
This example can be run on a local machine directly, but is easier to use with Docker.

The Docker image can be built and exported with the following commands:

```
# builds the image
sudo docker build -t fire_ext_detector .

# exports the image, uses pigz
sudo docker save fire_ext_detector | pigz > fire_ext_detector.tar.gz
```


## Execution
To run this example on a Spot CORE, run:

```
./start_server.sh
```

Otherwise, run:

```
sudo docker run -d --name retinanet_server --network host --env BOSDYN_CLIENT_USERNAME --env BOSDYN_CLIENT_PASSWORD --restart unless-stopped fire_ext_detector -d . --port $PORT $ROBOT_IP
```

- `$PORT` is the port to use for the server on the machine the server is running on
- `$ROBOT_IP` is the IP address or hostname of your Spot.
- `$USERNAME` is the username for the robot
- `$PASSWORD` is the password for the robot
