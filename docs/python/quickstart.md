# Boston Dynamics API - Python Quickstart

This guide gets you started with the Boston Dynamics API in Python with a simple example.

<!--ts-->
   * [Boston Dynamics API - Python Quickstart](#boston-dynamics-api---python-quickstart)
      * [Getting the code](#getting-the-code)
      * [Getting an Application Token](#getting-an-application-token)
      * [Exploring Spot's services.](#exploring-spots-services)
         * [Connecting to Spot](#connecting-to-spot)
         * [Getting Spot's ID](#getting-spots-id)
         * [Listing services](#listing-services)
      * [Using the SDK](#using-the-sdk)
         * [Creating the SDK object](#creating-the-sdk-object)
         * [Getting the Robot ID](#getting-the-robot-id)
         * [Inspecting robot state](#inspecting-robot-state)
         * [Capturing an image](#capturing-an-image)
         * [Configuring the E-Stop](#configuring-the-e-stop)
         * [Taking ownership of the robot.](#taking-ownership-of-the-robot)
         * [Powering on the robot](#powering-on-the-robot)
         * [Establishing timesync](#establishing-timesync)
         * [Commanding the robot](#commanding-the-robot)
         * [Powering off the robot](#powering-off-the-robot)
      * [Next Steps](#next-steps)
<!--te-->

## Getting the code

The Boston Dynamics API works with Python 2.7 or Python 3.6 or higher. Python 3.6 is recommended due to the impending end-of-life for Python 2.

Downloads and instructions for installing Python can be found at https://www.python.org/.

### Getting pip3 configured

If you are planning to use Python 2 only, you can skip this step.

First, check if pip3 is installed - and if so, what version.

```shell
$ pip3 --version
pip 19.2.1 from <path on your computer>
```

If pip3 is not found, you'll need to install it. There are a few options:
  * pip3 will come preinstalled with all Python 3 versions >= 3.4 downloaded from python.org
  * Use the `get-pip.py` [installation script](https://pip.pypa.io/en/stable/installing/).
  * Use an OS-specific package manager (such as the python3-pip package on Ubuntu)

**Important** The rest of the documentation assumes pip3 >= 18.0.0. If `pip3 --version` showed an older version (9.0.1 is quite common) you will need to upgrade it.

```shell
$ pip3 --version
pip 9.0.1 from <path on your computer>
$ pip3 install --upgrade pip
Collecting pip
  Cache entry deserialization failed, entry ignored
  Downloading https://files.pythonhosted.org/packages/8d/07/f7d7ced2f97ca3098c16565efbe6b15fafcba53e8d9bdb431e09140514b0/pip-19.2.2-py2.py3-none-any.whl (1.4MB)
    100% |████████████████████████████████| 1.4MB 1.3MB/s
Installing collected packages: pip
Successfully installed pip-19.2.2
```

Check that pip3 is up-to-date.
```shell
$ pip3 --version
pip 19.2.2 from <path on your computer>
```

**Ubuntu users:** The previous `pip3 --version` command may fail if you installed pip3 via the python3-pip package. If so, you might see an error like:

```shell
$ pip3 --version
Traceback (most recent call last):
  File "/usr/bin/pip3", line 9, in <module>
    from pip import main
ImportError: cannot import name 'main'
```

To fix this, you'll need to make a small fix to `/usr/bin/pip3`. See https://stackoverflow.com/a/51462434 for instructions on how to do that.

### Getting pip configured

If you are planning to use Python 3 only, you can skip this step.

First, check if pip is installed - and if so, what version.

```shell
$ pip --version
pip 19.2.1 from <path on your computer>
```

If pip is not found, you'll need to install it. There are a few options:
  * pip will come preinstalled with all Python 2 versions >= 2.7.9 downloaded from python.org
  * Use the `get-pip.py` [installation script](https://pip.pypa.io/en/stable/installing/).
  * Use an OS-specific package manager (such as the python-pip package on Ubuntu)

**Important** The rest of the documentation assumes pip >= 18.0.0. If `pip --version` showed an older version (9.0.1 is quite common) you will need to upgrade it.

```shell
$ pip --version
pip 9.0.1 from <path on your computer>
$ pip install --upgrade pip
Collecting pip
  Cache entry deserialization failed, entry ignored
  Downloading https://files.pythonhosted.org/packages/8d/07/f7d7ced2f97ca3098c16565efbe6b15fafcba53e8d9bdb431e09140514b0/pip-19.2.2-py2.py3-none-any.whl (1.4MB)
    100% |████████████████████████████████| 1.4MB 1.3MB/s
Installing collected packages: pip
Successfully installed pip-19.2.2
```

Check that pip is up-to-date.
```shell
$ pip --version
pip 19.2.2 from <path on your computer>
```

**Ubuntu users:** The previous `pip --version` command may fail if you installed pip via the python-pip package. If so, you might see an error like:

```shell
$ pip --version
Traceback (most recent call last):
  File "/usr/bin/pip", line 9, in <module>
    from pip import main
ImportError: cannot import name 'main'
```

To fix this, you'll need to make a small fix to `/usr/bin/pip`. See https://stackoverflow.com/a/51462434 for instructions on how to do that.

### Installing the Boston Dynamics Python Libraries

Now that you have pip and/or pip3 installed, it's time to install the Boston Dynamics Python libraries.

#### Python 3 steps for Linux, MacOS, or Windows Subsystem for Linux (WSL)

Assuming that the Boston Dynamics SDK directory is downloaded at `~/bosdyn-sdk-beta`, the following commands will install the libraries for Python 3.

```
$ pip3 install --upgrade --find-links=~/bosdyn-sdk-beta/prebuilt bosdyn-client
```

If you see an error like this:

```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied: <path>
Consider using the `--user` option or check the permissions.
```

then try the following command to install the Boston Dynamics Python libraries in a per-user location:

```
$ pip3 install --user --upgrade --find-links=~/bosdyn-sdk-beta/prebuilt bosdyn-client
```

Make sure that the packages have been installed. If you don't see listings for bosdyn-api, bosdyn-client, and bosdyn-core, something went wrong during installation.

```shell
$ pip3 list --format=columns | grep bosdyn
bosdyn-api                    1.0.1
bosdyn-client                 1.0.1
bosdyn-core                   1.0.1
```

Optionally, install Pillow - a library for handling images. Later in the quickstart we will use this to display images from the robot.

**WSL users:** while you can install Pillow, you won't be able to use it since WSL is terminal-based only.

```shell
$ pip3 install pillow
```

#### Python 3 steps for Windows

Assuming that the Boston Dynamics SDK directory is downloaded at `C:\Users\foobar\bosdyn-sdk-beta`, the following commands will install the libraries for Python 3.

```
$ pip3 install --upgrade --find-links=C:\Users\foobar\bosdyn-sdk-beta\prebuilt bosdyn-client
```

If you see an error like this:

```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied: <path>
Consider using the `--user` option or check the permissions.
```

then try the following command to install the Boston Dynamics Python libraries in a per-user location:

```
$ pip3 install --user --upgrade --find-links=C:\Users\foobar\bosdyn-sdk-beta\prebuilt bosdyn-client
```

Make sure that the packages have been installed. If you don't see listings for bosdyn-api, bosdyn-client, and bosdyn-core, something went wrong during installation.

```shell
$ pip3 list --format=columns
bosdyn-api                    1.0.1
bosdyn-client                 1.0.1
bosdyn-core                   1.0.1
```

Optionally, install Pillow - a library for handling images. Later in the quickstart we will use this to display images from the robot.

```shell
$ pip3 install pillow
```

#### Python 2 steps for Linux, MacOS, or Windows Subsystem for Linux (WSL)

Assuming that the Boston Dynamics SDK directory is downloaded at `~/bosdyn-sdk-beta`, the following commands will install the libraries for Python 2.

```
$ pip install --upgrade --find-links=~/bosdyn-sdk-beta/prebuilt bosdyn-client
```

If you see an error like this:

```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied: <path>
Consider using the `--user` option or check the permissions.
```

then try the following command to install the Boston Dynamics Python libraries in a per-user location:

```
$ pip install --user --upgrade --find-links=~/bosdyn-sdk-beta/prebuilt bosdyn-client
```

Make sure that the packages have been installed. If you don't see listings for bosdyn-api, bosdyn-client, and bosdyn-core, something went wrong during installation.

```shell
$ pip list --format=columns | grep bosdyn
bosdyn-api                    1.0.1
bosdyn-client                 1.0.1
bosdyn-core                   1.0.1
```

Optionally, install Pillow - a library for handling images. Later in the quickstart we will use this to display images from the robot.

**WSL users:** while you can install Pillow, you won't be able to use it since WSL is terminal-based only.

```shell
$ pip install pillow
```

#### Python 2 steps for Windows

Assuming that the Boston Dynamics SDK directory is downloaded at `C:\Users\foobar\bosdyn-sdk-beta`, the following commands will install the libraries for Python 2.

```
$ pip install --upgrade --find-links=C:\Users\foobar\bosdyn-sdk-beta\prebuilt bosdyn-client
```

If you see an error like this:

```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied: <path>
Consider using the `--user` option or check the permissions.
```

then try the following command to install the Boston Dynamics Python libraries in a per-user location:

```
$ pip install --user --upgrade --find-links=C:\Users\foobar\bosdyn-sdk-beta\prebuilt bosdyn-client
```

Make sure that the packages have been installed. If you don't see listings for bosdyn-api, bosdyn-client, and bosdyn-core, something went wrong during installation.

```shell
$ pip list --format=columns
bosdyn-api                    1.0.1
bosdyn-client                 1.0.1
bosdyn-core                   1.0.1
```

Optionally, install Pillow - a library for handling images. Later in the quickstart we will use this to display images from the robot.

```shell
$ pip install pillow
```

### Verifying that Boston Dynamics Python libraries are installed.

Verify that the libraries are correctly installed by importing them in Python.

#### Python 3

Start Python 3 in an interactive mode. Windows users may need to start Python 3 via the Start Menu, but users of other OS's will be able to start via a terminal application.

```shell
$ python3
Python 3.6.7 (default, Oct 22 2018, 11:32:17)
[GCC 8.2.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
```

Now, import the `bosdyn.client` library and get interactive help about the library. Assuming everything is installed correctly, you should see something like the following: 

```python
>>> import bosdyn.client
>>> help(bosdyn.client)
Help on package bosdyn.client in bosdyn:

NAME
    bosdyn.client

DESCRIPTION
    The client library package.
    Sets up some convenience imports for commonly used classes.

PACKAGE CONTENTS
    __main__
...
```

If the libraries are **not** installed correctly, you may see an error like this one:

```python
>>> import bosdyn.client
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'bosdyn.client'
```

If that's the case, first run `pip3 list` again to make sure that the Boston Dynamics Python libraries are installed. If they are and you run into this issue, send an email to dev@bostondynamics.com explaining the problem.

#### Python 2

Start Python 2 in an interactive mode. Windows users may need to start Python 2 via the Start Menu, but users of other OS's will be able to start via a terminal application.

```shell
$ python
Python 2.7.15rc1 (default, Nov 12 2018, 14:31:15)
[GCC 7.3.0] on linux2
Type "help", "copyright", "credits" or "license" for more information.
```

Now, import the `bosdyn.client` library and get interactive help about the library. Assuming everything is installed correctly, you should see something like the following: 

```python
>>> import bosdyn.client
>>> help(bosdyn.client)
Help on package bosdyn.client in bosdyn:

NAME
    bosdyn.client

DESCRIPTION
    The client library package.
    Sets up some convenience imports for commonly used classes.

PACKAGE CONTENTS
    __main__
...
```

If the libraries are **not** installed correctly, you may see an error like this one:

```python
>>> import bosdyn.client
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'bosdyn.client'
```

If that's the case, first run `pip list` again to make sure that the Boston Dynamics Python libraries are installed. If they are and you run into this issue, send an email to dev@bostondynamics.com explaining the problem.

## Getting an Application Token

Although you can start playing around with the Python libraries right now, to actually control a robot with you will need to get an Application Token from Boston Dynamics.

To get an Application Token, email dev@bostondynamics.com with subject "Application Token Request". You should receive an email with a link to an Application Token within one business day. Visit the link in your browser, and download the Application Token.

Once downloaded, it needs to be placed in a special `.bosdyn` directory in your home directory.

For Unix-based systems, assuming the token was downloaded to `~/Downloads/dev.app_token`

```sh
$ cd ~/
$ mkdir .bosdyn
$ cp ~/Downloads/dev.app_token ~/.bosdyn/
```

For Windows, assuming the home directory is `C:\Users\Developer` and the token was downloaded to `C:\Users\Developer\Downloads\dev.app_token`

```console
C:\WINDOWS>cd C:\Users\Developer
C:\Users\Developer>mkdir .bosdyn
C:\Users\Developer>cp Downloads\dev.app_token .bosdyn\
```

## Exploring Spot's services.

This section will explore some of what Spot has to offer using the command line tool. This tool is built on top of the Python libraries.

### Connecting to Spot

For the remainder of the quickstart, you'll need a Spot robot which is powered on, and network reachable from your development computer. You'll also need account credentials on the Spot robot for the majority of the exercises. Please refer to the Spot Administrator's guide for instructions on how to set those up.


This document assumes the following:
* You are connecting to Spot's WiFi access point
* Spot is accessible at the IP address 192.168.80.3
* There is an account with name "user" and password "password" on the robot.

### Getting Spot's ID

On the command line, issue the following command to get information about the robot. If run successfully, you should see output which includes the serial number of the Spot robot, the hardware version of the robot, and the software version installed on the robot.


```
$ python3 -m bosdyn.client 192.168.80.3 id
beta-BD-90370002                spot (V3)
 Software: 1.0.0 (ca559484e93 2019-06-03 15:58:43)
  Installed: 2019-06-03 16:19:11
```

There's two common error cases if that did not work.

The first case is when an Application Token was not installed correctly.

If you see an error like the one below, it means that the Application Token is not installed correctly.

```
$ python3 -m bosdyn.client 192.168.80.3 id
Traceback (most recent call last):
  File "/usr/lib/python3.6/runpy.py", line 193, in _run_module_as_main
    "__main__", mod_spec)
  File "/usr/lib/python3.6/runpy.py", line 85, in _run_code
    exec(code, run_globals)
  File "/home/BOSDYN/cbentzel/.local/lib/python3.6/site-packages/bosdyn/client/__main__.py", line 6, in <module>
    if not main():
  File "/home/BOSDYN/cbentzel/.local/lib/python3.6/site-packages/bosdyn/client/command_line.py", line 544, in main
    sdk.load_app_token(options.app_token)
  File "/home/BOSDYN/cbentzel/.local/lib/python3.6/site-packages/bosdyn/client/sdk.py", line 175, in load_app_token
    with open(resource_path, 'rb') as token_file:
TypeError: expected str, bytes or os.PathLike object, not NoneType
```

If you don't already have an Application Token, you will need to get one following the instructions above.  If you do have an Application Token, but it is not stored at the default location, you will need to specify the file path to it using the `--app-token` command line option.

If you see an error like the one below, it means that the robot is not powered on or is unreachable.

```
$ python3 -m bosdyn.client 192.168.80.3 id
Could not contact robot with hostname "192.168.80.3".
>
```

Assuming that the command worked successfully, it's time to look under the hood a bit more to understand how the command works. Specify the verbose flag with `-v` or `--verbose`, and you'll get a lot of information if everything works correctly. We'll explain it a bit more below.

```
$ python3 -m bosdyn.client --verbose 192.168.80.3 id
2019-06-06 13:11:13,454 - DEBUG - Creating standard Sdk, cert glob: "None"
2019-06-06 13:11:13,718 - DEBUG - Created client for robot-id with <class 'bosdyn.client.robot_id.RobotIdClient'>
2019-06-06 13:11:13,718 - DEBUG - Created channel to beta26 at port 443
2019-06-06 13:11:13,719 - DEBUG - blocking request: b'/bosdyn.api.RobotIdService/GetRobotId'
header {
  request_timestamp {
    seconds: 1559841073
    nanos: 719016960
  }
  client_name: "BosdynClientlaptop-cbentzel01:__main__.py-32664"
}


2019-06-06 13:11:13,743 - DEBUG - response: b'/bosdyn.api.RobotIdService/GetRobotId'
header {
  request_header {
    request_timestamp {
      seconds: 1559841073
      nanos: 719016960
    }
    client_name: "BosdynClientlaptop-cbentzel01:__main__.py-32664"
  }
  request_received_timestamp {
    seconds: 1559841069
    nanos: 399929111
  }
  response_timestamp {
    seconds: 1559841069
    nanos: 399957142
  }
  error {
    code: CODE_OK
  }
  request {
    type_url: "type.googleapis.com/bosdyn.api.RobotIdRequest"
    value: "\n?\n\014\010\261\222\345\347\005\020\200\250\355\326\002\022/BosdynClientlaptop-cbentzel01:__main__.py-32664"
  }
}
robot_id {
  serial_number: "beta-BD-90370002"
  species: "spot"
  version: "V3"
  software_release {
    version {
      major_version: 1
    }
    changeset_date {
      seconds: 1559591923
    }
    changeset: "ca559484e93"
    install_date {
      seconds: 1559593151
    }
    parameters {
      label: "use_leases"
      int_value: 1
    }
  }
  nickname: "beta-BD-90370002"
}


beta-BD-90370002                spot (V3)
 Software: 1.0.0 (ca559484e93 2019-06-03 15:58:43)
  Installed: 2019-06-03 16:19:11
```

All Boston Dynamics API examples will start by creating an SDK object, as shown in the log line below. This output text also demonstrates how the Python library makes use of Python's [logging facility](https://docs.python.org/3/library/logging.html).  This facility gives application developers a high level of flexibility for consuming the logged statements.

```
2019-06-06 13:11:13,454 - DEBUG - Creating standard Sdk, cert glob: "None"
```

The Boston Dynamics API exposes on-robot capabilities via a set of network-accessible services - similar to a [microservice](https://en.wikipedia.org/wiki/Microservices) architecture. The line below shows how a client for Robot ID service is being created by the command-line tool.

```
2019-06-06 13:11:13,718 - DEBUG - Created client for robot-id with <class 'bosdyn.client.robot_id.RobotIdClient'>
```

All communication to the robot is over a secure HTTPS connection, as seen in the following line.

```
2019-06-06 13:11:13,718 - DEBUG - Created channel to 192.168.80.3 at port 443
```

The Boston Dynamics API uses [gRPC](https://grpc.io) as the underlying RPC transport. gRPC is a high-performance, well-tested library which supports a wide variety of programming environments. gRPC uses [Protocol Buffers](https://developers.google.com/protocol-buffers/) as the messaging format, which has a compact over-the-wire representation and supports backwards and forwards compatibility.

In the block below, the `GetRobotId` RPC is made to the `bosdyn.api.RobotIdService` using the request message shown.

The Python library will take care of the gRPC details for you, but it is occasionally helpful to get to that level when debugging problems.

```
2019-06-06 13:11:13,719 - DEBUG - blocking request: b'/bosdyn.api.RobotIdService/GetRobotId'
header {
  request_timestamp {
    seconds: 1559841073
    nanos: 719016960
  }
  client_name: "BosdynClientlaptop-cbentzel01:__main__.py-32664"
}
```

Finally, the RobotIdService responds to the `GetRobotId` RPC with a response including information about the robot.

```
2019-06-06 13:11:13,743 - DEBUG - response: b'/bosdyn.api.RobotIdService/GetRobotId'
header {
  request_header {
    request_timestamp {
      seconds: 1559841073
      nanos: 719016960
    }
    client_name: "BosdynClientlaptop-cbentzel01:__main__.py-32664"
  }
  request_received_timestamp {
    seconds: 1559841069
    nanos: 399929111
  }
  response_timestamp {
    seconds: 1559841069
    nanos: 399957142
  }
  error {
    code: CODE_OK
  }
  request {
    type_url: "type.googleapis.com/bosdyn.api.RobotIdRequest"
    value: "\n?\n\014\010\261\222\345\347\005\020\200\250\355\326\002\022/BosdynClientlaptop-cbentzel01:__main__.py-32664"
  }
}
robot_id {
  serial_number: "beta-BD-90370002"
  species: "spot"
  version: "V3"
  software_release {
    version {
      major_version: 1
    }
    changeset_date {
      seconds: 1559591923
    }
    changeset: "ca559484e93"
    install_date {
      seconds: 1559593151
    }
    parameters {
      label: "use_leases"
      int_value: 1
    }
  }
  nickname: "beta-BD-90370002"
}
```

### Listing services

The following command lists all of the services available on the robot.

```
$ python3 -m bosdyn.client --user=user --password=password 192.168.80.3 dir list
name                    type                            authority                   tokens
------------------------------------------------------------------------------------------
auth                    bosdyn.api.AuthService          auth.spot.robot
estop                   bosdyn.api.EstopService         estop.spot.robot            app, user
image                   bosdyn.api.ImageService         api.spot.robot              app, user
lease                   bosdyn.api.LeaseService         api.spot.robot              app, user
log-annotation          bosdyn.api.LogAnnotationService log.spot.robot              app, user
power                   bosdyn.api.PowerService         power.spot.robot            app, user
robot-command           bosdyn.api.RobotCommandService  command.spot.robot          app, user
robot-id                bosdyn.api.RobotIdService       id.spot.robot               app
robot-state             bosdyn.api.RobotStateService    state.spot.robot            app, user
time-sync               bosdyn.api.TimeSyncService      api.spot.robot              app, user
```

Note that a valid username and password is needed to get a list of services. If you don't have one, you'll see an error like below.

```
$ python3 -m bosdyn.client --user=user --password=badpass 192.168.80.3 dir list
Traceback (most recent call last):
  File "/usr/lib/python3.6/runpy.py", line 193, in _run_module_as_main
    "__main__", mod_spec)
  File "/usr/lib/python3.6/runpy.py", line 85, in _run_code
    exec(code, run_globals)
  File "/home/BOSDYN/cbentzel/.local/lib/python3.6/site-packages/bosdyn/client/__main__.py", line 6, in <module>
    if not main():
  File "/home/BOSDYN/cbentzel/.local/lib/python3.6/site-packages/bosdyn/client/command_line.py", line 546, in main
    robot.authenticate(options.username, options.password)
  File "/home/BOSDYN/cbentzel/.local/lib/python3.6/site-packages/bosdyn/client/robot.py", line 115, in authenticate
    self.user_token = auth_client.auth(username, password)
  File "/home/BOSDYN/cbentzel/.local/lib/python3.6/site-packages/bosdyn/client/auth.py", line 82, in auth
    **kwargs)
  File "/home/BOSDYN/cbentzel/.local/lib/python3.6/site-packages/bosdyn/client/common.py", line 198, in call
    raise exc
bosdyn.client.auth.AuthInvalidLoginError: bosdyn.api.GetAuthTokenResponse: Username/password is invalid
```

You've already used the robot-id service via the id command above. The next section will cover the majority of the other services by getting Spot to power on, stand up, and sit back down.

## Using the SDK

### Creating the SDK object

Start up a python interpreter (you can also use ipython3).

```sh
$ python3
```

Import the bosdyn.client package - this should work assuming you've successfully made it through the QuickStart so far.

```python
>>> import bosdyn.client
```

All Boston Dynamics API programs start by creating an SDK object. The following block does that, and specifies a client name. The client name is used to help with debugging, and does not have any semantic information - so use whatever string is helpful for you.


```python
>>> sdk = bosdyn.client.create_standard_sdk('quickstart-spot')
```

You'll need to let the SDK know about the Application Token to use it.

```python
>>> import os
>>> sdk.load_app_token(os.path.expanduser('~/.bosdyn/dev.app_token'))
```

Now, let's get the robot id, similar to the command line example above. You'll first need to create a `robot` object. In this example, you'll only create one `robot` object, but it is possible to create and control multiple robots in the same program with the Boston Dynamics API.

Create the robot with the network address.

```python
>>> robot = sdk.create_robot('192.168.80.3')
```

### Getting the Robot ID

As discussed earlier, Spot exposes its capability via a number of services. The Boston Dynamics Python API has a corresponding set of clients for each service, which are created off of the robot object.

The following example creates a robot_id client, and gets the identification information.

```python
>>> id_client = robot.ensure_client('robot-id')
>>> id_client.get_id()
serial_number: "beta-BD-91270003"
species: "spot"
version: "V3"
software_release {
  version {
    major_version: 1
  }
  changeset_date {
    seconds: 1559664233
  }
  changeset: "896f9f94b3e"
  install_date {
    seconds: 1559665646
  }
  parameters {
    label: "use_leases"
    int_value: 1
  }
}
nickname: "beta-BD-91270003"
```

The `get_id` call above is blocking - it will not complete until after the RPC completes. It is possible to tweak some parameters for the call, such as a timeout for how long to wait. The following example sets a too short timeout and will likely fail.

```
>>> id_client.get_id(timeout=0.0001)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/BOSDYN/cbentzel/.local/lib/python3.6/site-packages/bosdyn/client/robot_id.py", line 32, in get_id
    error_from_response=common_header_errors, **kwargs)
  File "/home/BOSDYN/cbentzel/.local/lib/python3.6/site-packages/bosdyn/client/common.py", line 190, in call
    response = rpc_method(request, **kwargs)
  File "/home/BOSDYN/cbentzel/.local/lib/python3.6/site-packages/grpc/_channel.py", line 565, in __call__
    return _end_unary_response_blocking(state, call, False, None)
  File "/home/BOSDYN/cbentzel/.local/lib/python3.6/site-packages/grpc/_channel.py", line 467, in _end_unary_response_blocking
    raise _Rendezvous(state, None, None, deadline)
grpc._channel._Rendezvous: <_Rendezvous of RPC that terminated with:
        status = StatusCode.DEADLINE_EXCEEDED
        details = "Deadline Exceeded"
        debug_error_string = "{"created":"@1559849991.244348068","description":"Deadline Exceeded","file":"src/core/ext/filters/deadline/deadline_filter.cc","file_line":69,"grpc_status":4}"
>
```

In addition to blocking calls, clients support non-blocking asynchronous calls. This can be useful in high performance applications where a thread of execution can not stall waiting for an RPC to complete. Python's [futures](https://docs.python.org/3/library/concurrent.futures.html#future-objects) architecture is used as the underpinning of asynchronous communication.

The following example does an asynchronous call for the robot id, and waits for the result from the returned future object.

```python
>>> fut = id_client.get_id_async()
>>> fut.result()
serial_number: "beta-BD-91270003"
species: "spot"
version: "V3"
software_release {
  version {
    major_version: 1
  }
  changeset_date {
    seconds: 1559664233
  }
  changeset: "896f9f94b3e"
  install_date {
    seconds: 1559665646
  }
}
nickname: "beta-BD-91270003"
```

### Inspecting robot state

The robot state service contains dynamic information about the robot such as its location, battery status, and more.

Before it can be retrieved, you need to authenticate to the robot. The majority of services require the user to be authenticated - this prevents random network attackers from being able to control the robot, or read information which might be sensitive.

Assuming that the username is `user` and the password is `password`, issue the following command.

```python
>>> robot.authenticate('user', 'password')
```

If you provided the wrong credentials, an exception should be raised.

Now we can create a client for Robot State, and obtain information about it.

```python
>>> state_client = robot.ensure_client('robot-state')
>>> state_client.get_robot_state()
power_state {
  timestamp {
    seconds: 1559850904
    nanos: 816605952
  }
  state: STATE_ERROR
}
battery_states {
  timestamp {
    seconds: 1559850904
    nanos: 816605952
  }
  identifier: "a2-19409-0003"
}
... A lot more details removed.
```

The structure of the Robot State message can be seen in the [protobuf definition](../../protos/bosdyn/api/robot_state.proto).

### Capturing an image

Images can be captured from the five fisheye cameras around Spot's body. We use a human readable string to identify these image sources. The 'list_image_sources' RPC will return the source names.

```python
>>> from bosdyn.client.image import ImageClient
>>> image_client = robot.ensure_client(ImageClient.default_service_name)
>>> sources = image_client.list_image_sources()
>>> [source.name for source in sources]
['back_fisheye_image', 'frontleft_fisheye_image', 'frontright_fisheye_image',
 'left_fisheye_image', 'right_fisheye_image']
```

Using the source names above, we can capture an image from one or more image sources. These images can be captured in RAW format or JPG format (with specified quality). Multiple images requested in a single RPC will be hardware timesynced with one another.

```python
>>> image_response = image_client.get_image_from_sources(["left_fisheye_image"])[0]
# Optionally display the image.
# The following requires the Python "pillow" package to be available.
# See earlier in this guide for how to install that package.
>>> from PIL import Image
>>> import io
>>> image = Image.open(io.BytesIO(image_response.shot.image.data))
# Note: the following will *not* work if you are running python3/python
#  within WSL on Windows.
>>> image.show()
```

### Configuring the E-Stop

Before Spot can power on, the Emergency Stop, or E-Stop, system must be correctly configured. The E-Stop is a key safety feature of Spot which lets operators kill motor power immediately if a situation calls for it.

Let's take a look at the initial E-Stop state of the robot.

```python
>>> estop_client = robot.ensure_client('estop')
>>> estop_client.get_status()
stop_level: ESTOP_LEVEL_CUT
stop_level_details: "Not all endpoints are registered"
```

The `stop_level: ESTOP_LEVEL_CUT` line indicates that power will not be enabled since the E-Stop level is CUT.

The `stop_level_details: "Not all endpoints are registered"` line indicates that there are no E-Stop Endpoints registered. An E-Stop Endpoint is the client component of the E-Stop system which lets a user immediately kill power. Spot may have more than one E-Stop Endpoint registered at a time - for example, during operator training the trainee may have a tablet which lets them control the robot and kill power, and the trainer may have a tablet which lets them kill power but not control the robot.

The next step will create and register an E-Stop Endpoint.

SAFETY NOTE: it will trigger an emergency stop on the robot, so only perform this step when the robot is already powered off.

```python
>>> estop_endpoint = bosdyn.client.estop.EstopEndpoint(client=estop_client, name='hello-spot', estop_timeout=9.0)
>>> estop_endpoint.force_simple_setup()
```

A brief explanation of the EstopEndpoint arguments:
  * `client=estop_client`: the API client to communicate to the robot with.
  * `name='hello-spot'`: a debug-helper name to the Endpoint.
  * `estop_timeout=9.0`: E-Stop endpoints are expected to regularly-check in to the robot. This ensures that the client is still alive, and has network connectivity to the robot. If it has been more than `estop_timeout` seconds, the motor power will cut out. Tuning this number is important: too low of a number, and the power may cut out due to transient network issues; too large of a number, and there may be a long time between when the user wants the motors to power off and when they actually power off. Experimentally 9 seconds has been a generally applicable number, but the actual number depends on your circumstances.

The `force_simple_setup` call will issue a few API calls to make your E-Stop Endpoint the sole endpoint in a new E-Stop configuration.

Take a look at the E-Stop status after those steps completed.

```python
>>> estop_client.get_status()
endpoints {
  endpoint {
    role: "PDB_rooted"
    name: "hello-spot"
    unique_id: "0"
    timeout {
      seconds: 9
    }
  }
  stop_level: ESTOP_LEVEL_CUT
  time_since_valid_response {
    seconds: 1560288104
    nanos: 523911936
  }
}
stop_level: ESTOP_LEVEL_CUT
stop_level_details: "Endpoint timed out"
```

Now an E-Stop Endpoint appears with the name `hello-spot`. The endpoint itself says ESTOP_LEVEL_CUT, with a very long ago `time_since_valid_response`. No check-ins from the E-Stop Endpoint have happened yet. Both the endpoint and the E-Stop systems stop level is `ESTOP_LEVEL_CUT` - if a single Endpoint wants to cut power, the entire system will cut power.

To get the E-Stop Endpoint to allow power, it needs to check in on a regular basis. We'll use the EstopKeepAlive class to do these checkins on a regular basis on a background thread.

```python
>>> estop_keep_alive = bosdyn.client.estop.EstopKeepAlive(estop_endpoint)
>>> estop_client.get_status()
endpoints {
  endpoint {
    role: "PDB_rooted"
    name: "hello-spot"
    unique_id: "0"
    timeout {
      seconds: 9
    }
  }
  stop_level: ESTOP_LEVEL_NONE
  time_since_valid_response {
    seconds: 1
    nanos: 491014912
  }
}
stop_level: ESTOP_LEVEL_NONE
stop_level_details: "Set by an endpoint"
```

Now the `stop_level` is set to `ESTOP_LEVEL_NONE`, indicating that power can start up. Note that in many examples, you should specify the `keep_running_cb` argument in EstopKeepAlive, which is a function called on the background thread to see if check-ins should continue. For example, an interactive UI could pass in a `keep_running_cb` function which blocks until the UI thread has run a cycle. This prevents a frozen client from continuing to allow power to the robot.

### Taking ownership of the robot.

There's one more step before powering on the robot, and that's to grab ownership of the robot. Only one client at a time can control the robot, and the client controlling the robot can be different than the one who has the E-Stop.

To gain control of the robot, a client needs to acquire a Lease. The Lease must be presented with every command to the robot to show that the client still has ownership of the robot. Leases can be returned when the client no longer wants to return the robot. If another client currently has the lease to a robot, acquiring a lease will fail.

Like the E-Stop, Lease holders need to periodically check in to indicate that they are still alive and have a network connection to the robot. If it has been too long since a check-in, the robot will go through a Comms Loss policy - sitting down if it can, and then powering off.

Start by looking at what the leases are like at robot start.

```python
>>> lease_client = robot.ensure_client('lease')
>>> lease_client.list_leases()
resources {
  resource: "body"
  lease {
    resource: "body"
    epoch: "bjyCwJOQnSlghiZo"
    sequence: 1
  }
  lease_owner {
  }
}
```

The first field of `resource` indicates the name of the resource which uses leases for access control. The only resource supported is "body", which covers all of the motors on Spot.

The second field of `lease` covers the details of the lease object. It includes another copy of `resource`, and `epoch` which is randomized on every robot startup, and a monotonically increasing `sequence` number.

The third field of `lease_owner` indicates which client holds the lease. It is currently empty since it has not been acquired.

Now that we've looked at leases, it's time to acquire one.

```python
>>> lease_keep_alive = bosdyn.client.lease.LeaseKeepAlive(lease_client)
>>> lease = lease_client.acquire()
```

Let's take a look at what the lease looks like now.

```python
>>> lease_client.list_leases()
resources {
  resource: "body"
  lease {
    resource: "body"
    epoch: "bjyCwJOQnSlghiZo"
    sequence: 3
  }
  lease_owner {
    client_name: "cmdlaptop-cbentzel01:15239"
  }
}
```

### Powering on the robot

Now that you've authenticated to Spot, an E-Stop Endpoint has been created, and a Lease has been acquired, it's time to power on the robot.

Make sure that the robot is in a safe spot, in a seated position, with a charged battery, and not connected to shore power.

The command below first issues a power command to the robot, then queries the robot for power command feedback. This command returns once the robot is powered on, or throws an error if the power command fails for any reason. It will typically take several seconds to complete.

```python
>>> robot.power_on(timeout_sec=20)
```

The robot object provides a method to check the power status of the robot. This just uses the RobotStateService to check the PowerState, introduced above.

```python
>>> robot.is_powered_on()
True
```

### Establishing timesync

Time sync is required to issue commands to the robot. Specifically, this service estimates the clock skew between the robot's clock and the client's clock. From a safety perspective, this allows users to define a period of time for which a command will be valid. The robot class maintains a timesync thread. The `wait_for_sync` call below will start a time sync thread, and block until sync is established. After timesync is established, this thread will make periodic calls to maintain timesync. Each client is issued a clock identifier. This is used to validate that clients have performed timesync, for services that require this functionality. The client library is written such that most implementation details of time sync are taken care of in the background.

```python
>>> robot.time_sync.wait_for_sync()
```

### Commanding the robot

The RobotCommandService is the primary interface for commanding Spot. Spot commands include `stand`, `sit`, `selfright`, `safe_power_off`, `velocity`, and `trajectory`. For this tutorial, you will just issue stand and safe power off commands.

The API provides a helper function to stand Spot. This command wraps several RobotCommand RPC calls. First a stand command is issued. The robot checks some basic pre conditions (powered on, not faulted, not estopped) and returns a command id. This command id can then be passed to the robot command feedback RPC. This call returns both high level feedback (is the robot still processing the command) as well as command specific feedback (in the case of stand, is the robot standing).

```python
>>> from bosdyn.client.robot_command import RobotCommandClient, blocking_stand
>>> command_client = robot.ensure_client(RobotCommandClient.default_service_name)
>>> blocking_stand(command_client, timeout_sec=10)
```

The robot should now be standing. In addition from transitioning from sit to stand, the stand command can be issued to control the height of the body as well as the orientation of the body with respect to the footprint frame. The footprint frame is a gravity aligned frame with its origin located at the geometric center of the feet. The Z axis up, and the X axis is forward. The commands proto can be quite complex and expressive. This library provides several helper functions to build commands in single line function calls. Feel free to experiment with other parameters.

```python
# Command Spot to rotate about the Z axis.
>>> from bosdyn.geometry import EulerZXY
>>> footprint_R_body = EulerZXY(yaw=0.4, roll=0.0, pitch=0.0)
>>> from bosdyn.client.robot_command import RobotCommandBuilder
>>> cmd = RobotCommandBuilder.stand_command(footprint_R_body=footprint_R_body)
>>> command_client.robot_command(cmd)
# Command Spot to raise up.
>>> cmd = RobotCommandBuilder.stand_command(body_height=0.1)
>>> command_client.robot_command(cmd)
```

### Powering off the robot

Spot has two methods of turning off motor power. Both types of calls can be made through the robot object. The first, preferred method, is "safe_power_off". Internally, this means Spot will attempt to come to a stop and sit down before powering off. The emphasis of this command is on the safe aspect, rather than power off. The robot will not power off until it has sat down. The other power off option cuts motor power immediately, which would cause the robot to collapse.

```python
>>> robot.power_off(cut_immediately=False)
```

## Next Steps

If you made it through this QuickStart - congrats! You're well on your way to becoming a developer on the Boston Dynamics API.

The following are a number of possible next steps:
* Experiment with the API. [hello_spot.py](../../python/bosdyn-tutorials/src/bosdyn/tutorials/hello_spot.py) includes all of the behavior in this document, and you can use it as a starting point for your own behavior.
* Try out the [WASD tutorial](../../python/bosdyn-tutorials/src/bosdyn/tutorials/wasd.py). This is a more detailed example built on top of the Python API which lets you interactively control Spot using the keyboard on your development machine. It covers issuing commands in far more detail than this quick start.
* Read through the [protocol buffer definitions](../../protos/bosdyn/api) and [python source](reference/index.html) to understand even more.

If you have any questions, please email dev@bostondynamics.com with questions.
