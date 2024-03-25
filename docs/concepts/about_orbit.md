<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# About Orbit (formerly Scout)

Orbit is a collection of web services for site awareness, fleet management and data centralization deployed to an on-premise or cloud server. Learn more about the product and deployment [here](https://www.bostondynamics.com/products/orbit).

Orbit collects, organizes, and stores data from every mission and teleoperation session executed by a Spot fleet - this information is served to users through a programmatic Application Programming Interface (API) called the Orbit API.

## Orbit API

The Orbit API is a web API served by an Orbit instance. The API is interacted with by sending HTTPs requests to a number of resource endpoints. Each resource endpoint is prefixed with the API route `/api/v0/`. For example, a list of `run_events` may be retrieved by sending a `GET` request to `/api/v0/run_events`. A complete URL would add this to the URL of the Orbit instance - e.g. `https://my-orbit.com/api/v0/run_events/`.

The Orbit API is language-agnostic and may be programmed against using any programming language that supports sending HTTP requests.

For a complete list of resources and their methods, see the <a href="../orbit/docs.html">Orbit API Reference</a>.

## Contents

- <a href="../orbit/docs.html">Orbit API REST Reference</a>
- [Orbit API Python SDK](../../python/bosdyn-orbit/src/bosdyn/orbit/README.md)
- [Orbit API Python SDK Examples](../../python/examples/docs/orbit.md)
- [Authentication](#authentication)
- [Webhooks](#webhooks)
- [Scheduling Missions](#scheduling-missions)

### Authentication

Resources can only be requested by authorized Orbit users. In order to be authorized, users need to provide headers with an API token obtained from an Orbit instance's admin settings.

To authorize with the obtained API token, make a request to the login endpoint at `/api/v0/api_token/authenticate`:

```py
"""Authenticate with an API token obtained from an Orbit instance."""
import json
import requests

# Set API token in headers
headers = {'Authorization': 'Bearer ' + <MY ORBIT API TOKEN>}
# Check the validity of the API token
authenticate_response = requests.get(
    f'https://{my-orbit.com}/api/v0/api_token/authenticate', headers=headers)
if authenticate_response.ok:
    print('Client: Auth succeeded')
else:
    print('Client: Auth failed: {} Please, obtain a valid API token from the instance!'.
          format(authenticate_response.text))
```

Now that we have a valid API token, we can use it to request resources. When requesting, the API token needs to be provided as part of the `headers` argument:

```py
"""Use the cookies to fetch some robots. The same authorization strategy is used for other http methods."""
robots_response = requests.get(f'https://{hostname}/api/v0/robots', headers=headers, verify=False)
if not robots_response.ok:
  print(f'Encountered a problem while requesting robots: {robots_response.text}')
else:
  robots_json = robots_response.json()
  print("Fetched robots!")
```

The API token must be provided in every request aside from the request. If an unauthorized request is made, a `401` response is sent. Likewise, if an API link is visited in the browser without the user being authorized, `Forbidden` is shown.

## Orbit API and the Python SDK

The Spot Python SDK includes a `bosdyn-orbit` Python package and client implementation for the Orbit API. The `bosdyn-orbit` package documentation is [here](../../python/bosdyn-orbit/src/bosdyn/orbit/README.md).

Once instantiated and authenticated, a `Client` provides a number of helpful methods which abstract away the details of HTTP to simplify building programs with the Orbit API. Please refer to the [Hello Orbit](../../python/examples/orbit/hello_orbit/README.md) SDK example to get started developing with the Orbit API Python client.

### Deprecation Warning

Following the rebranding of "Scout" to "Orbit" in 4.0.0, the pre-existing Python package `bosdyn-scout` is being deprecated. All [SDK examples](../../python/examples/docs/orbit.md) now use `bosdyn-orbit` instead. Any previous applications that used `bosdyn-scout` will continue to work. It is highly recommended that `bosdyn-orbit` be used moving forward.

## Webhooks

In addition to providing programmatic and on-demand access to data via the API, Orbit can also _push_ data to applications via webhooks when an event occurs.

### What is a webhook?

Most generally, a webhook is a mechanism by which one system sends real-time data to another system when an event occurs. In this case, Orbit is the event source. Its job is to identify when an event occurs, at which point it will send an HTTP POST request with data about the event to any webhooks registered and subscribed to that event.

### Configuring Webhooks

Webhooks can be configured by an Orbit admin on the settings page or by a developer via the HTTP endpoints at `https://my-orbit.com/api/v0/webhooks/`. See the webhooks API documentation for more details on the webhooks endpoints.

For webhooks to work, Orbit needs to know _where_ and _when_ to send the data. When creating a webhook, a URL must be specified. This is the location of the target HTTP endpoint and will be called with a POST request when an event occurs. Additionally, Orbit requires a list of subscribed events for each webhook. When any one of these events occur, Orbit will send a request. See the section below for the list of supported events.

### Webhook Payloads

When Orbit makes a request to a registered webhook, it includes information about the source event in the body of the request. The structure of the event payload is shown below.

```javascript
{
  // Unique identifier for this event.
  uuid: string
  // The type of event that was triggered.
  type: string
  // ISO date string indicating when event was triggered.
  time: string
  // Data about the triggered event. The structure will depend on the event type.
  data: { ... }
}
```

### Webhook Events

Orbit allows a webhook to subscribe to multiple events. The webhook will be invoked if any one of the events occur.

#### Action Completed

The "action completed" event is triggered whenever a robot completes an action. The value of `type` in the request payload will be `"ACTION_COMPLETED"`. The structure of the `data` field will be identical to the `run_event` object. At a high level, it contains information about the completed action like the name of the action, when it occurred, any key results that were generated, as well as links to any images that were taken as part of the action. See the `run_events` API documentation for more details on the data contained in a `run_event`.

#### Action Completed With Alert

The "action completed with alert" event is triggered whenever a robot completes an action where anomalous data was collected. For example, if a thermal inspection identifies an object that is above the configured maximum temperature threshold, Orbit will trigger the "action completed with alert" event. The value of `type` in the request payload will be `"ACTION_COMPLETED_WITH_ALERT"`. The structure of the `data` field will be identical to the `run_event` object. At a high level, it contains information about the completed action like the name of the action, when it occurred, any key results that were generated, as well as links to any images that were taken as part of the action. See the `run_events` API documentation for more details on the data contained in a `run_event`.

### Securing Webhooks

Webhooks have a configurable `secret` property that is used for securing webhook payloads. The `secret` is a 64 character hex string used to sign each webhook request. The HTTP requests are sent with a `Orbit-Signature` header with the following format:

```
t=1701098596652,v1=<SIGNATURE>
```

The value of `t` in the header is the unix timestamp when the message was sent by Orbit. The value of `v1` is the hash-based message authentication code (HMAC) generated by:

1. Creating a timestamped payload string of the form `<t>.<payload_json_as_string>`
2. Creating an HMAC using the webhook secret as the key, the timestamped payload string as the message, and the SHA256 hash function
3. Generating the hexadecimal representation of the HMAC. This hex string should match the value of `v1`

The `bosdyn-orbit` module has a utility `validate_webhook_payload` that can be called from a webhook with the configured secret and the payload to handle these steps. This validation ensures that:

1. The payload came from Orbit.
2. The payload was not altered in transit by a man in the middle.
3. The payload was not replayed by a man in the middle.

#### HTTP vs HTTPS

Orbit supports the registration of endpoints using both `http` and `https`. Using `http` can be useful in certain development environments, but is **strongly discouraged** for production applications.

For `https` endpoints, by default, Orbit will validate the TLS certificate when establishing a connection to the server. Requests to servers with invalid certificates will fail. This can be overridden on the webhook configuration page or by setting `validateTlsCert` to `false` when creating a webhook through the REST API. Using unrecognized TLS certificates, like self-signed certs, can be useful during development but is **strongly discouraged** for production applications.

### Should I use webhooks or the Orbit API?

Orbit webhooks and REST API are both equally valid mechanisms for integrating with data collected by a robot. The choice of which to use depends on what needs to be done with the data.

#### When to use the Orbit API

The Orbit API is better suited for integrations that require on-demand access to data. For example, maybe an application generates a report of data collected by Orbit during a custom time period. At the click of a button, the application returns a report of the relevant data. This use case is more easily achieved using the REST API since the application may request data as-needed (e.g., whenever the button is clicked).

#### When to use webhooks

Webhooks are great for integrations that require real-time data or applications that want to do _something_ when a particular event occurs. For example, an application that creates a work order in an Enterprise Asset Management (EAM) system whenever the robot identifies an anomaly during an inspection. The application can host a webhook that subscribes to the `"ACTION_COMPLETED_WITH_ALERT"` event and sends the necessary data to the EAM system whenever the event is triggered.

## Scheduling Missions

Orbit has built-in functionality for scheduling missions. Once scheduled, Orbit will kick off and monitor the mission automatically at the prescribed time. The system supports multiple schedules per robot, adjustable repeat configurations, launch windows, and other features described below.

### Key Concepts

These concepts are the building blocks of the Orbit scheduling system.

- **Schedule**: A schedule is a description of _what_ a specific robot should do, _when_ it should do it, and _how often_ it should repeat the mission. For example, "Spot should run the mission called 'Gauge Reading' every day at 12:00pm".
- **Event**: Events are specific instances of a schedule. Taking the example above, if it is now Monday at 12:00pm, Orbit would start the _event_ that results in Spot executing the Gauge Reading mission.
- **Start Time**: The ideal time that an event will begin; "ideal" and not "actual" because many things could prevent the event from starting at the given time: a prior mission ran long, the robot is being teleoperated by a user, or there is a different schedule that takes priority - just to name a few. In the example above, the first start time is the timestamp of Monday at 12:00pm. The next start time will be automatically calculated once the event completes, and will be the original start time plus one day. This value will keep updating over time.
- **Repeat Interval**: The ideal gap between event kickoffs. This has a practical minimum of 60 seconds and no maximum. To specify a schedule that does not repeat, provide a non-positive value in this field. It's important to note that the repeat interval is relative to _start_ time, not end time. The system tries to keep start times locked to real-world time as much as possible. Taking the example above, the repeat interval is set to one day (expressed as milliseconds). It's possible that the robot will miss its start time, or be delayed in its mission and return late. In this case, the next start time is calculated to be Tuesday at 12:00pm, rather than Tuesday at 12:00pm plus the delay duration. This is to prevent a 12:00pm mission from creeping later and later and eventually running at midnight.
- **Blackout Times**: Blackout times are blocks of time when a schedule will not start events, even if the start time is valid. Let's modify the example case to be "Run the Gauge Reading mission every Monday, Wednesday, and Friday at 12:00pm". To achieve this, simply add _blackouts_, while keeping the same repeat type and repeat interval, to prevent the schedule from running on opposite days. In this case, after the Monday event, the scheduler will still pick Tuesday at 12:00pm for its next start time, but once that time rolls around, it will not start the event because that time is in _blackout_. The customer-facing term for this is _launch window_, and it is the inverse of blackouts. Note that there are some corner cases here to be aware of, which are discussed below.

### Weekly Repeat

The scheduler uses a week as its repeating unit, and Sunday as the first day of the week. That means that blackouts are specified as millisecond offsets since Sunday at midnight.

### Predicting Start Times

As noted above, the system uses event start times, not end times. Keep the following in mind when planning schedules:

1. If the robot needs to be out of a particular area at a particular time, and it has a schedule and mission that traverses that area, the schedule should have a buffer between that time and the start time to allow the robot to complete its mission. For example, if the robot is not allowed to be near some of its inspection points at 11:00am, the last possible start time might be 10:00am to account for an estimated mission duration plus a buffer. Note that this can also be done with blackouts, but the buffer idea still applies.
2. The specified _repeat interval_ is not guaranteed. The system prioritizes predictable start times over predictable intervals. For example, if a schedule has the repeat interval set to one hour, the system will try to start those events 60 minutes apart - it will _not_ wait one hour after the robot returns. In this case, it's possible that the robot starts a mission at 11:00am, returns at 11:55am, and starts the next event at 12:00pm, leaving only a 5 minute gap between mission completion and kickoff. This is intentional and by design.
3. If there are multiple schedules running for one robot, the schedules might interfere with each other. This is a normal and expected state to be in. The system will continue to start events according to their priority (described below), but predicting each event's start time gets more difficult. If very predictable start times are required, it is recommended to configure the schedules such that it is unlikely that a long-running mission will disrupt the next schedule - for example, one schedule that runs between 8:00am and 10:00am and another that runs at 12:00pm.

### Schedule Priority

As the number of robots and schedules increases, it is likely that multiple events will be eligible for dispatch at the same time - for example, a robot could have Schedule A that runs as fast as possible between 10:00am and 12:00pm, and Schedule B that runs once an hour between 9:00am and 5:00pm. For part of that duration, events from both schedules are allowed to run. This is how the system determines which one will actually be sent to the robot:

1. Run the "stalest" event first

- In steady state, this is the event that ran furthest in the past. If Schedule A last ran fifteen minutes ago, and Schedule B last ran two minutes ago, Schedule A is staler, and a Schedule A event will be started.
- If one of the two has never been run before, that one will be chosen. In the case of a tie, read on.

2. If two events are tied (most likely if they have been created at the same time), whichever mission's name comes first alphabetically is chosen.

### Scheduling "Gotchas"

The scheduler design has some side effects that are predictable, but worth shedding light on. If something strange is happening, one of the following situations may apply.

#### Missions Running at Midnight

If the scheduler misses a scheduled start time for any reason, it will try to dispatch the missed event at the earliest available opportunity. This can happen if the robot is late getting back from a prior mission. For example, suppose a schedule is set up to run an event at 12:00pm every Monday, Wednesday, and Friday. To accomplish this, the schedule must have blackout periods for Tuesday, Thursday, Saturday, and Sunday, from midnight to midnight. This scenario will play out as follows:

1. The robot runs its first mission on Monday at 12:00pm. The next start time is scheduled for 24 hours later, so Tuesday at 12:00pm.
2. Tuesday at 12:00pm rolls around, and the schedule is in a blackout period, so the event is not started.
3. The scheduler checks often (on the order of seconds) to see if it's able to dispatch the overdue event.
4. The clock ticks over from 11:59pm on Tuesday to 12:00am on Wednesday. This is the first time since the missed event that the schedule is not in blackout, so the scheduler starts it now - at midnight on Wednesday.

If running the robot at midnight is undesirable, this may be avoided by extending the blackout until the next desired start time. That is to say, blackouts must be added not just on the alternate days, but also from midnight to 12:00pm on Monday, Wednesday, and Friday. The result of this is that Tuesday's missed event is next valid on Wednesday at _noon_, not midnight.

#### Unpredictable "Fast as Possible" Schedules

An implicit race condition due to polling means that it is possible for an event to be passed over for dispatch in some cases. Ideally, three schedules (A, B, and C) should start events in a predictable order: A, B, C, A, B, C (recall the "stalest first" prioritization system). However, when scheduling with the API, a race condition could result in multiple "fast as possible" schedules dispatching in a non-deterministic order. In this case, set the repeat interval to be identical for all schedules. The recommended interval for "fast as possible" is 60 seconds (although it can be anything, as long as it is the same across all schedules).

#### Time Zones

The API expects Coordinated Universal Time (UTC) times. If the schedules run with an offset from the given times, check this.

#### Daylight Savings Time

The scheduler does not handle Daylight Savings Time yet. This is slated for a future release.
