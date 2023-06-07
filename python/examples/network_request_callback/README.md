<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Network Request Callback

Network requests can be used to trigger external devices such as doors or elevators, query a machine status, or interact with payloads along with many other possibilities. This remote mission service provides a callback that queries a network endpoint and then checks if the response contains a particular String.

The callback expects the following user parameters. These should be added manually after starting the service.

| User Parameter  | Type   | Description                                                           |
| --------------- | ------ | --------------------------------------------------------------------- |
| **Url**         | String | The address which receives the network request                        |
| **MustContain** | String | The string which the response must contain for the action to succeed. |

# Network Request Callback

For example, if Spot has internet access, this can be used to query the weather using a service like the one at `https://api.openweathermap.org/`. The action requires two User Parameters to be defined: _Url_ and _MustContain_. _Url_ is the network address and _MustContain_ is the substring that is required to be included in the response. If the reponse does not include the _MustContain_ string, then the action will fail.

In this example, Spot can avoid running a mission in poor weather. The response from openweathermap.org after setting up an API key is:

```
This XML file does not appear to have any style information associated with it. The document tree is shown below.
<current>
  <city id="4941935" name="Lexington">
    <coord lon="-71.2409" lat="42.4116"/>
    <country>US</country>
    <timezone>-14400</timezone>
    <sun rise="2022-06-27T09:09:49" set="2022-06-28T00:26:02"/>
  </city>
  <temperature value="295.71" min="293.98" max="297.49" unit="kelvin"/>
  <feels_like value="296.14" unit="kelvin"/>
  <humidity value="81" unit="%"/>
  <pressure value="1010" unit="hPa"/>
  <wind>
    <speed value="3.09" unit="m/s" name="Light breeze"/>
    <gusts/>
    <direction value="240" code="WSW" name="West-southwest"/>
  </wind>
  <clouds value="100" name="overcast clouds"/>
  <visibility value="3219"/>
  <precipitation value="3.76" mode="rain" unit="1h"/>
  <weather number="501" value="moderate rain" icon="10d"/>
  <lastupdate value="2022-06-27T15:31:12"/>
</current>
```

Rain is expected in the response above, but the _MustContain_ user parameter can be set to `precipitation mode="no"`.
The user parameter for _Url_ is set to: `https://api.openweathermap.org/data/2.5/weather?lat=<insert your latitude>&lon=<insert your longitude>&appid=<insert your appid>&mode=xml`
