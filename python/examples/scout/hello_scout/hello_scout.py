# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

'''Tutorial to show how to use the Scout client to interact with Scout through the Boston Dynamics Scout API.'''

import argparse
import logging
import sys

from bosdyn.scout.client import ScoutClient

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
log_format = "Hello, Scout!: %(levelname)s - %(message)s"
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter(log_format))
LOGGER.addHandler(ch)


def hello_scout(options):
    ''' A simple example to show how to use the Scout client to get information on the connected robots.
        - Args:
            - options(Namespace) : parsed args used for configuration options
        - Raises:
            - RequestExceptions: exceptions thrown by the Requests library 
            - UnauthenticatedScoutClientError: indicates that the scout client is not authenticated properly
        - Returns 
            - Boolean to indicate whether the function succeeded or not
    '''
    # Determine the value for the argument "verify"
    if options.verify in ["True", "False"]:
        verify = (options.verify == "True")
    else:
        LOGGER.info(
            "The provided value for the argument verify [{}] is not either 'True' or 'False'. Assuming verify is set to 'path/to/CA bundle'"
            .format(options.verify))
        verify = options.verify
    # A Scout client object represents a single Scout instance.
    scout_client = ScoutClient(hostname=options.hostname, verify=verify, cert=options.cert)
    # The Scout client needs to be authenticated before using its functions
    scout_client.authenticate_with_password()
    # Get all the robots currently configured on the specified Scout instance
    get_robots_response = scout_client.get_robots()
    if not get_robots_response.ok:
        LOGGER.error('get_robots() failed: {}'.format(get_robots_response.text))
        return False
    # Get the json form of the get_robots_response
    all_robots_on_scout = get_robots_response.json()
    # Query for the nicknames of the robots on Scout
    robot_nicknames = []
    for robot in all_robots_on_scout:
        robot_nickname = robot.get('nickname')
        if robot_nickname is not None:
            robot_nicknames.append(robot_nickname)
    LOGGER.info("Here are the robots connected to the Scout instance {}: {}".format(
        options.hostname, robot_nicknames))
    return True


def main(argv):
    '''Command line interface.'''
    parser = argparse.ArgumentParser()
    parser.add_argument('-hostname', help='IP address associated with the Scout instance',
                        required=True, type=str)
    parser.add_argument(
        '-verify',
        help=
        'verify(path to a CA bundle or Boolean): controls whether we verify the server’s TLS certificate',
        default=True,
    )
    parser.add_argument(
        '-cert', help=
        "(a .pem file or a tuple with ('cert', 'key') pair): a local cert to use as client side certificate ",
        nargs='+', default=None)
    options = parser.parse_args(argv)
    try:
        return hello_scout(options)
    except Exception as exc:
        LOGGER.error('Hello, Scout! threw an exception: %r', exc)
        return False


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
