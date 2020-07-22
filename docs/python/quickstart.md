<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# QuickStart

This guide will help you set up your programming environment to successfully command and control Boston Dynamics' `Spot` robot using the `Spot Python SDK`.

**Windows users:** Please find notes like this to help you.

<!--ts-->
  * [System Setup](#system-setup)
     * [System Requirements](#system-requirements)
     * [Python Requirements](#python-requirements)
     * [Pip Installation](#pip-installation)
     * [Manage Multiple Python Environments with virtualenv](#manage-multiple-python-environments)
  * [Install Spot SDK](#install-spot-sdk)
     * [Install Spot Packages from PyPI (recommended)](#install-spot-packages-from-pypi-recommended)
     * [Install Spot Packages from Git Repository](#install-spot-packages-from-git-repository-alternate)
        * [Download Git Repository](#download-git-repository)
        * [Install Prebuilt Packages from Git Repository](#install-prebuilt-packages-from-git-repository)
     * [Verify your Spot SDK installation](#verify-your-spot-sdk-installation)
  * [Verify you can talk to Spot using the SDK](#verify-you-can-talk-to-spot-using-the-sdk)
     * [Get a Spot Robot](#get-a-spot-robot)
     * [Get a user account on the robot](#get-a-user-account-on-the-robot)
     * [Ping Spot](#ping-spot)
     * [Request Spot's ID from Spot](#request-a-spot-robot-s-id)
     * [Run Hello Spot - let's see the robot move!](#run-hello-spot-let-s-see-the-robot-move)
       * [Run an Independent E-Stop](#run-an-independent-e-stop)
       * [Run Hello Spot (Take 2)](#run-hello-spot-take-2)
  * [Next Steps](#next-steps)
<!--te-->

## System setup

### System requirements

The Boston Dynamics Spot Python SDK works with most operating systems including:
* Linux Ubuntu 18.04 LTS
* Windows 10
* MacOS 10.14 (Mojave)

Windows WSL use is discouraged due to so many examples having graphics.

### Python requirements

Spot Python SDK works with Python 3.6 or Python 3.7 only. <u>Python 3.8 is not supported</u>.

Downloads and instructions for installing Python can be found at https://www.python.org/.

**IMPORTANT:** If you have multiple versions of Python installed then running `python` might reference an incorrect version (e.g. version 2.7).  For example, to run python 3 on Ubuntu 18.04 you would run `python3` and on Windows you could use the [Python launcher](https://docs.python.org/3/using/windows.html#launcher) and run `py -3`. Our documentation uses `python` assuming that the command launches a compatible version of Python.

Verify your python install is the correct version.  Open a command prompt or start your python IDE:
```
$ python --version
Python 3.6.8
```

**Windows users:** There are two common methods for starting the Python interpreter on the command
line. First, launch a terminal: Start > Command Prompt. At the command prompt, enter either:

    python.exe

or

    py.exe

The former will directly call the `python.exe` that is highest priority in the PATH environment variable. (Note you could also supply a full pathname `c:\path\to\install\python.exe` to directly call the executable).

The latter uses the Python launcher, which by default starts the most recent version of Python
installed.  You can also optionally pass arguments to the launcher to control what version of
python to launch:

`py.exe -2` (launches Python 2)

`py.exe -3` (launches Python 3)

`py.exe -3.6` (launches Python 3.6)

### Pip Installation


Pip is the package installer for Python. The Spot SDK and the third-party packages used by many of its programming examples use pip to install.

Check if pip is installed by requesting its version:

```
$ python -m pip --version
pip 19.2.1 from <path on your computer>
```

**Windows users:**

```shell
> py.exe -m pip --version.
```

If pip is not found, you'll need to install it. There are a few options:

  * pip comes preinstalled with all Python 3 versions >= 3.4 downloaded from python.org
  * Use the [`get-pip.py` installation script.](https://pip.pypa.io/en/stable/installing/)
  * Use an OS-specific package manager (such as the python3-pip package on Ubuntu)


**Permission Denied:** If you do not use virtualenv (described below), when you install packages using pip, you may receive Permission Denied errors, if so, add the `--user` option to your pip command.

### Manage multiple Python environments

**This section is optional, but recommended.**

Users with multiple python versions, anaconda, etc., are responsible for maintaining separation between those installs.  Common failures include using the wrong version of python, installing python packages to the wrong python, or using pip associated with the wrong python.  One way to improve the stability of your Spot code and your pre-existing python code is to keep them separate using virtual environments.  Here are some tips to working with [virtualenv](https://pypi.org/project/virtualenv).


*  Install virtualenv.
*  Create a virtualenv, being careful to point at the proper python executable.
*  Activate the virtualenv.
*  Install packages as needed, including Spot SDK.
*  When finished with a session, deactivate.

```
$ python -m pip install virtualenv
$ python -m virtualenv my_spot_v2_0_env
$ source my_spot_v2_0_env/bin/activate
$ (install packages including Spot SDK, code, edit, execute, etc.)
$ deactivate
```

**Note:** Please ensure the virtualenv was created using the expected version of python.  If you see:

```shell
$ python -m virtualenv my_spot_v2_0_env
Running virtualenv with interpreter /usr/bin/python2
...
```
Then the wrong interpreter is being used.  You can pass the interpreter as an additional argument, for example:

```shell
$ python -m virtualenv -p /usr/bin/python3 my_spot_v2_0_env
```


**Windows users:**

```
> py.exe -m pip install virtualenv
> py.exe -m virtualenv my_spot_v2_0_env
> .\my_spot_v2_0_env\Scripts\activate.bat
```

Install packages including Spot SDK, code, edit, execute, etc.

```
> .\my_spot_v2_0_env\Scripts\deactivate.bat
```

## Install Spot SDK

The recommended installation method is to install the SDK packages [from PyPI using pip](#install-spot-packages-from-pypi-recommended). The same SDK packages are available from the [git repository](https://github.com/boston-dynamics/spot-sdk), and can be installed from there.

The full documentation is also available at [https://dev.bostondynamics.com](https://dev.bostondynamics.com).

Example applications and sample code can be found in the git repository. Follow the [instructions below](#download-git-repository) to download from GitHub.

### Install Spot Packages from PyPI (recommended)

With `python` and `pip` properly installed and configured, the Python packages are easily installed
or upgraded from PyPI with the following command.

```
$ python -m pip install --upgrade bosdyn-client bosdyn-mission
```

Installing the `bosdyn-client` and `bosdyn-mission` packages will also install `bosdyn-api` and
`bosdyn-core` packages with the same version. The command above installs the latest version of the
packages. To install a different version of the packages from PyPI, for example 2.0.1, use the
following command.

```
$ python -m pip install bosdyn-client==2.0.1 bosdyn-mission==2.0.1
```


### Install Spot Packages from Git Repository (alternate)
This section descibes how to get and install the complete Spot SDK from the Git repository.

#### Download Git Repository

The Spot Python SDK is available at https://github.com/boston-dynamics/spot-sdk.

Users can either:

  * `git clone https://github.com/boston-dynamics/spot-sdk.git` (recommended)
  * Download a zipfile distribution:
    * Select green box "Clone or download" from the webpage.
    * Select "Download ZIP".
    * Unzip the file to your home directory.
    * Rename the top-level directory `spot-sdk-master` to `spot-sdk`.


#### Install Prebuilt Packages from Git Repository

This step is not needed if you have already installed the packages from PyPI.

Now that your python and pip are properly configured and you have Spot SDK downloaded or cloned, it is time to install the Spot SDK Python Packages.

The following commands require a pathname to the SDK which we will call `~/spot-sdk` in the following examples.  But your pathname may be different depending on where you cloned/downloaded the files.  For example, **Windows users** may have downloaded these files to `c:\Downloads\spot-sdk`.


```
$ cd ~/spot-sdk/prebuilt
$ python -m pip install *.whl
```

**Windows users:**
Instead of `*.whl`, please list all `.whl` files in the directory explicitly in the following order (api, core, client, mission), for example:

```shell
$ cd ~/spot-sdk/prebuilt
$ python -m pip install bosdyn_api-2.0.1-py2.py3-none-any.whl
$ python -m pip install bosdyn_core-2.0.1-py2.py3-none-any.whl
$ python -m pip install bosdyn_client-2.0.1-py2.py3-none-any.whl
$ python -m pip install bosdyn_mission-2.0.1-py2.py3-none-any.whl
```

**Version incompatibility:**

If you see a version incompatiblity error during pip install such as:

```
ERROR: bosdyn-core \<a version string> has requirement bosdyn-api==\<a version string>, but you'll
have bosdyn-api 2.0.1 which is incompatible.
```

Try uninstalling the bosdyn package and then reinstalling:

```shell
$ python -m pip uninstall bosdyn-api
$ python -m pip install bosdyn_api-2.0.1-py2.py3-none-any.whl
```

### Verify your Spot SDK installation
Make sure that the packages have been installed.

```
$ python -m pip list --format=columns | grep bosdyn
bosdyn-api                    2.0.1
bosdyn-client                 2.0.1
bosdyn-core                   2.0.1
bosdyn-mission                2.0.1
```
If you don't see these 4 packages with your target version, something went wrong during
installation.  Contact support@bostondynamics.com for help.

**Windows users:** Omit `grep` and replace with `findstr` if not recognized.

Next, start your python interpreter:

```
$ python
Python 3.6.8 (default, Jan 14 2019, 11:02:34)
[GCC 8.0.1 20180414 (experimental) [trunk revision 259383]] on linux
Type "help", "copyright", "credits" or "license" for more information.
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
If the packages are **not** installed correctly, you may see an error like this one:

```python
>>> import bosdyn.client
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'bosdyn.client'
```

If that's the case, run `python -m pip list` again to make sure that the Boston Dynamics Python packages are installed.

If you can't import bosdyn.client without an error, you may have multiple instances of Python on your computer, have installed bosdyn to one, and are now running the other.  Check the pathnames of your python executables. Are they where you'd expect them to be?  If not, this is a potential sign that you may have multiple python installs.  Consider using virtual environments (see above).  If all else fails, contact support@bostondynamics.com for help.

## Verify you can talk to Spot using the SDK

To use the SDK, you need:

*  A Spot Robot on the same version as your SDK,
*  A user account on the robot

### Get a Spot robot

Contact sales@bostondynamics.com to get a Spot robot.

### Get a user account on the robot

If you just unboxed your Spot robot, you will find a sticker inside the battery cavity with wifi, admin, and username "user" credentials.  Please note however that Boston Dynamics recommends that you first have your designated robot administrator log onto the robot with admin credentials and change passwords to increase security.

NOTE: The following examples will assume username "user" and password "password."

### Ping Spot

1. Power on Spot.  Wait for the fans to turn off (and maybe 10-20 seconds after that)
2. Connect to Spot via wifi.
3. Ping spot at 192.168.80.3


```
$ ping 192.168.80.3
```

### Request a Spot robot's ID

Issue the following command to get your Spot robot's ID:

```
$ python -m bosdyn.client 192.168.80.3 id
beta-BD-90490007     02-19904-9903   beta29     spot (V3)
Software: 2.0.1 (b11205d698e 2020-03-11 11:53:12)
Installed: 2020-03-11 15:06:57
```

If this worked for you, SUCCESS!  You are now successfully communicating with Spot using the SDK!  Note that the output returned shows your Spot robot's unique serial number, its nickname and robot type (Boston Dynamics has multiple robots), the software version, and install date.

If you see the following:

```shell
$ python -m bosdyn.client 192.168.80.3 id
Could not contact robot with hostname "192.168.80.3"
```

The robot is not powered on or is unreachable.  Go back and try to get your ping to work.  You can also try the `-v` or `--verbose` to get more information to debug the issue.

### Run Hello Spot - let's see the robot move!

OK, we now have our SDK installed properly and we are successfully able to command the robot to
give us its id.  Let's now see the robot do something!


Change your working directory to the hello_spot example. Do a pip install with `requirements.txt` as an argument so that any dependent packages are installed. Then run hello_spot:

**HELPFUL HINT: When working with any Spot SDK programming example, always use the associated `requirements.txt` to install dependent third party packages.**

```
$ cd ~/spot-sdk/python/examples/hello_spot # or wherever you installed Spot SDK
$ python -m pip install -r requirements.txt # will install dependent packages
$ python hello_spot.py --username user --password password 192.168.80.3
```

Hello_spot will fail because there is not an E-Stop endpoint.

```
2020-03-30 15:26:36,283 - ERROR - Robot is E-Stopped. Please use an external E-Stop client, such as
the E-Stop SDK example, to configure E-Stop.
```

If you see the following error:
```
$ python hello_spot.py --username usehername --password pazwierd 192.168.80.3
2020-04-03 15:10:28,189 - ERROR - Hello, Spot! threw an exception: bosdyn.api.GetAuthTokenResponse:
Provided username/password is invalid.
```

Your username or password is incorrect. Check your spelling and verify your credentials with your robot administrator.

#### Run an independent E-Stop

Change your working directory to the E-Stop example and run the nogui version:

```
$ cd ~/spot-sdk/python/examples/estop # or wherever you installed Spot SDK
$ python -m pip install -r requirements.txt # will install dependent packages
$ python estop_nogui.py --username user --password password 192.168.80.3
```

Now try to run the estop_gui version:
```
$ python estop_gui.py --username user --password password 192.168.80.3
```


You should now have a big red STOP button displayed on your screen. You're now ready to go! (or stop in an emergency!!)

#### Run Hello Spot (take 2)


OK, now we have an E-Stop. Leave it running, and open a second python window, and again run hello_spot:

```
$ cd ~/spot-sdk/python/examples/hello_spot # or wherever you installed Spot SDK
$ python hello_spot.py --username user --password password 192.168.80.3
```


Your Spot robot should have powered up its motors, stood up, made a few poses, taken a picture, and sat down.  If it didn't, be sure to check that the **Motor power enable** button on the back of Spot was properly turned on.

Try it again, and this time, push the E-Stop button and watch the robot do a "glide-stop."  Remember, E-Stop is your friend.

**Congratulations, you are now a full-fledged Spot Programming Example Operator!**

But, if you also want to be a full-fledged Spot Programmer, you need to understand more about how Spot works.  Here are the next steps we recommend:

## Next Steps

1.  Read our next section, [Spot Programming](./understanding_spot_programming.md)  Highly recommended!
2.  Take time to explore the [programming examples](../../python/examples/README) which all launch in essentially the same manner as hello_spot.
    *  Try making simple modifications to the code.  NOTE: If you installed the SDK using a zipfile, be careful to understand what changes you've made, as users sometimes inject errors into the SDK code unintentionally.  Git users can simply use `git diff` to understand all changes they have made.
    *  Try out the [wasd programming example](../../python/examples/wasd/README). This is a more detailed example built on top of the Python API which lets you interactively control Spot using the keyboard on your development machine. It covers issuing commands in far more detail than this quick start.  And it is fun!

3.  Read through the [protocol buffer definitions](../protos/README) and the Spot Python SDK [source code documentation](../../python/README) to understand even more.

If you have any questions, please email support@bostondynamics.com.
