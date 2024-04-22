<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Payload Software Interface

To log payload data and debug payload issues, payloads developed for the Spot platform should observe the following guidelines:

- Payloads gather and generate their own log data.
- Payloads generate and send their own text annotations to mark robot logs for preservation.
- Each payload component provides access to its own debug data.
- Logic on the payload determines what data to log and when to log it.

## Payload API services

The API provides two services for managing and registering payloads and payload services:

- PayloadService
- PayloadRegistrationService

Robot directory services are used to register services that a payload might offer so that they can be exposed on the robot.

- DirectoryService
- DirectoryRegistrationService

## Service and Payload Faults

The Fault Service enables external clients to raise service faults, which can be read by external clients via the robot state and are automatically displayed in the tablet. Service faults are a type of fault that can originate from both on the robot and external clients. Each service fault is associated with a service, a payload, or both.

Service faults enable services and payloads to easily display information about current systems health to operators. The faults should assist operators in effective debugging and resolution of any off-robot issues that arise during operation.

The [Fault documentation](../concepts/faults.md) provides more context on the different types of faults that may be used with Spot.

### DirectoryService RPCs

| RPC                | Description                                         |
| ------------------ | --------------------------------------------------- |
| GetServiceEntry    | Get information about a specific service.           |
| ListServiceEntries | List all known services at the time of the request. |

### DirectoryRegistrationService RPCs

| RPC               | Description                                                                           |
| ----------------- | ------------------------------------------------------------------------------------- |
| RegisterService   | Called by a system to announce, via the robot directory, a new service it is hosting. |
| UnregisterService | Called by a system to deregister a service from the robot directory.                  |
| UpdateService     | Update the ServiceEntry for a system hosting a service.                               |

### PayloadService RPCs

| RPC          | Description                                                  |
| ------------ | ------------------------------------------------------------ |
| ListPayloads | Query the robot for a list of currently-registered payloads. |

### PayloadRegistrationService RPCs

| RPC                 | Description                              |
| ------------------- | ---------------------------------------- |
| RegisterPayload     | Register a new payload with the robot.   |
| GetPayloadAuthToken | Get an auth token to enable the payload. |

## Time Synchronization

Spot hosts an NTP server for time synchronization purposes. This is especially useful for high precision timing, such as a payload sensor collecting data while the robot is moving (e.g. lidar).

If you wish to use this to synchronize a computing payload, such as a CORE, then here is an example of a one-line config file (typically saved as /etc/ntp.conf):

```
server 192.168.50.3 iburst minpoll 3 maxpoll 3
```

The NTP server and Spot's internal clock are not configurable.

## Registering payloads

This code snippet example uses the API to communicate payload configuration settings to Spot. The example first registers a payload then lists all payloads on the robot, including the newly registered payload.
It involves providing a "secret", which can be thought of as something akin to a password for the payload GUID, which is like a username.
The GUID and secret can be any string, but we typically recommend that both be at least 12 digits. A Version 4 UUID would work for this.
The "read_or_create_payload_credentials" helper function allows you to autogenerate these values per-robot and save them to a file. These values can thereafter be used for re-registering the same payload to the robot or as credentials once the payload has been authorized.

    ...
    # Authenticate robot before being able to use it
    bosdyn.client.util.authenticate(robot)

    # Create a payload registration client
    payload_registration_client = robot.ensure_client(
    PayloadRegistrationClient.default_service_name)

    # Create a payload
    payload = payload_protos.Payload()
    payload.GUID, payload_secret = bosdyn.client.util.read_or_create_payload_credentials(
        config.payload_credentials_file_1)
    payload.name = 'Client Registered Payload Ex'
    payload.description = 'This payload was created and registered by the register_payload.py client example.'
    payload.label_prefix.append("test_payload")
    payload.is_authorized = False
    payload.is_enabled = False
    payload.is_noncompute_payload = False

    # Register the payload
    payload_registration_client.register_payload(payload, secret=payload_secret)

    # Create a payload client
    payload_client = robot.ensure_client(PayloadClient.default_service_name)

    # List all payloads
    payloads = payload_client.list_payloads()
    print(payloads)
    ...

Refer to the [Python payload registration code example in the Spot SDK](../../python/examples/payloads/README.md) for details.

## Payload self-registration

The Payload Registration API gives developers the ability to deploy payloads that register themselves with the robot when they power on without the need to store user credentials on the payload.

The payload registration process completes after an admin operator accepts the payload using the robot's admin console. If the payload has registered itself, it should appear in the Payload section of the admin console.

- Payloads can register API services. Example: A LIDAR payload registers RemoteService callbacks to trigger scans during robot missions.
- Payload and service registration do not require robot user credentials.

