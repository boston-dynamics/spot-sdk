<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# [Spot SDK](../../README.md) > [Python Library](README.md) > QuickStart <a name="spot-sdk-python-quickstart"></a>

This guide will help you set up your programming environment to successfully command and control Boston Dynamics' `Spot` robot using the `Spot Python SDK`.

**Windows users:** Please find notes like this to help you. 

<!--ts-->
   * [Spot SDK Python Quickstart](#user-content-spot-sdk-python-quickstart)
      * [System Setup](#user-content-system-setup)
         * [System Requirements](#user-content-system-requirements)
         * [Python Requirements](#user-content-python-requirements)
         * [Pip](#user-content-pip)
         * [Managing Multiple Python Environments with virtualenv](#user-content-managing-multiple-python-environments-with-virtualenv)
      * [Install Spot Python SDK](#user-content-install-spot-python-sdk)
         * [Getting Spot Python SDK](#user-content-getting-spot-python-sdk)
         * [Installing Spot Python SDK](#user-content-installing-spot-python-sdk)
         * [Verify your Spot SDK installation](#user-content-verify-your-spot-sdk-installation)         
      * [Verify you can talk to Spot using the SDK](#user-content-verify-you-can-talk-to-spot-using-the-sdk)
         * [Get a Spot Robot](#user-content-get-a-spot-robot)
         * [Get and Install an Application Token](#user-content-get-and-install-an-application-token)
         * [Get a user account on the robot](#user-content-get-a-user-account-on-the-robot)
         * [Ping Spot](#user-content-ping-spot)
         * [Request Spot's ID from Spot](#user-content-request-spots-id-from-spot)
         * [Run Hello Spot...let's see the robot move!](#user-content-run-hello-spot-lets-see-the-robot-move)
           * [Run an Independent E-Stop](#user-content-run-an-independent-e-stop)
           * [Run Hello Spot (Take 2)](#user-content-run-hello-spot)
      * [Next Steps](#user-content-next-steps)
<!--te-->
## System Setup <a name="system-setup"></a>
### System Requirements <a name="system-requirements"></a>

The Boston Dynamics Spot Python SDK works with most operating systems including:
* Linux Ubuntu 18.04 LTS
* Windows 10
* MacOS 10.14 (Mojave)

Windows WSL use is discouraged due to so many examples having graphics.

### Python Requirements <a name="python-requirements"></a>

Spot Python SDK works with Python 3.6 or Python 3.7 only. <u>Python 3.8 is not supported</u>.

Downloads and instructions for installing Python can be found at https://www.python.org/.

**IMPORTANT:** If you have multiple versions of Python installed then running ```python``` might reference an incorrect version (e.g. version 2.7).  For example, to run python 3 on Ubuntu 18.04 you would run ```python3``` and on Windows you could use the [Python launcher](https://docs.python.org/3/using/windows.html#launcher) and run ```py -3```. Our documentation uses ```python``` assuming that command launches a compatible version of Python.

Verify your python install is the correct version.  Open a command prompt or start your python IDE:
```shell
$ python --version
Python 3.6.8 
$
```

**Windows users:** There are two common methods for starting the Python interpreter on the command line. First, launch a terminal: Start > Command Prompt. At the command prompt, enter either:

* `python.exe`
* `py.exe`

The former will directly call the python.exe that is highest priority in the PATH environment variable. (Note you could also supply a full pathname c:\path\to\install\python.exe to directly call the executable).

The latter uses the Python launcher, which by default starts the most recent version of Python installed.  You can also optionally pass arguments to the launcher to control what version of python to launch:

* `py.exe -2` (the most recent Python 2) 
* `py.exe -3` (the most recent Python 3)
* `py.exe -3.6` (the most recent Python 3.6)

### Pip <a name="pip"></a>

Pip is the package installer for Python. Spot SDK and the third packages used by many of its programming examples use pip to install.

Check if pip is installed by requesting its version:

```shell
$ python -m pip --version
pip 19.2.1 from <path on your computer>
```

**Windows users:** py.exe -m pip --version.

If pip is not found, you'll need to install it. There are a few options:
  * pip comes preinstalled with all Python 3 versions >= 3.4 downloaded from python.org
  * Use the [`get-pip.py` installation script.](https://pip.pypa.io/en/stable/installing/) 
  * Use an OS-specific package manager (such as the python3-pip package on Ubuntu)

**Permission Denied:** If you do not use virtualenv (described below), when you install packages using pip, you may receive Permission Denied errors, if so, add the --user command to your pip command.

### Managing Multiple Python Environments <a name="managing-multiple-python-environments-with-virtualenv"></a>
**This section is optional, but recommended.**
Users with multiple python versions, anaconda, etc., are responsible for maintaining separation between those installs.  Common failures include using the wrong version of python, installing python packages to the wrong python, or using pip associated with the wrong python.  One way to improve the stability of your Spot code and your pre-existing python code is to keep them separate using virtual environments.  Here are some tips to working with [virtualenv](https://pypi.org/project/virtualenv).


* Install virtualenv.
* Create a virtualenv, being careful to point at the proper python executable.
* Activate the virtualenv.
* Install packages as needed, including Spot SDK.
* When finished with a session, deactivate.

```shell
$ python -m pip install virtualenv
$ python -m virtualenv my_spot_v2_0_env
$ source my_spot_v2_0_env/bin/activate
$ (install packages including Spot SDK, code, edit, execute, etc.)
$ deactivate
```

**Note:** Please ensure the virtualenv was created using the expected version of python.  If you see
```shell
$ python -m virtualenv my_spot_v2_0_env
Running virtualenv with interpreter /usr/bin/python2
...
```
Then the wrong interpreter is being used.  You can pass the interpreter as an additional argument, for example
```shell
python -m virtualenv -p /usr/bin/python3 my_spot_v2_0_env
```


**Windows users:** 
```shell
> py.exe -m pip install virtualenv
> py.exe -m virtualenv my_spot_v2_0_env
> .\my_spot_v2_0_env\Scripts\activate.bat
 (install packages including Spot SDK, code, edit, execute, etc.)
> .\my_spot_v2_0_env\Scripts\deactivate.bat
```


## Install Spot Python SDK <a name="install-spot-python-sdk"></a>
### Getting Spot Python SDK <a name="getting-spot-python-sdk"></a>

The Spot Python SDK is available at https://github.com/boston-dynamics/spot-sdk.  It is open source.

Users can either:
  * git clone https://github.com/boston-dynamics/spot-sdk.git (recommended)
  * Download a zipfile distribution:
    * Select green box "Clone or download" from the webpage.
    * Select "Download ZIP".
    * Unzip the file to your home directory.
    * Rename the top-level directory ```spot-sdk-master``` to ```spot-sdk```.
 
### Installing Spot Python SDK <a name="installing-spot-python-sdk"></a>

Now that your python and pip are properly configured and you have Spot SDK downloaded or cloned, it's time to install the Spot SDK Python Packages.

The following commands require a pathname to the SDK which we will call ```~/spot-sdk``` in the following examples.  But your pathname may be different depending on where you cloned/downloaded the files.  For example, **Windows users** may have downloaded these files to ```c:\Downloads\spot-sdk```.


```
$ cd ~/spot-sdk/prebuilt
$ python -m pip install *.whl
```

**Windows users:**
Instead of *.whl, please list all .whl files in the directory explicitly in the following order (api, core, client, mission), for example:

```
$ cd ~/spot-sdk/prebuilt
$ python -m pip install bosdyn_api-2.0.0-py2.py3-none-any.whl
$ python -m pip install bosdyn_core-2.0.0-py2.py3-none-any.whl
$ python -m pip install bosdyn_client-2.0.0-py2.py3-none-any.whl
$ python -m pip install bosdyn_mission-2.0.0-py2.py3-none-any.whl
```

**Version incompatibility:**
If you see a version incompatiblity error during pip install like: 

```
ERROR: bosdyn-core \<a version string> has requirement bosdyn-api==\<a version string>, but you'll have bosdyn-api 2.0.0 which is incompatible.
```

try uninstalling the bosdyn package and then reinstalling:

```
$ python -m pip uninstall bosdyn-api
$ python -m pip install bosdyn_api-2.0.0-py2.py3-none-any.whl
```
### Verify your Spot SDK installation <a name="verify-your-spot-sdk-installation"></a>
Make sure that the packages have been installed. 
```shell
$ python -m pip list --format=columns | grep bosdyn
bosdyn-api                    2.0.0
bosdyn-client                 2.0.0
bosdyn-core                   2.0.0
bosdyn-mission                2.0.0
```
If you don't see these 4 packages with your target version, something went wrong during installation.  Contact support@bostondynamics.com for help.

**Windows users:** Omit "grep" if not recognized.

Next, start your python interpreter:

```shell
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
If the libraries are **not** installed correctly, you may see an error like this one:

```python
>>> import bosdyn.client
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'bosdyn.client'
```

If that's the case, run `python -m pip list` again to make sure that the Boston Dynamics Python libraries are installed. 

If you can't import bosdyn.client without an error, you may have multiple Python installs on your computer, have installed bosdyn to one, and are now running the other.  Check the pathnames of your python executables, are they where you'd expect them to be?  If not, this is a potential sign that you may have multiple python installs.  Consider using virtual environments (see above).  If all else fails, contact support@bostondynamics.com for help.

## Verify you can talk to Spot using the SDK <a name="verify-you-can-talk-to-spot-using-the-sdk"></a>

To use the SDK, you need:
* a Spot Robot on the same version as your SDK,
* an Application Token ("app_token"),
* a user account on the robot

### Get a Spot Robot <a name="get-a-spot-robot"></a>
Contact sales@bostondynamics.com to get a Spot Robot!

### Get and Install an Application Token <a name="get-and-install-an-application-token"></a>
To get an Application Token, email support@bostondynamics.com with subject "Application Token Request". You should receive an email with an attached Application Token within one business day.

While you can technically put your token anywhere, Boston Dynamics recommends you create a `.bosdyn` directory in your home directory and then copy your token to that directory, renaming it to `~/.bosdyn/dev.app_token`.  Spot SDK will always look for your token at this location.  If you do not put the token there, you will need to explicitly tell the SDK where your token is, often as an argument to your python executable.

### Get a user account on the robot <a name="get-a-user-account-on-the-robot"></a>
If you just unboxed your Spot robot, you will find a sticker inside the battery cavity with wifi, admin, and username "user" credentials.  Please note however that Boston Dynamics recommends that you first have your designated robot administrator log onto robot as admin and change passwords to increase security.

NOTE: The following examples will assume username "user" and password "password".

### Ping Spot <a name="ping-spot"></a>

<ol>
<li> Power on Spot.  Wait for the fans to turn off (and maybe 10-20 seconds after that)
<li> Connect to Spot via wifi.
<li> Ping spot at 192.168.80.3
</ol>

```shell
$ ping 192.168.80.3
```

### Request Spot's ID from Spot <a name="request-spots-id-from-spot"></a>

On the command line, issue the following command to get your Spot robot's ID:

```
$ python -m bosdyn.client 192.168.80.3 id
beta-BD-90490007     02-19904-9903   beta29     spot (V3)
 Software: 2.0.0 (b11205d698e 2020-03-11 11:53:12)
  Installed: 2020-03-11 15:06:57
```

If this worked for you, SUCCESS!  You are now successfully communicating with Spot using the SDK!  Note that the output returned shows your Spot robot's unique serial number, its nickname and robot type (Boston Dynamics has multiple robots), and the version and install date of the software running on robot.

If you see the following: 

```
$ python -m bosdyn.client 192.168.80.3 id
Could not contact robot with hostname "192.168.80.3".
$
```

then the robot is not powered on or is unreachable.  Go back and try to get your ping to work.  You can also try the `-v` or `--verbose` to get more information to debug the issue.

If you see the following:

```
$ python -m bosdyn.client 192.168.80.3 id
Cannot retrieve app token from "None".
$
```

Then the SDK failed to find a valid app_token.  Follow the earlier quickstart instructions to get an app_token.  If you do have an Application Token, but it is not stored at the default location, you will need to specify the file path to it using the `--app-token` command line option.

### Run Hello Spot...let's see the robot move! <a name="run-hello-spot-lets-see-the-robot-move"></a>

OK, we now have our SDK installed properly and we are successfully able to command the robot to give us its id.  Let's now see the robot do something!

Change your working directory to the hello_spot example, do a pip install with requirements.txt as an argument so that any dependent packages are installed, and then run hello_spot:

**HELPFUL HINT: When working with any Spot SDK programming example, always use the
 associated requirements.txt to install dependent third party packages.**

```shell
$ cd ~/spot-sdk/python/examples/hello_spot # or wherever you installed Spot SDK
$ python -m pip install -r requirements.txt # will install dependent packages
$ python hello_spot.py --username user --password password 192.168.80.3
```

Hello_spot will fail because there is not an estop endpoint.

```shell
2020-03-30 15:26:36,283 - ERROR - Robot is estopped. Please use an external E-Stop client, such as the estop SDK example, to configure E-Stop.
```

If you saw the error:
```
$ python hello_spot.py --username usehername --password pazwierd 192.168.80.3
2020-04-03 15:10:28,189 - ERROR - Hello, Spot! threw an exception: bosdyn.api.GetAuthTokenResponse: Provided username/password is invalid.
```

then your username or password is incorrect, check your spelling and verify your credentials with your robot administrator.

### Run an independent E-Stop <a name="run-an-independent-e-stop"></a>
Change your working directory to the E-Stop example and run the nogui version:

```shell
$ cd ~/spot-sdk/python/examples/estop # or wherever you installed Spot SDK
$ python -m pip install -r requirements.txt # will install dependent packages
$ python estop_nogui.py --username user --password password 192.168.80.3
```

Now try to run the estop_gui version:
```shell
$ python estop_gui.py --username user --password password 192.168.80.3
```

You should now have a big red STOP button displayed on your screen, you're ready to go! (or stop in an emergency!!)

### Run Hello Spot (Take 2) <a name="run-hello-spot"></a>

OK, now we have an E-Stop. Leave it running, and open a second python window and again run hello_spot:

```shell
$ cd ~/spot-sdk/python/examples/hello_spot # or wherever you installed Spot SDK
$ python hello_spot.py --username user --password password 192.168.80.3
```

Your Spot robot should have powered up the motors, stood up, made a few poses, taken a picture, and sat down.  If it didn't, be sure to check that the `motor power enable` button on the back of Spot was properly turned on.

Try it again, and this time, push the E-Stop button and watch the robot do a "glide-stop".  Remember, E-Stop is your friend.

<b>Congratulations, you are now a full-fledged Spot Programming Example Operator!</b>  

<b>But, if you also want to be a full-fledged Spot Programmer</b>, you are going to want to understand a little deeper how Spot works.  Here are the next steps we recommend:

## Next Steps <a name="next-steps"></a>
<ul>
<li> Read our next section, 
<a href=./understanding_spot_programming.html>Understanding Spot Programming</a>  Highly recommended!
<li>  Take time to explore the programming examples which all launch in essentially the same manner as hello_spot.  
<ul>
<li>Try making simple modifications to the code.  NOTE: If you installed the SDK using a zipfile, be careful to understand what changes you've made, as users sometimes inject errors into the SDK code unintentionally.  Git users can simply use `git diff` to understand all changes they have made.
<li>Try out the <a href=../../python/examples/wasd/wasd.py>wasd programming example</a>. This is a more detailed example built on top of the Python API which lets you interactively control Spot using the keyboard on your development machine. It covers issuing commands in far more detail than this quick start.  And it's fun!
</ul>
<li> Read through the <a href=../protobuf/index.md>protocol buffer definitions</a> and the Spot SDK <a href=reference/index.html>python sourcecode</a> to understand even more.
</ul>
If you have any questions, please email support@bostondynamics.com.