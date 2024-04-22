<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Autowalk Service

The autowalk service is a way for API clients to specify high level autonomous behavior for Spot using the autowalk format. This service is a partial abstraction of the [mission service][missions], so it is beneficial to have an understanding of the [mission service][missions].

## Terminology

| Term  |  Description |
| ----- | -----------|
| [Mission](../../../protos/bosdyn/api/mission/nodes.proto#node) | A `bosdyn.api.mission.Node` proto that fully defines a behavior tree.  The structure is infinitely recursive.
| [Mission Service](../../../protos/bosdyn/api/mission/mission_service.proto#missionservice)  |	A GRPC service that sits on top of the API and can compile & run a mission.
| Program | Some high level robot behavior that can either be expressed as a mission, a python script, or some other medium.
| [Autowalk](../../../protos/bosdyn/api/autowalk/walks.proto#walk) |	A `bosdyn.api.autowalk.Walk` proto that fully defines a program with structure sequence { go here, do this, go there, do that, etc }.
| [Autowalk Service](../../../protos/bosdyn/api/autowalk/autowalk_service.proto#autowalkservice) |	A GRPC service that translates an autowalk into a mission.

## How Autowalks Differs From Missions
The mission service and missions sit on top of the API.  There is nothing you can do with the mission service that you can’t do with a python script.  The reasons to write a program using missions instead of a python script are:
1. The program needs to be resilient to comms loss.
    * Missions are run on robot and can be run with an ~infinite end time.  Clients still have to send a single PlayMission request at the start but once they do, they do not have to communicate with the robot ever again.
    * A client running a python script needs constant communication with the robot in order to advance to different stages of the script.
1. To deal with as few RPC calls as possible.  RPCs can fail in many ways, and writing a program that does the right thing for every different failure mode is difficult.  Also, the API requires sending many RPCs to do something and wait for it to finish.
1. The python script has grown too complex to successfully develop on and debug.
    * Writing and debugging boilerplate state tracking logic can be time-consuming. The behavior trees offered by the mission service might be easier to use.
1. To seamlessly move a program from client to client.
    * Because missions are defined using protobufs, they are language agnostic. The proto defining a mission can be interpreted by any client.

The missions that the tablet generates as part of the autowalk application handle many different failure modes using the mission service's behavior tree structure.  Because of that, the corresponding behavior trees are very deep (42 layers) and very wide (1000’s of nodes).  However, at their core they are very simple: go to location A, perform action 1, go to location B, perform action 2, etc. Given the complex behavior tree, suppose you would like to remove location B and action 2 from the mission. Finding the nodes that correspond to location B and action 2 would be a difficult and tedious task. Therein lies the problem. Backing out a high level understanding of what a behavior tree does is hard. This is not a new problem. Anyone familiar with programming knows that assembly code is harder to read than the C code that generated the assembly code, and that the C code is harder to read than the MATLAB code that generated the C code, even though they all express the same identical thing. Autowalk is the formalized layer above missions, and like missions it is defined using protobufs. The language layer looks like:

![Autowalk language layer][autowalklanguage]

In its basic form, the autowalk format forces programs into the “go here, do this” pattern, which is a flexibility loss compared to missions. However, the benefit is having an easy to edit structure. Autowalk and the autowalk serivce provide some methods to break “go here, do this” pattern and obtain more flexibility similar to missions. These methods will be described in a later section.

## Autowalk Format
The walk proto defines the autowalk's “go here, do this” format. It is a linear series of actions and their associated locations. These actions and locations are encapsulated in a list of [elements][element]. To edit the autowalk, elements can be reordered, modified, removed, and/or added to the list. See the [Edit Autowalk Python SDK example][editautowalk] for further details.

### Components of an Element

| Term  |  Description |
| ----- | -----------|
| [Action](../../../protos/bosdyn/api/autowalk/walks.proto#action) | What the robot should do at a location.
| [Action Wrapper](../../../protos/bosdyn/api/autowalk/walks.proto#actionwrapper)  |	What the robot should do before and during an action.
| [Action Failure Behavior](../../../protos/bosdyn/api/autowalk/walks.proto#failurebehavior) | What the robot should do if the action fails.
| [Target](../../../protos/bosdyn/api/pautowalk/walks.proto#target) |	Where the robot should go. Targets are speicified within the context of a graph nav map.
| [Target Failure Behavior](../../../protos/bosdyn/api/autowalk/walks.proto#failurebehavior) |	What the robot should do if it fails to reach the target.
| [Battery Monitor](../../../protos/bosdyn/api/autowalk/walks.proto#batterymonitor) | The battery thresholds at which the robot should pause/resume mission execution.

## Autowalk Service RPCs
The autowalk service provides [RPCs][autowalkserivce] for clients to convert an autowalk to a mission.

| RPC  |  Description |
| ----- | -----------|
| CompileAutowalk | Convert an autowalk to a mission.
| LoadAutowalk  |	Convert an autowalk to a mission and load the mission to a robot.

After the conversion process, the mission service is responsible for loading the mission, playing the mission, and querying the mission status. Remember that targets in an autowalk are defined within the context of a graph nav map. This means that the associated graph nav map must be uploaded to the robot for the mission to play correctly.

### Node Identifiers
 Since the mission service is responsible for everything after conversion, the autowalk service returns several [`bosdyn.api.autowalk.NodeIdentifier` protos][nodeidentifier] in the RPC responses. Each node identifier contains two pieces of information, a `node_id` integer (equivalent to [`bosdyn.api.mission.NodeInfo.id`][nodeinfo]) that is set by the mission service when loading a mission and a `user_data_id` string (equivalent to [`bosdyn.api.mission.NodeInfo.UserData.id`][userdata]) that is set by the autowalk service when compiling a walk. These node identifiers give the client insights about the behavior tree generated by the autowalk service. This can be useful when playing the mission. When playing the mission, the client may want to know what parts of the mission are complete, are incomplete, or are currently executing. Using the `node_id` field in each node identifier, the client can make sense of the mission service's `GetState` RPC [response][getstateresponse]. Please note that when using the `CompileAutowalk` RPC, the `node_id` field in the node identifiers will not be populated because the node ids are set by the mission service when loading the mission to the robot. In this case, the client must use the `user_data_id` field in the node identifiers to determine the node ids set by the mission service after the mission is loaded to the robot. To see how node identifiers can be used to query the status of a mission, see the [Query Autowalk Status C++ SDK example][queryautowalkstatus].

### Debugging Autowalk Service RPC Failures
Aside from standard gRPC errors, there are user errors that can cause the autowalk service RPCs to fail. If a walk proto is malformed, the autowalk to mission compilation will fail. The RPC responses contain a map field called `failed_elements`. Inspect the errors strings within each [`FailedElement` proto][failedelement] in the map to determine why the compilation failed. The `FailedElement` message also contains warnings. Warnings can be resolved by the compiler, but can potentially result in unexpected behavior. Compile time walk modifications are reported back to the client in the warnings field. The `LoadAutowalk` RPC can fail during mission validation. To debug validation errors, inspect the `lease_use_results` and `failed_nodes` fields in the [server response][loadautowalkresponse].

## Breaking the "Go Here, Do This" Structure
As previously mentioned, missions offer more flexibility than autowalks because autowalks are largely confined to the "go here, do this" format. Consider the following example. Spot measures the temperature of an asset. If the temperature is above a certain threshold, Spot should record the temperature of all nearby assets and alert the operator. If the temperature is below the threshold, Spot should continue to the next target. This conditional behavior does not conform to the "go here, do this" autowalk format. However, there are still ways to achieve this behavior using autowalks and the autowalk service:
1. Inject a behavior tree into an autowalk action
    * The [`bosdyn.api.autowalk.Action` proto][action] allows the user to specify a [`bosdyn.api.mission.Node` proto][node] as the action. This node can implement a behavior tree that achieves the desired conditional behavior.
    * The downside to this method is that editors may not support editing mission parameters of the embedded behavior tree.
1. Compile and combine multiple autowalks
    * The `CompileAutowalk` RPC returns the root node of the resulting behavior tree. This node can be injected into other behavior trees. By compiling and combining multiple autowalks, the desired conditional behavior can be achieved.
    * Editors may not support editing the combined behavior tree, however the original autowalks can be edited, recompiled, and recombined.

<br/>

[autowalklanguage]: images/autowalk_language_layer.png "Analogy for how autowalks work"
[missions]: missions_service.md "Missions service"
[autowalkserivce]: ../../../protos/bosdyn/api/autowalk/autowalk_service.proto#autowalkservice "Autowalk Service RPCs"
[element]: ../../../protos/bosdyn/api/autowalk/walks.proto#element "Element Proto"
[nodeidentifier]: ../../../protos/bosdyn/api/autowalk/walks.proto#nodeidentifier "Node Identifier Proto"
[nodeinfo]: ../../../protos/bosdyn/api/mission/mission.proto#nodeinfo "Node Info Proto"
[userdata]: ../../../protos/bosdyn/api/mission/util.proto#userdata "User Data Proto"
[getstateresponse]: ../../../protos/bosdyn/api/mission/mission.proto#getstateresponse "Get State Response Proto"
[editautowalk]: ../../../python/examples/edit_autowalk/README.md "Edit Autowalk Example"
[queryautowalkstatus]: https://github.com/boston-dynamics/spot-cpp-sdk/tree/master/cpp/examples/query_autowalk_status "Query Autowalk Status Example"
[failedelement]: ../../../protos/bosdyn/api/autowalk/autowalk.proto#failedelement "Failed Element Proto"
[node]: ../../../protos/bosdyn/api/mission/nodes.proto#node "Node Proto"
[action]: ../../../protos/bosdyn/api/autowalk/walks.proto#action "Action Proto"
[loadautowalkresponse]: ../../../protos/bosdyn/api/autowalk/autowalk.proto#loadautowalkresponse "Load Autowalk Response Proto"