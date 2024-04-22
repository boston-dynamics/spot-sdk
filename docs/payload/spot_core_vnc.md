<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Spot CORE VNC
VNC allows users to launch and interact with graphical applications on remote machines.

This document details how to set up TigerVNC on the Spot CORE. We will also use the GNOME desktop environment, port forwarding, and systemd .service files in the content below.

## Overview
Spot CORE now comes preconfigured with TigerVNC. The following sections outline the steps necessary for enabling the service before use. 

- [TigerVNC Server Enable](#tigervnc-server-enable)
- [TigerVNC Viewer](#tigervnc-viewer)
- [TigerVNC Server Installation](#tigervnc-server-installation) 
  - Not required if the Spot CORE is on any software version greater than 2.0.1.

## TigerVNC Server Enable
First, access a terminal on the Spot CORE. To do this, you can either log in to Cockpit at https://192.168.80.3:21443 and go to the Terminal tab, or you can connect through the command line:
```
ssh -p 20022 spot@192.168.80.3
```

### Create a VNC password
A default password "password" will be created for you. This password is used to access the VNC session from a client, after which you need to log in with the standard username and password for the Spot CORE.
You may also choose to create a new VNC password with the following command (a view-only password is not required):
```
vncpasswd
```

Enable and start the service on the desired port.
```
sudo systemctl enable vncserver@15100 # Enable service with the desired port.
sudo systemctl start vncserver@15100  # Start service.
systemctl status vncserver@15100 # Check the service is running.
```
In the example commands above, the vncserver port number used is 21000 (5900 + **15100**). See [start vncserver](#start-vncserver) for more information.

## TigerVNC Viewer
Perform the following steps on the PC to start the VNC connection.

### Install vncviewer

Install vncviewer for 64-bit Windows by downloading `vncviewer64-1.10.1.exe` from [here](https://github.com/TigerVNC/tigervnc/releases).

Install tigervnc-viewer on Ubuntu using apt:
```
sudo apt install tigervnc-viewer
```

### Start vncviewer 
We need to create a secure connection using an SSH tunnel first. The below command assumes the user is connected to Spot's access point. Don't forget to change the ip address or port number if required. To run this ssh session in the background without executing any commands, add ` -fN` arguments to the end of the command.
```
ssh -4 -p 20022 spot@192.168.80.3 -L 21000:127.0.0.1:21000
```

Start VNC Viewer and pass the IP address and port number.
```
vncviewer localhost:21000
```

After entering the password set using `vncpasswd` earlier, a GNOME desktop environment should now be available.

## TigerVNC Server Installation
This section is not required if the Spot CORE is on any software version greater than or equal to 2.3.0.

### Install software
Install software required for the TigerVNC server on the Spot CORE using apt:
```
sudo apt install tigervnc-standalone-server tigervnc-common tigervnc-xorg-extension tigervnc-viewer
```

If the user has not set up a VNC password, please see the earlier instructions on how to [create a vnc password](#create-a-vnc-password).

### Prepare vncserver
To configure the GNOME desktop, create a xstartup file in `~/.vnc/xstartup` and add the following contents.
```
#!/bin/sh
[ -x /etc/vnc/xstartup ] && exec /etc/vnc/xstartup
[ -r $HOME/.Xresources ] && xrdb $HOME/.Xresources
vncconfig -iconic &
dbus-launch --exit-with-session gnome-session &
```

To enable permissions for remote sessions (such as VNC) to edit certain system settings, create the following files in `/etc/polkit-1/localauthority/50-local.d/`:

*10-network-manager.pkla*
```
[Let user spot modify system settings for network]
Identity=unix-user:spot
Action=org.freedesktop.NetworkManager.*
ResultAny=auth_admin_keep
ResultInactive=no
ResultActive=yes

```

*46-user-admin.pkla*
```
[control center administration]
Identity=unix-user:*
Action=org.gnome.controlcenter.*
ResultAny=auth_admin_keep
ResultInactive=no
ResultActive=yes
```

### Start vncserver

TigerVNC listens to ports 5900+. The default port is 5901 (5900 + **1**), which can be started using the following command.
```
vncserver :1
```

In order to specify a different port, such as 21000, run vncserver with the number equal to 21000 - 5900 = **15100**.
```
vncserver :15100
```

Use `-list` to see the previously started vnc servers.
```
vncserver -list
```

Use the below command to stop the previously started vnc servers.
```
vncserver -kill :1
vncserver -kill :15100
```

### Enable vncserver on boot
In order for vncserver to automatically run on Spot CORE whenever Spot is turned on, use a systemd .service file. Create a service file named `vncserver@.service` and add the following contents. This file can take a port number as an argument.

```
[Unit]
Description=TigerVNC server
After=network.target

[Service]
Type=simple
RemainAfterExit=yes
SuccessExitStatus=0

PIDFile=/home/spot/.vnc/%H:%i.pid
ExecStartPre=/bin/su -l spot -c "/usr/bin/vncserver -kill :%i > /dev/null"
ExecStart=/bin/su -l spot -c "/usr/bin/vncserver :%i -localhost no"
ExecStop=/bin/su -l spot -c "/usr/bin/vncserver -kill :%i"

[Install]
WantedBy=multi-user.target
```

Copy the file to /etc/systemd/system/ and start the service. Change the port number as desired. 
```
sudo cp vncserver@.service /etc/systemd/system/ 
sudo systemctl daemon-reload # Reloads all systemd services.
```

## Useful TigerVNC Resources
- [TigerVNC tutorial (primary resource used to create this document).](https://www.tecmint.com/install-and-configure-vnc-server-on-ubuntu/)
- [How to handle port forwarding with TigerVNC.](http://danielhnyk.cz/setting-vnc-remote-access-port-forwarding/)
- [How to use systemd.service files.](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [Additional TigerVNC tutorial.](https://www.cyberciti.biz/faq/install-and-configure-tigervnc-server-on-ubuntu-18-04/)
