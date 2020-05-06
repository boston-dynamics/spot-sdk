<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# [Spot SDK](../../README.md) > [Payload Developer Guide](README.md) > Electrical Interface

The Spot robot’s two payload ports provide power and communication to the robot through a DB25 connection. The robot presents a female DB25 connector at each payload port, pictured below. Note that pin 1 is on the right looking down at the robot. The payload must include a mating DB25 male connection in the proper orientation.

Robot front Robot presents db25 female

![db25 connector][elec-image1]

Robot back DB25 pinout


## Payload port pinouts by category


<table>
  <tr>
   <td><strong>Category</strong>
   </td>
   <td><strong>Pins</strong>
   </td>
   <td><strong>Specifications</strong>
   </td>
  </tr>
  <tr>
   <td>Power
   </td>
   <td>12, 13, 24, 25
   </td>
   <td>Voltage supply range: 35-59V
<p>
Absolute Maximum Voltage: 72V
<p>
Max current: 3A/pin
<p>
Max power: 150W/port
<p>
Bulk capacitance: 150uF/port
   </td>
  </tr>
  <tr>
   <td>Communication
   </td>
   <td>1-4, 7, 14-17
   </td>
   <td>Ethernet: 1000Base-T
<p>
PPS Accuracy: 5ppm
<p>
PPS Frequency: 1Hz
   </td>
  </tr>
  <tr>
   <td>Safety
   </td>
   <td>5, 6, 18, 19
   </td>
   <td>Payload power interlock
<p>
Motor power interlock
   </td>
  </tr>
</table>



## Payload port PIN specifications


<table>
  <tr>
   <td><strong>PIN #</strong>
   </td>
   <td><strong>NAME</strong>
   </td>
   <td><strong>DESCRIPTION</strong>
   </td>
  </tr>
  <tr>
   <td>1
   </td>
   <td>ETH0_D_N
   </td>
   <td>Ethernet Pair D negative
   </td>
  </tr>
  <tr>
   <td>2
   </td>
   <td>ETH0_D_P
   </td>
   <td>Ethernet Pair D Positive
   </td>
  </tr>
  <tr>
   <td>3
   </td>
   <td>ETH0_B_N
   </td>
   <td>Ethernet Pair B negative
   </td>
  </tr>
  <tr>
   <td>4
   </td>
   <td>ETH0_B_P
   </td>
   <td>Ethernet Pair B Positive
   </td>
  </tr>
  <tr>
   <td>5
   </td>
   <td>PL_SAFETY_O
   </td>
   <td>Payload power enabled when continuity is established between this pin and pin 18
   </td>
  </tr>
  <tr>
   <td>6
   </td>
   <td>MP_SAFETY_O
   </td>
   <td>Robot motor power enabled when continuity is established between this pin and pin 19
   </td>
  </tr>
  <tr>
   <td>7
   </td>
   <td>PPS
   </td>
   <td>Pulse-Per-Second signal referenced to payload ground
   </td>
  </tr>
  <tr>
   <td>8
   </td>
   <td>N/C
   </td>
   <td>Not Connected
   </td>
  </tr>
  <tr>
   <td>9
   </td>
   <td>P_GND
   </td>
   <td>Ground Reference for the payload. Each pin supports 3A of return current.
   </td>
  </tr>
  <tr>
   <td>10
   </td>
   <td>P_GND
   </td>
   <td>Ground Reference for the payload. Each pin supports 3A of return current.
   </td>
  </tr>
  <tr>
   <td>11
   </td>
   <td>N/C
   </td>
   <td>Not Connected
   </td>
  </tr>
  <tr>
   <td>12
   </td>
   <td>PWR
   </td>
   <td>Unregulated payload power from robot battery. Each pin supports 3A of supply current.
   </td>
  </tr>
  <tr>
   <td>13
   </td>
   <td>PWR
   </td>
   <td>Unregulated payload power from robot battery. Each pin supports 3A of supply current.
   </td>
  </tr>
  <tr>
   <td>14
   </td>
   <td>ETH0_C_N
   </td>
   <td>Ethernet Pair C negative
   </td>
  </tr>
  <tr>
   <td>15
   </td>
   <td>ETH0_C_P
   </td>
   <td>Ethernet Pair C Positive
   </td>
  </tr>
  <tr>
   <td>16
   </td>
   <td>ETH0_A_N
   </td>
   <td>Ethernet Pair A negative
   </td>
  </tr>
  <tr>
   <td>17
   </td>
   <td>ETH0_A_P
   </td>
   <td>Ethernet Pair A Positive
   </td>
  </tr>
  <tr>
   <td>18
   </td>
   <td>PL_SAFETY_IN
   </td>
   <td>Payload power enabled when continuity is established between this pin and pin 5
   </td>
  </tr>
  <tr>
   <td>19
   </td>
   <td>MP_SAFETY_IN
   </td>
   <td>Robot motor power enabled when continuity is established between this pin and pin 6
   </td>
  </tr>
  <tr>
   <td>20
   </td>
   <td>N/C
   </td>
   <td>Not Connected
   </td>
  </tr>
  <tr>
   <td>21
   </td>
   <td>P_GND
   </td>
   <td>Ground Reference for the payload. Each pin supports 3A of return current.
   </td>
  </tr>
  <tr>
   <td>22
   </td>
   <td>P_GND
   </td>
   <td>Ground Reference for the payload. Each pin supports 3A of return current.
   </td>
  </tr>
  <tr>
   <td>23
   </td>
   <td>N/C
   </td>
   <td>Not Connected
   </td>
  </tr>
  <tr>
   <td>24
   </td>
   <td>PWR
   </td>
   <td>Unregulated payload power from robot battery. Each pin supports 3A of supply current.
   </td>
  </tr>
  <tr>
   <td>25
   </td>
   <td>PWR
   </td>
   <td>Unregulated payload power from robot battery. Each pin supports 3A of supply current.
   </td>
  </tr>
  <tr>
   <td>MH1, MH2
   </td>
   <td>P_GND
   </td>
   <td>Connector Shell and Mounting Hardware is connected to payload ground
   </td>
  </tr>
