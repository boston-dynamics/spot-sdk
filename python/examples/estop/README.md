<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Creating an E-Stop endpoint

This example is an E-Stop controller for a Spot robot. The example registers as an E-Stop endpoint
with a Spot robot, and it provides an easy-to-use interface for users to trigger the E-Stop in the
robot. Please refer to the main SDK documentation for information on how the E-Stop functionality
works.

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip
using the command:

```
python3 -m pip install -r requirements.txt
```

## Run the Example

To run the example as a GUI:

```
python3 estop_gui.py ROBOT_IP
```

To run the example without a GUI:

```
python3 estop_nogui.py ROBOT_IP
```

### GUI Version

The GUI version of the example has two buttons. The red `STOP` button
engages the robot's E-Stop system, which cuts off power to all the motors. This operation also
changes the E-Stop status to `ESTOP_LEVEL_CUT`. To release the E-Stop and transition the robot to
an operational state, press the green `Release` button.

### Command-line version without a GUI

Similar to the usage of the GUI version, the non-GUI version of the example uses `Space` for
engaging the E-Stop system and `r` for releasing it.

## Troubleshooting

The following error may appear when the example as a GUI is run on linux:

```
qt.qpa.plugin: Could not load the Qt platform plugin "xcb" in "" even though it was found.
This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.

Available platform plugins are: eglfs, linuxfb, minimal, minimalegl, offscreen, vnc, wayland-egl, wayland, wayland-xcomposite-egl, wayland-xcomposite-glx, webgl, xcb.

Aborted (core dumped)
```

If so, execute the following command:

```
sudo apt-get install python3-pyqt5
```
