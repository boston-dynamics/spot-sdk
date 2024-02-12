<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Spot Choreography SDK

Develop advanced choreographed routines for Spot. The choreography service requires a special-permissions license, as well as Python and Spot SDK.

The Choreography SDK consists of:
  * The Choreography related API protocol definitions, found [here](../../../protos/bosdyn/api/README), defines choreography moves and parameters.
  * The Choreography [python client](../../../python/bosdyn-choreography-client/src/bosdyn/choreography/client/README) communicates with Spot to upload and execute sequences on the robot.
  * The Choreographer Application is used to author choreography sequences, synchronize music, and execute routines on the robot. The application, as well as additional documentation, can be downloaded from the [Support Center](https://support.bostondynamics.com) and used with a robot that has a choreography license.

This [documentation](choreography_service.md) provides an overview of the Choreography API and Client and a description of the different choreography terms. The [Move Reference Guide](move_reference.md) provides descriptions of each choreography move and its associated parameters, as well as GIF depictions of each move.

## Contents

* [Choreography Service](choreography_service.md)
* [Move Reference Guide](move_reference.md)
* [CustomGait Reference](custom_gait.md)
* [Choreographer Setup](choreographer_setup.md)
* [Choreographer Overview](choreographer.md)
* [Robot Connections in Choreographer](robot_controls_in_choreographer.md)
* [Animations in Choreography](animations_in_choreographer.md)
* [Animation File Format](animation_file_specification.md)
* [Tablet Choreography Mode](choreography_in_tablet.md)
* [Choreography Actions in Autowalk](choreography_in_autowalk.md)
