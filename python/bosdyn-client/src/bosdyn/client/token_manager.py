# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
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
from .error_callback_result import ErrorCallbackResult
from .exceptions import ResponseError, RpcError, TimedOutError
from .token_cache import WriteFailedError

_LOGGER = logging.getLogger(__name__)

USER_TOKEN_REFRESH_TIME_DELTA = datetime.timedelta(hours=1)
USER_TOKEN_RETRY_INTERVAL_START = datetime.timedelta(seconds=1)


class TokenManager:
    """Refreshes the user token in the robot object.

       The refresh policy assumes the token is minted and then the manager is
       launched."""

    def __init__(self, robot, timestamp=None, refresh_interval=USER_TOKEN_REFRESH_TIME_DELTA,
                 initial_retry_interval=USER_TOKEN_RETRY_INTERVAL_START):
        self.robot = robot

        self._last_timestamp = timestamp or datetime.datetime.now()
        self._refresh_interval = refresh_interval
        self._initial_retry_seconds = initial_retry_interval

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
        retry_interval = self._initial_retry_seconds
        wait_time = min(self._refresh_interval - (datetime.datetime.now() - self._last_timestamp),
                        self._refresh_interval)

        while not self._exit_thread.wait(wait_time.total_seconds()):
            start_time = datetime.datetime.now()
            action = ErrorCallbackResult.RESUME_NORMAL_OPERATION
            try:
                self.robot.authenticate_with_token(self.robot.user_token)
                self._last_timestamp = datetime.datetime.now()
            except WriteFailedError:
                _LOGGER.exception(
                    "Failed to save the token to the cache.  Continuing without caching.")
            except (InvalidTokenError, ResponseError, RpcError) as exc:
                _LOGGER.exception("Error refreshing the token.")
                # Default course of action is to retry with a back-off, unless the application
                # supplied callback directs us to do otherwise.
                action = ErrorCallbackResult.RETRY_WITH_EXPONENTIAL_BACK_OFF
                # If the application provided a callback and the error was encountered while
                # refreshing the token, invoke the callback so that the application can take
                # appropriate action.
                if self.robot.token_refresh_error_callback is not None and not isinstance(
                        exc, TimedOutError):
                    try:
                        action = self.robot.token_refresh_error_callback(exc)
                    except Exception:  #pylint: disable=broad-except
                        _LOGGER.exception(
                            "Exception thrown in the provided token refresh error callback")
                if action == ErrorCallbackResult.RESUME_NORMAL_OPERATION:
                    _LOGGER.warning("Refreshing token in %s", self._refresh_interval)

            elapsed = datetime.datetime.now() - start_time
            if action == ErrorCallbackResult.ABORT:
                _LOGGER.warning(
                    "Application-supplied callback directed the token refresh loop to exit.")
                break
            elif action == ErrorCallbackResult.RETRY_IMMEDIATELY:
                _LOGGER.warning("Retrying to refresh token immediately.")
                wait_time = datetime.timedelta(seconds=0)
            elif action == ErrorCallbackResult.RESUME_NORMAL_OPERATION:
                wait_time = self._refresh_interval - elapsed
                retry_interval = self._initial_retry_seconds
            else:
                # action doesn't match one of the enum values or is one of
                # RETRY_WITH_EXPONENTIAL_BACK_OFF or DEFAULT_ACTION
                _LOGGER.warning("Retrying token refresh in %s", retry_interval)
                wait_time = retry_interval - elapsed
                retry_interval = min(2 * retry_interval, self._refresh_interval)

        message = 'Shutting down monitoring of token belonging to robot {}'.format(
            self.robot.address)
        _LOGGER.debug(message)
