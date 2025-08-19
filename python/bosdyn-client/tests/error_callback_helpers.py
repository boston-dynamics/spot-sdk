# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import datetime
import threading
import time

from bosdyn.client.error_callback_result import ErrorCallbackResult


class SimpleCallback:
    """
    Callback that returns the specified result and tracks the callback time and passed error.
    """

    def __init__(self, result=ErrorCallbackResult.DEFAULT_ACTION, mock_time=None):
        """_summary_

        Args:
            result (ErrorCallbackResult, optional): The callback result to return to the caller.
                Defaults to ErrorCallbackResult.DEFAULT_ACTION.
            mock_time (Callable, optional): Instance of MockTime used for timing determinism in
                tests, or None to use the system clock. Defaults to None.
        """
        self.errors = []
        self.times = []
        self.result = result
        self.mock_time = mock_time or time

    def __call__(self, error):
        """
        Callback function provided to the unit under test.

        Args:
            error (Exception): The error that was passed to the callback.

        Returns:
            ErrorCallbackResult: The result returned to the unit under test.
        """
        self.errors.append(error)
        self.times.append(self.mock_time.time())
        return self.result


class PolicySwitchingCallback:
    """
    Callback that returns an initial policy for the first N iterations before switching to a final
    policy. Tracks the callback time and passed error.  This is useful for tests involving
    RETRY_IMMEDIATELY since these would result in an infinite loop in the test if the same result
    was returned every time.
    """

    def __init__(self, initial_policy, final_policy, iterations, mock_time=None):
        """_summary_

        Args:
            initial_policy (ErrorCallbackResult): The return value for the first N iterations.
            final_policy (ErrorCallbackResult): The return value to use for all subsequent
                iterations.
            iterations (int): The number of iterations to use the initial policy before switching to the final
                policy.
            mock_time (Callable, optional): Instance of MockTime used for timing determinism in
                tests, or None to use the system clock. Defaults to None.
        """
        self.errors = []
        self.times = []
        self.initial_policy = initial_policy
        self.final_policy = final_policy
        self.iterations = iterations
        self.mock_time = mock_time or time

    def __call__(self, error):
        """
        Callback function provided to the unit under test.

        Args:
            error (Exception): The error that was passed to the callback.

        Returns:
            ErrorCallbackResult: The result returned to the unit under test.
        """
        self.errors.append(error)
        self.times.append(self.mock_time.time())
        if len(self.times) <= self.iterations:
            return self.initial_policy
        return self.final_policy


def diff(vals):
    """Compute the difference between consecutive values in a list.

    Args:
        vals (List[float]): Values to compute the difference between.

    Returns:
        List[float]: List of differences between consecutive values.
    """
    return [b - a for a, b in zip(vals[:-1], vals[1:])]


class MockTime:
    """
    Stand-in for time and threading.wait to test the timing of various loops in a deterministic way.
    Units under test should have 'time' patched to an instance of this class and the threading Event
    used for thread exit should be patched with the same instance.

    Inside the loop under test, time() and wait() are called, where wait() advances the time by the
    waited amount, and time() returns the current simulated time.

    The loop is blocked until run() is called in the unit test. This allows the test to activate the
    error condition for testing without causing a race condition with the loop under test. run() also
    indicates the maximum simulated time the loop should run.
    """

    def __init__(self):
        self._time = 0.0
        self.max_time = None
        self._datetime_real = datetime.datetime
        # allow the loop to begin (awaited in wait())
        self._unblock_start = threading.Event()

    def time(self):
        """Return the simulated time in floating point seconds since epoch."""
        return self._time

    def now(self):
        """Return the simulated time as a datetime object."""
        return self._datetime_real.fromtimestamp(self._time)

    # methods to support the threading.Event interface
    def set(self):
        pass

    def clear(self):
        pass

    def is_set(self):
        return self.max_time is not None and self._time >= self.max_time

    def wait(self, wait_time):
        # Escape hatch in case unblock_start is never set.
        if not self._unblock_start.wait(1.0):
            raise RuntimeError("run() never called on MockTime instance")
        self._time = min(self._time + wait_time, self.max_time)
        return self.is_set()

    def run(self, test_duration_seconds):
        """
        Establish the test duration and unblock the loop under test.

        Args:
            test_duration_seconds (float): The amount of simulated time for the loop under test to run.
                When this time is reached, wait() will return True indicating that the loop under test
                should exit.
        """
        self.max_time = test_duration_seconds
        self._unblock_start.set()
