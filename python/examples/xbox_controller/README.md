<!--
Copyright (c) 2019 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Xbox Controller

Xbox Controller example allows users to control a Spot robot through an Xbox controller. The example was tested with an Xbox 360 wired controller. The button mapping is:

| Button Combination | Functionality            |
|--------------------|--------------------------|
| A                  | Walk                     |
| B                  | Stand                    |
| X                  | Sit                      |
| Y                  | Stairs                   |
| LB + :             |                          |
| - D-pad up/down    | Walk height              |
| - D-pad left/right | Self right               |
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
| LB + RB + B        | E-stop                   |
| Start              | Motor power              |
| Guide              | Control                  |
| Back               | Exit                     |


## User Guide
### Installation
Currently, the Xbox Controller supports only Ubuntu OS. To install this example on Ubuntu 18.04, follow these instructions:
- Install python3: `sudo apt-get install python3.6`
- Install pip3: `sudo apt-get install python3-pip`
- Install virtualenv: `pip3 install virtualenv`
- Install xboxdrv: `sudo apt-get install xboxdrv`
- Change into example directory: `cd xbox_controller`
- Create virtual environment (one time operation): `virtualenv -p {PATH_TO_PYTHON3_EXECUTABLE} venv`. The path to the executable is the output of `which python3` command, usually set to `/usr/bin/python3`.
- Start virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Run the example using instructions in the next section
- To exit the virtual environment, run `deactivate`

### Execution
This example follows the common pattern for expected arguments. It needs the common arguments used to configure the SDK and connect to a Spot:
- --username 
- --password 
- --app-token 
- hostname passed as the last argument

**1)** The example needs to be run as sudo. To run a python program as sudo within a virtual environment, you need to specify the python executable in the virtualenv folder:

`sudo venv/bin/python xbox_controller.py --user user --password password 192.168.80.3`

**2)** After the controller is connected, the example prints a status window:
```
E-Stop	Control	Motors On	Mode
```

**3)** Next, press the key combination `Left Button + Right Button + B` to turn E-Stop on:
```
E-Stop	Control	Motors On	Mode
X
```

**4)** Next, press the `Guide` button to acquire a lease with the robot:
```
E-Stop	Control	Motors On	Mode
X       X
```

**5)** Next, press the `Start` button to turn the motors on:
```
E-Stop	Control	Motors On	Mode
X       X       X
```

**6)** The robot is now ready to be controlled.

**7)** To exit and power off the robot, press the `Back` button.
