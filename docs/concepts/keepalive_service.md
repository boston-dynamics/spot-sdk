<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Keepalive Service (BETA)

*This service is currently in BETA and may undergo changes in future releases*

The Keepalive service, added in 3.3, unifies and expands the comms-loss behaviors of Spot. It lets a client specify one or more Policies, each containing one or more actions. Each action will automatically occur if a client does not send a CheckInRequest within a configurable amount of time.

For example, you may send a ModifyPolicyRequest that adds the following Policy:

"If this robot does not receive a CheckIn for this Policy, take these actions:
After 10 seconds, record an Event.
After 15 seconds, begin AutoReturn.
After 25 seconds, shut off motor power.
After 60 seconds, turn off the robot."

Clients may add or remove a Policy at any time, and the robot does not need any Policy to operate.

## Policy

A Policy tells the robot what to do, when. Zero or more clients may have zero or more Policies on the robot at any time.

### The Policy timer

When a Policy is added, the Keepalive service

1) provides the client with an ID for that Policy.
1) starts a timer associated with the ID.

The Policy's timer is reset to 0 when the Poicy is added or "checked into". Each Policy has a separate timer. The timer increments along with the robot's clock. When the timer increments past an action's associated duration, the action will automatically happen.

### Actions

The following actions are available in a Policy:

 - Record one or more Events, as if via the DataBufferService.
 - Begin AutoReturn, as if via the AutoReturnService.
 - Come to a controlled stop, then power motors off.
 - Immediately power the motors AND robot computers off.
 - Mark a Lease as stale.

Most actions can be configured by the client. For example, for the `RecordEvent` action, the client specifies the Events to be recorded.

## Removing a Policy

There are two main ways of removing a Policy.

1) Explicitly, by adding the target Policy ID to the `policy_ids_to_remove` field of `ModifyPolicyRequest`.
1) Implicitly, by adding to the `associated_leases` on the Policy.

For example, if a client has acquired `leaseA = [6]` from the robot and adds that lease to the `associated_leases` field of Policy `1`, the next time the robot gives out `leaseB = [7]`, Policy `1` will automatically be removed.

## Backwards compatibility

The Keepalive service shares some features with other services, namely

1) The [E-Stop Service](./estop_service.md)
1) The "staleness" feature of the [Lease Service](./lease_service.md)
1) The [AutoReturn Service](./autonomy/auto_return.md) 

These other services will still work as usual if the Keepalive service is not used, with a few exceptions:

1) It is now valid to have no E-Stop configuration.
1) If an E-Stop configuration with Endpoints is set, and one or more Endpoints time out, the error will reference the Keepalive service.

If you are using the Keepalive service, you may notice a few things:

1) Registering an E-Stop Endpoint automatically adds a Policy with a matching timeout.
1) Acquiring a Lease automatically adds a Policy with LeaseStale actions at the previously hardcoded timeout.

It is safe to remove those auto-generated Policies if you wish.
