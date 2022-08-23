<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Performing Asynchronous State Queries on Spot

This example program demonstrates how to query the robot state service using wait-until-done, block-until-done, and callback-when-done. Please look at the code to see how each asynchronous query is accomplished.

## Setup Dependencies

This example requires the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Running the Example

To run the example:

```
python3 get_robot_state_async.py ROBOT_IP
```