</table>



## Payload power requirements

Payloads require a battery to be installed in the robot to operate. The robot is powered by a 600W-hr Lithium Ion battery pack that also provides power to payloads through a dedicated enable circuit. Battery voltage ranges from 35V for a fully discharged battery to 58.8V for a full charge.

Regenerative energy from the robot’s motors can cause the robot’s bus voltage to exceed the normal battery voltage range for short durations. The robot contains a clamping circuit to ensure the battery voltage bus never exceeds 72V.

Electrical components in payloads should be selected to handle a maximum payload input voltage of at least 80V.

Payload power is enabled when pins 5 (PL_SAFETY_O) and 18 (PL_SAFETY_IN) are shorted together on both payload ports. Both payload ports are powered from the same bus. Power is enabled through a soft-start circuit ensuring a monotonic voltage rise. The bus can support inrush current for up to 150uF of bulk capacitance in each payload, or 300uF total.

The robot includes a current limiting circuit that will disable power to the payload in the event of an unintended current spike. The average power for each payload connector must not exceed 150W. The resettable current limiting circuit in the robot will disable payload power if the total current for both payloads combined exceeds a limit ranging from 9-13A. If an overcurrent event occurs and payload power is disabled, the current limiting circuit can be reset by cycling robot power using the power button.


## Motor power safety

The payload interface contains a safety interlock connection that allows the payload to disable motor power to all motors in the robot. All payloads must therefore ensure continuity between pins 6 (MP_SAFETY_O) and 19 (MP_SAFETY_IN) at all times for the robot to operate. If electrical continuity between these pins is interrupted, the robot will immediately disable power to all actuation systems. If the robot is standing, this will cause the robot to fall to the ground.


![payload electrical][elec-image2]



### Payload port requirements

The robot's payload caps include circuitry that completes the circuit between the pins involved in this system. If there is no payload present, the cap(s) must be installed to allow the robot to function. If the caps are removed or become loose during operation, the robot will immediately disable motor power and sit down.


## Robot Communication and pulse-per-second (PPS)

The payload connector includes pins to provide 1000Base-T Ethernet for connectivity to the payload. The robot also provides a Pulse Per Second (PPS) signal to the payloads via pin 7 (PPS) referenced to P_GND as shown below.

This signal operates at 1Hz with 5ppm accuracy. The payload can use this signal for synchronization with data provided by the robot. Spot’s CPU system times are synchronized to this pulse and can be communicated to the payload through the API.

Payloads must include a pull-up resistor to the appropriate logic voltage to accommodate the open collector output circuit as shown below, with a maximum current of 10mA. The pull-up resistor value must consider the series resistance on the robot (shown in the schematic below) to ensure adequate logic-low and logic-high signaling.


![onboard PPS][elec-image3]


<br />

<a href="guidelines_for_robust_payload_design.md" class="previous">&laquo; Previous</a>  |  <a href="configuring_payload_software.md" class="next">Next &raquo;</a>



<!--- image and page reference link definitions --->
[rails-image1]: images/rails-image1.png
[rails-image2]: images/rails-image2.png
[rails-image3]: images/rails-image3.png

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

[payload-top]: Readme.md "Developing and managing Spot payloads"
[configuration]: payload_configuration_requirements.md "Payload configuration requirements"
[mechanical]: mechanical_interfaces.md "Mechanical interfaces"
[mounting-rails]: robot_mounting_rails.md "Robot mounting rails"
[robust-payload]: guidelines_for_robust_payload_design.md "Guidelines for robust payload design"
[electrical]: robot_electrical_interface.md "Robot electrical interface"
[payload-software]: configuring_payload_software.md "Configuring payload software"
