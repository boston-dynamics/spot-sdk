<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Base Services

This document assumes knowledge of material covered in the SDK documentation on [networking](networking.md).

Base Services provide the architectural glue used by the rest of the Spot API. These services include authentication, service discovery, and time synchronization. Many applications will use the Base Services when starting up, and before using services higher in the stack such as Robot State, Robot Commands, and Autonomy.

## robot-id

The `robot-id` service provides metadata about the Spot robot. It is usually the first service accessed when bootstrapping a connection to Spot. The metadata is encoded in a `RobotId` message, as shown below:

```protobuf
/// Robot identity information, which should be static while robot is powered-on.
message RobotId {
    /// A unique string identifier for the particular robot.
    string serial_number = 1;

    /// Type of robot.  E.g., 'spot'.
    string species = 2;

    /// Robot version/platform.
    string version = 3;

    /// Version information about software running on the robot.
    RobotSoftwareRelease software_release = 4;

    /// Optional, customer-supplied nickname.
    string nickname = 5;

    /// Computer Serial Number. Unlike serial_number, which identifies a complete robot,
    ///  the computer_serial_number identifies the computer hardware used in the robot.
    string computer_serial_number = 6;
}
```

Examples of ways applications can use the `robot-id` include:

- Displaying the robot `nickname` in a list of possible Spot robots to connect to. Note that the same Spot can change `nickname` over time. Multiple Spots can share the same nickname.
- Using the `serial_number` as a key for cached username/passwords or other data about the robot. `Serial_number` will never change over time, and is guaranteed to be unique.
- Checking the `software_release` version to determine if the application is compatible with Spot, or to change behavior depending on Spot software version.

Unlike nearly all other services, the `robot-id` service does not require an authenticated user to access it. This is because the `RobotId` data includes information that can be helpful for the authentication sequence, such as the software version or a serial number that can help find user credentials.

## auth

The `auth` service is used to authenticate a user to Spot. A successful authentication attempt returns a user token that must be included in RPCs to all services other than `robot-id` and `auth` to get access. The user token is a [JWT](https://jwt.io) token that is valid for 12 hours and can only be used for accessing services on the robot that issued it. The token isn’t transferable to other robots.

There are two ways to authenticate a user:

1. With a username and password combination. The usernames and passwords are the same as those managed using the robot's admin console web page.
2. By refreshing an existing valid user token. This approach can be used to support a long-lived client application to minimize repeated prompts for username/password.

The `auth` service rate-limits invalid authentication attempts to prevent a network attacker from trying to guess users or passwords. After six consecutive failed authentication attempts, authentication is locked out for 1 minute. `STATUS_TEMPORARILY_LOCKED_OUT` is returned in this case.

## directory

Spot’s API consists of a variety of services. Some of these services ship with Spot. Some services are provided by payloads or applications running on CORE I/O. The `directory` service is used to discover which services are currently running on Spot.

Note that if an application is built with the Python client library only uses built-in services, it may never need to access the `directory` service. However, the Python client library uses the `directory` service to set up connections to the built-in services.

Services are described by the `ServiceEntry` message, and can be listed using the `ListServiceEntries` RPC. The command-line utility included in the Python library is a quick way to list these options, as shown below.

```
$ py.exe -3 -m bosdyn.client my-spot dir list
name                        type                                      authority               tokens
----------------------------------------------------------------------------------------------------
auth                        bosdyn.api.AuthService                    auth.spot.robot
directory                   bosdyn.api.DirectoryService               api.spot.robot          user
directory-registration      bosdyn.api.DirectoryRegistrationService   api.spot.robot          user
estop                       bosdyn.api.EstopService                   estop.spot.robot        user
graph-nav-service           bosdyn.api.graph_nav.GraphNavService      graph-nav.spot.robot    user
```

The `name` of the service is a user friendly name which provides some semantic information about what the service can do. The name must be unique across all services. For example, `auth` is the name of the service which provides authentication.

The `type` of the service is the gRPC service interface that the service implements. For example, `bosdyn.api.AuthService` is the `type` of the `auth` service. Multiple services can exist for the same type (although with different names and authorities). For example, a camera payload could host a `bosdyn.api.ImageService` which shares the same interface as the one built into Spot.

The `authority` is used to direct the RPC request to the correct service. The combination of the `authority` and the `type` of the service creates a URL. For example, the `auth` service has the URL: `https://auth.spot.robot/bosdyn.api.AuthService` This naming scheme is defined by gRPC itself. All authorities must be of the form `<authority-name>.spot.robot`. Multiple services of different types can share the same authority.

Services specify whether a user token is needed to access the service. This is demonstrated in the `tokens` column in the example above. Most services require a signed in user, but a few do not.

Note that not all services register with the `directory` service at Spot startup. Applications may need to periodically poll the `directory` service to catch changes that have been made. Built-in services may take a few seconds to register at system startup. Payload-provided services may register significantly later.

## time-sync

Time is critical for both interpreting when sensor data was recorded as well as for commanding Spot. The Spot API uses a single clock known as “Robot Time” as a basis for time commands.

Spot’s clock may not be the same as the application’s clock. For example, at a single point in time Spot may think it is 16:01, whereas the application’s clock may be an hour behind at 15:01. If the application treated Spot’s clock as being at the same time as its own clock, problems may result. Fresh sensor data from Spot would be interpreted as being generated in the future. Commands that are issued to expire in 10 seconds would be rejected by Spot since they would appear to have expired.

The `time-sync` service is used to estimate the offset between the application’s clock and Spot’s clock. Each `TimeSyncUpdate` RPC provides send and receive timestamps which form a single measurement. Initially the offset is unknown. It is initialized after several consecutive and consistent measurements are observed. Once an offset is calculated, applications can convert times recorded in Spot’s clock to the application’s clock and vice-versa. The offset is slowly updated to account for clock drift.

Applications built with the Python library can use the `TimeSyncThread` to simplify interaction with the `time-sync` service. The `TimeSyncThread` spawns a background thread which establishes an initial offset estimation, and periodically updates the estimation to avoid drift issues. It also exposes a number of methods to convert time or determine what the current estimate is. See the [`time_sync` example](../../python/examples/time_sync/README.md) for an example of how to use the `TimeSyncThread`.

This estimate is purely at the application layer. This is important for two reasons:

- Neither Spot’s clock nor the application's clock are adjusted, admin/root permissions are not needed.
- A client may connect to multiple Spot robots that are not synchronized to each other.

Clients needing high precision timing, such as a payload sensor collecting data while the robot is moving, should instead use NTP to synchronize to the robot.

## lease

The lease service provides methods to achieve ownership over controlling the robot and maintaining valid communication with that owner.

The lease is required to issue commands that control the robots mobility and motion, such as powering on the robot or commanding stand. To start, the lease must be acquired (or taken) to show ownership of the robot resources. Then retain lease signals must be sent throughout the duration of the operation to preserve ownership and indicate reliable communication with the lease owner. Ultimately the lease should be returned to free the resources to be reclaimed; however, it can be revoked during operation by another user or if the communication signals are not received within a certain period of time.

The [Lease documentation](lease_service.md) provides a more in-depth description of leases, typical lease usage, and how to understand lease errors.
