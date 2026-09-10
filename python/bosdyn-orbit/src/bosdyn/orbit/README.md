<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# Python Orbit

Client code and interfaces for the Boston Dynamics Orbit web API.
The Orbit web API provides access to a variety of resources through RESTful HTTPs endpoints.

The `OrbitClient` class in this package targets the **v0** Orbit API (`/api/v0/`). The new **v1** API introduced in Orbit v5.2 (`/api/fleet/v1/`, `/api/facilities/v1/`, …) is not wrapped by a dedicated client; call it directly with any HTTP client such as `requests`. See the [`orbit_v1_api`](../../../../examples/orbit/orbit_v1_api/README.md) example for the recommended pattern.

## Contents

- [Client](client)
- [Utils](utils)
- [Exceptions](exceptions)
