<!--
Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Ricoh Theta
This document will explain step-by-step how to setup a Ricoh Theta V or Z1 for an Autowalk Mission using the Remote Mission Service on the Spot CORE. This document assumes you are using the default settings of a Ricoh Theta camera and mounted/registered Spot CORE.

## Required Items
- Spot CORE
- USB WiFi dongle
- Ricoh Theta V or Z1
- Personal Computer

## Installation Steps
The following installation steps assume you:
- have read the ricoh theta online manual and understand client mode operation
- have the latest spot-sdk downloaded & installed on your PC
- familiar with SSH and using a Command Line Interface (CLI)

### Install Packages on PC
Navigate via the CLI on your PC to the ricoh_theta directory and review the requirements.txt document for this example before continuing. Several python packages will need to be installed along with the standard SDK:

```
pip install -r requirements.txt
```

### Test Ricoh Theta

A `test_driver.py` script has been included which will show the state of the camera and take a picture. Before running this script, wirelessly connect your personal computer to the ricoh theta camera and adjust the theta_ssid for your camera. The script is currently configured for direct mode ip settings for running on your PC. Edit the python script as desired.

```
python test_driver.py
```

### Connect Ricoh Theta to Spot
Perform the following steps on your PC to setup ricoh theta client mode.

1. Enable wireless connection on the ricoh theta and connect your PC to the ricoh theta via WiFi.
1. Run `ricoh_client_mode.py` on your PC via the CLI. Replace the capitilized letters in the command below with your Ricoh Theta SSID, Spot's WiFi SSID, and Spot's WiFi password.
    ```
    python ricoh_client_mode.py --theta-ssid THETAYL00196843 --wifi-ssid WIFI_SSID --wifi-password WIFI_PASSWORD
    ```
    If all goes well, you should see a positive response that shows the new static ip:
    ```
    Response Below:
    {
      "name": "camera._setAccessPoint",
      "state": "done"
    }
    New static ip: 192.168.80.110
    ```
    The above script will specify the access point settings for ricoh theta client mode and a static ip address. 
    
    For Developers: As an _additional_ option, you can configure the ip settings by editing the `__init__` function directly in `ricoh_theta.py` or when creating the Theta() object. These settings are featured below and have been tested on the Spot CORE.
    ```python
    def __init__(..., static_ip="192.168.80.110", subnet_mask="255.255.255.0", default_gateway="192.168.80.1"):
    ```
1. Enable client mode on your ricoh theta (press the wireless button again) and confirm connection with Spot's access point (the wireless indicator should stop blinking and become solid in client mode). Sometimes a ricoh theta power cycle is required.

### Edit Spot CORE Network Settings
These steps are required if you intend to connect your Spot CORE to the internet via a WiFi dongle and communicate from the Spot CORE to a device connected with the robot's access point. 

1. Ensure a WiFi dongle is connected to the Spot CORE.
1. ssh into the Spot CORE using your PC's CLI
    ```
    ssh -p 20022 spot@ROBOT_IP_ADDRESS
    ```

