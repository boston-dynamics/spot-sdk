<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# GraphNav Localization

Once the robot’s location has been initialized in GraphNav, clients can use the `GetLocalizationState` RPC. The response message will contain a localization object which reports the pose of the robot relative to a particular waypoint on the map.

A map's waypoints are combined with the cumulative point cloud data captured at each waypoint. It's important to understand that this point cloud data does not result in global consistency.


## Localization update interval

GraphNav updates localization at least twice a second. Internally, GraphNav uses the localization estimate to decide whether or not to switch the localization frame to a different waypoint on the map.

Localization is computed by combining prior information from the map, the robot’s odometry, and visual and geometric features in the world around the robot. The quality of the pose estimate varies depending on the environment, the sensor payload on Spot, how far away the robot is from a waypoint and how the robot got to its current position.

Situations that can have a negative effect on localization:


*   The robot is far enough away from the recorded map that it cannot see any features recorded in the map for a long period of time
*   The robot slips and falls or is carried to a new location while unpowered
*   The environment has changed dramatically since the map was recorded
*   The environment has few features
*   The environment is too dark

A robot equipped with a LIDAR payload can operate in darker environments than a robot without such a payload.


## Feature Deserts

GraphNav depends on features in the environment to localize. Where features are lacking, localization is more difficult or impossible.

For example, every position on a snow-covered field looks the same — there isn't enough detail for localization to succeed. Internally GraphNav estimates whether the robot's location provides sufficient data for localization. If not, any waypoints created are annotated as feature deserts.

GraphNav will not attempt to localize in feature deserts. Instead, it will rely on odometry to allow the robot to cross small feature deserts.


## Lost robots

The GraphNav service maintains an internal assessment of whether or not it believes the robot is lost or stuck. When lost, the service will refuse to navigate autonomously.

This determination is correlated with the amount of change in the environment where the map was recorded. A site that has changed significantly since recording will look very different to the robot. For example, a map of an empty parking lot will look different when cars are parked there.

When site changes cause the localization status to be `STATUS_LOST`, a new map of the site should be recorded.


## Stuck robots

The GraphNav service uses a system of constraints to keep the robot relatively close to the recorded route (roughly within a 3m corridor).

If a large object is placed in the robot’s path, the robot may not be able to get around it. If the robot takes longer than expected to get to its next destination, GraphNav will declare the robot stuck. This does NOT stop the robot, which will keep trying to return to the route. However, the API client may wish to intervene or prompt the operator.


## Stairs and other edge constraints

When recording a map that includes stairs, annotations will be added to the relevant edges in the map. The system will orient the robot to face up the stairs (both when ascending and descending) and reduce the maximum speed. Typically this results in the robot turning in place at the top of a stairwell and carefully descending.

Edges may also be annotated with related constraints to maintain direction. For example, this allows the robot to safely traverse stairs connected to a narrow hallway by turning around before entering the narrow region.

The robot must have enough space to turn around in between up- and down- stairs, otherwise the robot will report a navigation status of `STATUS_CONSTRAINT_FAULT`.

## GraphNav Origin
The localization object includes an additional field `seed_tform_body` since the 2.1.0 release. This field returns the pose of the robot body with respect to the starting fiducial frame as an SE3Pose, which can be considered the "origin" or "seed" of the GraphNav map.

Please reference this [document](https://support.bostondynamics.com/s/article/Site-inspection-with-teleoperation) for how to initialize and define a custom origin using the Tablet App outside of Autowalk since the 2.1.0 release. 

An example of how to access this field with the Spot API is available below. Please remember to initialize the GraphNav map first or the SE3Pose will be not be populated.

```python
def get_graphnav_origin(self):
    """ Returns seed_tform_body. """
    graph_nav_client = self.bosdyn_sdk_robot.ensure_client(GraphNavClient.default_service_name)
    state = graph_nav_client.get_localization_state()
    gn_origin_tform_body = state.localization.seed_tform_body
    return math_helpers.SE3Pose.from_proto(gn_origin_tform_body)
```

<!--- image and page reference link definitions --->
[autonomous-top]: Readme.md "Spot SDK: Autonomy, GraphNav, and Missions"
[code-examples]: autonomous_navigation_code_examples.md "Autonomous navigation code examples"
[components]: components_of_autonomous_navigation.md "Components of autonomous navigation"
[typical]: typical_autonomous_navigation_use_case.md "Typical autonomous navigation use cases"
[autonomous-services]: autonomous_navigation_services.md "Autonomous navigation services"
[service]: graphnav_service.md "GraphNav service"
[map-structure]: graphnav_map_structure.md "GraphNav map structure"
[initialization]: initialization.md "Initialization"
[localization]: localization.md "Localization"
[locomotion]: graphnav_and_robot_locomotion.md "GraphNav and robot locomotion"
[missions]: missions_service.md "Missions service"
