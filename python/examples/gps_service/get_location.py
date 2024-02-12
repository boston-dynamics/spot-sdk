# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

""" Example code for getting the GPS location of a robot """

import argparse
import os
import time

import bosdyn.client
import bosdyn.client.util

QUERIES_PER_SECOND = 1

# Parse command line arguments.
parser = argparse.ArgumentParser()
bosdyn.client.util.add_base_arguments(parser)
options = parser.parse_args()

# Create and authenticate the Robot client.
sdk = bosdyn.client.create_standard_sdk("get_location")
robot = sdk.create_robot(options.hostname)
bosdyn.client.util.authenticate(robot)

# Get the registration client and query the location.
reg_client = robot.ensure_client("gps-registration")
while True:
    # Clear the screen
    os.system('cls' if os.name == 'nt' else 'clear')
    # Print the location.
    print(reg_client.get_location())
    # Sleep for a second.
    time.sleep(QUERIES_PER_SECOND)
