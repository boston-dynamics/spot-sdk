<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Using the Log Status Service

This example program demonstrates how to query the log status service.

## Setup Dependencies

This example requires the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Example commands

Examples of commands that can be run with the `log-status` client:

```

python3 log_status.py ROBOT_IP get $LOG_ID

python3 log_status.py ROBOT_IP active

python3 log_status.py ROBOT_IP experiment timed $DURATION_IN_SECONDS

python3 log_status.py ROBOT_IP experiment continuous

python3 log_status.py ROBOT_IP retro $DURATION_IN_SECONDS

python3 log_status.py ROBOT_IP terminate $LOG_ID

```
