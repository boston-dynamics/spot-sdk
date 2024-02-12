<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Reset Safety Stop Command with the Python SDK

This example provides basic Python scripts to reset the primary and redundant safety stops on a robot configured for Safety-Related Stopping Function (SRSF). Robots equipped with this feature will be listed as Safety-Related Stopping Function (SRSF) "Enabled" under the hardware information section found in the "About" page on the robot's admin console.

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Using the Reset Safety Stop Command

All reset safety stop commands request the robot to reset the safety stop bit on a SRSF configured robot (either primary or redundant). The command requires the client to own the body lease to take effect.

All reset safety stop commands return header information, lease information, and a status. A reset safety stop command should return one of three immediate statuses:

1. STATUS_OK: Indicates that the robot accepted the reset safety stop command and executed it
2. STATUS_INCOMPATIBLE_HARDWARE_ERROR: Indicates that at the time the command was received, the robot was not configured for SRSF.
3. STATUS_FAILED: Indicates that the command was run and executed with an error.
4. STATUS_UNKNOWN_STOP_TYPE: Indicates that the command failed due to an unknown stop type in the request.

## Running The Reset Safety Stop Examples

### General Reset Safety Stop Usage

Using the reset safety stop commands in Python begins with the establishment of a Power Client, generally through something like

```
power_client = robot.ensure_client(PowerClient.default_service_name)
```

Once this is established, one can use `power_client.reset_safety_stop(safety_stop_type=power_pb2.ResetSafetyStopRequest.SAFETY_STOP_REDUNDANT, lease=None)` to issue a reset redundant safety stop command or `power_client.reset_primary_safety_stop(safety_stop_type=power_pb2.ResetSafetyStopRequest.SAFETY_STOP_PRIMARY, lease=None)` to issue a reset primary safety stop command, where the lease can be passed through context such as a LeaseKeepAlive.

### Reset Primary Safety Stop Example

To run the Reset primary safety stop example, run:

```
python3 reset_primary_safety_stop.py ROBOT_IP
```

Out of the box, this example issues a command that resets the primary safety stop bit on a SRSF configured robot.

### Reset Redundant Safety Stop Example

To run the reset redundant safety stop example, run:

```
python3 reset_redundant_safety_stop.py ROBOT_IP
```

Out of the box, this example issues a command that resets the redundant safety stop bit on a SRSF configured robot.
