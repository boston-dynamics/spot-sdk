<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Logging Through the API

This example program demonstrates the different methods of logging for Spot that application programs can use. It uses the annotation logging service to log text messages, operator comments, and blob logs (serialized protobuf messages).

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Run the Example

To run the example:

```
python3 log_spot_data.py ROBOT_IP
```
