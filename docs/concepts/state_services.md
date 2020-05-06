<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# [Spot SDK](../../README.md) > [Concepts](README.md) > State Services

Spot tracks knowledge about multiple sources of state, including the robot’s current physical state, the images captured by its cameras, and the terrain and objects around it.  This state information can be used to make decisions about how to control the robot or how to command the robot from a higher level application. The different state services available on Spot are:
- Robot State Service
- Image Service
- Local Grid Service
- World Object Service


## robot-state
The robot state service tracks all information about the measured and computed states of the robot at the current time.

The hardware configuration of the robot is described through a urdf and skeleton model, which represents each joint and link of the robot, and can be accessed using the `GetRobotHardwareConfiguration` rpc. This configuration representation is fully expressive of the robot’s joint states relative to each other and can be used to visualize the robot model.

The full robot state includes information about the batteries and power status, the status of network communication, known estop states, the foot states, system and behavior faults, and the kinematic state of the robot. The `GetRobotState` rpc can provide this state information for the current timestamp.
- **BatteryState, PowerState**: The battery and power information can be used to determine if the robot successfully powered on or off, the current charge of the battery, or if the battery is overheating. Applications can use this information to determine when to pause the progression of the application or if the robot needs a new battery.
- **CommsState**: The robot can report the type of communication network being used, so whether the robot is an access point or a client itself.
- **EStopState**: The robot can have multiple different E-Stops at once, including both software and hardware E-Stops, and the robot state service will track the names of these E-Stops and whether or not they are activated. If any one E-Stop is activated, then the robot will be unable to power on the actuators.
- **FootState**: The foot states of the robot describe the current position of the foot as an (x,y,z) coordinate with respect to the body, and whether or not the robot believes this foot is in contact with the ground at the given time.
- **SystemFaultState**: The system faults can inform a user about a perception fault with a certain camera or if a battery is overheating. The robot state services track both active faults that could affect robot operation, as well as historical faults that have occurred, which can be used to diagnose unexpected robot behavior. A fault can be related to both software and hardware for the robot, and is described with an error code and message, and a level of severity. An application can use this information to monitor the health of the robot and respond appropriately if a fault appears. For example, the tablet application will warn a user when there's a perception fault since this can significantly impact how well the robot navigates the terrain.
- **BehaviorFaultState**: Similar to a system fault, the behavior faults track errors related to behavior commands and issue warnings if a certain behavior fault will prevent execution of subsequent commands. The fault is described through an id, the potential cause of the fault, and if it can be cleared. An application can monitor these faults and respond to clearable faults; often times a behavior fault can be cleared and the application can continue its normal execution.
- **KinematicState**: The kinematic state of the robot describes the current estimated positions of the robot body and joints throughout the world. It includes a transform snapshot of the robot’s current known frames as well as joint states and the velocity of the body.

The robot state service also tracks different parameters for the robot and this information can be accessed with the `GetRobotMetrics` rpc. These metrics can be useful for monitoring the system status and health of the robot.


## image
Spot can have many different image sources, including the cameras on the base platform or any other payloads which implement the image service proto definitions, like Spot CAM. The image service provides a way to list all these different sources using the `ListImageSources` rpc and then query the sources for their images with the `GetImage` rpc.

Images can be regular pixel-based visual images, where the data value corresponds to the greyscale (or color) intensity, or depth images, where the data value corresponds to the depth measured from the camera sensor. These image types can also be combined by reprojecting the depth onto the visual image, as shown in [get_depth_plus_visual_image.py](../../python/examples/get_depth_plus_visual_image/README.md), which allows an application to use a detected bounding box of an object and determine a transform from the camera sensor to the detected object using on the pixel coordinates of the bounding box.

Since an image can be a lot of data, there are also different types of encodings and compression schemes that the image can be transmitted as to reduce the size of the data sent over the wire. The image service offers a `Format` field to describe the encoding of the image: `JPEG`, a lossy compression with tunable image quality, `RLE`, a run length encoding, or `RAW`, the raw uncompressed image data.


