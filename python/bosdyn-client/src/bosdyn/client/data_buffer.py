# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Client for the data-buffer service.

This allows client code to log the following to the robot's data buffer: text-messages,
operator comments, blobs, signal ticks, and protobuf messages.
"""

from __future__ import print_function

import functools
import logging
import sys
import threading
import time
import traceback
import uuid

from google.protobuf.duration_pb2 import Duration
from google.protobuf.timestamp_pb2 import Timestamp

import bosdyn.api.data_buffer_pb2 as data_buffer_protos
import bosdyn.api.data_buffer_service_pb2_grpc as data_buffer_service
from bosdyn import util as core_util
from bosdyn.api import parameter_pb2
from bosdyn.client import time_sync
from bosdyn.client.common import BaseClient, common_header_errors
from bosdyn.client.exceptions import Error, ResponseError, RpcError


class InvalidArgument(Error):
    """A given argument could not be used."""


def log_event(  # pylint: disable=too-many-arguments,no-member
        robot, event_type, level, description, start_timestamp_secs, end_timestamp_secs=None,
        id_str=None, parameters=None,
        log_preserve_hint=data_buffer_protos.Event.LOG_PRESERVE_HINT_NORMAL):
    """Add an Event to the Data Buffer.

    Args:
      robot:                          A Robot object.
      event_type (string):            The type of event.
      level (bosdyn.api.Event.Level): The relative importance of the event.
      description (string):           A human-readable description of the event.
      start_timestamp_secs (float):   Start of the event, in local time.
      end_timestamp_secs (float):     End of the event.  start_timestamp_secs is used if None.
      id_str (string):                      Unique id for event.  A uuid is generated if None.
      parameters ([bosdyn.api.Parameter]):  Parameters to attach to the event.
      log_preserve_hint (bosdyn.api.LogPreserveHint): Whether event should try to preserve log data.
    """

    data_buffer_client = robot.ensure_client(DataBufferClient.default_service_name)

    if not id_str:
        id_str = str(uuid.uuid1())

    robot.time_sync.wait_for_sync()
    robot_start_timestamp = robot.time_sync.robot_timestamp_from_local_secs(start_timestamp_secs)
    if end_timestamp_secs:
        robot_end_timestamp = robot.time_sync.robot_timestamp_from_local_secs(end_timestamp_secs)
    else:
        robot_end_timestamp = robot_start_timestamp

    # pylint: disable=no-member
    if isinstance(log_preserve_hint, bool):
        if log_preserve_hint:
            log_preserve_hint = data_buffer_protos.Event.LOG_PRESERVE_HINT_PRESERVE
        else:
            log_preserve_hint = data_buffer_protos.Event.LOG_PRESERVE_HINT_NORMAL

    event = data_buffer_protos.Event(type=event_type, description=description,
                                     source=robot.client_name, id=id_str,
                                     start_time=robot_start_timestamp, end_time=robot_end_timestamp,
                                     level=level, log_preserve_hint=log_preserve_hint)

    if parameters:
        for parameter in parameters:
            proto = event.parameters.add()
            proto.CopyFrom(parameter)

    data_buffer_client.add_events([event])


def make_parameter(label, value, units="", notes=""):
    """Create a parameter proto from a label and the parameter value."""
    parameter = parameter_pb2.Parameter(label=label, units=units, notes=notes)
    if isinstance(value, bool):
        parameter.bool_value = value
    elif isinstance(value, int):
        parameter.int_value = value
    elif isinstance(value, float):
        parameter.float_value = value
    elif isinstance(value, Timestamp):
        parameter.timestamp.CopyFrom(value)
    elif isinstance(value, Duration):
        parameter.duration.CopyFrom(value)
    elif isinstance(value, str):
        parameter.string_value = value
    else:
        return None

    return parameter


class DataBufferClient(BaseClient):
    """A client for adding to robot data buffer."""

    default_service_name = 'data-buffer'
    service_type = 'bosdyn.api.DataBufferService'

    def __init__(self):
        super(DataBufferClient, self).__init__(data_buffer_service.DataBufferServiceStub)
        self.log_tick_schemas = {}
        self._timesync_endpoint = None

    def update_from(self, other):
        super(DataBufferClient, self).update_from(other)

        # Grab a timesync endpoint if it is available.
        try:
            self._timesync_endpoint = other.time_sync.endpoint
        except AttributeError:
            pass  # other doesn't have a time_sync accessor

    def add_text_messages(self, text_messages, **kwargs):
        """Log text messages to the robot.

        Args:
            text_messages (List[TextMessage]):  Sequence of TextMessage protos.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        return self._do_add_text_messages(self.call, text_messages, **kwargs)

    def add_text_messages_async(self, text_messages, **kwargs):
        """Async version of add_text_messages."""
        return self._do_add_text_messages(self.call_async, text_messages, **kwargs)

    def _do_add_text_messages(self, func, text_messages, **kwargs):
        """Internal text message RPC stub call."""
        request = data_buffer_protos.RecordTextMessagesRequest()
        for in_text_msg in text_messages:
            # pylint: disable=no-member
            request.text_messages.add().CopyFrom(in_text_msg)

        return func(self._stub.RecordTextMessages, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def add_operator_comment(self, msg, robot_timestamp=None, **kwargs):
        """Add an operator comment to the robot log.

        Args:
            msg (string): Text of user comment to log.
            robot_timestamp(google.protobuf.Timestamp): Time of messages, in *robot time*.
                If not set, timestamp will be when the robot receives the message.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        return self._do_add_operator_comment(self.call, msg, robot_timestamp, **kwargs)

    def add_operator_comment_async(self, msg, robot_timestamp=None, **kwargs):
        """Async version of add_operator_comment."""
        return self._do_add_operator_comment(self.call_async, msg, robot_timestamp, **kwargs)

    def _do_add_operator_comment(self, func, msg, robot_timestamp=None, **kwargs):
        """Internal operator comment RPC stub call."""
        request = data_buffer_protos.RecordOperatorCommentsRequest()
        robot_timestamp = robot_timestamp or self.now_in_robot_basis(msg_type="Operator Comment")
        # pylint: disable=no-member
        request.operator_comments.add(message=msg, timestamp=robot_timestamp)
        return func(self._stub.RecordOperatorComments, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def add_blob(self, data, type_id, channel=None, robot_timestamp=None, write_sync=False,
                 **kwargs):
        """Log blob messages to the data buffer.

        Args:
            data (bytes): Binary data of one blob.
            type_id (string): Type of binary data of blob. For example, this could
                               be the full name of a protobuf message type.
            channel (string): The name by which messages are typically queried:
                               often the same as type_id, or of the form
                               '{prefix}/{type_id}'.
            robot_timestamp (google.protobuf.Timestamp): Time of messages, in *robot time*.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        return self._do_add_blob(self.call, data, type_id, channel, robot_timestamp, write_sync,
                                 **kwargs)

    def add_blob_async(self, data, type_id, channel=None, robot_timestamp=None, write_sync=False,
                       **kwargs):
        """Async version of add_blob."""
        return self._do_add_blob(self.call_async, data, type_id, channel, robot_timestamp,
                                 write_sync, **kwargs)

    def _do_add_blob(  # pylint: disable=too-many-arguments
            self, func, data, type_id, channel, robot_timestamp, write_sync, **kwargs):
        """Internal blob RPC stub call."""
        request = data_buffer_protos.RecordDataBlobsRequest()

        if not channel:
            channel = type_id

        robot_timestamp = robot_timestamp or self.now_in_robot_basis(msg_type=type_id)

        request.blob_data.add(  # pylint: disable=no-member
            timestamp=robot_timestamp, channel=channel, type_id=type_id, data=data)

        request.sync = write_sync

        return func(self._stub.RecordDataBlobs, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def add_protobuf(self, proto, channel=None, robot_timestamp=None, write_sync=False):
        """Log protobuf messages to the data buffer.

        Args:
          proto (Protobuf message): Serializable protobuf to log.
          channel (string): Name of channel for data.  If not set defaults to proto type name.
          robot_timestamp (google.protobuf.Timestamp): Time of proto, in *robot time*.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        return self._do_add_protobuf(self.add_blob, proto, channel, robot_timestamp, write_sync)

    def add_protobuf_async(self, proto, channel=None, robot_timestamp=None, write_sync=False):
        """Async version of add_protobuf."""
        return self._do_add_protobuf(self.add_blob_async, proto, channel, robot_timestamp,
                                     write_sync)

    def _do_add_protobuf(self, func, proto, channel, robot_timestamp, write_sync):
        """Internal blob stub call, serializes proto and logs as blob."""
        binary_data = proto.SerializeToString()
        robot_timestamp = robot_timestamp or self.now_in_robot_basis(proto=proto)
        type_id = proto.DESCRIPTOR.full_name
        channel = channel or type_id
        return func(data=binary_data, type_id=type_id, channel=channel,
                    robot_timestamp=robot_timestamp, write_sync=write_sync)

    def add_events(self, events, **kwargs):
        """Log event messages to the robot.

        Args:
            events (List[Event]): Sequence of Event protos.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        return self._do_add_events(self.call, events, **kwargs)

    def add_events_async(self, events, **kwargs):
        """Async version of add_events."""
        return self._do_add_events(self.call_async, events, **kwargs)

    def _do_add_events(self, func, events, **kwargs):
        """Internal event stub call."""
        request = data_buffer_protos.RecordEventsRequest()

        for event in events:
            request.events.add().CopyFrom(event)  # pylint: disable=no-member

        return func(self._stub.RecordEvents, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def register_signal_schema(self, variables, schema_name, **kwargs):
        """Log signal schema to the robot.

        Args:
            variables (List[SignalSchema.Variable]): List of SignalSchema variables
                                                      defining what is in tick.
            schema_name (string): Name of schema (defined previously by client).

        Raises:
            RpcError: Problem communicating with the robot.
        """
        return self._do_register_signal_schema(self.call, variables, schema_name, **kwargs)

    def register_signal_schema_async(self, variables, schema_name, **kwargs):
        """Async version of register_signal_schema"""
        return self._do_register_signal_schema(self.call_async, variables, schema_name, **kwargs)

    def _do_register_signal_schema(self, func, variables, schema_name, **kwargs):
        """Internal register stub call."""
        tick_schema = data_buffer_protos.SignalSchema(vars=variables, schema_name=schema_name)
        request = data_buffer_protos.RegisterSignalSchemaRequest()
        request.schema.CopyFrom(tick_schema)  # pylint: disable=no-member
        # Schemas are saved internally, according to their schema ID. We need to wait for the
        # response from the server to get the schema id. The response does not include the schema
        # itself so use a partial to process the response appropriately.
        value_from_response = functools.partial(self._save_schema_id, tick_schema)
        return func(self._stub.RegisterSignalSchema, request,
                    value_from_response=value_from_response,
                    error_from_response=common_header_errors, **kwargs)

    def add_signal_tick(  # pylint: disable=too-many-arguments,no-member
            self, data, schema_id, encoding=data_buffer_protos.SignalTick.ENCODING_RAW,
            sequence_id=0, source="client", **kwargs):
        """Log signal data to the robot data buffer.

        Schema should be sent before any ticks.

        Args:
            data (bytes): Single hunk of binary data.
            schema_id (int): ID name of schema (obtained from a previous schema registration)
            encoding (SignalTick.Encoding): Encoding of the data
            sequence_id (int): Index of which sequence tick this is
            source (string): String name representing client

        Raises:
            RpcError:       Problem communicating with the robot.
            LookupError:    The schema_id is unknown (not previously registered by this client)
        """
        return self._do_add_signal_tick(self.call, data, schema_id, encoding, sequence_id, source,
                                        **kwargs)

    def add_signal_tick_async(  # pylint: disable=too-many-arguments,no-member
            self, data, schema_id, encoding=data_buffer_protos.SignalTick.ENCODING_RAW,
            sequence_id=0, source="client", **kwargs):
        """Async version of add_signal_tick."""
        return self._do_add_signal_tick(self.call_async, data, schema_id, encoding, sequence_id,
                                        source, **kwargs)

    def _do_add_signal_tick(  # pylint: disable=too-many-arguments
            self, func, data, schema_id, encoding, sequence_id, source, **kwargs):
        """Internal add signal tick stub call."""
        if schema_id not in self.log_tick_schemas:
            raise LookupError('The log tick schema id "{}" is unknown'.format(schema_id))

        request = data_buffer_protos.RecordSignalTicksRequest()
        request.tick_data.add(  # pylint: disable=no-member
            sequence_id=sequence_id, source=source, schema_id=schema_id, encoding=encoding,
            data=data)
        return func(self._stub.RecordSignalTicks, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def _save_schema_id(self, schema, response):
        """Return schema id from response, after saving the schema in a dict indexed by id."""
        self.log_tick_schemas[response.schema_id] = schema
        return response.schema_id

    def now_in_robot_basis(self, msg_type=None, proto=None):
        """Get current time in robot clock basis if possible, None otherwise."""
        if self._timesync_endpoint:
            try:
                converter = self._timesync_endpoint.get_robot_time_converter()
            except time_sync.NotEstablishedError:
                # No timesync. That's OK -- the receiving host will provide the timestamp.
                self.logger.debug(
                    'Could not timestamp message of type %s',
                    (msg_type if msg_type is not None else
                     (proto.DESCRIPTOR.full_name if proto is not None else 'Unknown')))
            else:
                return converter.robot_timestamp_from_local_secs(time.time())
        return None


class LoggingHandler(logging.Handler):  # pylint: disable=too-many-instance-attributes
    """A logging system Handler that will publish text to a the data-buffer service.

    Args:
        service: Name of the service. See LogAnnotationTextMessage.
        data_buffer_client: API client that will send log messages.
        level: Python logging level. Defaults to NOTSET.
        time_sync_endpoint: A TimeSyncEndpoint, already synchronized to the remote clock.
        rpc_timeout: Timeout on RPCs made by data_buffer_client.
        msg_num_limit: If number of messages reaches this number, send data with data_buffer_client.
        msg_age_limit: If messages have been sitting locally for this many seconds, send data with
                       data_buffer_client.

    Raises:
        log_annotation.InvalidArgument: The TimeSyncEndpoint is not valid.
    """

    def __init__(  # pylint: disable=too-many-arguments
            self, service, data_buffer_client, level=logging.NOTSET, time_sync_endpoint=None,
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
        self._data_buffer_client = data_buffer_client
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
                self._data_buffer_client.add_text_messages(self._msg_queue,
                                                           timeout=self.rpc_timeout)
            # Catch all client library errors.
            except Error:
                self._num_failed_sends += 1
                with self._lock:
                    self._dump_msg_queue()
        logging.Handler.close(self)

    def is_thread_alive(self):
        """Return true if send-thread is running."""
        return self._send_thread.is_alive()

    def restart(self, data_buffer_client):
        """Restart the send thread.

        Raises:
          AssertionError if send thread is still alive.
        """
        assert not self.is_thread_alive()
        self._num_failed_sends_sequential = 0
        self._data_buffer_client = data_buffer_client
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

    @staticmethod
    def fallback_log(msg):
        """Handle log messages that were failed to be sent by printing to the console."""
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
                        self._data_buffer_client.add_text_messages(to_send,
                                                                   timeout=self.rpc_timeout)
                    except (ResponseError, RpcError):
                        self.fallback_log('Error:\n{}'.format(traceback.format_exc()))
                        send_errors += 1
                    except:  # pylint: disable=bare-except
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
        """Convert logging record to TextMessage proto."""
        level = self.record_level_to_proto_level(record.levelno)
        msg = data_buffer_protos.TextMessage(source=self.service, level=level,
                                             message=self.format(record))
        # pylint: disable=no-member
        if self.time_sync_endpoint is not None:
            try:
                msg.timestamp.CopyFrom(
                    self.time_sync_endpoint.robot_timestamp_from_local_secs(time.time()))
            except time_sync.NotEstablishedError:
                # If timestamp is not set in the proto, data-buffer will timestamp it on receipt.
                msg.message = '(No time sync!): ' + msg.message
        else:
            msg.timestamp.CopyFrom(core_util.now_timestamp())
        return msg

    @staticmethod
    def record_level_to_proto_level(record_level):
        """Convert logging record level to TextMessage proto level."""
        # pylint: disable=no-member
        if record_level >= logging.ERROR:
            return data_buffer_protos.TextMessage.LEVEL_ERROR
        if record_level >= logging.WARNING:
            return data_buffer_protos.TextMessage.LEVEL_WARN
        if record_level >= logging.INFO:
            return data_buffer_protos.TextMessage.LEVEL_INFO
        return data_buffer_protos.TextMessage.LEVEL_DEBUG
