# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import logging
import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.client.estop import EstopClient, EstopEndpoint, StopLevel

_LOGGER = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', type=float, help="Timeout of the estop (seconds)", default=1)
    bosdyn.client.util.add_base_arguments(parser)

    options = parser.parse_args()

    if options.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(level=log_level,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    sdk = bosdyn.client.create_standard_sdk('EstopClientWithSdk')

    robot = sdk.create_robot(options.hostname)

    bosdyn.client.util.authenticate(robot)

    estop_client = robot.ensure_client(EstopClient.default_service_name)
    estop_endpoint = EstopEndpoint(client=estop_client,
                                   name=bosdyn.client.sdk.generate_client_name('estop-tutorial:'),
                                   estop_timeout=options.timeout)

    estop_endpoint.force_simple_setup()

    call_and_check(estop_client, estop_endpoint, StopLevel.ESTOP_LEVEL_NONE, sync=True)
    call_and_check(estop_client, estop_endpoint, StopLevel.ESTOP_LEVEL_CUT, sync=True)
    call_and_check(estop_client, estop_endpoint, StopLevel.ESTOP_LEVEL_NONE, sync=True)
    call_and_check(estop_client, estop_endpoint, StopLevel.ESTOP_LEVEL_CUT, sync=True)

    call_and_check(estop_client, estop_endpoint, StopLevel.ESTOP_LEVEL_NONE, sync=False)
    call_and_check(estop_client, estop_endpoint, StopLevel.ESTOP_LEVEL_CUT, sync=False)
    call_and_check(estop_client, estop_endpoint, StopLevel.ESTOP_LEVEL_NONE, sync=False)
    call_and_check(estop_client, estop_endpoint, StopLevel.ESTOP_LEVEL_CUT, sync=False)

    current_config = estop_client.get_config()
    estop_client.deregister(current_config.unique_id, estop_endpoint)


def call_and_check(client, endpoint, expected_level, sync):
    if sync:
        if expected_level == StopLevel.ESTOP_LEVEL_CUT:
            endpoint.stop()
        if expected_level == StopLevel.ESTOP_LEVEL_NONE:
            endpoint.allow()
    else:
        if expected_level == StopLevel.ESTOP_LEVEL_CUT:
            fut = endpoint.stop_async()
        if expected_level == StopLevel.ESTOP_LEVEL_NONE:
            fut = endpoint.allow_async()
        fut.result()

    stop_level = client.get_status().stop_level
    assert stop_level == expected_level.value
    _LOGGER.info('Stop level: %s', StopLevel(stop_level))


if __name__ == '__main__':
    if not main():
        sys.exit(1)
