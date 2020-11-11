# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client for the log-annotation service (DEPRECATED).

The log-annotation service is deprecated and will be removed in a later release.
Instead, please use the data_buffer service going forward.
"""
from __future__ import print_function

import logging
import random
import string
import struct
import sys
import threading
import time
import traceback

from six.moves.queue import Queue

from bosdyn import util as core_util
from bosdyn.client.exceptions import Error, RpcError, ServerError
from bosdyn.client.common import BaseClient, common_header_errors
from bosdyn.client import time_sync
import bosdyn.api.log_annotation_pb2 as log_annotation_protos
import bosdyn.api.log_annotation_service_pb2_grpc as log_annotation_service


class InvalidArgument(Error):
    """A given argument could not be used."""


class LogAnnotationClient(BaseClient):
    """A client for adding annotations to robot logs (DEPRECATED).

    The log-annotation service is deprecated and will be removed in a later release.
    Instead, please use the data_buffer service going forward.
    """

    default_service_name = 'log-annotation'
    service_type = 'bosdyn.api.LogAnnotationService'

    def __init__(self):
        super(LogAnnotationClient, self).__init__(log_annotation_service.LogAnnotationServiceStub)
        self.log_tick_schemas = {}
        self._timesync_endpoint = None

    def update_from(self, other):
        super(LogAnnotationClient, self).update_from(other)

        # Grab a timesync endpoint if it is available.
        try:
            self._timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    def add_text_messages(self, text_messages, **kwargs):
        """Log text messages to the robot.

        Args:
          text_messages:  Sequence of LogAnnotationTextMessage protos.

        Raises:
          RpcError: Problem communicating with the robot.
        """
        return self._do_add_text_messages(self.call, text_messages, **kwargs)

    def add_text_messages_async(self, text_messages, **kwargs):
        """Async version of add_text_messages."""
        return self._do_add_text_messages(self.call_async, text_messages, **kwargs)

    def _do_add_text_messages(self, func, text_messages, **kwargs):
        request = log_annotation_protos.AddLogAnnotationRequest()
        for in_text_msg in text_messages:
            request.annotations.text_messages.add().CopyFrom(in_text_msg)

        return func(self._stub.AddLogAnnotation, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def add_operator_comment(self, msg, robot_timestamp=None, **kwargs):
        """Add an operator comment to the robot log.

        Args:
          msg:                  Text of user comment to log.
          robot_timestamp:      Time (google.protobuf.Timestamp) of messages, in *robot time*.
                                If not set, timestamp will be when the robot receives the message.

        Raises:
          RpcError: Problem communicating with the robot.
        """
        return self._do_add_operator_comment(self.call, msg, robot_timestamp, **kwargs)

    def add_operator_comment_async(self, msg, robot_timestamp=None, **kwargs):
        """Async version of add_operator_comment."""
        return self._do_add_operator_comment(self.call_async, msg, robot_timestamp, **kwargs)

    def _do_add_operator_comment(self, func, msg, robot_timestamp=None, **kwargs):
        request = log_annotation_protos.AddLogAnnotationRequest()
        robot_timestamp = robot_timestamp or self._now_in_robot_basis(msg_type="Operator Comment")
        request.annotations.operator_messages.add(message=msg, timestamp=robot_timestamp)
        return func(self._stub.AddLogAnnotation, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def add_log_blob(self, data, type_id, channel=None, robot_timestamp=None, **kwargs):
        """Log blob messages to the robot.

        Args:
          data:                 Binary data of one blob.
          type_id:              Type of binary data of blob.
          robot_timestamp:      Time (google.protobuf.Timestamp) of messages, in *robot time*.
                                If not set, timestamp will be when the robot receives the message.

        Raises:
          RpcError: Problem communicating with the robot.
        """
        return self._do_add_log_blob(self.call, data, type_id, channel, robot_timestamp, **kwargs)

    def add_log_blob_async(self, data, type_id, channel=None, robot_timestamp=None, **kwargs):
        """Async version of add_log_blob."""
        return self._do_add_log_blob(self.call_async, data, type_id, channel, robot_timestamp,
                                     **kwargs)

    def _do_add_log_blob(self, func, data, type_id, channel, robot_timestamp, **kwargs):
        request = log_annotation_protos.AddLogAnnotationRequest()

        if not channel:
            channel = type_id

        robot_timestamp = robot_timestamp or self._now_in_robot_basis(msg_type=type_id)
        request.annotations.blob_data.add(timestamp=robot_timestamp, channel=channel,
                                          type_id=type_id, data=data)

        return func(self._stub.AddLogAnnotation, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)


    def add_log_protobuf(self, proto, robot_timestamp=None):
        return self._do_add_log_protobuf(self.add_log_blob, proto, robot_timestamp)

    def add_log_protobuf_async(self, proto, robot_timestamp=None):
        return self._do_add_log_protobuf(self.add_log_blob_async, proto, robot_timestamp)

    def _do_add_log_protobuf(self, func, proto, robot_timestamp):
        binary_data = proto.SerializeToString()
        robot_timestamp = robot_timestamp or self._now_in_robot_basis(proto=proto)
        return func(data=binary_data, type_id=proto.DESCRIPTOR.full_name,
                    channel=proto.DESCRIPTOR.full_name, robot_timestamp=robot_timestamp)

    def _now_in_robot_basis(self, msg_type=None, proto=None):
        """Get current time in robot clock basis if possible, None otherwise."""
        if self._timesync_endpoint:
            try:
                converter = self._timesync_endpoint.get_robot_time_converter()
            except time_sync.NotEstablishedError:
                # No timesync. That's OK -- the receiving host will provide the timestamp.
                self.logger.debug('Could not timestamp message of type %s',
                                  (msg_type if msg_type is not None
                                   else (proto.DESCRIPTOR.full_name if proto is not None
                                         else 'Unknown')))
            else:
                return converter.robot_timestamp_from_local_secs(time.time())
        return None


class LogAnnotationHandler(logging.Handler):
    """A logging system Handler that will publish text to a bosdyn.api.LogAnnotationService.

    Args:
        service: Name of the service. See LogAnnotationTextMessage.
        log_client: API client that will send log messages.
        level: Python logging level. Defaults to NOTSET.
        time_sync_endpoint: A TimeSyncEndpoint, already synchronized to the remote clock.
        rpc_timeout: Timeout on RPCs made by log_client.
        msg_num_limit: If number of messages reaches this number, send data with log_client.
        msg_age_limit: If messages have been sitting locally for this many seconds, send data with
                       log_client.

    Raises:
        log_annotation.InvalidArgument: The TimeSyncEndpoint is not valid.
    """

    def __init__(self, service, log_client, level=logging.NOTSET, time_sync_endpoint=None,
                 rpc_timeout=1, msg_num_limit=10, msg_age_limit=1):
        logging.Handler.__init__(self, level=level)
        self.msg_age_limit = msg_age_limit
        self.msg_num_limit = msg_num_limit
        self.rpc_timeout = rpc_timeout
        self.service = service
        self.time_sync_endpoint = time_sync_endpoint
        if self.time_sync_endpoint and not self.time_sync_endpoint.has_established_time_sync:
            raise InvalidArgument('time_sync_endpoint must have already established timesync!')
        # If we have this many unsent messages in the queue after a failure to send,
        # "dump" the messages to stdout.
        self._dump_msg_count = 20
        # Internal tracking of errors.
        self._num_failed_sends = 0
        self._num_failed_sends_sequential = 0
        # If we have this many failed sends in a row, stop the send thread.
        self._limit_failed_sends_sequential = 5
        # Event to trigger immediate flush of messages to the log client.
        self._flush_event = threading.Event()
        # How long to wait for flush events. Dictates non-flush update rate.
        self._flush_event_wait_time = 0.1
        # Last time "emit" was called.
        self._last_emit_time = 0
        self._log_client = log_client
        self._lock = threading.Lock()
        self._msg_queue = []
        self._send_thread = threading.Thread(target=self._run_send_thread)
        # Set to stop the message send thread.
        self._shutdown_event = threading.Event()

        # This apparently needs to be a daemon thread to play nicely with python's Handler shutdown
        # procedure.
        self._send_thread.daemon = True
        self._send_thread.start()

    def __enter__(self):
        """Optionally use this as a ContextManager to be more cautious about sending messages."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """To ensure all messages have been sent to the best of our ability, call close()."""
        self.close()

    def emit(self, record):
        msg = self.record_to_msg(record)
        with self._lock:
            self._msg_queue.append(msg)
        self._last_emit_time = time.time()

    def flush(self):
        self._flush_event.set()

    def close(self):
        self._shutdown_event.set()
        self._send_thread.join()

        # One last attempt to send any messages.
        if self._msg_queue:
            try:
                self._log_client.add_text_messages(self._msg_queue, timeout=self.rpc_timeout)
            # Catch all client library errors.
            except Error:
                self._num_failed_sends += 1
                with self._lock:
                    self._dump_msg_queue()
        logging.Handler.close(self)

    def is_thread_alive(self):
        return self._send_thread.is_alive()

    def restart(self, log_client):
        """Restart the send thread.

        Raises:
          AssertionError if send thread is still alive.
        """
        assert not self.is_thread_alive()
        self._num_failed_sends_sequential = 0
        self._log_client = log_client
        self._send_thread = threading.Thread(target=self._run_send_thread)
        self._send_thread.daemon = True
        self._send_thread.start()

    def _dump_msg_queue(self):
        """Pop all of the message queue, using fallback_log to try and capture them.

        Should be called with the lock held.
        """
        self.fallback_log('Dumping {} messages!'.format(len(self._msg_queue)))
        for msg in self._msg_queue:
            self.fallback_log(msg)
        del self._msg_queue[:]

    def fallback_log(self, msg):
        print(msg, file=sys.stderr)

    def _run_send_thread(self):
        while (self._num_failed_sends_sequential < self._limit_failed_sends_sequential and
               not self._shutdown_event.is_set()):
            flush = self._flush_event.wait(self._flush_event_wait_time)
            msg_age = time.time() - self._last_emit_time
            with self._lock:
                num_msgs = len(self._msg_queue)
                to_send = self._msg_queue[:num_msgs]
            send_now = num_msgs >= 1 and (flush or msg_age >= self.msg_age_limit or
                                          num_msgs >= self.msg_num_limit)

            if send_now:
                self._flush_event.clear()

                send_errors = 0
                error_limit = 2

                sent = False
                while send_errors < error_limit and not self._shutdown_event.is_set():
                    try:
                        self._log_client.add_text_messages(to_send, timeout=self.rpc_timeout)
                    except (RpcError, ServerError):
                        self.fallback_log('Error:\n{}'.format(traceback.format_exc()))
                        send_errors += 1
                    except:
                        # Catch all other exceptions and log them.
                        self.fallback_log('Unexpected exception!\n{}'.format(
                            traceback.format_exc()))
                        break
                    else:
                        sent = True
                        break

                # Default to possibly dumping messages.
                maybe_dump = True
                if sent:
                    # We successfully sent logs to the log service! Delete relevant local cache.
                    with self._lock:
                        del self._msg_queue[:num_msgs]
                    maybe_dump = False
                    self._num_failed_sends_sequential = 0
                elif send_errors >= error_limit:
                    self._num_failed_sends += 1
                    self._num_failed_sends_sequential += 1
                elif self._shutdown_event.is_set():
                    # Don't dump if we're shutting down; we'll clear the messages in close().
                    maybe_dump = False
                else:
                    # We can hit this state if
                    # 1) We break out of the above loop without setting sent = True
                    # 2) There is a logic bug in the above handling code / while loop.
                    function_name = traceback.extract_stack()[-1][2]
                    self.fallback_log('Unexpected condition in {}.{}!'.format(
                        self.__class__.__name__, function_name))

                # If we decided we may need to dump the message queue...
                if maybe_dump:
                    with self._lock:
                        if len(self._msg_queue) >= self._dump_msg_count:
                            self._dump_msg_queue()

    def record_to_msg(self, record):
        level = self.record_level_to_proto_level(record.levelno)
        msg = log_annotation_protos.LogAnnotationTextMessage(service=self.service, level=level)
        msg.message = self.format(record)
        if self.time_sync_endpoint is not None:
            try:
                msg.timestamp.CopyFrom(
                    self.time_sync_endpoint.robot_timestamp_from_local_secs(time.time()))
            except time_sync.NotEstablishedError:
                msg.message = '(No time sync!): ' + msg.message
                msg.timestamp.CopyFrom(core_util.now_timestamp())
        else:
            msg.timestamp.CopyFrom(core_util.now_timestamp())
        return msg

    @staticmethod
    def record_level_to_proto_level(record_level):
        if record_level >= logging.ERROR:
            return log_annotation_protos.LogAnnotationTextMessage.LEVEL_ERROR
        elif record_level >= logging.WARNING:
            return log_annotation_protos.LogAnnotationTextMessage.LEVEL_WARN
        elif record_level >= logging.INFO:
            return log_annotation_protos.LogAnnotationTextMessage.LEVEL_INFO
        return log_annotation_protos.LogAnnotationTextMessage.LEVEL_DEBUG


