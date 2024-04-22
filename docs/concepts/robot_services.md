<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Robot Services

Spot tracks knowledge about multiple sources of state, including the robot's current physical state, the images captured by its cameras, and the terrain and objects around it.  This state information can be used to make decisions about how to control the robot or how to command the robot from a higher level application. The different state services available on Spot are:

*  Robot State Service
*  Image Service
*  Local Grid Service
*  World Object Service

To command and operate Spot, a client must take additional steps beyond authentication.  The client establishes application-layer time synchronization and acquires a lease; both processes are streamlined by the SDK.  Once fully in control of the robot, the client will need to maintain the software stop, enable motor power and send commands.

*  E-Stop Service
*  Power Service
*  Robot Command Service


## estop
The E-Stop service provides a secondary keep-alive mechanism by acting as a software stop.

First the E-Stop configuration is set; this specifies the expected endpoints (at least one) and their timeout.  Before enabling motor power all endpoints must be registered and checking in.

During operation all endpoints will be periodically checking in.  If an endpoint fails to check in (or does check in but denies the authority to operate) then the robot will turn off motor power.

Note:
- Abruptly turning off motor power will cause the robot to drop, clients are encouraged to use `stop_level=SETTLE_THEN_CUT` or the `SafePowerOffCommand` where possible.
- Changing the E-Stop configuration when motor power is on will abruptly turn it off, clients are encouraged to turn off motor power first.

The [E-Stop documentation](estop_service.md) provides a more in-depth description of E-stop configurations, registration and check-ins.

## power
The power service allows a client to power the motors on and off.

To turn on, the client should send a `PowerCommandRequest` RPC with `REQUEST_ON`.  This may take a few seconds.

To turn off, clients are encouraged to use the `SafePowerOffCommand` RPC from the robot-command service in nominal operation.  This RPC part of the robot-command service because it coordinates gently sitting the robot down prior to turning off motor power.  To turn off quickly, the client should send a `PowerCommandRequest` RPC with `REQUEST_OFF`.


## robot-command
The robot command service allows a client to move the robot.

There are many commands exposed to clients to make the robot self-right, sit, stand, move to a position, move with a velocity, stop and power off.  Most commands have associated parameters, for example the stand command contains an optional offset allowing the client to orient the robot's body.

Clients are encouraged to send short-lived commands and continuously resend them so that the robot stops in the even of a client-side issue.  For longer commands, client should cache the id returned by the CommandResponse and poll the associated CommandFeedbackRequest to monitor the command.

## robot-state
The robot state service tracks all information about the measured and computed states of the robot at the current time.

The hardware configuration of the robot is described through a urdf and skeleton model, which represents each joint and link of the robot, and can be accessed using the `GetRobotHardwareConfiguration` RPC. This configuration representation is fully expressive of the robot's joint states relative to each other and can be used to visualize the robot model. A urdf model of the base robot and its geometry can also be found [here](../../files/spot_base_urdf.zip).

The full robot state includes information about the batteries and power status, the status of network communication, known E-Stop states, the foot states, system and behavior faults, and the kinematic state of the robot. The `GetRobotState` RPC can provide this state information for the current timestamp.
*  **BatteryState, PowerState**: The battery and power information can be used to determine if the robot successfully powered on or off, the current charge of the battery, or if the battery is overheating. Applications can use this information to determine when to pause the progression of the application or if the robot needs a new battery.
*  **CommsState**: The robot can report the type of communication network being used, so whether the robot is an access point or a client itself.
*  **EStopState**: The robot can have multiple different E-Stops at once, including both software and hardware E-Stops, and the robot state service will track the names of these E-Stops and whether or not they are activated. If any one E-Stop is activated, then the robot will be unable to power on the actuators.
*  **FootState**: The foot states of the robot describe the current position of the foot as an (x,y,z) coordinate with respect to the body, and whether or not the robot believes this foot is in contact with the ground at the given time.
*  **SystemFaultState**: The system faults can inform a user about a perception fault with a certain camera or if a battery is overheating. The robot state services track both active faults that could affect robot operation, as well as historical faults that have occurred, which can be used to diagnose unexpected robot behavior. A fault can be related to both software and hardware for the robot, and is described with an error code and message, and a level of severity. An application can use this information to monitor the health of the robot and respond appropriately if a fault appears. For example, the tablet application will warn a user when there's a perception fault since this can significantly impact how well the robot navigates the terrain.
*  **BehaviorFaultState**: Similar to a system fault, the behavior faults track errors related to behavior commands and issue warnings if a certain behavior fault will prevent execution of subsequent commands. The fault is described through an id, the potential cause of the fault, and if it can be cleared. An application can monitor these faults and respond to clearable faults; often times a behavior fault can be cleared and the application can continue its normal execution.
*  **KinematicState**: The kinematic state of the robot describes the current estimated positions of the robot body and joints throughout the world. It includes a transform snapshot of the robot’s current known frames as well as joint states and the velocity of the body.
*  **SystemState**: The system state can be used to determine if the robot's motors are running hot.


The robot state service also tracks different parameters for the robot and this information can be accessed with the `GetRobotMetrics` RPC. These metrics can be useful for monitoring the system status and health of the robot.

