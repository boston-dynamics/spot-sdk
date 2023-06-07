<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Faults

Spot is a carefully designed and well-engineered device, but it is still likely to encounter a few unexpected issues while in the field. When an issue arises, either on or off of the robot, faults may be raised to inform the operator, developers, and other devices.

There are multiple different types of faults that are associated with different categories of problems. Each type of fault is grouped independently and can be accessed through the [robot state](../../protos/bosdyn/api/robot_state.proto).

## System Faults
System Faults indicate a hardware or software fault on the robot. They include an error code and message, and can inform a user about anything from a perception fault with a certain camera to a battery overheating. They are raised by internal robot systems when they are encountered and appear in the robot state and on the tablet. Resolving these faults requires following up on the specific issue outlined by the error code and message.

## Behavior Faults
Behavior Faults track faults related to behavior commands and issue warnings if a certain behavior fault will prevent execution of subsequent commands. Behavior faults include an ID, a cause, and clearable status. Clearable behavior faults can be cleared via the robot command service, accessible through the [robot command client](../../python/bosdyn-client/src/bosdyn/client/robot_command.py) provided in the Spot Python SDK. Behavior faults appear in the robot state and on the tablet.

## Service Faults
Third party payloads and services may encounter unexpected issues on hardware or software connected to Spot. External Service Faults are able to be reported and cleared via the API fault service, accessible through the [fault client](../../python/bosdyn-client/src/bosdyn/client/fault.py) provided in the Spot Python SDK. These faults can be associated with an API service, a registered payload, or both. All other consumers of the API are able to view the externally raised faults and determine how they might respond to different errors.

Service Faults also enable payload and service liveness monitoring. A payload or service registering with the robot can opt in by setting a liveness timeout at registration time. After registration, the external device must maintain liveness by repeatedly issuing heartbeats to the robot. If a payload or service times out the robot automatically raises a Service Fault on behalf of the external device. The payload and directory keep-alive classes provided in the Python SDK simplify this process.

### Service Fault Guidelines
Unlike system faults and behavior faults, API users are collectively responsible for raising, managing, and reacting to Service Faults. It is important to consider that the application you are writing may not be the only API user of a Spot. To ensure that all developers are able to take advantage of the fault system some guiding principles are laid out here.

**Associate faults correctly**
Associating new faults as precisely as possible enables them to be useful to other services and payloads that may be watching for faults in certain areas. If your fault is related to a specific service on your payload (e.g. crashed service, failure to retrieve data), the service name field should be populated. Otherwise, if the fault pertains to the payload at large (e.g. hardware failures, overheating) then the service name field should be left empty and the payload GUID should be set. When the service name is populated and the payload GUID is empty, the Fault Service automatically populates the payload information based on where the service is running.

**Clear owned faults**
A service or payload should clear any Service Faults they may have raised once the issue has been resolved. Leaving faults behind may result in long-lived and unnecessary fault that affects other users.

**Do not clear unknown faults**
Faults associated with a payload or a service that are outside of an application, it should not be arbitrarily programmatically cleared. Instead, an operator or developer should address the problem directly and determine if it can be resolved properly or ignored.

**Only react to faults of relevance**
Faults that are not relevant to an application should be ignored. This may not always be obvious, but the Fault ID's service name or payload GUID may indicate if the fault is pertinent.

**Do not spam the fault service**
Applications that fill up the fault service with many faults that relate to the same issue make it difficult for an operator to identify what the root cause is and other issues may be lost in the noise. To prevent this, developers should only raise a single fault per issue. Faults raised with a fault ID that matches an already active fault are safely ignored.

**Use liveness timeouts and keepalives**
The Spot Python SDK provides both payload and directory keepalive classes. These keepalives make it easy to implement liveness checks and maintain regular heartbeats with Spot. Having liveness monitoring in the background improves the reliability of your applications with minimal effort required. The code snippet below demonstrates how a directory keepalive can be implemented with relative ease.
```
dir_reg_client = robot.ensure_client(DirectoryRegistrationClient.default_service_name)
keep_alive = DirectoryRegistrationKeepAlive(dir_reg_client)
keep_alive.start(DIRECTORY_NAME, SERVICE_TYPE, AUTHORITY, HOST_IP, PORT)
```

**Remember auto clearing**
It is important to keep in mind that all faults associated with a service are cleared at directory registration time. This prevents unknown faults from previous instances living on forever. Specifically, if a fault is raised in the initialization of a server, before it is registered with the robot, service registration should be blocked or the fault should be associated with the payload and not the service.

**Maintain fault IDs**
In most cases, fault IDs are constant. A single fault ID should represent one possible issue that may occur in an application, even if the description of the issue varies. It is good practice to define all possible fault IDs at the beginning of your program. The pre-defined fault IDs can then be attached to a full fault and raised if needed or can be used to clear previous instances of that fault ID that may have been raised.
