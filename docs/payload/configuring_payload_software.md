<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# [Spot SDK](../../README.md) > [Payload Developer Guide](README.md) > Software Interface

To log payload data and debug payload issues, payloads developed for the Spot platform should observe the following guidelines:



*   Payloads gather and generate their own log data.
*   Payloads generate and send their own text annotations to mark robot logs for preservation.
*   Each payload component provides access to its own debug data.
*   Logic on the payload determines what data to log and when to log it.


## Payload API services

The API provides two services for managing and registering payloads and payload services:


*   RemoteMissionService
*   PayloadService
*   PayloadRegistrationService

Robot directory services are used to register services that a payload might offer so that they can be exposed on the robot.



*   DirectoryService
*   DirectoryRegistrationService


## RemoteMissionService RPCs

RemoteMissionService RPCs are called by MissionService to communicate with a robot  payload. The mission service uses these RPCs to communicate with a remote mission service.


<table>
  <tr>
   <td><strong>RPC</strong>
   </td>
   <td><strong>Description</strong>
   </td>
  </tr>
  <tr>
   <td>EstablishSession
   </td>
   <td>Call this once at mission load time, per node.
   </td>
  </tr>
  <tr>
   <td>Tick
   </td>
   <td>Call this every time the RemoteGrpc node is ticked.
   </td>
  </tr>
  <tr>
   <td>Stop
   </td>
   <td>Call this every time the RemoteGrpc node was ticked in the previous cycle, but not ticked in this cycle.
   </td>
  </tr>
  <tr>
   <td>TeardownSession
   </td>
   <td>Tells the service it can forget any data associated with the given session.
   </td>
  </tr>
</table>



### DirectoryService RPCs


<table>
  <tr>
   <td><strong>RPC</strong>
   </td>
   <td><strong>Description</strong>
   </td>
  </tr>
  <tr>
   <td>GetServiceEntry
   </td>
   <td>Get information about a specific service.
   </td>
  </tr>
  <tr>
   <td>ListServiceEntries
   </td>
   <td>List all known services at the time of the request.
   </td>
  </tr>
</table>



### DirectoryRegistrationService


<table>
  <tr>
   <td><strong>RPC</strong>
   </td>
   <td><strong>Description</strong>
   </td>
  </tr>
  <tr>
   <td>RegisterService
   </td>
   <td>Called by a system to announce, via the robot directory, a new service it is hosting.
   </td>
  </tr>
  <tr>
   <td>UnregisterService
   </td>
   <td>Called by a system to deregister a service from the robot directory.
   </td>
  </tr>
  <tr>
   <td>UpdateService
   </td>
   <td>Update the ServiceEntry for a system hosting a service.
   </td>
  </tr>
</table>



### PayloadService RPCs


<table>
  <tr>
   <td><strong>RPC</strong>
   </td>
   <td><strong>Description</strong>
   </td>
  </tr>
  <tr>
   <td>ListPayloads
   </td>
   <td>Query the robot for a list of currently-registered payloads.
   </td>
  </tr>
</table>



### PayloadRegistrationService RPCs


<table>
  <tr>
   <td><strong>RPC</strong>
   </td>
   <td><strong>Description</strong>
   </td>
  </tr>
  <tr>
   <td>RegisterPayload
   </td>
   <td>Register a new payload with the robot.
   </td>
  </tr>
  <tr>
   <td>GetPayloadAuthToken
   </td>
   <td>Get an auth token to enable the payload.
   </td>
  </tr>
</table>



## Registering payloads

This code snippet example uses the API to communicate payload configuration settings to Spot. The example first registers a payload then lists all payloads on the robot, including the newly registered payload.


    ...
    # Authenticate robot before being able to use it
    robot.authenticate(config.username, config.password)

    # Create a payload registration client
    payload_registration_client = robot.ensure_client(
    PayloadRegistrationClient.default_service_name)

    # Create a payload
    payload = payload_protos.Payload()
    payload.GUID = '78b076a2-b4ba-491d-a099-738928c4410c'
    payload.name = 'Client Registered Payload Ex'
    payload.description = 'This payload was created and registered by the register_payload.py client example.'
    payload.label_prefix.append("test_payload")
    payload.is_authorized = False
    payload.is_enabled = False
    payload.is_noncompute_payload = False

    # Register the payload
    payload_registration_client.register_payload(payload)

    # Create a payload client
    payload_client = robot.ensure_client(PayloadClient.default_service_name)

    # List all payloads
    payloads = payload_client.list_payloads()
    print(payloads)
    ...

Refer to the [Python payload registration code example in the Spot SDK](../../python/examples/payloads/payloads.py) for details.


## Payload self-registration

