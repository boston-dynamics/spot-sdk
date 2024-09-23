<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Controlling the Robot with an Xbox Controller

Xbox Controller example allows users to control a Spot robot through an Xbox controller. The example was tested with an Xbox 360 wired controller. The button mapping is:

| Button Combination | Functionality            |
| ------------------ | ------------------------ |
| A                  | Walk                     |
| B                  | Stand                    |
| X                  | Sit                      |
| Y                  | Stairs                   |
| LB + :             |                          |
| - D-pad up/down    | Walk height              |
| - D-pad left       | Battery-Change Pose      |
| - D-pad right      | Self right               |
| - Y                | Jog                      |
| - A                | Amble                    |
| - B                | Crawl                    |
| - X                | Hop                      |
|                    |                          |
| If Stand Mode      |                          |
| - Left Stick       |                          |
| -- X               | Rotate body in roll axis |
| -- Y               | Control height           |
| - Right Stick      |                          |
| -- X               | Turn body in yaw axis    |
| -- Y               | Turn body in pitch axis  |
| Else               |                          |
| - Left Stick       | Move                     |
| - Right Stick      | Turn                     |
|                    |                          |
| LB + RB + B        | E-Stop                   |
| Start              | Motor power & Control    |
| Back               | Exit                     |

## User Guide

### Installation

For your best learning experience, please use the [Quickstart Guide](../../../docs/python/quickstart.md)
found in the SDK's docs/python directory. That will help you get your Python programming
environment setup properly.

#### OS-Specific Dependencies

This example has external dependencies to communicate with an XBox controller, and those dependencies are OS-specific.

**Ubuntu**: On Ubuntu 18.04, the example uses the `xboxdrv` driver to communicate with the controller, so please install the driver by executing:

`sudo apt-get install xboxdrv`

The `xboxdrv` driver supports only Xbox360 controllers. Newer controllers are not supported.

**Windows**: On Windows, the example uses `XInput-Python` package, which is automatically installed with the pip command below. The `XInput` package officially supports Xbox360 controllers, but newer controllers also work with this example on Windows.

**MacOS**: This example is not supported on MacOS.

#### Installation Instructions

To install this example on Ubuntu and Windows, follow these instructions:

- Create virtual environment as described in this
  [Quickstart Guide virtualenv section](../../../docs/python/quickstart.md#manage-multiple-python-environments-with-virtualenv)
- Install dependencies: `python3 -m pip install -r requirements.txt`
- Run the example using instructions in the next section
- To exit the virtual environment, run `deactivate`

### Execution

This example follows the common pattern for expected arguments. It needs the common arguments used to configure the SDK and connect to a Spot:

- hostname passed as the last argument
- username and password should be set in the environment variables `BOSDYN_CLIENT_USERNAME` and `BOSDYN_CLIENT_PASSWORD`.

**1)** The example needs to be run as sudo. To run a python program as sudo within a virtual environment, you need to specify the python executable in the virtualenv folder.

To find the virtualenv python executable, activate the desired virtual environment and then run `which python`, which should return the python executable's path.

Then run the example with the following:
`sudo <path/to/python/executable> xbox_controller.py ROBOT_IP`

**2)** After the controller is connected, the example prints a status window:

```
E-Stop	Control	Motors On	Mode
```

**3)** Next, press the key combination `Left Button + Right Button + B` to turn E-Stop on:

```
E-Stop	Control	Motors On	Mode
X
```

**4)** Next, press the `Guide` button to acquire a lease with this Spot:

```
E-Stop	Control	Motors On	Mode
X       X
```

**5)** Next, press the `Start` button to turn the motors on:

```
E-Stop	Control	Motors On	Mode
X       X       X
```

**6)** Spot is now ready to be controlled.

**7)** To E-Stop Spot at any time, press the E-Stop button combination (LB + RB + B)

**8)** To exit and power off Spot, press the `Back` button.
