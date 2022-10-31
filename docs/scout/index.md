<!--
Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Scout API Docs

Scout collects, organizes, and stores data from every mission and teleoperation session executed by a Spot fleet - this information is open to Scout customers through a programmatic api called the Scout API.

## Getting Started

### Resources
The Scout API is a web api hosted on your sitehub. The API is interacted with by sending HTTPs requests to a number of resource endpoints. Each resource endpoint is prefixed with the api route `/api/v0/`. For example, a list of `run_events` can be retrieved by sending a `GET` request to `/api/v0/run_events`. A complete url would add this to the url of the Scout instance - e.g. `https://my-scout.com/api/v0/run_events/`.

### Authentication
Resources can only be requested by Scout users. In order to be authorized, cookies authenticated with a Scout account must be provided in each request.

To obtain the cookies, make a request to the login endpoint at `/api/v0/login`:
```py
import json
import requests

hostname = "YOUR SCOUT HOSTNAME"
username = "YOUR SCOUT USERNAME"
password = "YOUR SCOUT PASSWORD"

"""Get a set of cookies to be authenticated."""
cookies_response = requests.get(f'https://{hostname}', verify=False)
cookies = requests.utils.dict_from_cookiejar(cookies_response.cookies)

"""Authenticates the cookies by issuing a login request."""
login_response = requests.post(f'https://{hostname}/api/v0/login', data={
    'username': username,
    'password': password
}, headers={'x-csrf-token': cookies['x-csrf-token']}, cookies=cookies, verify=False)

if not login_response.ok:
  print(f'Authentication failed: {login_response.text}')
  exit()
else:
  print(f'Authenticated! Logged in as: {login_response.json()["username"]}.')
```

Now the `cookies` are authenticated and can be used to request resources. When requesting, the cookie is provided as an argument:
```py
"""Use the cookies to fetch some robots. The same authorization strategy is used for other http methods."""
robots_response = requests.get(f'https://{hostname}/api/v0/robots', cookies=cookies, verify=False)
if not robots_response.ok:
  print(f'Encountered a problem while requesting robots: {robots_response.text}')
else:
  robots_json = robots_response.json()
  print("Fetched robots!")
```

An authenticated set of cookies must be provided in every request aside from the request to authenticate (`/api/v0/login`). If an unauthorized request is made, a `403` response will be issued. Likewise, if an api link is visited in the browser without the user having logged in, `Forbidden` will be shown.

A session expires after 2 weeks. You can reauthenticate using the same method explained above.

## Learn More

For a complete list of resources and their methods, see the <a href="docs.html">Scout API Reference</a>.
