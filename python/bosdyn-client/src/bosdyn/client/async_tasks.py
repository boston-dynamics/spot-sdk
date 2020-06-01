# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Utilities for managing periodic tasks consisting of asynchronous GRPC calls."""
import abc
import time

import six

from grpc import RpcError

from .exceptions import ResponseError


class AsyncTasks(object):
    """Manages a set of tasks which work by periodically calling an update() method.

    Args:
        tasks: List of tasks to manage.
    """

    def __init__(self, tasks=None):
        self._tasks = tasks if tasks else []

    def add_task(self, task):
        """Add a task to be managed by this object.

        Args:
            task: Task to add.
        """
        self._tasks.append(task)

    def update(self):
        """Call this periodically to manage execution of tasks owned by this object."""
        for task in self._tasks:
            task.update()


@six.add_metaclass(abc.ABCMeta)  # pylint: disable=too-few-public-methods
class AsyncGRPCTask(object):
    """Task to be accomplished using asynchronous GRPC calls.

    When it is time to run the task, an async GRPC call is run resulting in a FutureWrapper object.
    The FutureWrapper is monitored for completion, and then an action is taken in response.
    """

    def __init__(self):
        self._last_call = 0
        self._future = None

    @abc.abstractmethod
    def _start_query(self):
        """Override to start async grpc query and return future-wrapper for result."""

    @abc.abstractmethod
    def _should_query(self, now_sec):
        """Called on update() when no query is running to determine whether to start a new query.

        Args:
            now_sec: Time now in seconds.

        Overrride to return True when a new query should be started.
        """

    @abc.abstractmethod
    def _handle_result(self, result):
        """Override to handle result of grpc query when it is available.

        Args:
            result: Result to handle.
        """

    @abc.abstractmethod
    def _handle_error(self, exception):
        """Override to handle any exception raised in handling GRPC result.

        Args:
            exception: Error exception to handle.
        """

    def update(self):
        """Call this periodically to manage execution of task represented by this object."""
        now_sec = time.time()
        if self._future is not None:
            if self._future.original_future.done():
                try:
                    self._handle_result(self._future.result())
                except (RpcError, ResponseError) as err:
                    self._handle_error(err)
                self._future = None
        elif self._should_query(now_sec):
            self._last_call = now_sec
            self._future = self._start_query()


# pylint: disable=too-few-public-methods
@six.add_metaclass(abc.ABCMeta)
class AsyncPeriodicGRPCTask(AsyncGRPCTask):
    """Periodic task to be accomplished using asynchronous GRPC calls.

    When it is time to run the task, an async GRPC call is run resulting in a FutureWrapper object.
    The FutureWrapper is monitored for completion, and then an action is taken in response.

    Args:
        periodic_sec: Time to wait in seconds between queries.
    """

    def __init__(self, period_sec):
        super(AsyncPeriodicGRPCTask, self).__init__()
        self._period_sec = period_sec

    def _should_query(self, now_sec):
        """Check if it is time to query again.

        Args:
            now_sec: Time now in seconds.

        Returns:
            True if it is time to query again based on now_sec, False otherwise.
        """
        return (now_sec - self._last_call) > self._period_sec

    @abc.abstractmethod
    def _start_query(self):
        """Override to start async grpc query and return future-wrapper for result."""

    @abc.abstractmethod
    def _handle_result(self, result):
        """Override to handle result of grpc query when it is available.

        Args:
            result: Result to handle.
        """

    @abc.abstractmethod
    def _handle_error(self, exception):
        """Override to handle any exception raised in handling GRPC result.

        Args:
            exception: Error exception to handle.
        """


class AsyncPeriodicQuery(AsyncPeriodicGRPCTask):
    """Query for robot data at some regular interval.

    Args:
        query_name: Name of the query.
        client: SDK client for the query.
        logger: Logger to use for logging errors.
        periodic_sec: Time in seconds between running the query.
    """

    def __init__(self, query_name, client, logger, period_sec):
        super(AsyncPeriodicQuery, self).__init__(period_sec)
        self._query_name = query_name
        self._client = client
        self._logger = logger
        self._proto = None

    @abc.abstractmethod
    def _start_query(self):
        """Override to start async grpc query and return future-wrapper for result."""

    @property
    def proto(self):
        """Get latest response proto."""
        return self._proto

    def _handle_result(self, result):
        """Handle result of grpc query when it is available.

        Args:
            result: Result to handle.
        """
        self._proto = result

    def _handle_error(self, exception):
        """Log exception.

        Args:
            exception: Error exception to log.
        """
        self._logger.exception("Failure getting %s: %s", self._query_name, exception)
