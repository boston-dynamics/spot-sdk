<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Using the Payload Service

This example program demonstrates how to create a payload and register this new payload with the payload service. As well, the example program shows how to list all payloads registered with Spot's payload service, which should include the newly registered payload created in the example.

## Setup Dependencies
This example requires the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Running the Example
To run the example:
```
python3 payloads.py --username USER --password PASSWORD ROBOT_IP
```
