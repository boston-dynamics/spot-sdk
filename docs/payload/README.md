<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

<p class="github-only">
<b>The Spot SDK documentation is best viewed via our developer site at <a href="https://dev.bostondynamics.com">dev.bostondynamics.com</a>. </b>
</p>

# Payload Developer Guide

This section of the Spot SDK documentation provides details about designing, configuring, and attaching payloads to the Spot platform. information in this section includes electrical, mechanical, and software requirements and interfaces.

## Introduction to Spot payloads

Boston Dynamics designed Spot as a versatile sensing and manipulation platform. Spot supports up to two payloads and an arm to provide application-specific functionality. Two ports provide electrical and data interfaces for payloads. Mounting rails provide mechanical attachment points.

A payload is any device attached to the robot. Many payloads will connect to the robot to access power and data interfaces. Non-interactive payloads are also supported.

The complexity of payload integration with the Spot platform ranges from:

- _Light_ — Attaching an inert payload to the back of the robot without connecting to the robot's payload ports or network.
- _Medium_ — The payload connects to a payload port and uses some or all of the services provided by the robot.
- _Heavy_ — A payload that registers and provides standard services that integrate with other components of the robot system, such as the tablet driving interface, or other payloads.

## Contents

- [Payload configuration requirements](payload_configuration_requirements.md)
- [Mechanical interfaces](mechanical_interfaces.md)
- [Robot mounting rails](robot_mounting_rails.md)
- [Guidelines for robust payload design](guidelines_for_robust_payload_design.md)
- [Robot electrical interface](robot_electrical_interface.md)
- [CORE I/O Documentation](coreio_documentation.md)
- [CORE I/O OpenVPN Extension](coreio_openvpn_extension.md)
- [Configuring payload software](configuring_payload_software.md)
- [Dockerize payload software](docker_containers.md)
- [Pre-3.2 Spot CORE Documentation](spot_core_documentation.md)
