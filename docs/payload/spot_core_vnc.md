<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Spot CORE VNC
VNC allows users to launch and interact with graphical applications on remote machines.

This document details how to setup TigerVNC on the Spot CORE. We will also use the XFCE desktop environment, port forwarding, and systemd .service files in the content below.

## Overview
Spot CORE now comes preconfigured with TigerVNC. The following sections outline the steps necessary for enabling the service before use. 

- [TigerVNC Server Enable](#tigervnc-server-enable)
- [TigerVNC Viewer](#tigervnc-viewer)
- [TigerVNC Server Installation](#tigervnc-server-installation) 
  - Not required if the Spot CORE is on any software version greater than 2.0.1.

## TigerVNC Server Enable
SSH into the Spot CORE. Wirelessly connect a PC to the Spot Robot and open a Command Line Interface (CLI) to run the following.

```
ssh -p 20022 spot@192.168.80.3
```

### Create a VNC password
Create a VNC password. A view-only password is not required.
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

Install vncviewer for 64-bit Windows by downloading `vncviewer64-1.10.1.exe` from [https://bintray.com/tigervnc/stable/tigervnc/](https://bintray.com/tigervnc/stable/tigervnc/).

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

An XFCE desktop environment should now be available.

## TigerVNC Server Installation
This section is not required if the Spot CORE is on any software version greater than 2.0.1.

### Install software
Install software required for the TigerVNC server on the Spot CORE using apt:
```
sudo apt install xfce4
sudo apt install tigervnc-standalone-server tigervnc-common tigervnc-xorg-extension tigervnc-viewer
```

If the user has not setup a VNC password, please see the earlier instructions on how to [create a vnc password](#create-a-vnc-password).

### Prepare vncserver
To configure the XFCE desktop, create a xstartup file in `~/.vnc/xstartup` and add the following contents.
```
#!/bin/sh

# Uncomment the following two lines for normal desktop:
# unset SESSION_MANAGER
# exec /etc/X11/xinit/xinitrc

[ -x /etc/vnc/xstartup ] && exec /etc/vnc/xstartup
[ -r $HOME/.Xresources ] && xrdb $HOME/.Xresources
xsetroot -solid grey
vncconfig -iconic &
x-terminal-emulator -geometry 80x24+10+10 -ls -title "$VNCDESKTOP Desktop" &
x-window-manager &

exec /usr/bin/startxfce4 &
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
In order for vncserver to automatically run on Spot CORE whenever Spot is turned on, use a systemd .service file. Create a servive file named `vncserver@.service` and add the following contents. This file can take a port number as an argument.

```
[Unit]
Description=Start TigerVNC server at startup
After=syslog.target network.target

[Service]
Type=forking
User=spot
Group=spot
WorkingDirectory=/home/spot

PIDFile=/home/spot/.vnc/%H:%i.pid
ExecStartPre=-/usr/bin/vncserver -kill :%i > /dev/null 2>&1
ExecStart=/usr/bin/vncserver -depth 24 -localhost no :%i
ExecStop=/usr/bin/vncserver -kill :%i

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
