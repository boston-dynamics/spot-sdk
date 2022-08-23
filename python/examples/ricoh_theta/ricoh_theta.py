# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""This script sends https requests to a Ricoh Theta."""

# Ricoh Theta API Documentation
# https://api.ricoh/products/theta-api/

import json
import os
import shutil
import time
import webbrowser

import requests
from requests.auth import HTTPDigestAuth


class Theta:
    """Class for interacting with a Ricoh Theta camera"""

    def __init__(self, theta_ssid=None, theta_pw=None, client_mode=True, static_ip="192.168.80.110",
                 subnet_mask="255.255.255.0", default_gateway="192.168.80.1",
                 show_state_at_init=True):
        """Creates object instance for ricoh theta.

        Args:
            theta_ssid(string): your camera's ssid
            theta_pw(string): your camera's password (if None specified, the code will use the default)
            client_mode(bool): True/False, use client or direct mode
            static_ip(string): theta static ip address for client mode
            subnet_mask(string): subnet mask
            default_gateway(string): default gateway
            show_state_at_init(bool): Make a HTTP request to show initial camera state at object creation time.
        """
        # Camera Parameters:
        # Adjust the below default parameters for your specific use case.
        self.theta_ssid = theta_ssid
        # Typical default password for the ricoh theta is the SSID without the first 7 letters
        self.theta_pw = theta_pw or self.theta_ssid[7:]  # use custom password or default
        self.client_ip = static_ip
        # Edit additional network settings here.
        self.client_subnet = subnet_mask
        self.client_default = default_gateway

        # Additional Setup
        self.setMode(client_mode)
        self.num_images_taken = 0  # keeps track of number of images taken since last download
        self.download_paths = []  # stores download paths used during mission
        self.cmd_id = ""  # shared variable for use once image processing is complete

        if show_state_at_init:
            # Use showState to check network http connection and show initial state of camera.
            self.showState()

    def setMode(self, client_mode=True):
        """Sets object instance to use client vs direct mode network settings."""
        if client_mode:
            self.baseip = self.client_ip
        else:  # default settings for direct mode
            self.baseip = "192.168.1.1"
        self.baseurl = "http://" + self.baseip

    def printj(self, res, message=None):
        """Pretty-Print JSON in Terminal."""
        if message is not None:
            print(message)
        pjson = json.loads(res.text)
        print(json.dumps(pjson, indent=2))

    def postf(self, ext, info, print_to_screen=True, stream=False):
        """Function to create an HTTP POST Request."""
        if print_to_screen:
            print("Request Contents:")
            print(json.dumps(info, indent=2))
        return requests.post(self.baseurl + ext, json=info, timeout=5,
                             auth=(HTTPDigestAuth(self.theta_ssid, self.theta_pw)), stream=stream)

    def sleepMode(self, enabled=None, delay=180, print_to_screen=True):
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
        res = self.postf(command, info, print_to_screen)
        if print_to_screen:
            self.printj(res, "Response to sleepMode:")

    def showState(self, print_to_screen=True):
        """Prints the current camera state to the screen."""
        command = "/osc/state"
        res = self.postf(command, info="", print_to_screen=print_to_screen)
        if print_to_screen:
            print("All commands to: " + self.baseurl)
            self.printj(res, "Response to state:")
        return res

    def takePicture(self, print_to_screen=True):
        """Takes a Photo"""
        if not self.waitUntilImageIsProcessed(print_to_screen):
            return
        command = "/osc/commands/execute"
        info = {"name": "camera.takePicture"}
        res = self.postf(command, info, print_to_screen)
        self.num_images_taken += 1
        if print_to_screen:
            self.printj(res, "Response to takePicture:")
        json_res = res.json()
        if "error" in json_res:
            print("takePicture failed due to: " + json_res["error"]["message"])
            return
        self.cmd_id = json_res["id"]

    def listFiles(self, num, print_to_screen=True):
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
        res = self.postf(command, info, print_to_screen)
        if print_to_screen:
            self.printj(res, "Response to listFiles:")
        return res

    def previewLastImage(self, print_to_screen=True):
        """Preview last image taken in a local web browser."""
        res = self.listFiles(1, print_to_screen)
        json_res = res.json()
        image_url = json_res["results"]["entries"][0]["fileUrl"]
        webbrowser.open(image_url)

    def downloadImage(self, image_url, directory, print_to_screen=True):
        """Download image as binary and write to file as JPG."""
        res = requests.get(image_url, stream=True,
                           auth=(HTTPDigestAuth(self.theta_ssid, self.theta_pw)))
        filename = os.path.basename(image_url)
        saveto = os.path.join(directory, filename)
        local_file = open(saveto, 'wb')
        res.raw.decode_content = True
        shutil.copyfileobj(res.raw, local_file)

        # image information
        if print_to_screen:
            print("- Image name: " + filename)
            if directory == "":
                print("- file saved in the same location as the python script")
            else:
                print("- file saved here: " + directory)
        return saveto

    def downloadLastImage(self, directory="", print_to_screen=True):
        """Downloads last picture taken using absolute url."""
        # directory = desired directory to store file

        # ensure image processing is complete
        if not self.waitUntilImageIsProcessed(print_to_screen):
            return False

        # Grab latest image url
        res = self.listFiles(1, print_to_screen)
        json_res = res.json()
        image_url = json_res["results"]["entries"][0]["fileUrl"]
        if print_to_screen:
            print("Downloading image from: " + image_url)

        # Download desired image
        saveto = self.downloadImage(image_url, directory, print_to_screen)
        return saveto

    def getLastImage(self, wait_for_latest=False, print_to_screen=True):
        """Downloads the last picture taken using the absolute url to local memory.

        Returns:
            Returns the complete image entry's json data in addition to the HTTP bytes result.
        """
        if wait_for_latest:
            # ensure image processing is complete for the last picture to be taken.
            if not self.waitUntilImageIsProcessed(print_to_screen):
                return None, None

        res = self.listFiles(1, print_to_screen)
        json_file_res = res.json()
        if not ("results" in json_file_res and "entries" in json_file_res["results"]):
            return None, None
        main_info = json_file_res["results"]["entries"][0]
        image_url = main_info["fileUrl"]
        img_res = requests.get(image_url, stream=True,
                               auth=(HTTPDigestAuth(self.theta_ssid, self.theta_pw)))
        return main_info, img_res

    def lastImageIsProcessed(self, print_to_screen=True):
        """Check if the last captured image is processed."""
        command = "/osc/commands/status"
        info = {"id": self.cmd_id}
        res = self.postf(command, info, print_to_screen)
        json_res = res.json()
        state = json_res["state"]  # check if inProgress or done
        return state == "done"

    def waitUntilImageIsProcessed(self, print_to_screen=True):
        """Checks image processing time on Ricoh Theta."""
        waittime = 10  # seconds, total wait time before quitting command
        check_status_timer = 0.25  # seconds, time between each status check
        timeout = time.time() + waittime
        if self.num_images_taken > 0:
            if print_to_screen:
                print(str(waittime) + " second timeout timer started for image processing:")
            while True:
                if print_to_screen:
                    print("- time remaining: " + str(round(timeout - time.time(), 2)) +
                          "s, check status again in " + str(check_status_timer) + "s")
                if self.lastImageIsProcessed(print_to_screen):
                    return True
                if time.time() > timeout:
                    if print_to_screen:
                        print("Not ready. Please try again.")
                    return False
                time.sleep(check_status_timer)
        else:
            return True

    def connectToAP(self, ap_ssid=None, ap_sec="WPA/WPA2 PSK", ap_pw=None, print_to_screen=True):
        """Sets Ricoh Theta to Client Mode and Connects to Access Point"""
        command = "/osc/commands/execute"
        info = {
            "name": "camera._setAccessPoint",
            "parameters": {
                "ssid": ap_ssid,
                "security": ap_sec,
                "password": ap_pw,
                "connectionPriority": 1,
                "ipAddressAllocation": "static",
                "ipAddress": self.client_ip,  # edit in constructor
                "subnetMask": self.client_subnet,  # edit in constructor
                "defaultGateway": self.client_default,  # edit in constructor
            }
        }
        res = self.postf(command, info, print_to_screen)
        if print_to_screen:
            self.printj(res, "Response to connectToAP:")
            print("New static ip: " + self.client_ip)
        return res

    def getCaptureParameters(self, print_to_screen=True):
        command = "/osc/commands/execute"
        info = {
            "name": "camera.getOptions",
            "parameters": {
                "optionNames": ["exposureDelay", "iso"]
            }
        }
        result = self.postf(command, info, print_to_screen)
        json_res = result.json()
        if not ("results" in json_res and "options" in json_res["results"]):
            # Unable to find the results from the HTTP request.
            return (None, None)
        res = json_res["results"]["options"]
        gain = None
        exposure = None
        if "iso" in res:
            gain = res["iso"]
        if "exposureDelay" in res:
            # According to the Ricoh Theta API documentation, this is defined in seconds.
            exposure = res["exposureDelay"]
        gain_exposure_tuple = (gain, exposure)
        if print_to_screen:
            print("Camera gain: " + str(gain_exposure_tuple[0]) + " and exposure time [seconds]: " +
                  str(gain_exposure_tuple[1]))
        return gain_exposure_tuple

    def getFileFormat(self, print_to_screen=True):
        command = "/osc/commands/execute"
        info = {"name": "camera.getOptions", "parameters": {"optionNames": ["fileFormat"]}}
        result = self.postf(command, info, print_to_screen)
        json_res = result.json()
        if not ("results" in json_res and "options" in json_res["results"]):
            # Unable to find the results from the HTTP request.
            return None
        format_res = json_res["results"]["options"]["fileFormat"]
        if print_to_screen:
            print("The image format is: ", format_res)
        return format_res

    def yieldLivePreview(self, print_to_screen=True):
        """
        Returns a generator for the live preview video stream as a series of jpegs (yielding the raw bytes).
        The capture mode must be 'image'.
        Credit for jpeg decoding:
        https://stackoverflow.com/questions/21702477/how-to-parse-mjpeg-http-stream-from-ip-camera
        Reference:
        https://developers.theta360.com/en/docs/v2/api_reference/commands/camera._get_live_preview.html
        """
        command = '/osc/commands/execute'
        info = {"name": "camera.getLivePreview"}
        response = self.postf(command, info, print_to_screen, stream=True)
        if print_to_screen:
            print("Creating the live preview had HTTP response: %s" % response)

        if response.status_code == 200:
            bytes_block = b''
            # Iterates over the response reading the bytes buffer in chunks of 16384 bytes.
            for block in response.iter_content(16384):
                bytes_block += block

                # Search the current block of bytes for the jpg start and end. These are common
                # jpeg frame start/stop indicators for mjpeg.
                a = bytes_block.find(b'\xff\xd8')
                b = bytes_block.find(b'\xff\xd9')

                # Found a jpg file in the bytes buffer!
                if a != -1 and b != -1:
                    jpg = bytes_block[a:b + 2]
                    yield jpg

                    # Reset the buffer to point to the next set of bytes. NOTE:we start after "b+2" so that we don't
                    # include the previous jpg's ending byte indicator (2 bytes long) in the updated buffer.
                    bytes_block = bytes_block[b + 2:]

    def getLivePreviewAndWriteToDisk(self, file_name_prefix="livePreview", time_limit_seconds=10,
                                     print_to_screen=True):
        """
        Save the live preview video stream to disk as a series of jpegs.
        The capture mode must be 'image'.
        """
        start_time = time.time()
        for i, jpg in enumerate(self.yieldLivePreview(print_to_screen)):
            frameFileName = "%s.%04d.jpg" % (file_name_prefix, i)
            with open(frameFileName, 'wb') as handle:
                handle.write(jpg)
            curr_time = time.time()
            if (curr_time - start_time) > time_limit_seconds:
                # End iterating and saving to disk after the time limit has elapsed.
                return
