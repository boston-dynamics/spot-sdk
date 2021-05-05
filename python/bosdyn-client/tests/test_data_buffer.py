# Copyright (c) 2021 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import itertools
import pytest
import struct
import sys
from bosdyn.client.data_buffer import DataBufferClient
from bosdyn.api.data_buffer_pb2 import (Event, RegisterSignalSchemaRequest, SignalSchema,
                                        TextMessage)
from google.protobuf import timestamp_pb2

if sys.version_info[0:2] >= (3, 3):
    # Python version 3.3 added unittest.mock
    from unittest import mock
else:
    # The backport is on PyPi as just "mock"
    import mock


@pytest.fixture(scope='function')
def constant_log_timestamp():
    return timestamp_pb2.Timestamp(seconds=12345, nanos=6789)


@pytest.fixture(scope='function')
def client(constant_log_timestamp):
    """Get a DataBufferClient with its stub and timesync endpoint mocked."""
    converter = mock.Mock()
    converter.robot_timestamp_from_local_secs.return_value = constant_log_timestamp

    client_ = DataBufferClient()
    # Mock out all the stubs so we can call AddLogAnnotation without a server.
    client_._stub = mock.Mock()
    future = mock.Mock()
    future.exception.return_value = None
    client_._stub.RecordTextMessages.future.return_value = future
    client_._stub.RecordDataBlobs.future.return_value = future
    client_._stub.RecordEvents.future.return_value = future
    # Set up the endpoint such that its conversions will return the constant_log_timestamp.
    client_._timesync_endpoint = mock.Mock()
    client_._timesync_endpoint.get_robot_time_converter.return_value = converter
    # Stub the schema id generation
    client_._stub.RegisterSignalSchema.future.return_value = future
    client_._stub.RecordSignalTicks.future.return_value = future

    def _save_schema_id(schema, response):
        client_.log_tick_schemas[1] = schema
        return 1

    client_._save_schema_id = mock.Mock()
    client_._save_schema_id.side_effect = _save_schema_id
    return client_


def test_add_text_messages(client):
    test_msg = TextMessage(source='foo', level=TextMessage.LEVEL_ERROR, message='hello world')
    client.add_text_messages([test_msg])
    assert client._stub.RecordTextMessages.call_count == 1
    client.add_text_messages_async([test_msg]).result()
    assert client._stub.RecordTextMessages.future.call_count == 1
    assert (client._stub.RecordTextMessages.call_args ==
            client._stub.RecordTextMessages.future.call_args)


def test_add_protobuf(client, constant_log_timestamp):
    proto = timestamp_pb2.Timestamp(seconds=1, nanos=123456789)
    # Asynchronous data buffer writes
    client.add_protobuf(proto)
    assert client._stub.RecordDataBlobs.call_count == 1
    assert client._stub.RecordDataBlobs.call_args[0][0].sync == False

    client.add_protobuf_async(proto).result()
    assert client._stub.RecordDataBlobs.future.call_count == 1
    assert (client._stub.RecordDataBlobs.call_args == client._stub.RecordDataBlobs.future.call_args)
    assert client._stub.RecordDataBlobs.call_args[0][0].sync == False
    assert (
        client._stub.RecordDataBlobs.call_args[0][0].blob_data[0].data == proto.SerializeToString())
    assert (client._stub.RecordDataBlobs.call_args[0][0].blob_data[0].timestamp ==
            constant_log_timestamp)

    # Synchronous data buffer writes
    client.add_protobuf(proto, write_sync=True)
    assert client._stub.RecordDataBlobs.call_count == 2
    assert client._stub.RecordDataBlobs.call_args[0][0].sync == True

    client.add_protobuf_async(proto, write_sync=True).result()
    assert client._stub.RecordDataBlobs.future.call_count == 2
    assert (client._stub.RecordDataBlobs.call_args == client._stub.RecordDataBlobs.future.call_args)
    assert client._stub.RecordDataBlobs.call_args[0][0].sync == True
    assert (
        client._stub.RecordDataBlobs.call_args[0][0].blob_data[0].data == proto.SerializeToString())
    assert (client._stub.RecordDataBlobs.call_args[0][0].blob_data[0].timestamp ==
            constant_log_timestamp)


def test_add_events(client):
    event = Event()
    event.type = 'test-event'
    event.description = 'test_add_events'
    event.source = 'pytest'
    event.id = '60c1b6a2-851b-4aed-a546-8702a6bebc43'
    event.start_time.GetCurrentTime()
    event.end_time.GetCurrentTime()

    client.add_events([event])
    assert client._stub.RecordEvents.call_count == 1
    client.add_events_async([event]).result()
    assert client._stub.RecordEvents.future.call_count == 1
    assert (client._stub.RecordEvents.call_args == client._stub.RecordEvents.future.call_args)


def test_signal_log(client):
    # Register a schema & log a tick
    schema_name = 'test_schema'
    vars = [
        SignalSchema.Variable(name='time', type=SignalSchema.Variable.TYPE_UINT64, is_time=True),
        SignalSchema.Variable(name='val', type=SignalSchema.Variable.TYPE_FLOAT64, is_time=False)
    ]
    data_bytes = struct.pack('<Qd', 0, 3.14)

    schema_id = client.register_signal_schema(vars, schema_name)
    assert client._stub.RegisterSignalSchema.call_count == 1
    assert schema_id == 1

    call_args = client._stub.RegisterSignalSchema.call_args[0]
    assert call_args[0].schema == SignalSchema(vars=vars, schema_name=schema_name)

    client.add_signal_tick(data_bytes, schema_id)
    assert client._stub.RecordSignalTicks.call_count == 1

    call_args = client._stub.RecordSignalTicks.call_args[0]
    assert len(call_args[0].tick_data) == 1
    assert call_args[0].tick_data[0].schema_id == schema_id
    assert call_args[0].tick_data[0].data == data_bytes

    # Re-register & log async
    schema_id = client.register_signal_schema_async(vars, schema_name).result()
    assert client._stub.RegisterSignalSchema.future.call_count == 1
    assert schema_id == 1

    call_args = client._stub.RegisterSignalSchema.call_args[0]
    assert call_args[0].schema == SignalSchema(vars=vars, schema_name=schema_name)

    client.add_signal_tick_async(data_bytes, schema_id)
    assert client._stub.RecordSignalTicks.future.call_count == 1

    call_args = client._stub.RecordSignalTicks.call_args[0]
    assert len(call_args[0].tick_data) == 1
    assert call_args[0].tick_data[0].schema_id == schema_id
    assert call_args[0].tick_data[0].data == data_bytes
