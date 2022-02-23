# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Simple interaction with the Mission service."""
import argparse
import logging

import bosdyn.client
import bosdyn.client.util
from bosdyn.mission.client import MissionClient


def main():
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()
    bosdyn.client.util.setup_logging(options.verbose)

    # Create an SDK that knows about the MissionClient type.
    sdk = bosdyn.client.create_standard_sdk('get-mission-state-example', [MissionClient])
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    client = robot.ensure_client(MissionClient.default_service_name)

    state = client.get_state()
    logger.info('Got mission state:\n%s', str(state))


if __name__ == '__main__':
    main()
