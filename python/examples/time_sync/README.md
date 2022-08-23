<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Using the Timesync Service

This example demonstrates how to use the timesync service to establish time sync between your computer and the robot's clock. Specifically, it creates a TimeSyncEndpoint, which can be used to establish timesync as well as determine the clock skew or round trip time.

## Setup Dependencies

This example needs to be run with python3, and have the Spot SDK installed. See the requirements.txt file for a list of dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Running the Example

To run the examples:

```
python3 time_sync_client.py ROBOT_IP
```