The Payload Registration API gives developers the ability to deploy payloads that register themselves with the robot when they power on without the need to store an app token or user credentials on the payload.

The payload registration process completes after an admin operator accepts the payload using the robot's admin console. If the payload has registered itself, it should appear in the Payload section of the admin console.



*   Payloads can register API services. Example: A LIDAR payload registers RemoteService callbacks to trigger scans during robot missions.
*   Payload and service registration do not require an app token or robot user credentials.


Once a payload has been authorized, its unique GUID and secret combination can be used as credentials to request a limited-access user token that will grant permission to the auth, directory, robot-state, and directory-registration services. The granted user token will be valid for 12 hours.


### Payload and service registration examples

The Spot SDK Python code examples includes payload registration and service registration examples that provide sample scripts, protos, and a list of dependencies: [Self-registration Python code examples in the Spot SDK](../../python/examples/self_registration/index.html).


## Configuring and authorizing payloads

A payload, like any software client, can access the API by using an app token and login credentials. However, for self-registration, paylaods can complete basic registration and get access to host services without needing to pass an app token or hardcoded user credentials.

Instead, a payload is manually authorized by an operator on the admin console Payloads page. To ensure that the payload authorization is not used by malicious payloads, each payload must provide a unique GUID and secret (password) at registration time. The GUID and secret can then be used to request a user token that grants access to the basic components of the API (directory, directory registration, robot-state).

Payload Services must periodically register with the Directory service in order to be used by the UI and the Autonomy Module. For example, during autonomous navigation, the robot may instruct the payload to store an image. It will address the payload service via the standard Directory service.


## Payload device network configuration

The robot’s default private IP address is 192.168.80.3. Users can configure these properties via the robot’s admin console. Use the network settings to change the robot’s network configuration from WiFi AP to WiFi client.

The robot’s rear ethernet port can be configured to a user desired IP address via the web interface.  By default, its IP is set to 10.0.0.3.

Payload devices should use the following network configuration:



*   IP v4 host address 192.168.50.5 for the front payload, 192.168.50.6 for rear payload
*   Netmask 255.255.255.0
*   Default gateway gateway will be set to 192.168.50.3

Devices on the payload network can reach the robot at 192.168.50.3 via port 443. Devices on the robot network can reach payload services as follows:



1. TCP traffic sent to the robot's IP address on ports 20022, 20080, or 20443 will be forwarded to 192.168.50.5 on ports 22, 80, or 443.
2. TCP/UDP traffic sent to the robot’s IP address  on ports 21000-22000 will be forwarded to 192.168.50.5 on that same port.
3. TCP traffic sent to the robot's IP address on ports 30022, 30080, or 30443 will be forwarded to 192.168.50.6 on ports 22, 80, or 443.
4. TCP/UDP traffic sent to the robot on ports 31000-32000 will be forwarded to 192.168.50.6.


## Payload port forwarding table


<table>
  <tr>
   <td><strong>DESCRIPTION</strong>
   </td>
   <td><strong>ROBOT PORT</strong>
   </td>
   <td><strong>TARGET</strong>
   </td>
   <td><strong>PROTOCOL</strong>
   </td>
  </tr>
  <tr>
   <td>Standard Forwards 1
   </td>
   <td>20000 + [22, 80, 443]
   </td>
   <td>192.168.50.5:[22, 80, 443]
   </td>
   <td>TCP
   </td>
  </tr>
  <tr>
   <td>Fixed Forwards 1
   </td>
   <td>21000-22000
   </td>
   <td>192.158.50.5:21000-22000
   </td>
   <td>TCP/UDP
   </td>
  </tr>
  <tr>
   <td>Standard Forwards 2
   </td>
   <td>30000 + [22, 80, 443]
   </td>
   <td>192.168.50.6:[22, 80, 443]
   </td>
   <td>TCP
   </td>
  </tr>
  <tr>
   <td>Fixed Forwards 2
   </td>
   <td>31000-32000
   </td>
   <td>192.158.50.6:31000-32000
   </td>
   <td>TCP/UDP
   </td>
  </tr>
</table>



## Configuring payload mass properties

In order to locomote properly, the robot needs to know the physical properties of any payload it is carrying. This includes the center of mass location relative to the base link of the robot, moments of inertia, and other values.

A payload self-registration service is available as part of the Spot 2.0 SDK.

The following payload configuration table shows configuration values for the Spot CORE payload as they would appear in the robot's admin console GUI.

This table provides a reference when developing a client application using the the RegisterPayload RPC to register a Spot payload.