Once a payload has been authorized, its unique GUID and secret combination can be used as credentials to request a limited-access user token that will grant permission to the auth, directory, robot-state, and directory-registration services. The granted user token will be valid for 12 hours.

### Registration examples

The Spot SDK Python code examples includes payload registration and service registration examples that provide sample scripts, protos, and a list of dependencies: [Self-registration Python code examples in the Spot SDK](../../python/examples/self_registration/README.md).

## Configuring and authorizing payloads

A payload, like any software client, can access the API by using login credentials. However, for self-registration, payloads can complete basic registration and get access to host services without needing to pass hard-coded user credentials.

Instead, a payload is manually authorized by an operator on the admin console Payloads page. To ensure that the payload authorization is not used by malicious payloads, each payload must provide a unique GUID and secret (password) at registration time. The GUID and secret can then be used to request a user token that grants access to the basic components of the API (directory, directory registration, robot-state).

## Payload device network configuration

Users can communicate with the payloads attached to Spot via WiFi (Access Point (AP) or Client Mode) or Ethernet connection. Spot acts a medium when communicating with payloads which is allowed via built-in internal port forwarding rules.

Different payloads require different ports, and since the internal port forwarding cannot be changed, some additional ports are forwarded for development purposes.

The rear ethernet port can be configured to a user-desired IP address via the web interface. By default, the ethernet port IP is set to 10.0.0.3.

Payload devices should use the following network configurations:

 - Spot CORE I/O and Spot EAP 2: 192.168.50.5 (default from Boston Dynamics).
 - Spot CAM: 192.168.50.6 (default from Boston Dynamics).
 - Fluke SV600: 192.168.50.8 (default from Fluke).
 - Netmask: 255.255.255.0.
 - Default gateway will be set to 192.168.50.3.

Ports actively in use and reserved for other payloads can only be used once. For example, attempting to use port 192.168.50.6 for both an attached Spot CAM and another custom payload will cause both payloads to fail.

## Payload port forwarding table

| Description         | Robot port            | Target                     | Protocol |
| ------------------- | --------------------- | -------------------------- | -------- |
| Standard Forwards 1 | 20000 + [22, 80, 443] | 192.168.50.5:[22, 80, 443] | TCP      |
| Fixed Forwards 1    | 21000-22000           | 192.168.50.5:21000-22000   | TCP/UDP  |
| Standard Forwards 2 | 30000 + [22, 80, 443] | 192.168.50.6:[22, 80, 443] | TCP      |
| Fixed Forwards 2    | 31000-32000           | 192.168.50.6:31000-32000   | TCP/UDP  |
| Standard Forwards 3 | 23000 + [22, 80, 443] | 192.168.50.7:[22, 80, 443] | TCP      |
| Fixed Forwards 3    | 23100-23199           | 192.168.50.7:23100-23199   | TCP/UDP  |
| Standard Forwards 3 | 24000 + [22, 80, 443] | 192.168.50.8:[22, 80, 443] | TCP      |
| Fixed Forwards 3    | 24100-24199           | 192.168.50.8:24100-24199   | TCP/UDP  |
| Standard Forwards 3 | 25000 + [22, 80, 443] | 192.168.50.9:[22, 80, 443] | TCP      |
| Fixed Forwards 3    | 25100-25199           | 192.168.50.9:25100-25199   | TCP/UDP  |

Devices on the payload network can reach the robot at 192.168.50.3 via port 443. Devices on the robot network can reach payload services as follows:

1. TCP traffic sent to the robot's IP address on ports 20022, 20080, or 20443 will be forwarded to 192.168.50.5 on ports 22, 80, or 443.
2. TCP/UDP traffic sent to the robot’s IP address on ports 21000-22000 will be forwarded to 192.168.50.5 on that same port.
3. TCP traffic sent to the robot's IP address on ports 30022, 30080, or 30443 will be forwarded to 192.168.50.6 on ports 22, 80, or 443.
4. TCP/UDP traffic sent to the robot on ports 31000-32000 will be forwarded to 192.168.50.6.
5. TCP traffic sent to the robot's IP address on ports 23022, 23080, or 23443 will be forwarded to 192.168.50.7 on ports 22, 80, or 443.
6. TCP/UDP traffic sent to the robot’s IP address on ports 23100-23199 will be forwarded to 192.168.50.7 on that same port.
7. TCP traffic sent to the robot's IP address on ports 24022, 24080, or 24443 will be forwarded to 192.168.50.8 on ports 22, 80, or 443.
8. TCP/UDP traffic sent to the robot’s IP address on ports 24100-24199 will be forwarded to 192.168.50.8 on that same port.
9. TCP traffic sent to the robot's IP address on ports 25022, 25080, or 25443 will be forwarded to 192.168.50.9 on ports 22, 80, or 443.
10. TCP/UDP traffic sent to the robot’s IP address on ports 25100-25199 will be forwarded to 192.168.50.9 on that same port.

