<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Upload and Execute Choreography Sequence

This example shows how to use the Choreography service to upload an existing choreographed sequence to the robot, and have the robot execute that uploaded routine. The terminology and the api for the choreography service is described further in the [Choreography Service documentation](../../../docs/concepts/choreography/choreography_service.md).

## E-Stop

You will have to launch a software E-Stop separately in order to run this example. See [the E-Stop examples](../estop/README.md) from the Spot SDK or use the tablet as the estop.

## Setup Dependencies

This example needs to be run with python3, and have the Spot SDK installed. See the requirements.txt file for a list of dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Run the Example

To run the example:

```
python3 upload_choreographed_sequence.py ROBOT_IP
```

There is an optional argument `--choreography-filepath` which can be used to pass an absolute (or relative) filepath to a choreographed routine that is saved as a protobuf text file. If this argument is not provided, then the example program will use the default_dance.csq file as the choreographed sequence to be loaded to the robot.
