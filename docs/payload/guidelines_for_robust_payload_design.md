<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Guidelines for Robust Payload Design

Spot is designed for industrial use. The payload designer should assume the robot might fall on its side while walking or sustain forces from its industrial environments.


## Crash protection

Spot is covered in a dual crash protection material that has an outer layer of polycarbonate-blend plastic and an inner layer of foam. The outer layer provides durability and helps to diffuse point loads from the environment across its surface area.

Payloads should include a crash structure to protect sensitive components from contact with the environment. Example: a rigid frame structure that surrounds and protects a device from impacts. Structural or shock absorbing material should be added, especially to the edges and corners of any payload.

For impact protection, Boston Dynamics recommends that payload designers consider sculpted cross-linked polyethylene foam as a protection material. This type of machinable foam can be shaped easily and is durable without external covering.


## Shock loads

In crashes onto hard surfaces, shocks of up to 180 g can be experienced by the robot’s body and hence payloads connected to it.

While not required to interface with the robot, payload developers who want to produce robust hardware should target this value or higher. Boston Dynamics recommends paying particular attention to electrical connections such as board-to-board interconnects and heavy components soldered to PCBAs.


## Ingress protection

Spot is designed to operate indoors and outdoors. The robot is sealed to IP54 ensuring that it is protected from dust and splashing water. Spot robot payloads should also conform to this standard to ensure the same indoor and outdoor capability.


## External cabling

If a payload includes external cables, care must be taken to ensure a robust and survivable cable management system for the robot’s dynamic environment. When possible, external cables should be avoided. All external cables should be tied down tightly to minimize any exposed loops or connectors to avoid getting pinched or caught on the environment.


## Designing for edge-case leg interference

When the robot is unpowered, the robot’s legs may move into the designated design space above the robot, as shown in this illustration:

<img src="images/guidelines-image1.png" style="width:388px;height:382px">

While robot control software attempts to avoid putting the legs in these areas, a robust payload must assume potential contact with the legs and should protect the payload accordingly.


## Enabling self-righting

Spot can usually right itself upon command when it falls. However, certain payload geometries can interfere with the self-righting behavior and prevent the robot from righting itself. In order to maintain the self-righting capability, a payload developer should seek further guidance from Boston Dynamics.


<!--- image and page reference link definitions --->
[config-image1]: images/payload1.png
[config-image2]: images/payload2.png
[config-image3]: images/payload3.png
[config-image4]: images/payload4.png
[config-image5]: images/config-image5.png
[config-image6]: images/config-image6.png
[config-image7]: images/payload7.png
[config-image8]: images/payload8.png

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
[rails-image3]: images/rails3.png



[payload-top]: Readme.md "Developing and managing Spot payloads"
[configuration]: payload_configuration_requirements.md "Payload configuration requirements"
[mechanical]: mechanical_interfaces.md "Mechanical interfaces"
[mounting-rails]: robot_mounting_rails.md "Robot mounting rails"
[robust-payload]: guidelines_for_robust_payload_design.md "Guidelines for robust payload design"
[electrical]: robot_electrical_interface.md "Robot electrical interface"
[payload-software]: configuring_payload_software.md "Configuring payload software"
