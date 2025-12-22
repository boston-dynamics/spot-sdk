<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Hazard Avoidance

Spot provides the ability to specifiy "hazards" in Spot's vicinity, which modify both where Spot can walk and where Spot will prefer to walk during autonomous navigation. This service is the same used by Spot's [hazard avoidance capabilities based on foundation models](https://bostondynamics.com/blog/put-it-in-context-with-visual-foundation-models/), which were introduced in the 4.1 software release.

Note that this service only provides the means to communicate to Spot the locations and properties of hazards. To take advantage of this service, the user needs to implement a separate application for detecting hazards from raw sensor data (or otherwise determining the existence of hazards).

## What are "hazards" in this context?

Conceptually, a "hazard" is an object or area that a user desires Spot to avoid. This could be due to a dangerous situation, like spilled liquid in Spot's path or unstable terrain. It could also be an operational concern, such as preventing Spot from crossing certain boundaries. It is not a safety system and is not a way to report dangerous conditions to Spot's operator.

### When might a user want to add hazards?

This API provides a flexible way to modify where Spot will or will not navigate, which can be used for many different reasons. There are three major cases why a user might want to though:

1. To identify obstacles Spot may not otherwise see. For example, thin wires and glass walls might be missed by Spot's ordinary obstacle detection system.
2. To identify dangers to Spot that cannot be inferred from geometry alone. For example, the shape of a wheeled cart may resemble a stable platform Spot could traverse, when in reality it would be dangerous for Spot to attempt to do so.
3. To identify objects or regions that are not directly dangerous to Spot but which should still be avoided. For example, preventing Spot from walking under a ladder or telling Spot not to step on specific pieces of equipment that could be damaged.

Generally, this service can be used when a user desires Spot to avoid walking over something that it would otherwise.

### What are some considerations when adding hazards?

The primary consideration will be the tradeoff between avoiding the hazard and sucessfully navigating to a location. If hazard observations are added too aggressively, it may become impossible for Spot to reach its destination, or perhaps even move at all. One aspect of this is the type associated to the hazard. Types that enforce strict avoidance (`TYPE_NEVER_STEP_ON`, `TYPE_NEVER_STEP_ACROSS`, and similar) will block potential paths for Spot; too many of these can lead to all paths being blocked. On the other hand, types that only encourage avoidance (`TYPE_PREFER_AVOID_WEAK` and `TYPE_PREFER_AVOID_STRONG`) will never prevent Spot from navigating to a location but also may not prevent Spot from avoiding the hazard. Another consideration is the size of the hazard. If the geometry specified in the hazard observation is large, Spot will need to avoid a wider region. This could lead to large deviations from the desired path or cause Spot to become stuck.

It is important for a user to observe and assess Spot's behavior after adding a hazard. If Spot appears to be behaving too cautiously and/or is unable to navigate to a desired location, the user may need to specify a smaller size for the hazard or a more permissive type. If Spot is too aggressive and fails to avoid the hazard, the user may need to specify a more restrictive type or increase the size of the hazard. Furthermore, always verify that the frames and associated transforms provided in a `HazardObservation` are correct, as otherwise Spot will believe the hazard to be at an incorrect location.

## Requesting To Add Hazards

The [Hazard Avoidance Service](../../../protos/bosdyn/api/hazard_avoidance_service.proto) enables a client to submit [requests to add hazard observations](../../../protos/bosdyn/api/hazard_avoidance.proto) that will be used to modify Spot's navigation.

## Hazard Observations

An instance of a `AddHazardsRequest` contains a list of `HazardObservation`s. Each hazard observation specifies the geometry and location of a hazard, as well as how Spot should treat the region occupied by that geometry. The observation may also optionally specify a margin around the hazard. A `HazardObservation` will expire over time, causing Spot to "forget" about it unless a new observation is submitted. Therefore `AddHazardsRequest`s should continue to be submitted as long as the hazard remains present in the world. It is recommended to submit these requests at a rate of 2Hz to 10Hz.

### How to specify observation data

There are currently five ways to describe the geometry of a hazard:

1. As a `PointCloud`:
   - This will contain a list of 3D points corresponding to the hazard.
   - The points should be expressed in a stationary frame, such as "odom" or "vision".
2. As an `ImageCaptureAndSource`:
   - This will contain an `ImageCapture`, with a segmented depth image (of type `PIXEL_FORMAT_DEPTH_U16`). Each positive pixel represents the distance to a point on the hazard.
   - The `ImageCapture` will also contain a `FrameTreeSnapshot` that describes the pose of the camera relative to the "vision" (visual odometry) frame of Spot at the time the observation occurred.
   - This will also contain an `ImageSource`, with a `PinholeModel` and `depth_scale` describing the intrinsics of the camera.
3. As a `Box2WithFrame`:
   - This will contain a 2D rectangle encompassing the footprint of the hazard.
   - This will also contain an `SE3Pose` with the (x, y) position and the yaw rotation of the box in the XY plane of Spot's "vision" (visual odometry) frame.
4. As a `Circle`:
   - This will contain a radius in meters and the center of the hazard along the XY plane of Spot's "vision" (visual odometry) frame.
5. As a `CircleList`:
   - This will contain a list of `Circle`s, each treated as described above.

### How to specify observation type

There are currently seven "types" that can be specified to determine how Spot should treat the region occupied by a hazard:

1. `TYPE_NEVER_STEP_ACROSS`
   - Treats the hazard as an obstacle, and will prevent Spot from moving any part of its body over the region occupied by the hazard. Any margin is treated the same.
   - This will impact Spot's behavior in all scenarios, including teleop control.
   - Example use cases: carts, ladders, dangling wires, and other things that are hazardous for Spot to move under or over.
   - This is the most restrictive type as well as the most commonly used.
2. `TYPE_NEVER_STEP_ON`
   - Will prevent Spot from placing any foot in the region occupied by the hazard, but Spot may still step over the region. Any margin is treated the same.
   - This will impact Spot's behavior in all scenarios, including teleop control.
   - Example use cases: wires on the floor, holes, ice, and other things that could cause Spot to trip/fall. Other good use cases would be equipment and items that a user wishes Spot to avoid stepping on (regardless of danger to Spot itself).
3. `TYPE_PREFER_AVOID_WEAK`
   - Will add a low penalty for Spot to walk over the hazard during autonomous navigation. Any margin is treated the same.
   - This only impacts Spot's behavior during autonomous navigation, such as executing an autowalk mission.
   - Example use case: avoiding puddles, small debris, spills, and other things Spot should try to walk around but aren't dangerous.
4. `TYPE_PREFER_AVOID_STRONG`
   - Will add a high penalty for Spot to walk over the hazard during autonomous navigation. Any margin is treated the same.
   - This only impacts Spot's behavior during autonomous navigation, such as executing an autowalk mission.
   - Example use case: avoiding pallets, large debris, and other things Spot should try to walk around that could inhibit its mobility.
5. `TYPE_PREFER_STEP_ON`
   - Opposite of a hazard. Will clear previous hazards from the space occupied by the observation, and mark the region as a "good" place for Spot to walk. Any margin is treated the same.
   - Example use cases: floor, flat ground, sidewalks, and other surfaces that Spot should prefer to walk over.
6. `TYPE_NEVER_STEP_ON_AVOID_MARGIN`
   - The same as `TYPE_NEVER_STEP_ON`, except the margin around Spot will be treated as `TYPE_PREFER_AVOID_WEAK`.
7. `TYPE_NEVER_STEP_ACROSS_AVOID_MARGIN`
   - The same as `TYPE_NEVER_STEP_ACROSS`, except the margin around Spot will be treated as `TYPE_PREFER_AVOID_STRONG`.

### Additional components of a hazard observation

In addition to the geometry and type of the hazard, an observation will also specify:

1. The `likelihood` of the observation, a value from 0 to 1 representing the confidence that the hazard exists. This affects how strongly and for how long a hazard observation will influence Spot's behavior, with larger values corresponding to stronger influence that persists for longer durations.
2. A `semantic_label` that provides a human-interpetable label for the kind of hazard encountered (e.g., `wires`, `spill`). This is just for debugging convenience and has no impact on Spot's behavior.
3. A `margin` around the hazard, in meters. A positive margin will expand the region covered by the observation, with the region covered by the margin handled as described above. A negative margin will shrink the region covered by the observation.