## log-status
The log status service provides users access to files Spot generates that contains data about its performance during operation. Files can be generated with data from the past, such files are known as retro logs. Files can also be generated with present data and into the future, such files are called experiment logs. The `LogStatus` object in the response of each API displays the status of the requested file and the id that can be provided to BD support for assistance in debugging issues. The steps for sending logs to our support team are outlined [here](https://support.bostondynamics.com/s/article/Spot-robot-logging#DownloadSendLog).

## metrics_logging
The metrics logging service aggregates internal operation and usability metrics to help Boston Dynamics improve performance and user experience. You can retrieve metrics by using the RPCs defined in the [service definition](../../protos/bosdyn/api/metrics_logging/metrics_logging_robot_service.proto). For a working example, see `Metrics over CORE I/O` from [Payloads Examples](../../python/examples/docs/payloads_examples.md), which uses the [MetricsLoggingClient](../../python/bosdyn-client/src/bosdyn/client/metrics_logging.py).

## image

Spot can have many different image sources, including the cameras on the base platform or any other payloads which implement the image service proto definitions, like Spot CAM. The image service provides a way to list all these different sources using the `ListImageSources` RPC and then query the sources for their images with the `GetImage` RPC.

Images can be regular pixel-based visual images where the data value corresponds to the greyscale (or color) intensity. They can also be depth images where the data value corresponds to the depth measured from the camera sensor. To align depth data with visual image data, use the `depth_in_visual_frame` sources ([example code](../../python/examples/get_depth_plus_visual_image/README.md)), which reprojects the depth onto the same projection as the visual image.

Since an image can be a lot of data, there are also different types of encodings and compression schemes that the image can be transmitted as to reduce the size of the data sent over the wire. The image service offers a `Format` field to describe the encoding of the image:

*  `JPEG`: a lossy compression with tunable image quality
*  `RLE`: a run length encoding
*  `RAW`: the raw uncompressed image data


## local-grid

Spot uses its sensors and information about its body to develop an idea about nearby terrain and obstacles. This information is stored as a grid-based map where each cell of the grid has a parameterized dimension and relates to a specific location in the world specified in the frame tree snapshot.

The grid cells contain information about the surrounding environment and terrain local to Spot. The local grid service does not store or compose the grids over time, but rather creates a grid for each instance of time based on Spot's current location and surroundings.

The different types of grids available in the local grid service are "terrain," "terrain_valid," "intensity," "no_step," and "obstacle_distance" grids. Similar to the image service, these grid sources can be listed using the `GetLocalGridTypes` RPC, and then the grid data can be requested with the `GetLocalGrids` RPC.

The Spot robot's estimates of the height of the terrain are stored in the "terrain" grid, where each data value for a given cell represents the z-height of the world. This grid source can be combined with the "terrain_valid" grid to filter cells which have invalid height estimates. A cell could be considered invalid if the height estimate is too extreme for Spot's sensors. In addition, the intensity values of each terrain grid cell are stored as raw grayscale values in the "intensity" grid source and can be used to colorize the terrain grid.



![Obstacle Distance Example Grid](obstacle_map.png)



Spot considers walls, large obstacles, and even platforms that are too high (a height of > 40 cm) to be obstacles. Information about the obstacles near the robot is stored in the "obstacle_distance" grid, where the data value in each grid cell represents the signed distance to the nearest obstacle region.

A positive distance is measured from outside the obstacle, and a negative distance is measured from inside the obstacle. For example, the image shows a box being considered an obstacle by Spot, and the fake "obstacle_distance" grid with cell values representing distance in an arbitrary unit. Knowing the distance to the nearest obstacle can be used within an application to determine where the robot is able to walk or to create a safety barrier for the robot such that it must remain a certain distance from all obstacles.

In addition to detecting obstacles, Spot can use information about its body and the nearby terrain and obstacles to determine whether or not it is capable of stepping in a certain location. The "no_step" grid stores this information within each grid cell as a boolean value.



## world-object

The world object service provides a way to track and store objects detected in the world around Spot. A world object is considered a higher-level item in the scene that has some amount of semantic information associated with it. For example, a world object could be an AprilTag fiducial, a door handle, the stairs, or a virtual object drawn for debugging purposes.

While these objects all have different properties associated with them, they also share common properties of a human-readable name, an id assigned by the world object service, an acquisition timestamp representing the time at which the object was most recently detected, and a transform snapshot (described in the [Geometry and Frames](geometry_and_frames.md) section) with transform information for the given acquisition timestamp. The service assigns a guaranteed unique id to the object when it is first detected. The service will re-associate this id with the object across detections.

Currently, the most common use case for the world object service is to expose Spot's internal detection of AprilTag fiducials from the robot's base cameras. Fiducials are commonly used as ground truth reference objects, notably in the GraphNav system to initialize the robot's localization. Any fiducials detected within the robot's base cameras will be returned as world objects through the service. The `ListWorldObjects` RPC will return all world objects detected by Spot within the last 15 seconds, and can be filtered to return only certain types of objects or objects after a specific timestamp.

In addition to tracking objects detected by Spot's base cameras, the world object service allows users to inform Spot of other objects that could be detected, either with the base cameras or through other cameras, using the `MutateWorldObjects` RPC. For example, if an application using Spot CAM detects fiducials at a much larger range than the base platform, this information can be added into the world object service and used to improve performance of applications which rely on fiducials or influence different behaviors.

The `MutateWorldObjects` RPC allows objects to be added, changed/modified, or removed from the perception scene. A request which adds an object to the scene will inform Spot about the new object and return a unique id for this new object to the client application. A request which changes or deletes an object from the scene will only be applied to the objects that are added by external applications and require the object id assigned by the world object service when the object is first added to the scene to correctly identify which object to modify or delete. The world objects detected by Spot's base platform cannot be modified or deleted by external applications.

The ability to mutate and add objects into Spot's perception scene can be used to enhance the performance of existing applications, such as GraphNav, or can be used to communicate to multiple clients about different objects. For example, one client application could be running on an external GPU to detect bounding boxes of a certain object; this client can send this information to Spot as image coordinates in the world object service such that a different client application can use these coordinates to get the location of this object in the vision frame.
