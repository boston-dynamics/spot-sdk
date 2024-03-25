<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Send robot back to the dock during a mission playback

This example program is the introductory programming example for the Orbit client, which uses the Orbit web API. It demonstrates how to initialize the Orbit client, authenticate with an API token, and send robot back to the dock while the robot is playing back the mission. The process is in three steps.

1. Generating a mission from a current waypoint back to the dock
2. Obtaining the current driver ID
3. Dispatching a mission generated from step 1 using the driver ID from step 2

## Understanding Orbit Web API

Please begin with the [Quickstart Guide](../../../../docs/python/quickstart.md) to get your Python programming environment set up properly. Then, specifically for this example, look at the [Orbit API Docs](../../../../docs/concepts/about_orbit.md). For a complete list of resources and their methods, see the <a href="../../../../docs/orbit/docs.html">Orbit API Reference</a>.

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Run the Example

To run the example for local development and testing, run the following command with verify set to False. When set to False, requests will skip server's TLS certificate verifications which will make your application vulnerable. For production software, we recommend you set verify to True or a path to CA bundle.

```
python3 send_robot_back_to_dock.py --hostname ORBIT_IP --robot_nickname ROBOT_NICKNAME --site_dock_uuid SITE_DOCK_UUID --verify False
```

The above command prompts you to provide the API token obtained from the Orbit admin settings page. Alternatively, you can set the environment variable `BOSDYN_ORBIT_CLIENT_API_TOKEN` to the API token obtained from Orbit admin settings page.
