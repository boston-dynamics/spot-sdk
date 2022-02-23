# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Start AutoReturn manually with a force-acquired lease."""

import argparse

import bosdyn.client
import bosdyn.client.util
from bosdyn.api.auto_return import auto_return_pb2
from bosdyn.client.auto_return import AutoReturnClient
from bosdyn.client.lease import LeaseClient
from bosdyn.util import seconds_to_duration


def main():
    """Run program."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument('--disp', type=float, help='Maximum displacement to travel (m)',
                        default=12.5)
    parser.add_argument('--duration', type=float, help='Maximum duration (s)')
    options = parser.parse_args()
    bosdyn.client.util.setup_logging(options.verbose)

    sdk = bosdyn.client.create_standard_sdk('AutoReturnExample')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)

    # Forcibly take the lease.  This is bad practice, but for this example we want to
    # steal control away from the owner of the robot in order to immediately trigger auto return.
    lease_client = robot.ensure_client(LeaseClient.default_service_name)
    lease_client.take()

    # Configure AutoReturn with the latest lease.
    autoreturn_client = robot.ensure_client(AutoReturnClient.default_service_name)
    params = auto_return_pb2.Params(max_displacement=options.disp)
    if options.duration:
        params.max_duration.CopyFrom(seconds_to_duration(options.duration))

    autoreturn_client.configure(params, [lease_client.lease_wallet.get_lease().create_newer()])

    # Begin the AutoReturn logic.
    autoreturn_client.start()


if __name__ == "__main__":
    main()
