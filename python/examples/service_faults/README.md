<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Handling Service Faults

This example program demonstrates how to trigger, clear, and display service faults. Additionally, it shows how to take advantage of the directory liveness
system to enable automatic faulting when a service crashes or fails to maintain liveness.

## Setup Dependencies

This example requires the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Running the Example

To run the example:

```
python3 service_faults.py --guid GUID --secret SECRET ROBOT_IP
```

OR

```
python3 service_faults.py ROBOT_IP

```

In addition to the standard arguments, the example program takes command line arguments `--guid` and `--secret`, which can be used to operate this example as if it were running on a payload. This allows the user to bypass the need for robot user credentials and will allow Spot to automatically associate faults with their host payload. Note that this must be a GUID and secret of a registered and authorized payload on Spot. See documentation on [configuration of payload software](../../../docs/payload/configuring_payload_software.md#Configuring-and-authorizing-payloads) for more information.
