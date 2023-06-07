<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Mechanical Interfaces


Payloads should be designed to interface correctly with a cable connector and mount to the top of Spot. Detailed CAD is available on the Support Center at https://support.bostondynamics.com/s/article/Defeatured-Spot-CAD-Models.


## Cable and connector interface

Boston Dynamics provides a fully shielded, over-molded DB25 cable to make the connection between Spot’s payload ports and payloads. Payloads designed for the robot should have an interface for this cabling to maintain IP54 ingress protection.


### Correct orientation of DB25 relative to front of robot



![port detail][mech-image1]


### Keepout dimensions in mm

Boston Dynamics provides robust, environmentally sealed payload cables. A payload must ensure that the necessary keepout regions are compatible with the DB25 overmold on these cables.


![port keepout][mech-image2]


### Sealing gland geometry in mm

Payloads should incorporate a small ridge around the DB25 connector. This ridge should be about 3mm tall and of 21mm by 63mm. Corner radius is 5mm. The ridge presses into a foam gasket on the cable side to create a seal.


![port sealing gland][mech-image3]


![port sealing gland side view][mech-image4]


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

[guidelines-image1]: images/guidelines-image3.png

[mech-image1]: images/mech-image1.png
[mech-image2]: images/mech-image2.png
[mech-image3]: images/mech-image3.png
[mech-image4]: images/mech-image4.png

[rails-image1]: images/rails-image1.png
[rails-image2]: images/rails-image2.png
[rails-image3]: images/rails-image3.png

[payload-top]: Readme.md "Developing and managing Spot payloads"
[configuration]: payload_configuration_requirements.md "Payload configuration requirements"
[mechanical]: mechanical_interfaces.md "Mechanical interfaces"
[mounting-rails]: robot_mounting_rails.md "Robot mounting rails"
[robust-payload]: guidelines_for_robust_payload_design.md "Guidelines for robust payload design"
[electrical]: robot_electrical_interface.md "Robot electrical interface"
[payload-software]: configuring_payload_software.md "Configuring payload software"
