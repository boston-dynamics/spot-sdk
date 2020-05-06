<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# [Spot SDK](../../README.md) > [Concepts](README.md) > About Spot


![Spot anatomy](getstarted-image1.png)



## Cameras

Spot has 5 pairs of stereo cameras that provide black and white images and video.


## Hips and joints

Spot has 2 actuators in each hip, one in each knee



*   12 DOFs, 3 per leg
*   HX: +/- 45 degrees from vertical (45 degrees of internal and external rotation from vertical)
*   HY: +/- 91 degrees with 50 degree bias from vertical (flexion/extension)
*   KN: +/- 14-160 degrees from straight (flexion/extension range from 14 to 160 degrees)


![Spot side view](getstarted-image2.png)


![Spot front view](getstarted-image3.png)


Each leg has two hip joints, referred to as HX and HY, for each plane of rotation, and a knee. Legs are front or hind and left or right. Examples: FL (front left) and HL (hind left). So, a complete joint reference for one leg looks like this:



*   fl.hx for front left hip X
*   fl.hy for front left hip Y
*   fl.kn for front left knee


![Spot geometry](getstarted-image4.png)

The [get_robot_state.py example](../../python/examples/get_robot_state/README.md) in the Spot SDK returns data about the robot, including information about joints and legs. The following snippet shows the data returned for hip X on the front left leg (values in radians):


    ...
    joint_states {
        name: "fl.hx"
        position {
          value: 0.21174180507659912
        }
        velocity {
          value: 0.003905495163053274
        }
        acceleration {
          value: 2.1059951782226562
        }
        load {
          value: -1.86274254322052
        }
      }
    ...


## Robot specifications


<table>
  <tr>
   <td><strong>Category</strong>
   </td>
   <td><strong>Specification</strong>
   </td>
   <td><strong>Value</strong>
   </td>
  </tr>
  <tr>
   <td rowspan="8" >Dimensions
   </td>
   <td>Robot type
   </td>
   <td>Spot Gamma
   </td>
  </tr>
  <tr>
   <td>Length
   </td>
   <td>1100 mm (43.3 in)
   </td>
  </tr>
  <tr>
   <td>Width
   </td>
   <td>500 mm (19.7 in)
   </td>
  </tr>
  <tr>
   <td>Height (standing)
   </td>
   <td>840 mm (33.1 in)
   </td>
  </tr>
  <tr>
   <td>Height (sitting)
   </td>
   <td>191 mm (7.5 in)
   </td>
  </tr>
  <tr>
   <td>Net weight
   </td>
   <td>32.5 kg (71.7 lbs)
   </td>
  </tr>
  <tr>
   <td>Degrees of freedom
   </td>
   <td>12
   </td>
  </tr>
  <tr>
   <td>Maximum speed
   </td>
   <td>1.6 m/s
   </td>
  </tr>
  <tr>
   <td rowspan="6" >Environment
   </td>
   <td>Ingress protection
   </td>
   <td>IP54
   </td>
  </tr>
  <tr>
   <td>Operating temperature
   </td>
   <td>-20C to 45C
   </td>
  </tr>
  <tr>
   <td>Slopes
   </td>
   <td>+/- 30 degrees
   </td>
  </tr>
  <tr>
   <td>Stairways
   </td>
   <td>Stair dimensions that meet US building code standards, typically with 7 in. rise for 10-11 in. run
   </td>
  </tr>
  <tr>
   <td>Max step height
   </td>
   <td>300 mm (11.8 in)
   </td>
  </tr>
  <tr>
   <td>Lighting
   </td>
   <td>Above 2 lux
   </td>
  </tr>
  <tr>
   <td rowspan="7" >Power
   </td>
   <td>Battery capacity
   </td>
   <td>605 Wh
   </td>
  </tr>
  <tr>
   <td>Max battery voltage
   </td>
   <td>58.8V
   </td>
  </tr>
  <tr>
   <td>Typical runtime
   </td>
   <td>90 minutes
   </td>
  </tr>
  <tr>
   <td>Standby time
   </td>
   <td>180 minutes
   </td>
  </tr>
  <tr>
   <td>Charger power
   </td>
   <td>400W
   </td>
  </tr>
  <tr>
   <td>Max charge current
   </td>
   <td>7A
   </td>
  </tr>
  <tr>
   <td>Time to charge
   </td>
   <td>120 minutes
   </td>
  </tr>
  <tr>
   <td rowspan="3" >Payload
   </td>
   <td>Max weight
   </td>
   <td>14 kg (30.9 lbs)
   </td>
  </tr>
  <tr>
   <td>Max power per port
   </td>
   <td>150W
   </td>
  </tr>
  <tr>
   <td>Payload ports
   </td>
   <td>2
   </td>
  </tr>
  <tr>
   <td rowspan="3" >Sensing
   </td>
   <td>Camera type
   </td>
   <td>Projected stereo
   </td>
  </tr>
  <tr>
   <td>Field of view
   </td>
   <td>360 degrees
   </td>
  </tr>
  <tr>
   <td>Operating range
   </td>
   <td>4 m (13 ft)
   </td>
  </tr>
  <tr>
   <td rowspan="2" >Connectivity
   </td>
   <td colspan="2" >802.11
   </td>
  </tr>
  <tr>
   <td colspan="2" >Ethernet: 1000Base-T
   </td>
  </tr>
</table>
