<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Orbit v1 API

This example demonstrates the Orbit **v1** REST API, introduced in Orbit v5.2. It lists robots and site walks via the Fleet and Facilities services using raw HTTP calls with the [`requests`](https://requests.readthedocs.io/) library.

`OrbitClient` from `bosdyn-orbit` targets the v0 API. For v1, no dedicated client is bundled. This example uses `requests` directly to make calls to v1 endpoints.

## What this example shows

- Authenticating to v1 endpoints with the same `Authorization: Bearer <token>` header used for v0.
- Listing robots via `GET /api/fleet/v1/robots`.
- Listing site walks via `GET /api/facilities/v1/site-walks`.
- Walking `limit`/`offset` pagination using the standard v1 `{items, page}` envelope.
- Fetching a single resource by id (e.g. `GET /api/fleet/v1/robots/{id}`) and handling the uniform `{code, message, details}` error shape.

## v1 design at a glance

- **Service-oriented paths**: endpoints are grouped by domain (`/api/fleet/v1/`, `/api/facilities/v1/`) rather than by resource type in a single flat namespace.
- **Opaque identifiers**: every v1 resource is addressed by an `id` string. Many are UUIDs, but the format is not guaranteed per-resource. Treat ids as opaque tokens and do not parse them.
- **Paginated by default**: list endpoints accept `limit` and `offset` query parameters and return a `page` block with `count`, `limit`, and `offset`.
- **Standard error shape**: every error response is `{ "code": "...", "message": "...", "details": { ... } }`.
- **Live OpenAPI docs**: browse and try every endpoint at `https://{my-orbit.com}/api/v1/docs` (with a dropdown to switch between Fleet and Facilities).

## Setup

```
python3 -m pip install -r requirements.txt
```

## Run

Provide the Orbit hostname and an API token (obtained from Orbit's admin settings page). The token can be set via the `BOSDYN_ORBIT_CLIENT_API_TOKEN` environment variable or entered at the password prompt.

```
python3 orbit_v1_api.py --hostname ORBIT_IP --verify False
```

To fetch a specific robot by id:

```
python3 orbit_v1_api.py --hostname ORBIT_IP --verify False \
    --robot-id 00000000-0000-0000-0000-000000000000
```

`--verify False` disables TLS certificate verification and is intended for local development only. For production use, pass `--verify True` (default) or a path to a CA bundle.

## Learn more

- [Orbit API documentation](../../../../docs/concepts/orbit/orbit_api.md)
- Live v1 OpenAPI docs at `https://{my-orbit.com}/api/v1/docs`
