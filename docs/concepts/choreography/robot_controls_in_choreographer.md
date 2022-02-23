<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Connecting Robots to Choreographer

Robots can either be connected to Choreographer before starting the application, or they can be dynamically connected and disconnected from the application once it is running.

In order to connect your robot to Choreographer, you must start Choreographer from the command line and pass in the arguments `--hostname {IP/Hostname of your Spot} --user {Username you use to log in to your Spot} --password {Password for your Spot}`. If you wish to connect to multiple Spots at once, simply add more copies of those command line arguments, one set for each Spot.

To connect your robot after the application has been started, select the Robot Management Tab (shown in the image below), and then click the "Add" button. This will prompt you for the robot's hostname, username, and then password. To remove any robot connections, click the "Disconnect" button and check any robots that you want to disconnect from. Note: disconnecting from a robot will power off the robot and release the lease and E-Stop.

![Robot Management Tab](images/robot_management.png)

Choreographer supports connecting to multiple robots at once. In the Robot Management Tab, you can select which robots are being controlled at a given time. Additionally, you can apply different choreographies to each robot and start them all at the same time.

## Robot Controls

The Robot Controls bar is disabled if there are no robots connected to the Choreographer program. If a robot is connected, the buttons will have the following effects:


Button|Function
----|----
Power Off| Powers off the Spot’s motors. Always press this before approaching your Spot.
Power On | Powers on your Spot’s motors. You must activate this before your Spot can stand or start choreography.
E-Stop | Enables or disables your Spot’s E-Stop. In an emergency, use this to stop the Spot immediately.
Self-Right | If your Spot has fallen, this will attempt to right it into a sitting position
Sit | Sits the Spot in-place. Cancels all current choreography and music, but E-Stop or Power Off should be used in an emergency.
Stand | Brings Spot to a stand. Cancels all current choreography and music, but E-Stop or Power Off should be used in an emergency.
Enable Joystick | Activated Joystick Controls (see Joystick Controls section)
Enable WASD Driving | Activates "WASD" keyboard driving (see WASD Controls section)
Return To Start | Spot will walk from its current location to the last location it started a dance (either a full choreography or the move preview dance).
Start Choreography | Sends your choreography sequence to your Spot, then starts a 3 second countdown before the robot begins dancing. Any loaded music will automatically start as soon as Spot begins to dance.

Note: The return to start button (added in the Spot 2.4 release) will bring all selected robots back to their starting position after completing a choreography. If multiple robots are being controlled, there is obstacle avoidance enabled when they are navigating back to the starting position. To adjust this obstacle padding distance (in meters), the command line argument `--obs-padding DIST_IN_METERS` can be provided when starting the Choreographer application.

## Joystick Controls

![Joystick Controls](images/joystick_help.png)

A X-Box gamepad controller can be used with the GUI for convenience of moving and positioning the robot.  The button layout is set up for X-Box 360 controllers, which are readily available, and can be connected to a computer through a USB port.  Many of the buttons in the GUI are linked to gamepad buttons, and the gamepad button will behave the same as the corresponding GUI button.  As shown in the diagram above they are:

Button | Function
----|-----
A | Stop
B | Enable Joystick
X | Start Choreography
Y | Stand
Left-Bumper | Self Right
Right-Bumper | Sit
Start | Power On
Back | Power Off

When the joystick is enabled (either through hitting the "B" button on the gamepad or through the GUI button), the robot will walk, and can be driven by the joysticks. As shown in the diagram above, the left joystick controls translation, and the right joystick controls yaw. When the robot is controlled through any of the other Robot Controls buttons, when WASD mode is enabled, or when a dance routine has been started, joystick driving will be disabled however other buttons will still work.

While using Choreographer, the joystick controller mapping diagram can be accessed as a reminder using the menus Help->Joystick Controller Mapping.

Note: the X-Box controller must be connected to the computer via USB port before opening the Choreographer application.

## Keyboard Controls

Similar to the joystick control, we provide the ability to drive the robot using the WASD keys on the keyboard. When enabled (either through hitting the GUI button or by pressing "v" on the keyboard), the robot will walk and can be driven using the WASD keys. Joystick mode will be disabled while driving in WASD mode. The hotkeys are setup to mimic the joystick button key presses when applicable. When the robot is controlled through any of the other Robot Controls buttons, when joystick mode is enabled, or when a dance routine has been started, the WASD driving will be disabled, however other keypresses will still be available.

Key | Function
----|-----
v | Enable WASD mode
b | Enable Joystick mode
k | Power On
l | Power Off
y | Stand
x | Start Choreography
[ | Sit
] | Self-right
w | Walk forward
a | Strafe left
s | Walk backwards
d | Strafe right
q | Turn left
e | Turn right

While using Choreographer, a table of available keystrokes can be accessed as a reminder using the menus Help->Hotkeys Documentation.
