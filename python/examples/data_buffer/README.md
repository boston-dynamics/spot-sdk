<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Using the Data Buffer service

The Data Buffer service can be used to log data to the robot which can later be retrieved via API calls to the [Data Service](../data_service/README.md) or by [bddf-download](../bddf_download/README.md). This example shows how to log various kinds of data to robot.

## Setup Dependencies

This example requires the bosdyn API and client to be installed, and must be run using python3. Using pip, these dependencies can be installed using:

```
python3 -m pip install -r requirements.txt
```

## Running the Example

The example requires that you specify a username and password to authenticate with the robot.

### Add an 'operator comment' to the log

This example adds an operator comment to the robot log. This comment will show up in the comments list in the robot log download web page.

```
python3 data_buffer.py HOSTNAME operator 'This is a test of the Data Buffer client.'
```

### Add 'blob' data to the log

This example adds a serialized protobuf to the log using the `add_blob()` method of the Data Buffer client.

```
python3 data_buffer.py HOSTNAME blob
```

### Add 'protobuf' data to the log

This is similar to the 'blob' data example, but it serializes the protobuf automatically and sets the message type from the full protobuf type name.

```
python3 data_buffer.py HOSTNAME protobuf
```

### Add an event to the log

This writes an example event into the log.

```
python3 data_buffer.py HOSTNAME event
```
