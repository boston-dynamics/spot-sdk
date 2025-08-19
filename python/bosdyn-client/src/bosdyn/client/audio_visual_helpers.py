# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import logging
import threading
import time
from concurrent.futures import Future

import bosdyn.client
from bosdyn.api import audio_visual_pb2
from bosdyn.client.audio_visual import (AudioVisualClient, BehaviorExpiredError, DoesNotExistError,
                                        InvalidClientError)

_LOGGER = logging.getLogger(__name__)


class AudioVisualHelper:
    """Context manager that runs an AV behavior for the duration of the context.

    Use as follows:

    .. code-block:: python

        with AudioVisualHelper(robot, behavior_name, refresh_rate):
            # Lights and sounds will play here
        # Lights and sounds will stop here.

    Args:
        robot: Robot object for creating clients
        behavior_name: Name of the desired behavior to run
        refresh_rate: What rate to refresh the behavior (seconds)
    """

    def __init__(self, robot, behavior_name, refresh_rate, logger=None):
        self.robot = robot
        self.logger = logger
        self.behavior_name = behavior_name
        self.refresh_rate = refresh_rate
        self.av_client = None
        self._behavior_running_fut = None

        try:
            self.av_client = robot.ensure_client(AudioVisualClient.default_service_name)
        except:
            _LOGGER.warning("Could not initialize AV client, skipping AudioVisualHelper.")

        self.av_thread = None
        self.stop_event = threading.Event()

    def __enter__(self):
        self._behavior_running_fut = Future()
        self._behavior_running_fut.set_running_or_notify_cancel()

        if self.av_client:
            self.av_thread = threading.Thread(target=self._run_behavior_thread, args=())
            self.av_thread.start()
        else:
            self._behavior_running_fut.set_result(False)

        return self._behavior_running_fut

    def __exit__(self, exc_type, exc_value, tb):
        if self.av_thread:
            self.stop_event.set()
            self.av_thread.join()

    def _run_behavior_thread(self):
        # Check if the robot has AV hardware
        if not self.robot.get_cached_hardware_hardware_configuration().has_audio_visual_system:
            self._behavior_running_fut.set_result(False)
            return

        def set_future_result(result):
            if not self._behavior_running_fut.done():
                self._behavior_running_fut.set_result(result)

        def set_future_exception(exc):
            if not self._behavior_running_fut.done():
                self._behavior_running_fut.set_exception(exc)

        # Run the AV behavior until the stop_event is triggered
        while not self.stop_event.wait(self.refresh_rate):
            try:
                end_time_secs = time.time() + self.refresh_rate + 0.10  # add 100ms margin
                result = self.av_client.run_behavior(self.behavior_name, end_time_secs)
                set_future_result(
                    result.run_result == audio_visual_pb2.RunBehaviorResponse.RESULT_BEHAVIOR_RUN)
            except DoesNotExistError as exc:
                set_future_exception(exc)
                _LOGGER.exception(f'Audio Visual Behavior {self.behavior_name} does not exist.')
                return  # Since the behavior doesn't exist, we can stop trying to run it
            except BehaviorExpiredError as exc:
                set_future_exception(exc)
                _LOGGER.warning('Behavior was expired when received by client.')
            except bosdyn.client.PersistentRpcError as exc:
                set_future_exception(exc)
                _LOGGER.exception('Failed to run behavior. Quitting AudioVisualHelper.')
                return  # A persistent error means we can't talk to the AV service, we can stop.
            except bosdyn.client.RpcError:
                _LOGGER.exception('Failed to run behavior. Retrying.')
            except bosdyn.client.Error as exc:
                set_future_exception(exc)
                _LOGGER.exception('Unknown exception caught, quitting AudioVisualHelper.')
                return

        try:
            self.av_client.stop_behavior(self.behavior_name)
        except InvalidClientError:
            _LOGGER.warning('Failed to stop behavior, run by a different client.')