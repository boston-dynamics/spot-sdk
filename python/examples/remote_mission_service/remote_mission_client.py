# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Example of how to talk to the remote_mission_service."""

import argparse
import time

import grpc

from bosdyn.api.mission import remote_pb2, util_pb2
import bosdyn.mission.remote_client
import bosdyn.client.lease
import bosdyn.client.util


def main():
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    parser.add_argument('--port', help='Port that service is listening on', type=int, required=True)
    parser.add_argument('--lease-host', help='Host that provides leases. Typically the robot.')
    parser.add_argument(
        '--user-string',
        help='Specify the user-string input to Tick. Set to the node name in Autowalk missions.')
    options = parser.parse_args()

    # Build a client that can talk to the RemoteMissionService implementation.
    client = bosdyn.mission.remote_client.RemoteClient()
    # Point the client at the service. We're assuming there is no encryption to set up.
    client.channel = grpc.insecure_channel('{}:{}'.format(options.hostname, options.port))

    inputs = []
    input_values = []

    if options.user_string:
        name = 'user-string'
        inputs = [
            util_pb2.VariableDeclaration(name=name, type=util_pb2.VariableDeclaration.TYPE_STRING)
        ]
        input_values = [
            util_pb2.KeyValue(key=name, value=util_pb2.Value(
                constant=util_pb2.ConstantValue(string_value=options.user_string)))
        ]

    lease_client = None
    body_lease = None
    leases = []

    # If we're using a lease, we'll have to authenticate to the robot to acquire it.
    if options.lease_host:
        sdk = bosdyn.client.create_standard_sdk('RemoteMissionClientExample')
        sdk.load_app_token(options.app_token)
        robot = sdk.create_robot(options.lease_host)

        robot.authenticate(options.username, options.password)

        lease_client = robot.ensure_client(bosdyn.client.lease.LeaseClient.default_service_name)
        # Acquire a lease and save it in the list of leases we pass to the servicer.
        body_lease = lease_client.acquire()
        leases = [body_lease]

    # Now run through a typical sequence of calls to the remote servicer.
    try:
        # Establish the session, telling the servicer to perform any one-time tasks.
        try:
            session_id = client.establish_session(leases=leases, inputs=inputs)
        except bosdyn.client.UnimplementedError:
            # EstablishSession is optional, so we can ignore this error.
            print('EstablishSession is unimplemented.')
            session_id = None

        # Begin ticking, and tick until the server indicates something other than RUNNING.
        response = client.tick(session_id, leases=leases, inputs=input_values)
        while response.status == remote_pb2.TickResponse.STATUS_RUNNING:
            time.sleep(0.1)
            response = client.tick(session_id, leases=leases, inputs=input_values)
        print('Servicer stopped with status {}'.format(
            remote_pb2.TickResponse.Status.Name(response.status)))
        if response.error_message:
            print('\tError message: {}'.format(response.error_message))

        try:
            # We're done ticking for now -- stop this session.
            client.stop(session_id)
            # We don't want to tick with this particular session every again -- tear it down.
            client.teardown_session(session_id)
        except bosdyn.client.UnimplementedError as exc:
            # The exception itself can tell us what's not implemented.
            print('Either Stop or TeardownSession is unimplemented.')

    finally:
        # Try to return the lease, if applicable.
        if lease_client and body_lease:
            lease_client.return_lease(body_lease)


if __name__ == '__main__':
    main()
