<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Using the Payload Service

These example programs demonstrate how to use the payload service.

The payload.py example demonstrates how to create a payload and register this new payload with the payload service, and also how to list all payloads registered with Spot's payload service. The list should include the newly registered payload created in the example.

The attach_detach_payload.py example demonstrates how to tell the robot that a payload is attached or detached through the service. This can also be done via the webserver. This is particularly useful if you are attaching and removing payloads from the robot while the robot is working (like picking up a sensor in the gripper), and you'd like to inform the robot of the updates programmatically.

## Setup Dependencies

These examples require the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Running the Payload Registration Example

Because payloads must have unique GUIDs and secrets per robot, this example creates and persist these into a "payloads-credentials-file" for each payload. Simply choose a writeable, unique filename where you would like this to be stored upon first-time payload registration, and future registrations will reuse these credentials. If building a CORE I/O extension, we suggest writing this to a subdirectory of /data or /persist and mounting that file to your Extension's Docker container.

To run the payload registration example:

```
python3 payloads.py ROBOT_IP --payload-credentials-file-1 <credentials-filename-1> --payload-credentials-file-2 <credentials-filename-2>
```

## Running the Attach or Detach Payload Example

A payload must be registered and authorized before it can be attached and detached over the API.

1. Register a payload, e.g. using the above example. When you register the payload, save the GUID and secret that you choose for the payload. In the above example, these are set to variable names `payload.GUID` and `payload_secret`.
2. Use the Spot webserver to "authorize" the payload. Open up the webserver, select the 'Payloads' tab, then click 'authorize' for the payload you wish to authorize. If a payload has multiple presets associated with it, you will be prompted to select a preset before authorizing.
3. Run the example with one of the following calls, passing the path to one of the payload credentials files from the above payload registration example.:

To attach the payload, run:

```
python3 attach_detach_payload.py ROBOT_IP --payload-credentials-file <credentials-filename> --attach
```

To detach the payload, run:

```
python3 attach_detach_payload.py ROBOT_IP --payload-credentials-file <credentials-filename> --detach
```
