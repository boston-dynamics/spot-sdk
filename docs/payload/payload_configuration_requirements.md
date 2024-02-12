<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Configuration Requirements

Spot can be configured to carry up to two payloads. The following describes considerations for designing payloads. If designing a payload to be used in conjunction with other payloads, you must keep the total weight of all payloads under 14 kg. A urdf model of the robot and its geometry can be found [here](../../files/spot_base_urdf.zip).


### Payload ports

Spot comes with two payload ports that provide power, communication, time-synchronization, and safety system integration.


![robot ports][config-image1]


NOTE: Robot will not work without a cap or payload attached to each port.


### Payload width

The maximum recommended width for a body-mounted payload is 190mm. Wider payloads will result in reduced overall mobility and significant interference with the legs. Payload designers should avoid interference with the robot’s legs as shown above by avoiding the areas immediately adjacent to the robot's hips.

Designers should include a scallop or elevate the payload enough to create clearance around this section, shown in pink. A 3D STEP model of Spot’s back including payload mounting area detail is available upon request. We recommend that payload developers request and study this model.


![payload width][config-image2]



### Payload length

Do not overhang the front or rear of the robot as this will reduce maneuverability. In special cases the software can be modified to support larger extents, but we recommend staying inside the given design space.


![payload clearance][config-image3]



### Payload height

The height of the payload impacts the robot’s ability to self-right and increases the height of the center of mass. Keep the center of mass low, as the robot may not self-right if top-heavy.


![top clearance][config-image4]



### Payload weight

Spot can support 14 kg total combined capacity distributed over the top of the robot. This total payload capacity must include all payloads. Spot can better handle payload mass if the combined center of mass lies between the front and rear hips. Spot will be more agile and less likely to fall if the total payload mass is centered on the middle of the robot.


### Payload leg Interference

Spot’s legs have a very wide range of motion as shown below. When the robot climbs stairs, transitions from sit to stand, and self-rights, the knees may rise above the top plane of the robot where payloads may be mounted. Even with following these guidelines, robot legs might come in contact with a payload. This is considered normal, and payloads should be designed robustly to withstand occasional contact with legs.


### Isometric and top views of robot legs ROM


![leg clearance][config-image5]

![leg clearance][config-image6]


The robot’s legs can extend above and over the robot’s back.

Note: A 3D Step model of the robot’s body including typical leg swing areas is available on the Support Center at https://support.bostondynamics.com/s/article/Defeatured-Spot-CAD-Models.


### Payload clearance with robot arm



![arm clearance][config-image7]



### Payload under arm clearance



![arm clearance][config-image8]


NOTE: The Spot Arm weighs 8 kg. Total combined payload weight should be within the 14 kg maximum payload limit.


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

[guidelines-image1]: images/elec-image3.png

[mech-image1]: images/mech-image1.png
[mech-image2]: images/mech-image2.png
[mech-image3]: images/mech-image3.png
[mech-image4]: images/mech-image4.png

[rails-image1]: images/rails-image1.png
[rails-image2]: images/rails-image2.png
[rails-image3]: images/rails-image3.png

[payload-top]: Readme.md
[configuration]: payload_configuration_requirements.md#1
[mechanical]: mechanical_interfaces.md
[mounting-rails]: robot_mounting_rails.md
[robust-payload]: guidelines_for_robust_payload_design.md
[electrical]: robot_electrical_interface.md
[payload-software]: configuring_payload_software.md
