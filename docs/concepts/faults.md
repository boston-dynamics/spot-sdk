<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Faults

Spot is a carefully designed and well-engineered device, but it is still likely to encounter a few unexpected issues while in the field. When an issue arises, either on or off of the robot, faults may be raised to inform the operator, developers, and other devices.

## Fault Types
There are multiple different types of faults that are associated with different categories of problems. Each type of fault is grouped independently and can be accessed through the [robot state](../../protos/bosdyn/api/robot_state.proto).

### System Faults
System Faults indicate a hardware or software fault on the robot. They include an error code and message, and can inform a user about anything from a perception fault with a certain camera to a battery overheating. They will be raised by internal robot systems when they are encountered and will appear in the robot state and on the tablet. Resolving these faults will require following up on the specific issue outlined by the error code and message.

### Behavior Faults
Behavior Faults track faults related to behavior commands and issue warnings if a certain behavior fault will prevent execution of subsequent commands. Behavior faults include an idn a cause, and clearable status. Clearable behavior faults can be cleared via the robot command service, accessible through the [robot command client](../../python/bosdyn-client/src/bosdyn/client/robot_command.py) provided in the Spot Python SDK. Behavior faults will appear in the robot state and on the tablet.

### Service Faults
Third party payloads and services may encounter unexpected issues on hardware or software connected to Spot. External Service Faults are able to be reported and cleared via the API fault service, accessible through the [fault client](../../python/bosdyn-client/src/bosdyn/client/fault.py) provided in the Spot Python SDK. These faults can be associated with an API service, a registered payload, or both. All other consumers of the API will be able to view the externally raised faults and determine how they might respond to different errors.

Service Faults also enable payload and service liveness monitoring. A payload or service registering with the robot can opt in by setting a liveness timeout at registration time. After registration, the external device must maintain liveness by repeatedly issuing heartbeats to the robot. If a payload or service times out the robot will automatically raise a service Fault on behalf of the external device. This system is made easier to implement by the payload and directory keep alive classes provided in the Python SDK.
