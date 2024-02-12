<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Install Choreographer

The Choreographer application allows you to easily author sequences by combining and parameterizing a variety of pre-defined moves and custom animations as well as execute  on the robot with music synchronization.

The application can be downloaded from the [Boston Dynamics Support Center](https://support.bostondynamics.com/s/downloads) (login required).  Most Choreography API commands require a special license to use.

## System requirements

Choreographer supports 64-bit Microsoft Windows 10 and 64-bit Ubuntu 18.04 Linux. No other system dependencies are required to run the Choreographer application. However, to use the Choreography SDK independently of the Choreographer application, both Python 3 and the `bosdyn-api` and `bosdyn-choreography-client` wheels must be installed.

## Installing and running Choreographer

The Choreographer application is an executable which can be run directly on a laptop or desktop computer. Download the `choreographer.exe` (windows) or `choreographer` (linux) executable from the [Boston Dynamics Support Center](https://support.bostondynamics.com/s/downloads).

**Note for Linux**: It may be necessary to grant executable permissions for the `choreographer` file before it can be executed. To do so, run the following command:

```
sudo chmod +x choreographer
```

To run Choreographer, double-click on the executable to open it or run it from command line.

Command line arguments can be used to immediately connect to one or more robots upon opening.

* On windows:
    ```
    choreographer.exe --hostname {ROBOT_IP} --user {USERNAME} --password {PASSWORD}
    ```
* On Linux:

    ```
    ./choreographer --hostname {ROBOT_IP} --user {USERNAME} --password {PASSWORD}
    ```

* `--hostname` is the robot's IP address or hostname of the Spot robot to connect to Choreographer.
* `--username` and `--password` are the credentials needed for the robot. Note, unlike many of the API examples, the ROBOT_IP argument now requires the command line flag `--hostname` to precede the actual ROBOT_IP argument.

Multiple robots can be connected to Choreographer at once. The command line arguments `--hostname`, `--username`, `--password` must be provided for each robot.

You will also be able to connect to robots through the interface after Choreographer is open.  Doing so from command line is sometimes more convenient when repeatedly connecting to the same robot(s), especially when working with multiple robots.
