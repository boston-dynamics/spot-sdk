<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# [Spot SDK](../../README.md) > Payload Developer Guide

This section of the Spot SDK documentation provides details about designing, configuring, and attaching payloads to the Spot platform. information in this section includes electrical, mechanical, and software requirements and interfaces.

## Contents

*   [Payload configuration requirements][configuration]
*   [Mechanical interfaces][mechanical]
*   [Robot mounting rails][mounting-rails]
*   [Guidelines for robust payload design][robust-payload]
*   [Robot electrical interface][electrical]
*   [Configuring payload software][payload-software]


## Introduction to Spot payloads

Boston Dynamics designed Spot as a versatile sensing and manipulation platform. Spot supports up to two payloads and an arm to provide application-specific functionality. Two ports provide electrical and data interfaces for payloads. Mounting rails provide mechanical attachment points.

A payload is any device attached to the robot. Many payloads will connect to the robot to access power and data interfaces. Non-interactive payloads are also supported.  


The complexity of payload integration with the Spot platform ranges from:

*   *Light* — Attaching an inert payload to the back of the robot without connecting to the robot's payload ports or network.
*   *Medium* — The payload connects to a payload port and uses some or all of the services provided by the robot.
*   *Heavy* — A payload that registers and provides standard services that integrate with other components of the robot system, such as the tablet driving interface, or other payloads.


<br />

<a href="payload_configuration_requirements.md" class="next">Next &raquo;</a>




<!--- image and page reference link definitions --->
[config-image1]: images/config-image1.png
[config-image2]: images/config-image2.png
[config-image3]: images/config-image3.png
[config-image4]: images/config-image4.png
[config-image5]: images/config-image5.png
[config-image6]: images/config-image6.png
[elec-image1]: images/elec-image1.png
[elec-image2]: images/elec-image2.png
[elec-image3]: images/elec-image3.png
[guidelines-image1]: images/guidelines-image1.png
[mech-image1]: images/mech-image1.png
[mech-image2]: images/mech-image2.png
[mech-image3]: images/mech-image3.png
[mech-image4]: images/mech-image4.png
[rails-image1]: images/rails-image1.png
[rails-image2]: images/rails-image2.png
[rails-image3]: images/rails-image3.png

[payload-top]: Readme.md
[configuration]: payload_configuration_requirements.md
[mechanical]: mechanical_interfaces.md
[mounting-rails]: robot_mounting_rails.md
[robust-payload]: guidelines_for_robust_payload_design.md
[electrical]: robot_electrical_interface.md
[payload-software]: configuring_payload_software.md
