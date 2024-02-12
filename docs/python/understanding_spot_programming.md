<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Understanding Spot Programming

This guide will help you understand the programming principles that drive Spot and the Spot Python SDK.

<!--ts-->
  * [Fundamental Robot Services](#fundamental-robot-services)
      * [Understanding the "id" command](#understanding-the-id-command)
      * [Listing Services](#listing-services)
  * [Understanding How to Setup and Command Spot to Move](#how-to-setup-and-command-spot-to-move)
      * [Create the SDK object](#create-the-sdk-object)
      * [Create a Robot object](#create-a-robot-object)
      * [Retrieve the Robot ID](#retrieve-the-robot-id)
      * [Blocking vs. Asynchronous Spot Python SDK functions](#blocking-vs-asynchronous-spot-python-sdk-functions)
      * [Inspecting robot state](#inspecting-robot-state)
        * [Services and Authentication](#services-and-authentication)
        * [Retrieving Robot State](#retrieving-robot-state)
        * [Robot State was a Message, Messages are defined by Protobufs](#robot-state-was-a-message-messages-are-defined-by-protobufs)
      * [Capture and View Camera images](#capture-and-view-camera-images)
      * [Configuring "Motor Power Authority" (software E-Stop)](#configuring-motor-power-authority-software-e-stop)
        * [Create and register an E-Stop Endpoint](#create-and-register-an-e-stop-endpoint)
        * [Clear the E-Stop](#clear-the-e-stop)
      * [Taking ownership of Spot (Leases)](#taking-ownership-of-spot-leases)
      * [Powering on the robot](#powering-on-the-robot)
      * [Establishing timesync](#establishing-timesync)
      * [Commanding the robot](#commanding-the-robot)
      * [Powering off the robot](#powering-off-the-robot)
<!--te-->
## Fundamental Robot Services
### Understanding the "id" command

The "id" command is one of the simplest Spot commands, so it's useful to understand how it works, since every command to Spot performs many of the same basic functions.

Specify the verbose flag with `--verbose` , and you'll get a lot of information! We'll explain the pieces...

```
$ python -m bosdyn.client --verbose 192.168.80.3 id
2020-03-26 17:30:27,571 - DEBUG - Creating standard Sdk, cert glob: "None"
2020-03-26 17:30:27,610 - DEBUG - Created client for robot-id
2020-03-26 17:30:27,615 - DEBUG - Created channel to 192.168.80.3 at port 443 with authority id.spot.robot
...
```
The first output line creates a Spot SDK object.  All Spot API programs start this way.

Note that the output text itself demonstrates Spot's use of Python's [logging facility](https://docs.python.org/3/library/logging.html), we recommend you perform your logging with the same.

The third line creates a `client` of Spot's `robot-id` service. The Spot API exposes on-robot capabilities via a set of network-accessible services - similar to a [microservice](https://en.wikipedia.org/wiki/Microservices) architecture.

The final line of output above shows the command initiating a gRPC channel to Spot.  All communication to the robot is over a secure HTTPS connection.  Spot API uses [gRPC](https://grpc.io) as its underlying RPC (Remote Procedure Call) transport. gRPC is a high-performance  networking connection for services which supports a wide variety of programming environments. gRPC uses [Protocol Buffers](https://developers.google.com/protocol-buffers/) as the messaging format, which has a compact over-the-wire representation and supports backwards and forwards compatibility.

```
2020-03-26 17:30:27,616 - DEBUG - blocking request: b'/bosdyn.api.RobotIdService/GetRobotId'
header {
  request_timestamp {
    seconds: 1585258227
    nanos: 616570624
  }
  client_name: "BosdynClientbblank02:__main__.py-28906"
}
```

In the above output, a blocking `GetRobotId` RPC can be seen being made to the `bosdyn.api.RobotIdService`.

Finally, the RobotIdService responds to the GetRobotId RPC with a response including information about the robot.

```
2020-03-26 17:30:27,650 - DEBUG - response: b'/bosdyn.api.RobotIdService/GetRobotId'
header {
  request_header {
    request_timestamp {
      seconds: 1585258227
      nanos: 616570624
    }
    client_name: "BosdynClientbblank02:__main__.py-28906"
  }
  request_received_timestamp {
    seconds: 1585258226
    nanos: 224952738
  }
  response_timestamp {
    seconds: 1585258226
    nanos: 224990830
  }
  error {
    code: CODE_OK
  }
  request {
    type_url: "type.googleapis.com/bosdyn.api.RobotIdRequest"
    value: "\n6\n\014\010\363\275\364\363\005\020\200\276\200\246\002\022&BosdynClientbblank02:__main__.py-28906"
  }
}
robot_id {
  serial_number: "beta-BD-90490007"
  species: "spot"
  version: "V3"
  software_release {
    version {
      major_version: 2
    }
    changeset_date {
      seconds: 1583941992
    }
    changeset: "b11205d698e"
    install_date {
      seconds: 1583953617
    }
  }
  nickname: "beta29"
  computer_serial_number: "02-19904-9903"
}
```

### Listing services

The following command lists all of the services available on the robot.  Note the `robot-id` service is listed, which we just used in the previous section.  Services are what you communicate with on Spot, use them to issue commands, retrieve information, etc.

```
$ python -m bosdyn.client --user user --password password 192.168.80.3 dir list
name                             type                                              authority                                   tokens
------------------------------------------------------------------------------------------------------------------------------------
auth                             bosdyn.api.AuthService                            auth.spot.robot
directory                        bosdyn.api.DirectoryService                       api.spot.robot                              user
directory-registration           bosdyn.api.DirectoryRegistrationService           api.spot.robot                              user
estop                            bosdyn.api.EstopService                           estop.spot.robot                            user
graph-nav-service                bosdyn.api.graph_nav.GraphNavService              graph-nav.spot.robot                        user
image                            bosdyn.api.ImageService                           api.spot.robot                              user
lease                            bosdyn.api.LeaseService                           api.spot.robot                              user
...
```

See the Concept documents for more details about [Spot's API Architecture](../concepts/README.md).

## How to Setup and Command Spot to Move

It is useful to run Spot from the command line to understand the basics for commanding Spot.

Start up a python interpreter and import the bosdyn.client package - this should work assuming you've successfully completed our [Spot Python SDK Quickstart](./quickstart.md).

```sh
$ python
Python 3.6.8 (default, Jan 14 2019, 11:02:34)
[GCC 8.0.1 20180414 (experimental) [trunk revision 259383]] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import bosdyn.client
```

### Create the SDK object

All Boston Dynamics API programs start by creating an SDK object with a client name argument. The client name is used to help with debugging, and does not have any semantic information - so use whatever string is helpful for you.


```python
>>> sdk = bosdyn.client.create_standard_sdk('understanding-spot')
```

### Create a robot object
To retrieve the robot id like we did in [Spot Python SDK Quickstart](./quickstart.md) we'll first need to create a `robot` object, using its network address as an argument. In this example, we only create one `robot` object, but it is possible to create and control multiple robots in the same program with the Boston Dynamics API.

```python
>>> robot = sdk.create_robot('192.168.80.3')
```

### Retrieve the Robot ID

As discussed earlier, Spot exposes its capability via a number of services. The Boston Dynamics Python API has a corresponding set of clients for each service, which are created off of the robot object.

Let's create a `RobotIdClient` of the `robot-id` service, and then retrieve id information:

```python
>>> id_client = robot.ensure_client('robot-id')
>>> id_client.get_id()
serial_number: "beta-BD-90490007"
species: "spot"
...
```

### Blocking vs. Asynchronous Spot Python SDK functions
The `get_id()` call above is blocking - it will not complete until after the RPC completes. It is possible to tweak parameters for the call, such as a timeout for how long to wait. The following example sets a too short timeout and fails...

```
>>> id_client.get_id(timeout=0.0001)
Traceback (most recent call last):
  File "/mnt/c/spot_v2_0/bblank_spot_v2_0_env/lib/python3.6/site-packages/bosdyn/client/common.py", line 290, in call
    response = rpc_method(request, **kwargs)
  File "/mnt/c/spot_v2_0/bblank_spot_v2_0_env/lib/python3.6/site-packages/grpc/_channel.py", line 826, in __call__
    return _end_unary_response_blocking(state, call, False, None)
  File "/mnt/c/spot_v2_0/bblank_spot_v2_0_env/lib/python3.6/site-packages/grpc/_channel.py", line 729, in _end_unary_response_blocking
    raise _InactiveRpcError(state)
grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:
        status = StatusCode.DEADLINE_EXCEEDED
        details = "Deadline Exceeded"
        debug_error_string = "{"created":"@1585323526.280242100","description":"Error received from peer ipv4:192.168.80.3:443","file":"src/core/lib/surface/call.cc","file_line":1056,"grpc_message":"Deadline Exceeded","grpc_status":4}"
>
```

In addition to blocking calls, clients support non-blocking asynchronous calls. This can be useful in high performance applications where a thread of execution can not stall waiting for an RPC to complete. Python's [futures](https://docs.python.org/3/library/concurrent.futures.html#future-objects) architecture is used as the underpinning of asynchronous communication.  See the [get_robot_state_async programming example](../../python/examples/get_robot_state_async/README.md) for how to use these functions.

Let's make an asynchronous call for the robot id and wait for the result from the returned future object:

```python
>>> fut = id_client.get_id_async()
>>> fut.result()
serial_number: "beta-BD-90490007"
species: "spot"
...
```

### Inspecting robot state

The `robot-state` service contains dynamic information about the robot such as location, battery status, etc.

#### Services and Authentication
Before robot state can be retrieved, you need to authenticate to the robot. The majority of services require the user to be authenticated - this prevents random network attackers from being able to control the robot or intercept information which might be sensitive.

Assuming that the username is `user` and the password is `password`, issue the following command.

```python
>>> robot.authenticate('user', 'password')
```

If you provided the wrong credentials, an exception will be raised.

#### Retrieving robot state
Now we can create a `RobotStateClient` for the `robot-state` service, and obtain information about Spot:

```python
>>> state_client = robot.ensure_client('robot-state')
>>> state_client.get_robot_state()
power_state {
  timestamp {
    seconds: 1585324337
    nanos: 644209920
  }
  ... a whole lot more
```

#### Robot State was a message, messages are defined by protobufs
The structure of the robot state message retrieved above is defined by its *protobuf definition*.  This is the language the robot speaks.  Spot SDK completely exposes the protobuf, so to really understand Spot programming you want to look at and understand the protobufs. Take a look, they are right here in your distribution!   [../../protos/bosdyn/api/robot_state.proto](../../protos/bosdyn/api/robot_state.proto)

### Spot's Frames

Often, it is useful to know about the position of Spot and how it relates to the world around it. To express this information, Spot uses frames to represent objects and locations (e.g. the "body" frame) and 3D transformations to describe the relationship between two frames using a translation vector and a rotation quaternion. See the [Geometry and Frames](../concepts/geometry_and_frames.md) documentation for much more detail on frames and transformations, the math possible with 3D transformations, and the different frame's Spot knows about.

### Capture and View Camera Images

Spot has 5 "fisheye" cameras in addition to 5 depth cameras.  Images can be captured from the  these image sources. The 'list_image_sources' RPC returns valid camera source names.

```python
>>> from bosdyn.client.image import ImageClient
>>> image_client = robot.ensure_client(ImageClient.default_service_name)
>>> sources = image_client.list_image_sources()
>>> [source.name for source in sources]
['back_depth', 'back_depth_in_visual_frame', 'back_fisheye_image', 'frontleft_depth', 'frontleft_depth_in_visual_frame', 'frontleft_fisheye_image', 'frontright_depth', 'frontright_depth_in_visual_frame', 'frontright_fisheye_image', 'left_depth', 'left_depth_in_visual_frame', 'left_fisheye_image', 'right_depth', 'right_depth_in_visual_frame', 'right_fisheye_image']
```

Using the source names listed above, we can capture an image from one or more image sources. These images can be captured in RAW format or JPG format (with specified quality). Multiple images requested in a single RPC will be hardware time-synced with one another.  Let's retrieve the left_fisheye_image and display it (unless you are on MacOS or WSL)...

```python
>>> image_response = image_client.get_image_from_sources(["left_fisheye_image"])[0]
>>> from PIL import Image
>>> import io
>>> image = Image.open(io.BytesIO(image_response.shot.image.data))
>>> image.show()
```

### Configuring "Motor Power Authority" (software E-Stop)

Before Spot can power on, an independent *Motor Power Authority* must be correctly configured.  We use the term "E-Stop" below and in our functions as shorthand for Motor Power Authority. The E-Stop is a key safety feature of Spot which lets operators kill motor power immediately if a situation calls for it. Note that in some circles the term "E-Stop" implies a hardware power short-circuit, hence our semantic dancing, as Spot's Motor Power Authority is a networked software solution, not a hardware solution.

Let's take a look at the initial E-Stop state of the robot by creating a client to the E-Stop service and requesting status:

```python
>>> estop_client = robot.ensure_client('estop')
>>> estop_client.get_status()
stop_level: ESTOP_LEVEL_CUT
stop_level_details: "Not all endpoints are registered"
```

The `stop_level: ESTOP_LEVEL_CUT` line indicates that power will not be enabled since the E-Stop level is CUT.

The `stop_level_details: "Not all endpoints are registered"` line indicates that there are no E-Stop Endpoints registered. An E-Stop Endpoint is the client component of the E-Stop system which lets a user immediately kill power.

#### Create and register an E-Stop Endpoint

```python
>>> estop_endpoint = bosdyn.client.estop.EstopEndpoint(client=estop_client, name='my_estop', estop_timeout=9.0)
>>> estop_endpoint.force_simple_setup()
```

E-Stop endpoints are expected to regularly check in to the robot to assure the robot is safely being controlled.  If it has been more than `estop_timeout` seconds, the motor power will be cut. Tuning this number is important: too low a number, and the power may cut out due to transient network issues; too large a number and you run the risk of Spot operating without safe supervision.

The `force_simple_setup` call issues a few API calls to make your E-Stop Endpoint the sole endpoint in a new E-Stop configuration.

Let's request E-Stop status after registering our endpoint:

```python
>>> estop_client.get_status()
endpoints {
  endpoint {
    role: "PDB_rooted"
    name: "my_estop"
    unique_id: "0"
    timeout {
      seconds: 9
    }
    cut_power_timeout {
      seconds: 13
    }
  }
  stop_level: ESTOP_LEVEL_CUT
  time_since_valid_response {
  }
}
stop_level: ESTOP_LEVEL_CUT
stop_level_details: "Endpoint requested stop"
```

Now an E-Stop Endpoint appears with the name `my_estop`. The endpoint itself says `ESTOP_LEVEL_CUT`, with a very long ago `time_since_valid_response`. No check-ins from the E-Stop Endpoint have happened yet. Both the endpoint and the E-Stop systems stop level is `ESTOP_LEVEL_CUT` - if a single Endpoint wants to cut power, the entire system will cut power.

#### Clear the E-Stop

To change E-Stop status and allow power, the endpoint needs to check in on a regular basis. We'll use the `EstopKeepAlive` class to do these check-ins on a regular basis from a background thread.

```python
>>> estop_keep_alive = bosdyn.client.estop.EstopKeepAlive(estop_endpoint)
>>> estop_client.get_status()
endpoints {
  endpoint {
    role: "PDB_rooted"
    name: "my_estop"
    unique_id: "0"
    timeout {
      seconds: 9
    }
    cut_power_timeout {
      seconds: 13
    }
  }
  stop_level: ESTOP_LEVEL_NONE
  time_since_valid_response {
    nanos: 996009984
  }
}
stop_level: ESTOP_LEVEL_NONE
```

The `stop_level` is now `ESTOP_LEVEL_NONE`, indicating that power can start up.

Note that in many implementations, you should specify the `keep_running_cb` argument to EstopKeepAlive, a function called by the background thread to see if check-ins should continue. For example, an interactive UI should give the E-Stop system a `keep_running_cb` function which blocks until the UI thread has run a cycle. This prevents a frozen client from continuing to allow power to the robot.

See the Concept documents for more details about [Spot's software E-Stop Service](../concepts/estop_service.md).

### Taking ownership of Spot (Leases)

There's one more step before powering on Spot's motors, and that's to acquire ownership of the robot.  The robot can have multiple clients but only one can control the robot even as other clients may be requesting data or acting as E-Stop endpoints.

To gain control of the robot, a client needs to acquire a `Lease`. A valid lease must be presented with every mobility command to the robot. Leases can be returned when the client no longer wants to control the robot.

Like the E-Stop, lease-holders need to periodically check in with Spot to indicate that they are still actively controlling the robot.  If it has been too long since a check-in, the robot will commence a Comms Loss Procedure - sitting down if it can, and then powering off.

Let's make a `LeaseClient` for the `lease` service and list the current leases:

```python
>>> lease_client = robot.ensure_client('lease')
>>> lease_client.list_leases()
[resource: "all-leases"
lease {
  resource: "all-leases"
  epoch: "ZBEwqFkjbTznJRxU"
  sequence: 1
  client_names: "root"
}
lease_owner {
}
, resource: "body"
lease {
  resource: "body"
  epoch: "ZBEwqFkjbTznJRxU"
  sequence: 1
  client_names: "root"
}
lease_owner {
}
, resource: "mobility"
lease {
  resource: "mobility"
  epoch: "ZBEwqFkjbTznJRxU"
  sequence: 1
  client_names: "root"
}
lease_owner {
}
]

```

The lease-able resources are listed: "body", "mobility", ("full-arm", "gripper", "arm" for robots with an arm). The "body" resource covers all of the motors on Spot and for most use-cases it is sufficient to issue all commands just using the "body" lease since services on Spot will break apart the lease to use the minimal set of resources necessary.

NOTE: the `lease_owner` field is empty since no one has acquired the body lease.

When taking lease control of Spot, the lease should first be acquired, and then the "keepalive" should be created to retain ownership of the lease resource.
Let's acquire a lease, create the keepalive, and again list:

```python
>>> lease = lease_client.acquire()
>>> lease_keep_alive = bosdyn.client.lease.LeaseKeepAlive(lease_client)
>>> lease_client.list_leases()
[resource: "all-leases"
lease {
  resource: "all-leases"
  epoch: "ZBEwqFkjbTznJRxU"
  sequence: 2
  client_names: "root"
}
lease_owner {
  client_name: "HelloSpotClientlaptop-kbrandes01:hello_spot.py-32049"
}
, resource: "body"
lease {
  resource: "body"
  epoch: "ZBEwqFkjbTznJRxU"
  sequence: 2
  client_names: "root"
}
lease_owner {
  client_name: "HelloSpotClientlaptop-kbrandes01:hello_spot.py-32049"
}
, resource: "mobility"
lease {
  resource: "mobility"
  epoch: "ZBEwqFkjbTznJRxU"
  sequence: 2
  client_names: "root"
}
lease_owner {
  client_name: "HelloSpotClientlaptop-kbrandes01:hello_spot.py-32049"
}
]
```

After acquiring the "body" lease, you take ownership of the sub-resource "mobility". For a robot with an arm, you will also take ownership of the sub-resources "full-arm", "arm", and "gripper" when acquiring the "body" lease.

NOTE: the lease keepalive object must remain in scope for the entire duration of the program that is using the lease for commands.

### Powering on the robot

Now that you've authenticated to Spot, created an E-Stop endpoint, and acquired a lease, it's time to power on the robot.

Make sure that the robot is in a safe spot, in a seated position, with a charged battery, and not connected to shore power.

The `power_on` helper function first issues a lower level power command to the robot and then waits for power command feedback. This command returns once the robot is powered on or throws an error if the power command fails for any reason. It typically takes several seconds to complete.

```python
>>> robot.power_on(timeout_sec=20)
```

The robot object provides a method to check the power status of the robot. This just uses the RobotStateService to check the PowerState:

```python
>>> robot.is_powered_on()
True
```

### Establishing timesync

Timesync is required to coordinate clock skew between your device and Spot.   From a safety perspective, this allows users to define a period of time for which a command will be valid. The robot class maintains a timesync thread. The `wait_for_sync` call below will start a timesync thread, and block until sync is established. After timesync is established, this thread will make periodic calls to maintain timesync. Each client is issued a clock identifier which is used to validate that the client has performed timesync, for services that require this functionality. The client library is written such that most implementation details of timesync are taken care of in the background.

```python
>>> robot.time_sync.wait_for_sync()
```

### Commanding the robot

The RobotCommandService is the primary interface for commanding mobility. Mobility and mobility-related commands include `stand`, `sit`, `selfright`, `safe_power_off`, `velocity`, and `trajectory`. For this tutorial, we will just issue stand and safe power off commands.

The API provides a helper function to stand Spot. This command wraps several RobotCommand RPC calls. First a stand command is issued. The robot checks some basic pre-conditions (powered on, not faulted, not E-Stopped) and returns a command id. This command id can then be passed to the robot command feedback RPC. This call returns both high level feedback ("is the robot still processing the command?") as well as command specific feedback (in the case of stand, "is the robot standing?").

```python
>>> from bosdyn.client.robot_command import RobotCommandClient, blocking_stand
>>> command_client = robot.ensure_client(RobotCommandClient.default_service_name)
>>> blocking_stand(command_client, timeout_sec=10)
```

The robot should now be standing. In addition, the stand command can be modified to control the height of the body as well as the orientation of the body with respect to the **footprint frame**. The footprint frame is a gravity aligned frame with its origin located at the geometric center of the feet. The Z axis up, and the X axis is forward.

The commands proto can be quite expressive, and therefore, if going beyond default parameters, non-trivial.  To increase simplicity, Spot API provides several helper functions that combine Spot API RPC commands into single line functions.

We encourage you to experiment with these various parameters, referencing the [robot_command proto](../../protos/bosdyn/api/robot_command.proto) parent class for general Boston Dynamics robots and the [robot command proto](../../protos/bosdyn/api/spot/robot_command.proto) Spot subclass.

```python
# Command Spot to rotate about the Z axis.
>>> from bosdyn.geometry import EulerZXY
>>> footprint_R_body = EulerZXY(yaw=0.4, roll=0.0, pitch=0.0)
>>> from bosdyn.client.robot_command import RobotCommandBuilder
>>> cmd = RobotCommandBuilder.synchro_stand_command(footprint_R_body=footprint_R_body)
>>> command_client.robot_command(cmd)
# Command Spot to raise up.
>>> cmd = RobotCommandBuilder.synchro_stand_command(body_height=0.1)
>>> command_client.robot_command(cmd)
```

### Powering off the robot

Power off the robot using the `power_off` command.  Note the preferred method is with `cut_immediately=False` where Spot will come to a stop and sit down gently before powering off.  The other power off option cuts motor power immediately, which causes the robot to collapse.

```python
>>> robot.power_off(cut_immediately=False)
```
