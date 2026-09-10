# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Demonstrate the Orbit v1 API by listing robots and site walks using raw HTTP.

This example intentionally uses ``requests`` directly (not ``OrbitClient``) to
make the v1 REST shape tangible. ``OrbitClient`` targets v0; for v1, any HTTP
client works because the API is fully described by the OpenAPI specs at
``/api/v1/docs``.
"""

import argparse
import getpass
import logging
import os
import sys
from typing import Any, Dict, Iterator

import requests

LOGGER = logging.getLogger("orbit_v1_api")
LOGGER.setLevel(logging.INFO)
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("orbit_v1_api: %(levelname)s - %(message)s"))
LOGGER.addHandler(_handler)


def paginate(session: requests.Session, url: str, page_size: int = 25) -> Iterator[Dict[str, Any]]:
    """Yield every item from a v1 list endpoint, walking ``limit``/``offset`` pages.

    All v1 list endpoints return ``{"items": [...], "page": {"count", "limit", "offset"}}``.
    """
    offset = 0
    while True:
        response = session.get(url, params={"limit": page_size, "offset": offset})
        response.raise_for_status()
        payload = response.json()
        items = payload.get("items", [])
        page = payload.get("page", {})
        for item in items:
            yield item
        total = page.get("count", 0)
        offset += len(items)
        if not items or offset >= total:
            return


def list_robots(session: requests.Session, base_url: str) -> None:
    """Fetch and print every robot exposed by the v1 Fleet service."""
    LOGGER.info("Listing robots from %s/api/fleet/v1/robots", base_url)
    count = 0
    for robot in paginate(session, f"{base_url}/api/fleet/v1/robots"):
        # v1 ids are opaque strings - do not assume UUID.
        LOGGER.info("  robot id=%s nickname=%s", robot.get("id"), robot.get("nickname"))
        count += 1
    LOGGER.info("Fetched %d robot(s) total", count)


def list_site_walks(session: requests.Session, base_url: str) -> None:
    """Fetch and print every site walk exposed by the v1 Facilities service."""
    LOGGER.info("Listing site walks from %s/api/facilities/v1/site-walks", base_url)
    count = 0
    for site_walk in paginate(session, f"{base_url}/api/facilities/v1/site-walks"):
        LOGGER.info("  site-walk id=%s name=%s", site_walk.get("id"), site_walk.get("name"))
        count += 1
    LOGGER.info("Fetched %d site walk(s) total", count)


def get_robot_by_id(session: requests.Session, base_url: str, robot_id: str) -> None:
    """Fetch a single robot by its id and print key fields."""
    url = f"{base_url}/api/fleet/v1/robots/{robot_id}"
    LOGGER.info("Fetching %s", url)
    response = session.get(url)
    if response.status_code == 404:
        # v1 errors share the shape: {code, message} where code is resource-specific.
        error = response.json()
        LOGGER.error("Not found: code=%s message=%s", error.get("code"), error.get("message"))
        return
    response.raise_for_status()
    robot = response.json()
    LOGGER.info("Robot: %s", robot)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hostname", required=True,
                        help="Orbit hostname, e.g. my-orbit.example.com")
    parser.add_argument(
        "--verify", default="True",
        help="Path to a CA bundle, or 'True'/'False'. Use 'False' only for "
        "local development.")
    parser.add_argument("--robot-id",
                        help="Optional v1 robot id to fetch via /api/fleet/v1/robots/{id}.")
    args = parser.parse_args()

    if args.verify in ("True", "False"):
        verify: Any = args.verify == "True"
    else:
        verify = args.verify

    api_token = os.environ.get("BOSDYN_ORBIT_CLIENT_API_TOKEN")
    if not api_token:
        api_token = getpass.getpass("Orbit API token: ")

    base_url = f"https://{args.hostname}"
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_token}"})
    session.verify = verify

    try:
        list_robots(session, base_url)
        list_site_walks(session, base_url)
        if args.robot_id:
            get_robot_by_id(session, base_url, args.robot_id)
    except requests.HTTPError as exc:
        LOGGER.error("HTTP error: %s", exc)
        if exc.response is not None:
            LOGGER.error("Response body: %s", exc.response.text)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
