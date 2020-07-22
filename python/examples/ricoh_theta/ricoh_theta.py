# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""This script sends https requests to a Richo Theta."""

# Ricoh Theta API Documentation
# https://api.ricoh/products/theta-api/

import os
import json
import shutil
import webbrowser
import time
import requests
from requests.auth import HTTPDigestAuth

class Theta:
    """Class for interacting with a Ricoh Theta camera"""

    def __init__(self, theta_ssid=None, theta_pw=None, client_mode=True,
                 static_ip="192.168.80.110", subnet_mask="255.255.255.0", default_gateway="192.168.80.1"):
        """Creates object instance for ricoh theta.

        Args:
            theta_ssid = "your camera's ssid"
            theta_pw = "your camera's password" (if None specified, the code will use the default)
            client_mode = True/False, use client or direct mode
            static_ip = "theta static ip address for client mode"
            subnet_mask = "subnet mask"
            default_gateway = "default gateway"
        """
        # Camera Parameters:
        # Adjust the below default parameters for your specific use case.
        self.theta_ssid = theta_ssid
        # Typical default password for the ricoh theta is the SSID without the first 7 letters
        self.theta_pw = theta_pw or self.theta_ssid[7:] # use custom password or default
        self.client_ip = static_ip
        # Edit additional network settings here.
        self.client_subnet = subnet_mask
        self.client_default = default_gateway

        # Additional Setup
        self.setMode(client_mode)
        self.num_images_taken = 0 # keeps track of number of images taken since last download
        self.download_paths = [] # stores download paths used during mission
        self.cmd_id = "" # shared variable for use once image processing is complete

        # Use showState to check network http connection and show initial state of camera.
        self.showState()

    def setMode(self, client_mode=True):
        """Sets object instance to use client vs direct mode network settings."""
        if client_mode:
            self.baseip = self.client_ip
        else: # default settings for direct mode
            self.baseip = "192.168.1.1"
        self.baseurl = "http://" + self.baseip

    def printj(self, res, message=None):
        """Pretty-Print JSON in Terminal."""
        if message is not None:
            print(message)
        pjson = json.loads(res.text)
        print(json.dumps(pjson, indent=2))

    def postf(self, ext, info):
        """Function to create an HTTP POST Request."""
        print("Request Contents:")
        print(json.dumps(info, indent=2))
        return requests.post(self.baseurl + ext, json=info,
                             timeout=5, auth=(HTTPDigestAuth(self.theta_ssid, self.theta_pw)))

    def sleepMode(self, enabled=None, delay=180):
        """Alter sleep mode."""
        command = "/osc/commands/execute"
        if not enabled:
            delay = 65535
        info = {
            # Enable sleep mode, 180s, 300s, 420s, 600s
            "name": "camera.setOptions",
            "parameters": {
                "options": {
                    "sleepDelay": delay
                }
            }
        }
        res = self.postf(command, info)
        self.printj(res, "Response to sleepMode:")

    def showState(self):
        """Takes a Photo"""
        command = "/osc/state"
        print("All commands to: " + self.baseurl)
        res = self.postf(command, info="")
        self.printj(res, "Response to state:")

    def takePicture(self):
        """Takes a Photo"""
        if not self.waitUntilImageIsProcessed():
            return
        command = "/osc/commands/execute"
        info = {
            "name": "camera.takePicture"
        }
        res = self.postf(command, info)
        self.num_images_taken += 1
        self.printj(res, "Response to takePicture:")
        json_res = res.json()
        self.cmd_id = json_res["id"]

    def listFiles(self, num):
        """List specific number of files on theta from most recent image."""
        command = "/osc/commands/execute"
        info = {
            "name": "camera.listFiles",
            "parameters": {
                "fileType": "all",
                "entryCount": num,
                "maxThumbSize": 0
            }
        }
        res = self.postf(command, info)
        self.printj(res, "Response to listFiles:")
        return res

    def previewLastImage(self):
        """Preview last image taken in a local web browser."""
        res = self.listFiles(1)
        json_res = res.json()
        image_url = json_res["results"]["entries"][0]["fileUrl"]
        webbrowser.open(image_url)

    def createDownloadPath(self, parent_dir):
        """Create directory for downloaded images."""
        timestr = time.strftime("%Y%m%d-%H%M%S")
        path = os.path.join(parent_dir, timestr, '')
        os.mkdir(path)
        self.download_paths.append(path)
        return path

    def downloadImage(self, image_url, directory):
        """Download image as binary amd write to file as JPG."""
        res = requests.get(image_url, stream=True, auth=(HTTPDigestAuth(self.theta_ssid, self.theta_pw)))
        filename = os.path.basename(image_url)
        saveto = os.path.join(directory, filename)
        local_file = open(saveto, 'wb')
        res.raw.decode_content = True
        shutil.copyfileobj(res.raw, local_file)

        # image information
        print("- Image name: " + filename)
        if directory == "":
            print("- file saved in the same location as the python script")
        else:
            print("- file saved here: " + directory)
        return saveto

    def downloadLastImage(self, directory=""):
        """Downloads last picture taken using absolute url."""
        # directory = desired directory to store file

        # ensure image processing is complete
        if not self.waitUntilImageIsProcessed():
            return False

        # Grab latest image url
        res = self.listFiles(1)
        json_res = res.json()
        image_url = json_res["results"]["entries"][0]["fileUrl"]
        print("Downloading image from: " + image_url)

        # Download desired image
        saveto = self.downloadImage(image_url, directory)
        return saveto

    def lastImageIsProcessed(self):
        """Check if image is processed."""
        command = "/osc/commands/status"
        info = {
            "id": self.cmd_id
        }
        res = self.postf(command, info)
        json_res = res.json()
        state = json_res["state"] # check if inProgress or done
        return state == "done"

    def waitUntilImageIsProcessed(self):
        """Checks image processing time on Ricoh Theta."""
        waittime = 10 # seconds, total wait time before quitting command
        check_status_timer = 0.25 # seconds, time between each status check
        timeout = time.time() + waittime
        if self.num_images_taken > 0:
            print(str(waittime) + " second timeout timer started for image processing:")
            while True:
                print("- time remaining: " + str(round(timeout - time.time(), 2)) +
                      "s, check status again in " + str(check_status_timer) + "s")
                if self.lastImageIsProcessed():
                    return True
                if time.time() > timeout:
                    print("Not ready. Please try again.")
                    return False
                time.sleep(check_status_timer)
        else:
            return True

    def downloadMissionImages(self, directory=""):
        """Downloads all mission images"""
        # directory = desired directory to store files
        if directory != "":
            directory = self.createDownloadPath(directory)

        # Check number of image files taken during mission.
        if self.num_images_taken < 1:
            print("No images to download.")
            return False

        # Ensure image processing is complete.
        if not self.waitUntilImageIsProcessed():
            return False

        # Grab list of files from camera.
        res = self.listFiles(self.num_images_taken)
        json_res = res.json()

        print("Downloading " + str(self.num_images_taken) + " Images:")
        # Downloads each image recorded during mission.
        for i in range(self.num_images_taken):
            image_url = json_res["results"]["entries"][i]["fileUrl"]
            self.downloadImage(image_url, directory)
        self.num_images_taken = 0 # reset counter
        print("All mission images since last mission download succesfully transferred.")
        return True

    def connectToAP(self, ap_ssid=None, ap_sec="WPA/WPA2 PSK", ap_pw=None):
        """Sets Richo Theta to Client Mode and Connects to Access Point"""
        command = "/osc/commands/execute"
        info = {
            "name": "camera._setAccessPoint",
            "parameters": {
                "ssid": ap_ssid,
                "security": ap_sec,
                "password": ap_pw,
                "connectionPriority": 1,
                "ipAddressAllocation": "static",
                "ipAddress": self.client_ip, # edit in constructor
                "subnetMask": self.client_subnet, # edit in constructor
                "defaultGateway": self.client_default, # edit in constructor
            }
        }
        res = self.postf(command, info)
        self.printj(res, "Response to connectToAP:")
        print("New static ip: " + self.client_ip)
        return res
