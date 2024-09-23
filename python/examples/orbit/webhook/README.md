<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Hello Webhooks

A webhook is a mechanism or method of communication used in web development and API integration. It allows one application or service to automatically send data to another application or service when specific events occur, rather than requiring continuous polling for updates.

This example program is the introductory programming example for using the webhooks part of the Orbit client, which uses the Orbit web API. It demonstrates how to initialize the Orbit client, authenticate with an API token, and create, update, list, and delete webhooks instance.

## Understanding Orbit Web API

Please begin with the [Quickstart Guide](../../../../docs/python/quickstart.md) to get your Python programming environment set up properly. Then, specifically for this example, look at the [Orbit API Docs](../../../../docs/concepts/orbit/orbit_api.md). For a complete list of resources and their methods, see the <a href="../../../../docs/orbit/docs.html">Orbit API Reference</a>.

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Run the Example

To run the example for local development and testing, run the following command with verify set to False. When set to False, requests will skip server's TLS certificate verifications which will make your application vulnerable. For production software, we recommend you set verify to True or a path to CA bundle.

```
python3 hello_webhooks.py --hostname ORBIT_IP --verify False
```

Please look into the optional arguments.

The above command prompts you to provide the API token obtained from the Orbit admin settings page. Alternatively, you can set the environment variable `BOSDYN_ORBIT_CLIENT_API_TOKEN` to the API token obtained from Orbit admin settings page.
