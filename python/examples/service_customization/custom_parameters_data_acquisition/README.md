<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Custom Parameter Data Acquisition

This example programs demonstrate how to create a data acquisition plugin service with custom parameters and run the service such that it can communicate with the data acquisition service on-robot. A data acquisition plugin service is used to communicate with external payloads and hardware, retrieve the data from these sensors, and save the data in the data acquisition store service. The custom parameters enable developers to add user inputs to the actions.

This example is mostly a copy of the [Data Acquisition Service ](../../data_acquisition_service/README.md). However in this example, the data acquisition contains custom parameters that enable clients to add user input and extract the input from the request.

This example can be run on an external computer.

## Prerequisites

This example requires bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Example Execution

This example will run the data acquisition service locally and register it with the robot's directory service using a directory keep alive. After running the example, clients will be able to send requests to this service through the robot.

To run the example from this directory on an external computer, issue the command:

```
python3 daq_plugin_custom_params.py --host-ip {COMPUTER_IP} {ROBOT_IP}
```

The example can be safely exited by issuing a SIGINT (Ctrl + C) to the caller.

This example takes two different IP addresses as arguments. The `--host-ip` argument describes the IP address for the computer that will be running the data acquisition plugin service. A helper exists to try to determine the correct IP address. This command must be run on the same computer that will be running the plugin service:

```
python3 -m bosdyn.client {ROBOT_IP} self-ip
```
