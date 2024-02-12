<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# E-Stop Service

The "estop" service uses a heartbeat-based, software-implemented service to help guarantee a communications link between one or more off-robot host machines. In 3.2 and earlier, the robot will not allow the motors to be powered without properly setting up this service. In 3.3, it's possible to operate the robot WITHOUT involving this service.

In short, one or more pre-determined clients must confirm that they can talk to the robot by sending a special message. In the parlance of the service, one or more Endpoints that have been Registered against the Configuration must send CheckIn messages.

Clients can set one of the following "stop levels":
 - `CUT` -- actuator power is cut immediately.
 - `SETTLE_THEN_CUT` -- the robot attempts to come to a stop, sit down, and then cut actuator power.
 - `NONE` -- no stop level. Actuators are allowed to power on. This does NOT turn the actuators on.

The setup happens over the course of several steps: Configuration, Registration, and CheckIn. Once all registered endpoints have checked in, actuators can be powered on.

The Python library takes care of these steps for you. See the E-Stop example in [`estop_nogui` example](../../python/examples/estop/README.md) and the client implementation in [`bosdyn/client/estop.py`](../../python/bosdyn-client/src/bosdyn/client/estop.py) for an example usage and implementation.

## Configuration

The client sending the `SetEstopConfigRequest` is saying "This is the exact number of endpoints I expect to exist, and how often they must check in." Endpoints in the configuration have two important values they must fill out:

1) role
2) timeout

See the protobuf's documentation for more details.

There are some limitations on the configuration:

1) In 3.2 and earlier, there must be exactly one Endpoint with a role set to `PDB_rooted`. In 3.3 and later, it is also acceptable to have a configuration without any Endpoints.
2) The `PDB_rooted` Endpoint must have a `timeout` of 65530 seconds or less.

The `PDB_rooted` endpoint has its communications verified in the firmware, which is why it has special requirements on its configuration.

Once the configuration is set, the robot waits for individual endpoints to register themselves. In the simplest case, a client will set a configuration with one endpoint.

*By setting a configuration, any currently registered endpoints are forgotten about. This means the robot will behave as if the CUT stop level was sent by a client*

## Registration

One or more clients must now send one or more `RegisterEstopEndpointRequest` messages. The request must specify `target_endpoint.role`, as well as the relevant fields in `new_endpoint`. See the protobuf's documentation for more details.

In the simplest case, the same client that sent the configuration with a single endpoint will immediately register itself as that endpoint.

## CheckIn

A registered endpoint can now send an `EstopCheckInRequest`. Each such request contains a `challenge` and a `response`, to help guarantee a live communications link between the robot and a responsive client. The `response` must be the 1's compliment of the provided `challenge`.

The `EstopCheckInResponse` received by the client will have a new `challenge` that should be responded to.

The first check-in sent by an endpoint will not have a valid challenge/response pair, so the first response will provide a `INCORRECT_CHALLENGE_RESPONSE` status, but it can be safely ignored.

If an incorrect challenge/response pair is received by the server, that check-in does not reset the timeout.

## Operation

The E-Stop service will allow actuators to be powered on as long as the following conditions are met:

1) There is a valid configuration
1) All endpoints in the configuration have been registered
1) All registered endpoints have checked in with the NONE stop level
1) The number of seconds between each endpoint's previous check-in and now is less than each endpoint's timeout