<table>
  <tr>
   <td><strong>Configuration</strong>
   </td>
   <td><strong>Item</strong>
   </td>
   <td><strong>Value</strong>
   </td>
   <td><strong>Units</strong>
   </td>
  </tr>
  <tr>
   <td rowspan="3" >Position (m)
   </td>
   <td>X
   </td>
   <td>-0.16
   </td>
   <td>m
   </td>
  </tr>
  <tr>
   <td>Y
   </td>
   <td>0
   </td>
   <td>m
   </td>
  </tr>
  <tr>
   <td>Z
   </td>
   <td>0
   </td>
   <td>m
   </td>
  </tr>
  <tr>
   <td rowspan="3" >Orientation (radians)
   </td>
   <td>Yaw
   </td>
   <td>0
   </td>
   <td>rad.
   </td>
  </tr>
  <tr>
   <td>Roll
   </td>
   <td>0
   </td>
   <td>rad.
   </td>
  </tr>
  <tr>
   <td>Pitch
   </td>
   <td>0
   </td>
   <td>rad.
   </td>
  </tr>
  <tr>
   <td>Total mass (kg)
   </td>
   <td>
   </td>
   <td>2.0
   </td>
   <td>kg
   </td>
  </tr>
  <tr>
   <td rowspan="3" >Position of Center of Mass (m)
   </td>
   <td>X
   </td>
   <td>-0.13
   </td>
   <td>m
   </td>
  </tr>
  <tr>
   <td>Y
   </td>
   <td>0
   </td>
   <td>m
   </td>
  </tr>
  <tr>
   <td>Z
   </td>
   <td>0.045
   </td>
   <td>m
   </td>
  </tr>
  <tr>
   <td rowspan="6" >Moment of inertia tensor (kg-m<sup>2</sup>)
   </td>
   <td>XX
   </td>
   <td>0.00675
   </td>
   <td>kg-m<sup>2</sup>
   </td>
  </tr>
  <tr>
   <td>XY
   </td>
   <td>0
   </td>
   <td>kg-m<sup>2</sup>
   </td>
  </tr>
  <tr>
   <td>XZ
   </td>
   <td>0
   </td>
   <td>kg-m<sup>2</sup>
   </td>
  </tr>
  <tr>
   <td>YY
   </td>
   <td>0.0126167
   </td>
   <td>kg-m<sup>2</sup>
   </td>
  </tr>
  <tr>
   <td>YZ
   </td>
   <td>0
   </td>
   <td>kg-m<sup>2</sup>
   </td>
  </tr>
  <tr>
   <td>ZZ
   </td>
   <td>0.0166667
   </td>
   <td>kg-m<sup>2</sup>
   </td>
  </tr>
  <tr>
   <td rowspan="3" >Bounding boxes:  \
Center (m)
   </td>
   <td>X
   </td>
   <td>-0.13m
   </td>
   <td>m
   </td>
  </tr>
  <tr>
   <td>Y
   </td>
   <td>0
   </td>
   <td>m
   </td>
  </tr>
  <tr>
   <td>Z
   </td>
   <td>0.045
   </td>
   <td>m
   </td>
  </tr>
  <tr>
   <td rowspan="3" >Bounding boxes:  \
Orientation (radians) ZXY
   </td>
   <td>Yaw
   </td>
   <td>0
   </td>
   <td>rad.
   </td>
  </tr>
  <tr>
   <td>Roll
   </td>
   <td>0
   </td>
   <td>rad.
   </td>
  </tr>
  <tr>
   <td>Pitch
   </td>
   <td>0
   </td>
   <td>rad.
   </td>
  </tr>
  <tr>
   <td rowspan="3" >Bounding boxes:  \
XYZ extent (m)
   </td>
   <td>X
   </td>
   <td>0.13
   </td>
   <td>m
   </td>
  </tr>
  <tr>
   <td>Y
   </td>
   <td>0.095
   </td>
   <td>m
   </td>
  </tr>
  <tr>
   <td>Z
   </td>
   <td>0.045
   </td>
   <td>m
   </td>
  </tr>
</table>


The [payload.proto](../../protos/bosdyn/api/payload.proto) file in the Spot SDK provides details about fields and data types.


<br />

<a href="robot_electrical_interface.md" class="previous">&laquo; Previous</a>



<!--- image and page reference link definitions --->
[payload-top]: Readme.md "Developing and managing Spot payloads"
[configuration]: payload_configuration_requirements.md "Payload configuration requirements"
[mechanical]: mechanical_interfaces.md "Mechanical interfaces"
[mounting-rails]: robot_mounting_rails.md "Robot mounting rails"
[robust-payload]: guidelines_for_robust_payload_design.md "Guidelines for robust payload design"
[electrical]: robot_electrical_interface.md "Robot electrical interface"
[payload-software]: configuring_payload_software.md "Configuring payload software"
