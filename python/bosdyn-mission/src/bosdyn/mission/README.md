<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Python Mission

Client code and interfaces missions.

## Contents

- [Client](client)
- [Constants](constants)
- [Exceptions](exceptions)
- [Remote Client](remote_client)
- [Server Util](server_util)
- [Util](util)

## RPC Clients

The table below specifies the protobuf service definitions supported by each client.

|                 Client                 |                                     RPCs Supported                                      |
| :------------------------------------: | :-------------------------------------------------------------------------------------: |
|    [**MissionClient**](./client.py)    | [mission_service.proto](../../../../../protos/bosdyn/api/mission/mission_service.proto) |
| [**RemoteClient**](./remote_client.py) |  [remote_service.proto](../../../../../protos/bosdyn/api/mission/remote_service.proto)  |
