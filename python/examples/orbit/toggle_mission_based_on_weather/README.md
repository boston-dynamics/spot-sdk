<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Enable - disable Orbit missions based on weather forcast

This example program is the introductory programming example for the Orbit client, which uses the Orbit web API. It demonstrates how to initialize the Orbit client, authenticate with an API token, and enable or disable all scheduled missions depending on the weather forecast.

## Understanding Orbit Web API

Please begin with the [Quickstart Guide](../../../../docs/python/quickstart.md) to get your Python programming environment set up properly. Then, specifically for this example, look at the [Orbit API Docs](../../../../docs/concepts/orbit/orbit_api.md). For a complete list of resources and their methods, see the <a href="../../../../docs/orbit/docs.html">Orbit API Reference</a>.

## Setup Dependencies

See the requirements.txt file for a list of python dependencies which can be installed with pip using the command:

```
python3 -m pip install -r requirements.txt
```

This example uses [OpenWeatherMap](https://openweathermap.org/api)'s python API ([pyowm](https://github.com/csparpa/pyowm)) to fetch the 3 hr weather forecast for the given city. Please feel free to modify the code to use your preferred service. To run the example, you will need the OpenWeatherMap API key.

## Run the Example

To run the example for local development and testing, run the following command with verify set to False. When set to False, requests will skip server's TLS certificate verifications which will make your application vulnerable. For production software, we recommend you set verify to True or a path to CA bundle.

```
python3 toggle_mission_based_on_weather.py --hostname ORBIT_IP --owmapikey API_KEY --city CITY --country COUNTRY --verify False
```

The above command prompts you to provide the API token obtained from the Orbit admin settings page. Alternatively, you can set the environment variable `BOSDYN_ORBIT_CLIENT_API_TOKEN` to the API token obtained from Orbit admin settings page.
