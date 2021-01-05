# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tutorial to show how to use the Boston Dynamics API"""
from __future__ import print_function
import argparse
import sys

import bosdyn.api.data_index_pb2 as data_index_protos
import bosdyn.client
from bosdyn.client.data_service import DataServiceClient
import bosdyn.client.util


def get_comments(config):
    """Get comments from robot"""

    bosdyn.client.util.setup_logging(config.verbose)
    sdk = bosdyn.client.create_standard_sdk('GetCommentsClient')
    robot = sdk.create_robot(config.hostname)
    robot.authenticate(config.username, config.password)
    service_client = robot.ensure_client(DataServiceClient.default_service_name)
    query = data_index_protos.EventsCommentsSpec()
    query.comments = True
    print(service_client.get_events_comments(query))

def main(argv):
    """Command line interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_common_arguments(parser)
    options = parser.parse_args(argv)
    try:
        get_comments(options)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger = bosdyn.client.util.get_logger()
        logger.error("get_comments threw an exception: %r", exc)
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
