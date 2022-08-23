<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Run and Interact with a RemoteMissionService.

This example demonstrates how to

1. Run a gRPC server that implements the RemoteMissionService service definition
2. Connect a RemoteClient directly to that server.
3. Build a mission that talks to that server.

This is the new pattern used by "callback" actions of Autowalk missions.

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Running the Example

### Running without a robot

You can test the example server without involving the robot at all. Start the hello world service with

```
python3 hello_world_mission_service.py local --port {PORT}
```

On success, you should see service logs appear in your terminal like this:

```
2021-01-27 10:29:27,602 - INFO - Started the HelloWorldServicer server.
hello-world-callback service running.
Ctrl + C to shutdown.
```

To start the client, run

```
python3 remote_mission_client.py --hello-world local --host-ip localhost --port {PORT}
```

Where `PORT` matches the port number provided to the server application. The client should immediately connect to the local server, and the server and client will both print out some information.

The server output will look like this:

```
2021-01-27 10:37:23,338 - INFO - EstablishSession unimplemented!
2021-01-27 10:37:23,339 - INFO - Hello World!
2021-01-27 10:37:23,340 - INFO - Stop unimplemented!
2021-01-27 10:37:23,340 - INFO - TeardownSession unimplemented!
```

The client output will look like this:

```
Servicer stopped with status STATUS_SUCCESS
```

You can change the `Hello World!` text with an option to the client. For example, if you run the client again with the additional `--user-string` option:

```
python3 remote_mission_client.py --hello-world --user-string Spot local --host-ip localhost --port {PORT}
```

The server will print out "Hello Spot!" instead of "Hello World!"

### Running with a robot

There is another example servicer that will power the robot down safely. To run this example, you will need a connection between a robot and the computer running the examples.

```
python3 power_off_mission_service.py ROBOT_IP --port {PORT} --host-ip {ENDPOINT_IP}
```

A port number for the service can be specified using the --port argument. It is possible to bypass the port argument and allow a random port number to be selected, but it is discouraged since restarts may result in unexpected changes to a services listening port. This port number will be used with the host-ip ("ENDPOINT_IP") to fully specify where the service is running. The port must be open and cannot be blocked by a local firewall. If the port is blocked, the service will be unreachable from the robot and the directory registration service.

This example takes two different IP addresses as arguments. The `--host-ip` argument describes the IP address for the computer that will be running the service. A helper exists to try to determine the correct IP address. This command must be run on the same computer that will be running the remote mission service:

```
python3 -m bosdyn.client {ROBOT_IP} self-ip
```

The other IP address is the traditional robot hostname ("ROBOT_IP") argument, which describes the IP address of the robot hosting the directory service.

Now if you run the example client with:

```
python3 remote_mission_client.py --power-off robot ROBOT_IP
```

The robot should shut down and you will see this output from the client:

```
Servicer stopped with status STATUS_SUCCESS
```

To see the servicer actually power the robot off, you will have to perform the following steps:

1. Use the wasd example to power the robot on and stand it up.
2. Return wasd's lease with the [l] key.
3. Run the client.

You must run the client within 3 seconds of returning wasd's lease, otherwise the normal comms loss policy will kick in. To avoid Lease errors when triggering the callback via the tablet, select the "3rd Party" option before confirming the action.

## Using the example as part of an Autowalk mission

The mission service examples will work as part of an Autowalk mission, performing its action when Spot reaches a callback.

### Step one: Start the remote mission server

The following two command lines show starting the service on a CORE or a wifi laptop

```
(on core) python3 hello_world_mission_service.py robot --host-ip 192.168.50.5 192.168.50.3

(on laptop over wifi) python3 hello_world_mission_service.py robot --host-ip {YOUR_IP} --port {OPEN_PORT} 192.168.80.3
```

both commands should output something like:

```
2020-10-30 14:21:41,577 - INFO - Started the HelloWorldServicer server.
2020-10-30 14:21:41,585 - INFO - hello-world-callback service registered/updated.
2020-10-30 14:21:41,585 - INFO - Starting directory registration loop for hello-world-callback
```

Note that both commands target the robot, but also inform the robot of the ip address where the server itself is running. You may have to change your firewall settings in order for communication to succeed.

### Step two: Record an Autowalk mission with a callback

You must start the server (Step one) prior to recording the Autowalk mission.

1. On the Tablet, select Actions from the hamburger menu. You should see the callback listed, such as "Hello World Callback". Note that if you did not do Step one, this does not appear!
2. If you click on Callback Default, you can name the callback and configure any user variables you'd like to send to the server.
3. Stand up Spot and select Autowalk.
4. Move the robot a bit and then select the + sign to create an action waypoint.
5. Select your callback.
6. Finish the recording and playback, you should see your server print out something like:

```
2020-11-04 14:00:24,695 - INFO - EstablishSession unimplemented!
2020-11-04 14:00:34,009 - INFO - Hello Hello World Callback - Hello World Callback - 1!
2020-11-04 14:00:34,109 - INFO - Stop unimplemented!
```

Note that the "Hello Hello World Callback - Hello World Callback - 1!" shows that you did indeed receive the callback, so you only now need to implement the methods in the server to perform your desired work, make decisions, etc.
