<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Anomalies in Orbit

This Orbit API example demonstrates how to retrieve and edit anomaly data with a Boston Dynamics Orbit API client.

## Understanding Orbit Web API

Please begin with the [Quickstart Guide](../../../../docs/python/quickstart.md) to get your Python programming environment set up properly. Then, specifically for this example, look at the [Orbit API Docs](../../../../docs/concepts/orbit/orbit_api.md). For a complete list of resources and their methods, see the <a href="../../../../docs/orbit/docs.html">Orbit API Reference</a>.

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

## Run the Example

To run the example to get anomalies stored on your Orbit instance, run the following command with verify set to False. When set to False, requests will skip server's TLS certificate verifications which will make your application vulnerable. For production software, we recommend you set verify to True or a path to CA bundle.

```
python3 get_anomalies.py --hostname ORBIT_IP --verify False
```

To close multiple anomaly alerts at once obtain their elementIds from the get_anomalies.py example and use them as arguments in the following command:

```
python3 patch_anomalies.py --hostname ORBIT_IP --bulk-close-element-ids ELEMENT_ID_1 ELEMENT_ID_2 ELEMENT_ID_3 --verify False
```

To edit an anomaly alert, obtain the anomaly uuid from the get_anomalies.py example and use it as an argument in the following command, and set the status flag to **open** or **closed** and patch the anomaly:

```
python3 patch_anomalies.py --hostname ORBIT_IP --anomaly-uuid ANOMALY_UUID_1 --status STATUS --verify False
```

Command to open a specific anomaly:

```
python3 patch_anomalies.py --hostname ORBIT_IP --anomaly-uuid ANOMALY_UUID_1 --status open --verify False
```

Command to close a specific anomaly:

```
python3 patch_anomalies.py --hostname ORBIT_IP --anomaly-uuid ANOMALY_UUID_1 --status closed --verify False
```

The above command prompts you to provide the API token obtained from the Orbit admin settings page. Alternatively, you can set the environment variable `BOSDYN_ORBIT_CLIENT_API_TOKEN` to the API token obtained from Orbit admin settings page.
