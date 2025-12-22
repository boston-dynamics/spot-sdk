<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Access Controlled Door API Example

This example provides two scripts for testing API calls to an access-controlled door system:

- `test_door_api_call.py`: Make API calls to authenticate and open and close doors.
- `get_cert_from_server.py`: Retrieve and save the SSL/TLS certificate from the API server.

## Setup

Install dependencies:

```
python3 -m pip install -r requirements.txt
```

## Usage

### 1. Retrieve the Server Certificate

Use `get_cert_from_server.py` to download the server certificate:

```
python3 get_cert_from_server.py --hostname <ACCESS_CONTROL_SYSTEM_IP> --port 443 --cert door_api.cer
```

where `<ACCESS_CONTROL_SYSTEM_IP>` needs to be replaced with the IP address of the access control system.

Executing this script will save the server certificate to `door_api.cer` for subsequent use with the `test_door_api_call.py` script.

### 2. Make Door API Calls

Use `test_door_api_call.py` to send commands to the door API:

```
python3 test_door_api_call.py --api-config config.json --cert door_api.cer --commands AUTH OPEN --door-id 123
```

where `--api-config` is the path to the API configuration file in JSON format, `--cert` is the path to the certificate file (from server directly or via step 1), `--commands` is one or more commands (e.g., `--commands AUTH OPEN` will authenticate and open the door, provided the API configuration file specifies both these methods correctly), and `--door-id` is the unique ID of the door in the access control system.

## Notes

- The `test_door_api_call.py` script requires, among other things, an API configuration file corresponding to your access control system's API. Please see the [Example Configuration File](#example-api-configuration-file) section for more details.
- The certificate file must have a `.cer` extension.
- The `OPEN` and `CLOSE` commands require a door ID.

## Example API Configuration File

There is an example configuration file for Bosch Access Management System (AMS) [here](https://github.com/boston-dynamics/spot-sdk/tree/master/python/examples/access_controlled_doors/bosch_ams_example.json). Note that everything in angle-bracketed placeholders (<...>) needs to be replaced, the contents of which are dependent upon whether the API configuration file is in use locally (i.e., via the `test_door_api_call.py` script) or on the robot. For example, for the `route` argument:

- On the robot, only `WIFI`, `LTE`, or `ETHERNET` are valid options.
- On your local machine, set `route` to the actual network adapter (as shown by `ifconfig` on Ubuntu or `ipconfig` on Windows).

A brief explanation of the other angle-bracketed placeholders follows:

- "url": "https://<BOSCH_AMS_IP>:44333/connect/token",
  - Replace <BOSCH_AMS_IP> with the IP address of the computer running Bosch AMS.
- "sni_hostname": "<BOSCH_AMS_HOSTNAME>",
  - Replace <BOSCH_AMS_HOSTNAME> with the hostname of the computer running Bosch AMS. To get the hostname, execute the `hostname` command in `Command Prompt` on said computer.
- "client_id": "<USERNAME>",
  - Replace <USERNAME> with the username of the user provisioned for Spot in Bosch AMS.
- "client_secret": "<PASSWORD>"
  - Replace <PASSWORD> with the password of the user provisioned for Spot in Bosch AMS.

The API documentation for Bosch AMS is available for reference [here](https://github.com/boston-dynamics/spot-sdk/tree/master/python/examples/access_controlled_doors/bosch_ams_api.pdf).

A brief explanation of some other items of interest in the example configuration file follows.

### Access Token

The authentication response from Bosch AMS contains a parameter called `access_token`.

```
"token": "access_token"
```

The key, `token`, is mentioned in the `OPEN` and `CLOSE` methods and is hence subtituted for `{token}` in said methods.

```
`headers": {"Authorization": "Bearer ${token}"}`.
```

### deviceId and commandTypeId

The keys, `deviceId` and `commandTypeId`, correspond to supported command types in Bosch AMS. Please see the [documentation](https://github.com/boston-dynamics/spot-sdk/tree/master/python/examples/access_controlled_doors/bosch_ams_api.pdf) for the `/api/devices/execute` endpoint for more information.

```
"json": {
  "deviceId": "${door_id}",
  "commandTypeId": "SetDigitalOutput"
}
```

Setting the digital output activates the relay, thereby unlocking the door.

```
"json": {
  "deviceId": "${door_id}",
  "commandTypeId": "ClearDigitalOutput"
}
```

Clearing the digital output deactivates the relay, thereby locking the door.
