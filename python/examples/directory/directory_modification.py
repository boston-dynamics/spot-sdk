# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""
Example code for using the directory (registration) service API
"""
from __future__ import print_function

import argparse
import io
import logging
import struct
import sys
import time

import bosdyn.api.directory_pb2 as directory_protos
import bosdyn.api.directory_registration_pb2 as directory_registration_protos
import bosdyn.client.directory
import bosdyn.client.directory_registration
import bosdyn.client.util


def directory_spot(config):
    """A simple example of using the Boston Dynamics API to read/modify service configs with spot.

    Lists all known services with a robot, adds a service, lists all, modifies the service, lists
    all, deletes the service, lists all.
    """
    sdk = bosdyn.client.create_standard_sdk("directory_example")

    robot = sdk.create_robot(config.hostname)

    # Authenticate robot before being able to use it
    bosdyn.client.util.authenticate(robot)

    directory_client = robot.ensure_client(
        bosdyn.client.directory.DirectoryClient.default_service_name)
    directory_registration_client = robot.ensure_client(
        bosdyn.client.directory_registration.DirectoryRegistrationClient.default_service_name)

    kServiceName = "foo-service"
    kServiceAuthority = "auth.spot.robot"
    kServiceIp = "192.168.50.5"
    kServicePort = 52789

    print_services(directory_client.list())
    # Register service
    directory_registration_client.register(kServiceName, "bosdyn.api.FooService", kServiceAuthority,
                                           kServiceIp, kServicePort)
    print_services(directory_client.list())

    # Update service
    directory_registration_client.update(kServiceName, "bosdyn.api.BarService", kServiceAuthority,
                                         kServiceIp, kServicePort)
    print_services(directory_client.list())

    # Unregister service
    directory_registration_client.unregister(kServiceName)
    print_services(directory_client.list())


def print_services(services):
    print('\n\nServices running on robot:')
    for s in services:
        print('{: <20}\t{: <20}'.format(s.name, s.authority))


def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    options = parser.parse_args(argv)

    directory_spot(options)

    return True


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
