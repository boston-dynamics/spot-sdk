<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Fan Power Commands with the Python SDK

This example

1. Provides a basic Python script to call and receive feedback on a fan command
2. Provides a usable template for writing a callback that issues and blocks during a fan command.

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Using Fan Commands

Fan Commands request the robot to power the fans to a certain percent level (0 being off, 100 being full power) for a certain duration, for use cases such as temporarily turning the fans off during an audio recording. They require the client to own the fan lease to take effect, and as with other long-running commands have a parallel Fan Command Feedback request that can give the status of a previously issued fan command by passing in the previous fan command's ID.

A fan command returns header information, lease information, a status, the desired command end time, and a command ID for future feedback queries. A fan command should return one of two immediate statuses:

1. STATUS_OK: Indicates that the robot is cool enough to accept the command and will attempt to execute the command
2. STATUS_TEMPERATURE_TOO_HIGH: Indicates that at the time the command was received, the robot was already too hot to safely execute this command, and therefore is rejecting the command.

A fan command being accepted does not guarantee that it'll work for its entire duration, however. This results in the following possible feedback statuses:

1. STATUS_COMPLETE: The queried fan command succeeded for its entire duration, and is now no longer in effect due to being past the desired end time.
2. STATUS_RUNNING: The queried fan command is still in effect, but the current time is before the fan command's desired end time.
3. STATUS_TEMPERATURE_STOP: At some point during the queried fan command's desired in-effect period (either when initially issued or before the desired end time), the robot ran too hot and therefore took back control of the fans
4. STATUS_OVERRIDDEN_BY_COMMAND: The queried fan command had been running successfully, but then another fan command was received which overrode the queried fan command.

Feedback also provides standard header info, copies the desired end time of the queried command, and for cases (3) and (4) provides an early stop time when the queried command stopped being in effect.

## Running The Fan Command Examples

### General Fan Command Usage

Using fan commands in Python begins with the establishment of a Power Client, generally through something like

```
power_client = robot.ensure_client(PowerClient.default_service_name)
```

Once this is established, one can use `power_client.fan_power_command(percent_power, duration, lease=None)` to issue a Fan Command, where duration is in seconds and the lease can be passed through context such as a LeaseKeepAlive. One can then use `power_client.fan_power_command_feedback(command_id)` with the command ID returned from a fan command to get feedback on a past fan command.

### Basic Fan Command Example

To run the basic fan command example, run:

```
python3 basic_fan_command.py ROBOT_IP
```

Out of the box, this example issues a command that turns the fans on to full power (100%) for 5 seconds, and checks the feedback both during and after the command. This can be easily adjusted for cases such as turning the fans off as well as attempting to explore other feedback responses.

### Fan Remote Mission Service

This is an example remote mission service that allows a tablet user to issue a fan command during an Autowalk that (in the out-of-the-box configuration) will turn the fans off for 10 seconds. This is heavily modeled off of the existing "power_off_mission_service" in the Remote Mission Service Examples.

As with the other remote mission service examples, you will need a connection between a robot and the computer running the examples.

```
python3 fan_control_mission_service.py --host-ip {ENDPOINT_IP} ROBOT_IP
```

This example takes two different IP addresses as arguments. The `--host-ip` argument describes the IP address for the computer that will be running the service. A helper exists to try to determine the correct IP address. This command must be run on the same computer that will be running the remote mission service, with the computer connected to the robot's wifi ssid:

```
python3 -m bosdyn.client 192.168.80.3 self-ip
```

The other IP address is the traditional robot hostname ("ROBOT_IP") argument, which describes the IP address of the robot hosting the directory service. This is `192.168.80.3` when connected to the robot's wifi. You may also supply an additional `--fan-off-secs` argument followed by a desired number of seconds that the callback will turn the fans off for (default: 10 seconds).

To avoid Lease errors when triggering the callback via the tablet, select the "3rd Party" option before confirming the action. See the steps in the Remote Mission Service examples for more detailed information about how to use this service alongside the tablet in an Autowalk.
