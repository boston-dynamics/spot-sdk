# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""For clients to automate token refresh.

TokenManager -- Wrapper around token fresh policy.
"""

import datetime
import logging
import threading

from .auth import InvalidTokenError
from .exceptions import (ResponseError, RpcError)
from .token_cache import WriteFailedError

_LOGGER = logging.getLogger(__name__)


class TokenManager:
    """Refreshes the user token in the robot object.

       The refresh policy assumes the token is minted and then the manager is
       launched."""

    def __init__(self, robot, timestamp=None):
        self.robot = robot

        self._last_timestamp = timestamp or datetime.datetime.now()

        # Daemon threads can still run during shutdown after python has
        # started to clear out things in globals().
        # Fixed in Python3: https://bugs.python.org/issue1856
        # Do not use threading.Timer or sleep() because that will slow down
        # real time services.  Use a thread instead.
        self._exit_thread = threading.Event()
        self._exit_thread.clear()

        self.th = threading.Thread(name='token_manager', target=self.update)
        self.th.daemon = True
        self.th.start()

    def is_alive(self):
        return self.th.is_alive()

    def stop(self):
        self._exit_thread.set()

    def update(self):
        """Refresh the user token as needed."""
        USER_TOKEN_REFRESH_TIME_DELTA = datetime.timedelta(hours=1)
        USER_TOKEN_RETRY_INTERVAL_START = datetime.timedelta(seconds=1)

        retry_interval = USER_TOKEN_RETRY_INTERVAL_START
        while not self._exit_thread.is_set():
            elapsed_time = datetime.datetime.now() - self._last_timestamp
            if elapsed_time >= USER_TOKEN_REFRESH_TIME_DELTA:
                try:
                    self.robot.authenticate_with_token(self.robot.user_token)
                except WriteFailedError:
                    _LOGGER.exception("Failed to save the token to the cache.  Continuing without caching.")
                except (InvalidTokenError, ResponseError, RpcError):
                    _LOGGER.exception("Error refreshing the token.  Retry in %s", retry_interval)

                    # Exponential back-off on retrying
                    self._exit_thread.wait(retry_interval.seconds)
                    retry_interval = min(2 * retry_interval, USER_TOKEN_REFRESH_TIME_DELTA)
                    continue

                retry_interval = USER_TOKEN_RETRY_INTERVAL_START

                # Wait until the specified time or get interrupted by user.
                self._last_timestamp = datetime.datetime.now()
                elapsed_time = USER_TOKEN_REFRESH_TIME_DELTA

            self._exit_thread.wait(elapsed_time.seconds)
        message = 'Shutting down monitoring of token belonging to robot {}'.format(
            self.robot.address)
        _LOGGER.debug(message)