1. Follow [these instructions](https://docs.ubuntu.com/core/en/stacks/network/network-manager/docs/configure-wifi-connections) to configure your WiFi adapter from the terminal. A condensed version is below. Connecting to a wireless access point can also be achieved using the standard desktop environment with a montior, keyboard, and mouse plugged into the Spot CORE.
    ```
    nmcli d
    nmcli r wifi on
    nmcli d wifi list
    ```
    From the listed wireless access points, replace the captilized letters of the command below with your desired wifi network (that has internet access) and password.
    ```
    sudo nmcli d wifi connect MY_WIFI password MY_PASSWORD
    ```

1. Edit the interface file. Run:
    ```
    sudo nano /etc/network/interfaces
    ```
    Comment out or remove this line: "gateway 192.168.50.3" (which will enable internet access after reboot); and add a route pointing to Spot's access point: "up ip route add 192.168.80.0/24 via 192.168.50.3"

    The network interface file should now look similar to this:
    ```
    # Default payload network settings
    # LOOPBACK
    auto lo
    iface lo inet loopback

    auto enp2s0
    iface enp2s0 inet static
        address 192.168.50.5/24
        # gateway 192.168.50.3
        up ip route add 192.168.80.0/24 via 192.168.50.3

    auto eno1
    iface eno1 inet static
        address 192.168.1.9/24

    ```
1. Reboot the Spot CORE. This will close the ssh connection.
    ```
    sudo reboot
    ```

1. After 30 seconds, check Spot CORE network settings:

    ssh back into the Spot CORE
    ```
    ssh -p 20022 spot@ROBOT_IP_ADDRESS
    ```

    Ping an external address to confirm internet connection. You should see an ip address in paraentheses following google. Use Ctrl + C to exit.
    ```
    ping google.com

    PING google.com (172.217.6.238) 56(84) bytes of data.
    64 bytes from lga25s55-in-f238.1e100.net (172.217.6.238): icmp_seq=1 ttl=56 time=20.8 ms
    64 bytes from lga25s55-in-f238.1e100.net (172.217.6.238): icmp_seq=2 ttl=56 time=23.5 ms
    64 bytes from lga25s55-in-f238.1e100.net (172.217.6.238): icmp_seq=3 ttl=56 time=17.6 ms
    ...
    ```

    Enable client mode on your ricoh theta and ping the static ip once connected. You should see repeated responses. Use Ctrl + C to exit.
    ```
    ping 192.168.80.110
    ```

    Lastly, close ssh connection. Ctrl + D

### Edit Remote Mission Service
The `remote_mission_service_ricoh.py` script uses a couple of global variables near the top of the script that you will need to edit for your specific use case. The current settings are featured below:

```python
DEFAULT_PATH = '/home/spot/Pictures/'
GCP_BUCKET_NAME = 'c-imagedemo'
AWS_BUCKET_NAME = 'aws-imagedemo'
YOUR_THETA_SSID = 'THETAYL00196843'
```

### Install Packages on Spot CORE
The changes made to these files on your local PC will need to be mirrored on the Spot CORE. In your PC's CLI, you can use the below scp command to copy the files from your PC's local SDK ricoh_client directory into the `/home/spot/` folder on your Spot CORE.
```
scp -r -P 20022 ricoh_theta/ spot@ROBOT_IP_ADDRESS:
```

You will also need to copy over the cloud_upload example.
```
scp -r -P 20022 cloud_upload/ spot@ROBOT_IP_ADDRESS:
```

Don't forget to install the python packages on the Spot CORE. SSH into the Spot CORE, navigate via the terminal on the Spot CORE to the ricoh_theta directory, and install the requirements.txt document for this example before continuing. Like on the PC, several python packages will need to be installed along with the standard SDK:

```
pip3 install -r requirements.txt
```

The assumed installation structure on the Spot CORE is featured below.

```
/home/spot/
    ricoh_theta/
        README.md  
        remote_mission_service_ricoh.py 
        requirements.txt 
        ricoh_client_mode.py
        ricoh.service
        ricoh_theta.py
        run.sh 
        test_driver.py
    cloud_upload/
        cloud_upload.py
        README.md  
        requirements.txt
```

Because of the above structure, an adjustment to PYTHONPATH for cloud_upload import used in `remote_mission_service_ricoh.py` will likely be required.

```
export PYTHONPATH=/home/spot
```
Add the above line to your .bashrc file to make permanent. If a PYTHONPATH has already been set, add to it instead and use: 
```
PYTHONPATH=$PYTHONPATH:/home/spot
```

## Run Remote Mission Service

In order to use a ricoh theta with an autowalk mission, a remote mission service script must be running. Use `remote_mission_service_ricoh.py` to test ricoh_theta callbacks.

```
python3 remote_mission_service_ricoh.py 192.168.50.3 --payload-token --directory-host 192.168.50.3 --my-host 192.168.50.5 --theta-client
```

Create an autowalk mission and add callbacks when desired (these actions will execute during mission replay, not during record time). Several options are below:

1. "take theta image"
    - Sends a command to the ricoh theta to take a picture.
    - Note: image processing takes around 3 seconds to complete.
1. "download theta images"
    - Downloads all the ricoh theta images taken during that mission (or since the last download) to the Spot CORE.
    - Find the images in the DEFAULT_PATH (/home/spot/Pictures/)
1. "upload to gcp"
    - Uploads all images taken during the mission to a Google Cloud Platform (GCP) bucket.
    - Review the cloud_upload [README](../cloud_upload/README.md) for more details. Additional configuration is required.
1. "upload to aws"
    - Uploads all images taken during the mission to an Amazon Web Services (AWS) S3 bucket.
    - Review the cloud_upload [README](../cloud_upload/README.md) for more details. Additional configuration is required.


## Run Remote Mission Service on Boot

Autoboot sample files `ricoh.service` and `run.sh` may also need to be updated depending on the location of the files on the Spot CORE. For instance, the default Spot CORE PYTHONPATH is currently set to /home/spot/ in the ricoh.service file in order to import from the cloud_upload directory. If you intend to "upload to gcp", the systemd `ricoh.service` file will need an additional argument under `[Service]` for the GOOGLE_APPLICATION_CREDENTIALS environmental variable.

```
Environment="GOOGLE_APPLICATION_CREDENTIALS=<path-to-file>/<filename>.json"
```

Perform the following commands in order to make `run.sh` executable and copy `ricoh.service` to the correct directory.
```
chmod +x ricoh_theta/run.sh
sudo cp ricoh_theta/ricoh.service /lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable ricoh.service
sudo systemctl start ricoh.service
```

Use the below systemctl command to check the status of the service. It should be: `active (running)`.

```
systemctl status ricoh.service
```

Journalctl is also a useful tool for debugging.

```
journalctl -efu ricoh.service
```

Here is an external sparkfun [link](https://learn.sparkfun.com/tutorials/how-to-run-a-raspberry-pi-program-on-startup/all#method-3-systemd) to a systemd example on how to run a python script on linux boot.

## Developer Comments
To learn more about the remote mission service, review the remote_mission_service [README](../remote_mission_service/README.md) for details. For the Ricoh Theta integration, the `remote_mission_service_ricoh.py` script has several key edits to a couple functions. Review the comments above each function that have specific "Ricoh Theta Integration Notes" to learn more.

For Ricoh Theta API Documentation, visit [https://api.ricoh/products/theta-api/](https://api.ricoh/products/theta-api/)