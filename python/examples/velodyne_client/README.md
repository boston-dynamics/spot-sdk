<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Using the Velodyne Point Cloud Service

This example demonstrates how to use the Velodyne service to query for point clouds. It authenticates with the robot and sets up a PointCloudClient. Once the client is set up, it polls the service for updated point clouds and displays them using Pyplot.

## Setup Dependencies
This example needs to be run with python3 and have the Spot SDK installed. It also requires PyQt5.
On Linux, it is recommended to not install this through pip so that system theming works correctly. In order to use system PyQt packages in a virtual environment, create the virtualenv with `--system-site-packages`.
See the requirements.txt file for a list of dependencies. Install dependencies with pip using the following commands:

Linux:
```
python -m pip install -r requirements.txt
sudo apt install python3-pyqt5 python3-pyqt5.qtopengl qt5-style-plugins
```

Windows:
```
py.exe -3 -m pip install -r requirements.txt
py.exe -3 -m pip install PyOpenGL pyqt5
```


## Running the Example
To run the examples:
```
python client.py --username USER --password PASSWORD ROBOT_HOSTNAME
```