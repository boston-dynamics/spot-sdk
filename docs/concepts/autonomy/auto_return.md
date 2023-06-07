<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# AutoReturn Service

## What is AutoReturn?
AutoReturn is a service that will walk Spot back along a recently traversed path. It can be configured to happen automatically when Spot stops receiving commands from a user.

## Why would I want to use AutoReturn?
If you are piloting Spot through an area inaccessible to people and suddenly lose the communication link to Spot, the standard behavior is for Spot to sit down and power off. It may be valuable to instead tell Spot to automatically come back along the path it walked, hopefully putting Spot back into communication range.

## Why would I NOT want to use AutoReturn?
Depending on the environment Spot is in when AutoReturn activates, Spot may make things worse by trying to autonomously navigate. It’s very likely that AutoReturn will activate when there is poor or no communication to Spot, leaving it walking around unsupervised.

It's also important to note the following:

- **AutoReturn does not bypass or modify the [E-stop Service](../estop_service.md) settings in any way.** If that system’s timeout is triggered, Spot will sit down and power off, even if it is in the middle of executing AutoReturn. If you need to use a stricter E-stop timeout, AutoReturn may not work well for you.
- **AutoReturn will behave better in certain environments than others.** For example, if Spot becomes trapped while executing AutoReturn, Spot will continue to try and return, possibly until the battery drops below the operation threshold, at which point Spot will sit down and power off. If the environment around Spot changes and blocks Spot's previous path, Spot may end up in a worse location than before.

## How do I use AutoReturn?
AutoReturn must be explicitly enabled, and will only work for the user that is driving Spot when AutoReturn is enabled. For example, if user A enables AutoReturn and then user B takes control of Spot, AutoReturn will not automatically run. If user B wants to enable AutoReturn, they must do it themselves.

### Configuring AutoReturn

The primary AutoReturn setting to tune is the maximum displacement parameter, which tells Spot how far away it is allowed to travel. Spot may travel a number of meters more than the maximum displacement if the path it takes contains turns.

For example, the distance traveled is equal to the displacement in this path:

![Straight AutoReturn Path][straightpath]

but very different in this path:

![Hairpin AutoReturn Path][hairpinpath]

The maximum displacement acts as a radial limit from the robot's current position. AutoReturn will not walk the robot outside of that limit.

For example, AutoReturn will walk Spot back along this dotted line:

![In-bounds AutoReturn Path][inboundspath]

but will only walk Spot up to or before the boundary in this example, omitting the portion of the path in red.

![Out-of-bounds AutoReturn Path][outofboundspath]

Tablet users will find AutoReturn settings under the “Comms” section of the main menu.

## What happens when AutoReturn finishes?
It depends on whether communication to a user has been restored. If Spot does not hear from a user by the time AutoReturn finishes, Spot’s normal comms loss behavior will begin.

## Using AutoReturn Safely
**AutoReturn can potentially cause the robot to operate autonomously for unexpected distances. This can be dangerous for anyone nearby.**

Tips for safe use of AutoReturn:
- Set the max displacement as low as possible to minimize the potential for the robot to venture any further than necessary.
- Keep the E-stop Service timeout as low as possible to limit the amount of time the robot is moving without Operator control. This setting can be found under "Autowalk Replay Supervision" in the tablet, alongside the AutoReturn settings.

<!--- image and page reference link definitions --->

[straightpath]: images/straight_auto_return_path.png "AutoReturn path in a straight line"
[hairpinpath]: images/hairpin_auto_return_path.png "AutoReturn path around a 180 degree turn"
[inboundspath]: images/auto_return_inside_disp.png "Path that will not be truncated by AutoReturn"
[outofboundspath]: images/auto_return_outside_disp.png "Path that will be truncated by AutoReturn"
