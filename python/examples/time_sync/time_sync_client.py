# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Simple time sync tutorial."""
import sys

import bosdyn.client
import bosdyn.client.util
from bosdyn.api.time_sync_pb2 import TimeSyncState
from bosdyn.client.time_sync import TimeSyncClient, TimeSyncEndpoint


def main():
    """Command-line interface."""
    import argparse
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args()

    # Create robot object with an image client.
    sdk = bosdyn.client.create_standard_sdk('TimeSyncClient')
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    time_sync_client = robot.ensure_client(TimeSyncClient.default_service_name)

    # The TimeSyncEndpoint wraps the TimeSyncClient
    time_sync_endpoint = TimeSyncEndpoint(time_sync_client)

    # The easiest way to establish time sync is to use this function, which makes several RPC calls
    # to TimeSyncUpdate, continually updating the clock skew estimate.
    did_establish = time_sync_endpoint.establish_timesync(max_samples=10, break_on_success=False)

    print(f'Did establish timesync: {did_establish}')
    print('status:', TimeSyncState.Status.Name(time_sync_endpoint.response.state.status))
    if did_establish:
        print(f'Client ID: {time_sync_endpoint.clock_identifier}')
        print(
            f'Clock skew seconds: {time_sync_endpoint.clock_skew.seconds} nanos: {time_sync_endpoint.clock_skew.nanos}'
        )
        print(f'Round trip time: {time_sync_endpoint.round_trip_time}')
    return did_establish


if __name__ == '__main__':
    if not main():
        sys.exit(1)
