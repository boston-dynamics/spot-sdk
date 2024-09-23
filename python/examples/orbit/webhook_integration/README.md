<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Webhook Integrations

## Getting Started

Please begin with the [Quickstart Guide](../../../../docs/python/quickstart.md) to get your Python programming environment set up properly. Then, specifically for this example, look at the [Orbit API Docs](../../../../docs/concepts/orbit/about_orbit.md). For a complete list of resources and their methods, see the <a href="../../../../docs/orbit/docs.html">Orbit API Reference</a>.

# Example Overview

In case you missed it in our quickstart guide, a webhook is a mechanism or method of communication used in web development and API integration. It allows one application or service to automatically send data to another application or service when specific events occur, rather than requiring continuous polling for updates.

This example program builds upon the "hello_webhook.py" introductory programming example under the webhook folder.
"hello_webhook.py" shows how to use webhooks as part of the Orbit client, which uses the Orbit web API. It demonstrates how to initialize the Orbit client, authenticate with an API token, and create, update, list, and delete webhooks instance.

This example takes this one step further to provide an example to create a docker image of this a webhook listener, listen for webhooks, perform some data manipulation and send it on to a further backend system.

## Setup Dependencies

See the requirements.txt file for a list of Python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r docker-requirements.txt

```

## Key Vocabulary

**API Token:** Orbit API token. This is created in the API token sub section of the settings menu. This acts as the method of authentication with Orbit.
**Webhook Secret:** Secret associated with the webhook endpoint. Security feature sent along with the inspection webhook to ensure the data is coming from the correct source.
**Webhook URL:** Listener URL the webhook JSON will be sent to.
**Webhook Port:** Port where the webhook listener will be listening at.
**Hostname:** Orbit IP or Hostname.
**Backend or Integration URL:** May be the same as the webhook URL. This is the ultimate endpoint the listener will send the finally JSON data package to.

## Run the Example Locally

To run the example for local development and testing, run the following command from the project directory with verify set to False. When set to False, requests will skip server's TLS certificate verifications which will make your application vulnerable. For production software, we recommend you set verify to True or a path to CA bundle.

```
python3 webhook_integration.py --hostname "YOUR_ORBIT_IP" --verify False --webhook-host "YOUR_COMPUTER'S IP" --webhook-port 5000
```

## Run the Example On Sitehub-Hosted Orbit

Step 1: Set Environment Variables & Create Webhooks

There are a few environment variables that need to be set in order to properly host the extension on your Orbit instance. The main two that are required to start are

**.env**

1. Integration URL: URL of the integration server to send the webhook data
2. API Key: API Key created within the Orbit instance. This can be found in the settings menu and should be copied over upon creation.
3. Webhook Secret: This can be grabbed after the first time the extension is ran and it builds the webhook or configured ahead of time after building a webhook to send to url http://0.0.0.0:21600.

**Dockerfile**

1. Desired Port: Desired port to host on within Orbit's supported range. This needs to be updated in the Dockerfile and docker-compose. By default this is set to 21800.

## Run the Example On Cloud Orbit

To run on a cloud instance, the docker container will need to be hosted within the cloud service or on a local device. Please reach out to support@bostondynamics.com for further questions regarding hosting cloud base extensions.

### Allowed Port Ranges

The following port ranges are what are reserved for extension hosting on Spot. The extension is preconfigured to use port '21600' but this is not required. If changing this, be sure to update with the DockerFile.

TCP: 21000-22000 (except 21443 on CORE I/O which is reserved for an internal use case)
UDP: 21000-22000

Step 2: Build the Extension - we recommend utilizing the build extension helper function in the Spot Python Examples library

```
python3 ../../extensions/build_extension.py --amd64  --dockerfile-paths Dockerfile --build-image-tags webhook_integration:latest --image-archive webhook_integration.tar.gz --icon ./extension/image.png --package-dir ./extension/ --spx ./webhook_integration.spx
```

Step 3. Check integration fields and networking

1. Ensure all actions desired for integration have Asset IDs, metadata for fields or other connecting variables between desired systems.
2. Ensure Orbit IP and port will be able to reach Integration URL. This often requires firewall rules put in place.

Step 4. Load Extension

Load extension to Orbit through the extensions webpage. Ensure no errors are within the logging page and verify it is working utilizing the test payload functionality in the webhook page found in settings.
