<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# bosdyn-orbit

The bosdyn-orbit wheel contains the Orbit client for the Boston Dynamics Orbit API. The Orbit API is hosted on your Orbit. The Orbit client interacts with the Orbit API by sending HTTPs requests to a number of resource endpoints. The client offers the following main functionalities:

- Retrieve Orbit software version info
- Get Orbit's current system time
- List robots
- List site walks, site elements, and site docks
- List posted calendar events
- Access resources such as runs, run events, and run captures
- Get images
- Export and import site walks
- Create a site walk, site element, and site dock
- Add robots to the specified Orbit instance
- Create a calendar event to play a mission
- Delete site walks, site elements, and site docks
- Remove robots
- Delete calendar event
