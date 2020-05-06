# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import getpass
import glob
import logging
import os
import six
import bosdyn.client.sdk

from .auth import InvalidLoginError
from .exceptions import Error

_LOGGER = logging.getLogger(__name__)


def cli_login_prompt(username=None, password=None):
    """Interactive CLI for scripting conveniences."""
    if username is None:
        username = six.moves.input('Username for robot: ')
    else:
        name = six.moves.input('Username for robot [{}]: '.format(username))
        if name:
            username = name

    password = password or getpass.getpass()
    return (username, password)


def cli_auth(robot, username=None, password=None):
    """Interactive CLI for authenticating with the robot."""
    successful = False
    while not successful:
        username, password = cli_login_prompt(username, password)
        try:
            robot.authenticate(username, password)
            successful = True
        except (InvalidLoginError, Error) as e:
            _LOGGER.exception(e)


def setup_logging(verbose=False):
    """Setup a basic streaming console handler at the root logger.

    Args:
       verbose: if False (default) show messages at INFO level and above,
                if True show messages at DEBUG level and above.
    """

    logger = get_logger()
    if logger.handlers:
        return  # Avoid duplicate formatters.

    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    streamlog = logging.StreamHandler()
    streamlog.setLevel(level)
    streamlog.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger = logging.getLogger()
    logger.addHandler(streamlog)
    logger.setLevel(level)


def get_logger():
    return logging.getLogger()


def default_app_token_path():
    """Returns a default app-token path, if a sensible option exists.  Otherwise, returns None."""
    glob_expr = os.path.join(bosdyn.client.sdk.BOSDYN_RESOURCE_ROOT, '*.app_token')
    candidates = sorted(f for f in glob.glob(glob_expr) if os.path.isfile(f))
    return candidates[0] if candidates else None


def add_common_arguments(parser):
    """Add arguments common to most applications.

    Args:
        parser: argument parser object.
    """
    default_app_token = None
    try:
        default_app_token = default_app_token_path()
    # In the unlikely case that anything here raises an exception, we'd like to know about it.
    except Exception:  # pylint: disable=broad-except
        setup_logging()
        _LOGGER.exception('Exception occurred while determining default application token!')
        _LOGGER.warning('Continuing to add parser arguments.')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print debug-level messages')
    parser.add_argument('--username', help='User name of account to get credentials for.')
    parser.add_argument('--password', help='Password to get credentials for.')
    parser.add_argument('--app-token', default=default_app_token, help='Application token')
    parser.add_argument('hostname', help='Hostname or address of robot,'
                        ' e.g. "beta25-p" or "192.168.80.3"')
