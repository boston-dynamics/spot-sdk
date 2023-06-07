<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Lease Service

Leases represent ownership of the robot for the purpose of issuing commands to control the robot. There can only ever be a single owner of a specific robot resource at any given time, however an application can delegate the lease to other systems to perform various tasks. Leases can be returned by one application and subsequently acquired by a different application to change ownership. Alternatively, a lease can be revoked by another application to change ownership forcefully.

In addition to identifying ownership, the lease system is used to confirm that a robot is still being controlled and that there are valid communications to the owner. If an owner can no longer be reached within a certain period of time, the lease will become "stale" and may be acquired by another client.  If the owner returns to valid communications before another client acquires, the lease will become "fresh" again.

## Basic Lease Usage

Services which command or control the robot require a lease. These services will reject incoming requests which are from non-owners or contain older ownership information. Ownership semantics provides additional safety to operation workflows by preventing accidental commands from disturbing the current owner’s application. Note, some services will only read information from the robot, and do not require a lease (e.g. image service or robot-state service).

Applications which want to control the robot will begin by acquiring a lease to the robot. A lease can be acquired with the `AcquireLease` RPC when it has no existing owner.

Throughout the duration of the application, the client should continue to send “keep-alive” signals to continue ownership of the robot’s resources. The “keep-alive” signal is sent as the `RetainLease` RPC. If enough time passes between the last retain lease request received, ownership of the lease will be marked "stale" such that other applications can acquire ownership.

When issuing robot commands, the robot will be sent a version of the lease with the specific command to permit the robot to complete the desired command. This lease will automatically be included with the command request when using the SDK

Finally, when the application is complete, it should return the lease. The `ReturnLease` RPC should be used when a client is finished with their ownership to indicate that the robot is no longer owned without waiting for a revocation timeout. Note, an application should only return the lease when it was the one who acquired the lease using the `AcquireLease` RPC. In the case of a remote mission service callback or other services which are delegated the lease by a different main service, the application's service should *not* return the lease when finished - the main service acquired the lease and will return it when complete.

## [Advanced] Understanding Lease Errors

When a command is sent including a lease, the service checks the following things before accepting the command:
 - The incoming lease is valid: contains the current epoch, has known robot resources and the resources are correct for this type of command, has a non-empty sequence with a root lease number which has been issued by the lease service.
 - The incoming lease shows ownership as the newest lease: compares the incoming lease with the service’s current known lease.

The service will then respond to the command with a `LeaseUseResult` proto that indicates whether the incoming lease passed the checks and includes additional information to aid in debugging.

When a command with a lease fails with a lease error, the status within the lease use result provides the root-cause of the failure. In addition to the status, the `LeaseUseResult` proto contains information about the current lease owner of the incoming lease’s resource, the most recent lease known to the system for the incoming lease’s resource, the latest leases for each leaf resource (since these can be different depending on the types of commands sent). This information can be used to react to the lease failure within the client application.

## [Advanced] Lease Resources

A lease can claim ownership of the entire robot or specific resources. The “body” resource describes ownership of the entire robot, and can be broken down into sub-resources for the arm, gripper, and mobility (controlling only the legs), as shown in the image below. In most use cases, an application simply needs to send the "body" lease and the robot will determine which specific resources it needs for the command being issued.

![Resource Tree](resource_tree.png)

The different robot resources create a tree-structured hierarchy such that the client can control a subset of the robot or the entire robot without needing to manage individual resources. Owning a lease with a parent resource represents control over the entire subtree.

## [Advanced] Additional Lease Usage Patterns

Typically, the lease and ownership can be gained using the `AcquireLease` RPC> If the lease is actively being owned, the `TakeLease` RPC provides an alternative that will forcefully take ownership of the lease resources to give control to the application issuing the RPC. This should only be used expressly by a human who is aware of what they’re taking control from.

When issuing a specific command which requires a lease, the robot should be sent a sub-lease of the main, acquired lease. This delegates the ownership of that lease’s resources to the particular service being sent the command. Note, the creation of a sub-lease for a specific command is done automatically by the client library. Commands which require a lease will respond with `LeaseUseResult` protos, which reflect whether or not the lease provides proper ownership of the robot.

Additionally, clients should simply send the “body” lease and the robot service’s will split the lease into only the necessary parts. This allows clients to issue multiple commands which control different resources (e.x. a gripper command and a body trajectory command) without worrying about breaking apart a lease themselves. Clients can split leases into sub-resources, but will need to be careful to preserve the sequence number.

## [Advanced] Lease Representation

A lease contains the resource which it controls ownership, a sequence, an epoch, and set of client names.

The sequence is a list of integer numbers which indicates when the lease was generated and if it is a sub-lease. The first number in the sequence is the root lease number, and is generated by the base lease service. Sequence numbers are incremented when creating new leases. Additional sequence numbers can be appended to the lease sequence when creating a sub-lease to delegate ownership to a specific service. For example, the lease sequence `lease=[3, 1]` has a root lease number of `3`, and a single sub-lease with value `1`.

Resource ownership is determined by whichever lease has the highest root lease number. For example, when comparing `leaseA = [6, 1]` and `leaseB = [5, 13]`, leaseA is considered newer and the current owner.

In addition to ownership, the lease sequences are used by services to determine which command should be executing currently. Services will use and execute whichever command shows ownership of the necessary resources and has the newest lease sequence. To compare leases, the sequence number with the first higher number is considered the newest lease. For example, when comparing `leaseA = [1, 2, 10]` and `leaseB = [1, 2, 11]`, `leaseB` is considered newer since the second sequence number is higher in `leaseB` than in `leaseA`.

The epoch is used to create a scope for the sequence field, such that only leases with the same epoch can be compared. The client names are a list of each client which has held the lease; these can be helpful for debugging to see which services were delegated ownership and created sub-leases.

Consider the example below.

![Lease Usage Example](lease_example.png)

A client application took the lease from the tablet (or the tablet lost communication) and now owns the robot. The client application delegates control to graph-nav by creating a sub-lease, and graph-nav again creates a sub-lease to give control to the robot command service. When the tablet attempts to issue a robot command, it will be rejected because it is now considered older.