Robot port forwards for ports ending in 443, 22, and 80 masquerade, which means they should allow the payload to respond to forwarded traffic to the robot on any of the robot's ports.

All other forwarded ports are purely port forwarded, meaning that packets received by the payload still have the original address of the sender. These port forwards will only connect for hosts on one of the LANs attached to the robot or for hosts located on the default route as configured in the robot network page.

## Configuring payload mass properties

In order to locomote properly, the robot needs to know the physical properties of any payload it is carrying. This includes the center of mass location relative to the base link of the robot, moments of inertia, and other values.

A payload self-registration service is available as part of the Spot SDK.

The following payload configuration table shows configuration values for the rear-mounted CORE I/O EAP payload as they would appear in the robot's admin console GUI.

This table provides a reference when developing a client application using the RegisterPayload RPC to register a Spot payload.

### Position (m)

| Item | Value  | Units |
| ---- | ------ | ----- |
| X    | -0.259 | m     |
| Y    | 0      | m     |
| Z    | 0      | m     |

### Orientation (radians)

| Item  | Value | Units |
| ----- | ----- | ----- |
| Yaw   | 0     | rad.  |
| Roll  | 0     | rad.  |
| Pitch | 0     | rad.  |

### Total mass (kg)

| Item   | Value | Units |
| ------ | ----- | ----- |
| &nbsp; | 3.11  | kg    |

### Position of Center of Mass (m)

| Item | Value  | Units |
| ---- | ------ | ----- |
| X    | -0.156 | m     |
| Y    | 0      | m     |
| Z    | 0.071  | m     |

### Moment of inertia tensor (kg-m2)

| Item | Value        | Units |
| ---- | ------------ | ----- |
| XX   | 0.0125249699 | kg-m2 |
| XY   | 0            | kg-m2 |
| XZ   | -0.00340958  | kg-m2 |
| YY   | 0.0186853204 | kg-m2 |
| YZ   | 0            | kg-m2 |
| ZZ   | 0.0156701095 | kg-m2 |

### Bounding boxes: Center (m)

The two bounding boxes for the CORE I/O EAP payload, one for the CORE I/O and one for the EAP on top of it, are listed separately.

| Item | Value | Units |
| ---- | ----- | ----- |
| X    | -0.13 | m     |
| Y    | 0     | m     |
| Z    | 0.045 | m     |

| Item | Value  | Units |
| ---- | ------ | ----- |
| X    | -0.183 | m     |
| Y    | 0      | m     |
| Z    | 0.117  | m     |

### Bounding boxes: Orientation (radians) ZXY

| Item  | Value | Units |
| ----- | ----- | ----- |
| Yaw   | 0     | rad.  |
| Roll  | 0     | rad.  |
| Pitch | 0     | rad.  |

| Item  | Value | Units |
| ----- | ----- | ----- |
| Yaw   | 0     | rad.  |
| Roll  | 0     | rad.  |
| Pitch | 0     | rad.  |

### Bounding boxes: XYZ extent (m)

| Item | Value | Units |
| ---- | ----- | ----- |
| X    | 0.13  | m     |
| Y    | 0.095 | m     |
| Z    | 0.045 | m     |

| Item | Value | Units |
| ---- | ----- | ----- |
| X    | 0.088 | m     |
| Y    | 0.088 | m     |
| Z    | 0.067 | m     |

The [payload.proto](../../protos/bosdyn/api/payload.proto) file in the Spot SDK provides details about fields and data types.

<!--- image and page reference link definitions --->

[config-image1]: images/payload1.png
[config-image2]: images/payload2.png
[config-image3]: images/payload3.png
[config-image4]: images/payload4.png
[config-image5]: images/config-image5.png
[config-image6]: images/config-image6.png
[config-image7]: images/payload7.png
[config-image8]: images/payload8.png
[payload-top]: Readme.md "Developing and managing Spot payloads"
[configuration]: payload_configuration_requirements.md "Payload configuration requirements"
[mechanical]: mechanical_interfaces.md "Mechanical interfaces"
[mounting-rails]: robot_mounting_rails.md "Robot mounting rails"
[robust-payload]: guidelines_for_robust_payload_design.md "Guidelines for robust payload design"
[electrical]: robot_electrical_interface.md "Robot electrical interface"
[payload-software]: configuring_payload_software.md "Configuring payload software"
