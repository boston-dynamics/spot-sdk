<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Python Mission

Client code and interfaces missions.

## Contents

* [Client](client)
* [Constants](constants)
* [Exceptions](exceptions)
* [Remote Client](remote_client)
* [Server Util](server_util)
* [Util](util)

## RPC Clients
The table below specifies the protobuf service definitions supported by each client.

| Client | RPCs Supported  |
|:------:|:-------------:|
| [**MissionClient**](client) | [mission_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#mission-mission-service-proto) |
| [**RemoteClient**](remote_client) | [remote_service.proto](../../../../../protos/bosdyn/api/proto_reference.html#mission-remote-service-proto) |
