<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Orbit Backups

This Orbit API example demonstrates how to create, manage, and retrieve Orbit backups using the Boston Dynamics Orbit API client.

## Understanding Orbit Web API

To get started with the Orbit Web API, please begin with the [Quickstart Guide](../../../../docs/python/quickstart.md) to set up your Python programming environment correctly. For details specific to this example, refer to the [Orbit API Docs](../../../../docs/concepts/orbit/about_orbit.md). For a complete list of resources and their methods, see the <a href="../../../../docs/orbit/docs.html">Orbit API Reference</a>.

## Setup Dependencies

See the `requirements.txt` file for a list of Python dependencies, which can be installed using pip with the following command:

```
python3 -m pip install -r requirements.txt
```

## Run the Example

To run the example for local development and testing, run the following command with verify set to False. When set to False, requests will skip server's TLS certificate verifications which will make your application vulnerable. For production software, we recommend you set verify to True or a path to CA bundle.

To start a backup including missions and data captures, execute:

```
python3 get_backup.py --hostname ORBIT_IP --verify False --include-missions --include-captures
```

Note that the above backup process can take a while. For the purpose of this example, we recommend backing up missions first since it will be relatively quick by running the following command:

```
python3 get_backup.py --hostname ORBIT_IP --verify False --include-missions
```

To specify where to save the backup file, use the `--file-path` option. Otherwise, the backup file will be saved in the current directory:

```
python3 get_backup.py --hostname ORBIT_IP --verify False --file-path /path/to/save/backup.tar
```

The above command prompts you to provide the API token obtained from the Orbit admin settings page. Alternatively, you can set the environment variable `BOSDYN_ORBIT_CLIENT_API_TOKEN` to the API token obtained from Orbit admin settings page.
