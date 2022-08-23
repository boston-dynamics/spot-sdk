# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Example that registers a remote server with the robot's directory for use with network compute bridge.

This lets you run a server in the cloud, or somewhere that can't easily reach out to every robot serves, and still perform ML or other computation.
"""
import argparse
import sys

import bosdyn.api.directory_pb2 as directory_protos
import bosdyn.api.directory_registration_pb2 as directory_registration_protos
import bosdyn.client.directory
import bosdyn.client.directory_registration
import bosdyn.client.util


def main(argv):
    """Command line interface.

    Args:
        argv: List of command-line arguments passed to the program.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--server-ip', help='IP address of the server to register',
                        required=True)
    parser.add_argument('-p', '--server-port', help='Port of the server to register', required=True)
    parser.add_argument('-n', '--service-name', help='Name for the service you are registering',
                        required=True)
    parser.add_argument('-a', '--authority', help='Authority for the service you are registering',
                        required=False)
    parser.add_argument('-f', '--force', help='Overwrite existing clients using this name.',
                        action='store_true')

    bosdyn.client.util.add_base_arguments(parser)

    options = parser.parse_args(argv)

    kServiceAuthority = options.authority or "remote-server-worker.spot.robot"

    sdk = bosdyn.client.create_standard_sdk("register_remote_server")

    robot = sdk.create_robot(options.hostname)

    # Authenticate robot before being able to use it
    bosdyn.client.util.authenticate(robot)

    directory_client = robot.ensure_client(
        bosdyn.client.directory.DirectoryClient.default_service_name)
    directory_registration_client = robot.ensure_client(
        bosdyn.client.directory_registration.DirectoryRegistrationClient.default_service_name)

    # Check to see if a service is already registered with our name
    services = directory_client.list()
    for s in services:
        if s.name == options.service_name:
            print("WARNING: existing service with name: \"" + options.service_name + "\"")

            if options.force:
                print("Removing that client...")
                directory_registration_client.unregister(options.service_name)
            else:
                print("Pass the --force option to remove that client.")
                print("Exit.")
                sys.exit(1)
            break

    # Register service
    print('Attempting to register ' + options.server_ip + ':' + options.server_port + ' onto ' +
          options.hostname + ' directory...')
    directory_registration_client.register(options.service_name,
                                           "bosdyn.api.NetworkComputeBridgeWorker",
                                           kServiceAuthority, options.server_ip,
                                           int(options.server_port))
    print('Done.')

    return True


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
