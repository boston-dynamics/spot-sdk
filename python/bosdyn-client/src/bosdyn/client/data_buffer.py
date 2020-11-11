# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
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
import time

from bosdyn.client.exceptions import Error
from bosdyn.client.common import BaseClient, common_header_errors
from bosdyn.client import time_sync
import bosdyn.api.data_buffer_pb2 as data_buffer_protos
import bosdyn.api.data_buffer_service_pb2_grpc as data_buffer_service


class InvalidArgument(Error):
    """A given argument could not be used."""


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
        robot_timestamp = robot_timestamp or self._now_in_robot_basis(msg_type="Operator Comment")
        request.operator_comments.add(message=msg, timestamp=robot_timestamp)
        return func(self._stub.RecordOperatorComments, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def add_blob(self, data, type_id, channel=None, robot_timestamp=None, **kwargs):
        """Log blob messages to the data buffer.

        Args:
            data (bytes): Binary data of one blob.
            type_id (string): Type of binary data of blob. For example, this could be the full name of
                            a protobuf message type.
            channel (string): The name by which messages are typically queried: often the same as
                            type_id, or of the form '{prefix}/{type_id}'.
            robot_timestamp (google.protobuf.Timestamp): Time of messages, in *robot time*.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        return self._do_add_blob(self.call, data, type_id, channel, robot_timestamp, **kwargs)

    def add_blob_async(self, data, type_id, channel=None, robot_timestamp=None, **kwargs):
        """Async version of add_blob."""
        return self._do_add_blob(self.call_async, data, type_id, channel, robot_timestamp, **kwargs)

    def _do_add_blob(self, func, data, type_id, channel, robot_timestamp, **kwargs):
        """Internal blob RPC stub call."""
        request = data_buffer_protos.RecordDataBlobsRequest()

        if not channel:
            channel = type_id

        robot_timestamp = robot_timestamp or self._now_in_robot_basis(msg_type=type_id)
        request.blob_data.add(timestamp=robot_timestamp, channel=channel, type_id=type_id,
                              data=data)

        return func(self._stub.RecordDataBlobs, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def add_protobuf(self, proto, channel=None, robot_timestamp=None):
        """Log protobuf messages to the data buffer.

        Args:
          proto (Protobuf message): Serializable protobuf to log.
          channel (string): Name of channel for data.  If not set defaults to proto type name.
          robot_timestamp (google.protobuf.Timestamp): Time of proto, in *robot time*.

        Raises:
            RpcError: Problem communicating with the robot.
        """
        return self._do_add_protobuf(self.add_blob, proto, channel, robot_timestamp)

    def add_protobuf_async(self, proto, channel=None, robot_timestamp=None):
        """Async version of add_protobuf."""
        return self._do_add_protobuf(self.add_blob_async, proto, channel, robot_timestamp)

    def _do_add_protobuf(self, func, proto, channel, robot_timestamp):
        """Internal blob stub call, serializes proto and logs as blob."""
        binary_data = proto.SerializeToString()
        robot_timestamp = robot_timestamp or self._now_in_robot_basis(proto=proto)
        type_id = proto.DESCRIPTOR.full_name
        channel = channel or type_id
        return func(data=binary_data, type_id=type_id, channel=channel,
                    robot_timestamp=robot_timestamp)

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
            request.events.add().CopyFrom(event)

        return func(self._stub.RecordEvents, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def register_signal_schema(self, variables, schema_name, **kwargs):
        """Log signal schema to the robot.

        Args:
            variables (List[SignalSchema.Variable]): List of SignalSchema variables defining what is in tick.
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
        request.schema.CopyFrom(tick_schema)
        # Schemas are saved internally, according to their schema ID. We need to wait for the
        # response from the server to get the schema id. The response does not include the schema
        # itself so use a partial to process the response appropriately.
        value_from_response = functools.partial(self._save_schema_id, tick_schema)
        return func(self._stub.RegisterSignalSchema, request,
                    value_from_response=value_from_response,
                    error_from_response=common_header_errors, **kwargs)

    def add_signal_tick(self, data, schema_id, encoding=data_buffer_protos.SignalTick.ENCODING_RAW,
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

    def add_signal_tick_async(self, data, schema_id,
                              encoding=data_buffer_protos.SignalTick.ENCODING_RAW, sequence_id=0,
                              source="client", **kwargs):
        """Async version of add_signal_tick."""
        return self._do_add_signal_tick(self.call_async, data, schema_id, encoding, sequence_id,
                                        source, **kwargs)

    def _do_add_signal_tick(self, func, data, schema_id, encoding, sequence_id, source, **kwargs):
        """Internal add signal tick stub call."""
        if schema_id not in self.log_tick_schemas:
            raise LookupError('The log tick schema id "{}" is unknown'.format(schema_id))

        request = data_buffer_protos.RecordSignalTicksRequest()
        request.tick_data.add(sequence_id=sequence_id, source=source, schema_id=schema_id,
                              encoding=encoding, data=data)
        return func(self._stub.RecordSignalTicks, request, value_from_response=None,
                    error_from_response=common_header_errors, **kwargs)

    def _save_schema_id(self, schema, response):
        """Return schema id from response, after saving the schema in a dict indexed by id."""
        self.log_tick_schemas[response.schema_id] = schema
        return response.schema_id

    def _now_in_robot_basis(self, msg_type=None, proto=None):
        """Get current time in robot clock basis if possible, None otherwise."""
        if self._timesync_endpoint:
            try:
                converter = self._timesync_endpoint.get_robot_time_converter()
            except time_sync.NotEstablishedError:
                # No timesync. That's OK -- the receiving host will provide the timestamp.
                self.logger.debug('Could not timestamp message of type %s',
                                  (msg_type if msg_type is not None else
                                   (proto.DESCRIPTOR.full_name
                                    if proto is not None else 'Unknown')))
            else:
                return converter.robot_timestamp_from_local_secs(time.time())
        return None
