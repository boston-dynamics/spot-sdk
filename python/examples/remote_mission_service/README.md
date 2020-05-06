<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# API Example - Run and interact with a RemoteMissionService.

This example demonstrates how to
1) Run a gRPC server that implements the RemoteMissionService service definition
2) Connect a RemoteClient directly to that server.
3) Build a mission that talks to that server.

This is the new pattern used by "callback" elements of Autowalk missions.

## Setup Dependencies
See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:
```
python -m pip install -r requirements.txt
```

## Running the Example

### Running without a robot

You can test the example server without involving the robot at all. Start the server with
```
python -m remote_mission_service localhost
```

On success, you should see a new line on your terminal like this one:
```
Starting server on port PORT (remote_mission_service.py:71)
```
To start the client, run
```
python -m remote_mission_client localhost --port PORT
```

where `PORT` matches the port number printed out by the server application. The client should immediately connect to the local server, and the server and client will both print out some information.

The client output will look like this:

```
EstablishSession is unimplemented.
Servicer stopped with status STATUS_SUCCESS
Either Stop or TeardownSession is unimplemented.
```

The server output will look like this:

```
Exception calling application: Method not implemented! (_server.py:400)
Traceback (most recent call last):
  File "site-packages/grpc/_server.py", line 392, in _call_behavior
    return behavior(argument, context), True
  File "remote_service_pb2_grpc.py", line 48, in EstablishSession
    raise NotImplementedError('Method not implemented!')
NotImplementedError: Method not implemented!
Hello World! (example_servicers.py:43)
Exception calling application: Method not implemented! (_server.py:400)
Traceback (most recent call last):
  File "site-packages/grpc/_server.py", line 392, in _call_behavior
    return behavior(argument, context), True
  File "remote_service_pb2_grpc.py", line 63, in Stop
    raise NotImplementedError('Method not implemented!')
NotImplementedError: Method not implemented!
```

The NotImplementedError tracebacks are normal and can be ignored. They are just telling you that the EstablishSession and Stop RPCs are not implemented in the basic servicer.

You can change the `Hello World!` text with an option to the client. For example, if you run the client again with the additional `--user-string` option:
```
python -m remote_mission_client localhost --port PORT --user-string Spot
```

The server will print out `Hello Spot!` instead of `Hello World!`

### Running with a robot

There is another example servicer that will power the robot down in a safe way. To run this example, you will need a connection between a robot and the computer running the examples. Here's an example, assuming the host running the examples is connected to the robot's WiFi network:
```
python -m remote_mission_service 192.168.80.3 --servicer PowerOff --username USER --password PASSWORD
```

Now if you run the client with:
```
python -m remote_mission_client localhost --port PORT --lease-host 192.168.80.3 --username USER --password PASSWORD
```
and assuming the robot is already powered off and sitting on the ground, you'll see this output from the server:

```
Ticked by node "<unknown>" (example_servicers.py:107)
Ticked by node "<unknown>" (example_servicers.py:107)
Ticked by node "<unknown>" (example_servicers.py:107)
```

and this output from the client:

```
Servicer stopped with status STATUS_SUCCESS
```

To see the servicer actually power the robot off, you will have to perform the following steps:
1) Use the wasd example to power the robot on and stand it up.
1) Return wasd's lease with the [l] key
1) Run the client.

You must run the client within 3 seconds of returning wasd's lease, otherwise the normal comms loss policy will kick in.


## Using the example as part of an Autowalk mission

The example will work as part of an Autowalk mission, performing its action during a callback element. A few extra options are necessary, in order to tell the robot about the new callback service. Here is an example command line, assuming the server is being launched on a Spot CORE attached to a Spot with the default networking setup:
```
python -m remote_mission_service 192.168.50.3 --my-host 192.168.50.5 --directory-host 192.168.50.3 --username USER --password PASSWORD
```

The additional options provide details for directory registration, which lets Spot know how to contact your service. `192.168.50.5` is the address of the host running the service, and `192.168.50.3` is the address of the robot. You must provide an address that Spot knows how to reach for the `--my-host` option.

Here is an example command line, assuming the server is being launched on your computer used in earlier examples. Note: You may have to change your firewall settings in order for communication to succeed.
```
python -m remote_mission_service 192.168.80.3 --my-host <your_ip> --directory-host 192.168.80.3 --username USER --password PASSWORD
```
