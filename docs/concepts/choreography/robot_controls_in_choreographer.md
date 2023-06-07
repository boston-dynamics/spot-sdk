<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Connecting robots to Choreographer

Robots can either be connected to Choreographer before starting the application or dynamically connected and disconnected from the application once it is running.

To connect your robot to Choreographer, start Choreographer from the command line with arguments:


    --hostname {IP/Hostname of your Spot} --user {Username you use to log in to your Spot} --password {Password for your Spot}


To connect multiple Spots at once include additional command line arguments, one set for each Spot.

To connect your robot after the application has been started

1. Select the Robot Management Tab (shown in the image below)

1. Click **Add**. Enter the robot's hostname, username, and password.

To remove robot connections, click **Disconnect** and check any robots that you want to disconnect. Note: Disconnecting from a robot will power off the robot and release the lease and E-Stop.

![Robot Management tab](images/robot_management.png)

Choreographer supports connections to multiple robots. In the Robot Management Tab, you can select which robots are being controlled at a given time. Additionally, you can apply different choreographies to each robot and start them all at the same time.

## Robot controls

The **Robot Controls** bar is disabled if there are no robots connected to Choreographer. If a robot is connected to Choreographer, the buttons will have the following effects:

Button | Function
----|----
Power Off| Powers off Spot’s motors. Always press Power off before approaching the robot.
Power On | Powers on your Spot’s motors. You must activate this before your Spot can stand or start choreography.
E-Stop | Enables or disables your Spot’s E-Stop. In an emergency, use this to stop the Spot immediately.
Self-Right | If your Spot has fallen, self-righting causes the robot to attempt to return to the sitting pose.
Sit | Sits the Spot in-place. Cancels all current choreography and music. E-Stop and  Power Off can still be used in an emergency.
Stand | Brings Spot to a stand. Cancels all current choreography and music. E-Stop and Power Off can still be used in an emergency.
Enable Joystick | Activates joystick controls (see Joystick controls section)
Enable WASD Driving | Activates WASD keyboard driving (see WASD Controls section)
Return To Start | Spot walks from its current location to the last location it started a dance (either a full choreography or the move preview dance).
Start Choreography | Sends a choreography sequence to the robot, then starts a 3 second countdown before the robot begins dancing. Any loaded music will automatically start as soon as Spot begins to dance.

Note: **Return to Start** brings all selected robots back to their starting position after completing a choreography. If multiple robots are being controlled, obstacle avoidance is enabled when they are navigating back to the starting position. To adjust this obstacle padding distance (in meters) the command line argument `--obs-padding DIST_IN_METERS` can be added to the Choreographer command line.

## Joystick controls

![Joystick Controls](images/joystick_help.png)

An Xbox gamepad controller can be used with the GUI for moving and positioning the robot.  The button layout is set up for Xbox 360 controllers. Xbox controllers are connected to a computer using a USB port.  Many of the buttons in the GUI are linked to gamepad buttons, and the gamepad button will behave the same as the corresponding GUI button.  As shown in the diagram above they are:

Button | Function
----|-----
A | Stop
B | Enable joystick
X | Start choreography
Y | Stand
Left-Bumper | Self-right
Right-Bumper | Sit
Start | Power on
Back | Power off

When the joystick is enabled by tapping the **B** button on the gamepad or using the GUI button, the robot walks and can be driven using the joysticks. As shown in the diagram above, the left joystick controls translation. The right joystick controls yaw.

When the robot is controlled through any of the other Robot Controls buttons, when WASD mode is enabled, or when a dance routine has been started, joystick driving will be. Other buttons still work.

View the joystick controller mapping diagram by selecting **Joystick Controller Mapping** from the Help menu.

Note: The Xbox controller must be connected to the computer via USB port before opening the Choreographer application.

## Keyboard controls

Similar to the joystick control, you can drive the robot using the WASD keys on the keyboard.

When enabled, the robot can be driven using the WASD keys. Joystick mode is disabled while driving in WASD mode. The hotkeys are set up to mimic the joystick button keys, when applicable.

When the robot is controlled through any of the other Robot Controls buttons, WASD driving is disabled. Other keypresses still work.


Key | Function
----|-----
v | Enable WASD mode
b | Enable joystick mode
k | Power on
l | Power off
y | Stand
x | Start choreography
[ | Sit
] | Self-right
w | Walk forward
a | Strafe left
s | Walk backwards
d | Strafe right
q | Turn left
e | Turn right

Select **Hotkeys Documentation** from the Help menu to view a keystroke mapping table.
