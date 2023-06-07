<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Hello Scout

This example program is the introductory programming example for the Scout client, which uses the Scout web API. It demonstrates how to initialize the Scout client, authenticate with user name and password, and finally list the names of the robots connected to Scout.

## Understanding Scout Web API

Please begin with the [Quickstart Guide](../../../../docs/python/quickstart.md) to get your Python programming environment set up properly. Then, specifically for Hello Scout, look at the [Scout API Docs](../../../../docs/concepts/about_scout.md). For a complete list of resources and their methods, see the <a href="../../../../docs/scout/docs.html">Scout API Reference</a>.

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Run the Example

To run the example:

```
python3 hello_scout.py -hostname SCOUT_IP
```
