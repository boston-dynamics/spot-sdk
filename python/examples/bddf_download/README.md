<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# BDDF data download

This example shows how to download data from GRPC logs and/or the data-buffer service as bddf data. The bddf format is a Boston Dynamics file format added to the SDK in 2.1.

## Setup Dependencies

These examples need to be run with python3, and have the Spot SDK installed. See the requirements.txt file for a list of dependencies which can be installed with pip.

```
$ python3 -m pip install -r requirements.txt
```

## Running the Examples

There are two primary scripts in this example. The first is `bddf_download.py`, which downloads specified data from a robot and saves it as a bddf file.

Another example script is `bddf_read.py`, which extracts and prints protobuf messages stored in a bddf file.

To see the types of messages currently supported by the script, run

```
$ python3 ./bddf_read.py types
```

To list the available series of messages in a given bddf file, try

```
$ python3 ./bddf_read.py series {bddf-file}
```

To extract and print all operator comment messages in a bddf file, run

```
$ python3 ./bddf_read.py show {bddf-file} bosdyn.api.OperatorComment

```

To show `RobotId()` GRPC request messages stored in a bddf file, use

```
$ python3 ./bddf_read.py show-grpc {bddf-file} bosdyn.api.RobotIdRequest

```

To run the script `bddf_download.py` in the example command lines below, we will use the following variables (Bourne-shell syntax):

```
USERNAME=<username>
PASSWORD=<password>
ROBOT_IP=<ip-address>

DOWNLOAD_BDDF="python3 bddf_download.py ${ROBOT_IP}"
```

### Specifying time spans

To get a list of formats supported for specifying time spans for data selection in `bddf_download.py`:

```
$ python3 bddf_download.py ${ROBOT_IP} --help-timespan
A timespan is {val} or {val}-{val} where:

{val} has one of these formats:
 - yyyymmdd_hhmmss  (e.g., 20200120_120000)
 - yyyymmdd         (e.g., 20200120)
 -  {n}d    {n} days ago
 -  {n}h    {n} hours ago
 -  {n}m    {n} minutes ago
 -  {n}s    {n} seconds ago
 - nnnnnnnnnn[.nn]       (e.g., 1581869515.256)  Seconds since epoch
 - nnnnnnnnnnnnnnnnnnnn  Nanoseconds since epoch

For example:
  '5m'                    From 5 minutes ago until now.
  '20201107-20201108'     All of 2020/11/07.
```

### Basic data download

Download all data from the last 5 minutes (the default time span). The data is saved to `./download.bddf` by default.

```
$ ${DOWNLOAD_BDDF}
```

### Operator comments

Download all operator comments sent to the data-buffer in last day and save to `comments.bddf`.

```
$ ${DOWNLOAD_BDDF} --timespan 1d --type bosdyn.api.OperatorComment -o comments.bddf
```

Print the comments:

```
$ python3 ./bddf_read.py show comments.bddf bosdyn.api.OperatorComment
```

### Events

Download all events from stored in the data-buffer on 2022/11/07, and save to `events.bddf`.

```
$ ${DOWNLOAD_BDDF} --timespan 20201107-20201108 --type bosdyn.api.Event -o events.bddf
```

Print the events.

```
$ python3 ./bddf_read.py show events.bddf bosdyn.api.Event
```

### GRPC requests/responses

Download robot-id GRPC requests/responses from 20 minutes ago to 10 minutes ago, and store them in file `robot-id.bddf`.

```
$ ${DOWNLOAD_BDDF} --timespan 20m-10m --service robot-id -o robot-id.bddf
```

Print the request and response messages with

```
$ python3 ./bddf_read.py show-grpc robot-id.bddf bosdyn.api.RobotIdRequest
$ python3 ./bddf_read.py show-grpc robot-id.bddf bosdyn.api.RobotIdResponse
```

## GUI

A graphical user interface is also available using `bddf_download_gui.py`. An additional PyQt5 dependency is required.

```
$ python3 -m pip install -r gui_requirements.txt
```

To run the example as a GUI:

```
$ python3 bddf_download_gui.py
```
