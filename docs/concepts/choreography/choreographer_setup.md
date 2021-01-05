<!--
Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Install Choreographer

Choreographer is an application to easily author choreographies with advanced moves and parameters and execute the routines on robot with music synchronization. The application and choreography service require a special license to use. The application can be downloaded from the [Support Center](https://support.bostondynamics.com) in the "Downloads Page" for the 2.1 Release. Additionally, the Support Center provides in depth documentation for how to use Choreographer to create routines, modify moves, connect to robots to execute routines, and debug issues with a FAQs section.

## System Requirements

Choreographer supports 64-bit Microsoft Windows 10 and 64-bit Ubuntu 18.04 Linux. No other system dependencies are required to run the Choreographer application. However, to use the Choreography SDK independently from the Choreographer application, both python 3 and the `bosdyn-choreography-protos` and `bosdyn-choreography-client` wheels must be installed.

## Installation and Running Choreographer

The Choreographer application is an executable which can be run directly on a laptop. Download the `choreographer.exe` (or `choreographer` executable depending on the system OS) file from the Support Center 2.1 Downloads Page.

**Note for Linux machines**: the `choreographer` file may need to be converted to an executable manually after downloading it. Run the following command in the same directory as the `choreographer` file on the command line:
```
sudo chmod +x choreographer
```

To run Choroeographer without any robots connected, just double-click on the executable to open it.

To run Choreographer with robots, start Choreographer from the command line, in the directory where the executable was download, with the following options:
* On windows:
    ```
    choreographer.exe --hostname {ROBOT_IP} --user {USERNAME} --password {PASSWORD}
    ```
* On Linux:

    ```
    ./choreographer --hostname {ROBOT_IP} --user {USERNAME} --password {PASSWORD}
    ```

The `--hostname` is the robot's IP address or hostname of the Spot robot that will be connected to Choreographer. The `--username` and `--password` are the credentials needed for the robot. Note, unlike many of the API examples, the ROBOT_IP argument now requires the command line flag `--hostname` to precede the actual ROBOT_IP argument.

Multiple robots can be connected to Choreographer at once. The command line arguments `--hostname`, `--username`, `--password` need to be provided as a group for each robot that will be connected.
