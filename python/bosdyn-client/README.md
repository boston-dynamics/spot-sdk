<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# bosdyn-client

<p align="center">
<img src="https://www.bostondynamics.com/sites/default/files/2020-05/spot.png" style="max-width:50%;">
</p>

The bosdyn-client wheel contains client interfaces for interacting with the Boston Dynamics Spot
API. The client interfaces implement the Remote Procedure Calls (RPCs) defined in the
[bosdyn-api wheel](https://pypi.org/project/bosdyn-api/).

## Main Classes

The main classes contained in this wheel are Sdk and Robot.

- **Sdk**: Class for settings typically common to a single developer and/or robot fleet.
- **Robot**: Class for settings common to one user's access to one robot. This is the main point
  of access to all client functionality.

For example, to list the robot image sources using the Image client, simply create an Sdk object,
create a Robot object, authenticate, create the client and call the
corresponding method, as shown below. It is that simple!

```pycon
>>> import bosdyn.client
>>> sdk = bosdyn.client.create_standard_sdk('image_capture')
>>> robot = sdk.create_robot(hostname)
>>> robot.authenticate(username, password)
>>> image_client = robot.ensure_client(ImageClient.default_service_name)
>>> image_sources = image_client.list_image_sources()
```

Clients that trigger robot movement also need to set up the TimeSync, Lease and E-Stop clients. Our
[examples](https://github.com/boston-dynamics/spot-sdk/tree/master/python/examples) repository
contains many tutorials on how to use the clients included in this wheel.

## Command-line Support

Some of the clients included in this wheel can also be accessed directly from the command-line.

```
python3 -m bosdyn.client hostname -h
usage: bosdyn.client [-h] [-v] [--username USERNAME] [--password PASSWORD]
                     hostname
                     {dir,id,state,log,time-sync,lease,become-estop,image,local_grid}
                     ...

Command-line interface for interacting with robot services.
...
```

For example, to list the robot image sources from the command-line:

```
$ python3 -m bosdyn.client hostname image list-sources
back_depth                     (240x424)
back_depth_in_visual_frame     (480x640)
back_fisheye_image             (480x640)
frontleft_depth                (240x424)
frontleft_depth_in_visual_frame (480x640)
frontleft_fisheye_image        (480x640)
frontright_depth               (240x424)
frontright_depth_in_visual_frame (480x640)
frontright_fisheye_image       (480x640)
left_depth                     (240x424)
left_depth_in_visual_frame     (480x640)
left_fisheye_image             (480x640)
right_depth                    (240x424)
right_depth_in_visual_frame    (480x640)
right_fisheye_image            (480x640)
```