## local-grid
Spot uses its sensor and information about its body to develop an idea about the terrain and obstacles near to the robot. This information is stored as a grid-based map where each cell of the grid has a parameterized dimension and relates to a specific location in the world specified in the frame tree snapshot. The grid cells contain information about the surrounding environment and terrain local to Spot. The local grid service does not store or compose the grids over time, but rather creates a grid for each instance of time based on Spot’s current location and surroundings. The different types of grids available in the local grid service are “terrain”, “terrain_valid”, “intensity”, “no_step”, and “obstacle_distance” grids. Similar to the image service, these grid sources can be listed using the `GetLocalGridTypes` rpc, and then the grid data can be requested with the `GetLocalGrids` rpc.

Spot’s estimates of the height of the terrain are stored in the “terrain” grid, where each data value for a given cell represents the z-height of the world. This grid source can be combined with the “terrain_valid” grid to filter cells which have invalid height estimates. A cell could be considered invalid if the height estimate is too extreme for Spot’s sensors. As well, the intensity values of each terrain grid cell are stored as raw grayscale values in the “intensity” grid source and can be used to colorize the terrain grid.<br>

![Obstacle Distance Example Grid](obstacle_map.png)

Spot considers walls, large obstacles, and even platforms that are too high (a height of > 40 cm) to be obstacles. Information about the obstacles near the robot is stored in the “obstacle_distance” grid, where the data value in each grid cell represents the signed distance to the nearest obstacle region. A positive distance is measured from outside the obstacle, and a negative distance is measured from inside the obstacle. For example, the image shows a box being considered an obstacle by Spot, and the fake "obstacle_distance" grid with cell values representing distance in an arbitrary unit. Knowing the distance to the nearest obstacle can be used within an application to determine where the robot is able to walk or to create a safety barrier for the robot such that it must remain a certain distance from all obstacles.

In addition to detecting obstacles, Spot can use information about its body and the nearby terrain and obstacles to determine whether or not it is capable of stepping in a certain location. The “no_step” grid stores this information within each grid cell as a boolean value.



## world-object
The world object service provides a way to track and store objects detected in the world around Spot. A world object is considered a higher-level item in the scene that has some amount of semantic information associated with it. For example, a world object could be an AprilTag fiducial, a door handle, the stairs, or a virtual object drawn for debugging purposes. While these objects all have different properties associated with them, they also share common properties of a human-readable name, an id assigned by the world object service, an acquisition timestamp representing the time at which the object was most recently detected, and a transform snapshot (described in the [Geometry and Frames](geometry_and_frames.md) section) with transform information for the given acquisition timestamp. The service assigns the id to the object when it is first detected such that it is guaranteed to be unique, and it will re-associate this id with the object across detections.

Currently, the most common use case of the world object service is to expose Spot’s internal detection of AprilTag fiducials from the robot’s base cameras. Fiducials are commonly used as ground truth reference objects, notably in the GraphNav system to initialize the robot’s localization. Any fiducials detected within the robot’s base cameras will be returned as world objects through the service. The `ListWorldObjects` rpc will return all world objects detected by Spot within the last 15 seconds, and can be filtered to return only certain types of objects or objects after a specific timestamp.

In addition to tracking objects detected by Spot’s base cameras, the world object service allows users to inform Spot of other objects that could be detected, either with the base cameras or through other cameras, using the `MutateWorldObjects` rpc. For example, if an application using Spot CAM detects fiducials at a much larger range than the base platform, this information can be added into the world object service and used to improve performance of applications which rely on fiducials or influence different behaviors.

The `MutateWorldObjects` rpc allows objects to be added, changed/modified, or removed from the perception scene. A request which adds an object to the scene will inform Spot about the new object and return a unique id for this new object to the client application. A request which changes or deletes an object from the scene will only be applied to the objects that are added by external applications and require the object id assigned by the world object service when the object is first added to the scene to correctly identify which object to modify or delete. The world objects detected by Spot’s base platform cannot be modified or deleted by external applications.

The ability to mutate and add objects into Spot’s perception scene can be used to enhance the performance of existing applications, such as GraphNav, or can be used to communicate to multiple clients about different objects. For example, one client application could be running on an external GPU to detect bounding boxes of a certain object; this client can send this information to Spot as image coordinates in the world object service such that a different client application can use these coordinates to get the location of this object in the vision frame.
