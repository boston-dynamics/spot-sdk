<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Spot Choreography SDK

Develop advanced choreographed routines for Spot. The choreography service requires a special-permissions license, as well as Python and Spot SDK.

The Choreography SDK consists of:
  * The Choreography API [protocol definitions](../../../choreography_protos/bosdyn/api/README), which defines the choreography moves and parameters.
  * The Choreography [python client](../../../python/bosdyn-choreography-client/src/bosdyn/choreography/client/README), which communicates with Spot to upload and execute choreographies on robot.
  * The Choreographer Application, which is an application to author choreographies and execute the routines on robot with music synchronization. The application, as well as additional documentation, can be downloaded from the [Support Center](https://support.bostondynamics.com) and used with a robot that has a choreography license.

The high-level [documentation](choreography_service.md) provides an overview of the Choreography API and Client and a description of the different choreography terms. Additionally, descriptions of each choreography move and its associated parameters, as well as GIFs showing a preview of the move, are available in the [Move Reference Guide](move_reference.md).

## Contents

* [Choreography Service](choreography_service.md)
* [Move Reference Guide](move_reference.md)
* [Choreographer Setup](choreographer_setup.md)
* [Choreographer Overview](choreographer.md)