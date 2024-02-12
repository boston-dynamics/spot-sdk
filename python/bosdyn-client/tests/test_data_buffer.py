# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""data-buffer pytests"""
import logging
import struct
import sys
import time
import types
from unittest import mock

import pytest
from google.protobuf import timestamp_pb2

from bosdyn.api import header_pb2
from bosdyn.api.data_buffer_pb2 import Event, SignalSchema, TextMessage
from bosdyn.client.data_buffer import DataBufferClient, InvalidArgument, LoggingHandler


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
    # Make sure we're setting a valid common error code on responses.
    future.result.return_value = mock.Mock()
    future.result.return_value.header.error.code = header_pb2.CommonError.CODE_OK
    client_._stub.RecordTextMessages.future.return_value = future
    client_._stub.RecordDataBlobs.future.return_value = future
    client_._stub.RecordEvents.future.return_value = future
    client_._stub.RecordTextMessages.return_value = future.result.return_value
    client_._stub.RecordDataBlobs.return_value = future.result.return_value
    client_._stub.RecordEvents.return_value = future.result.return_value
    # Set up the endpoint such that its conversions will return the constant_log_timestamp.
    client_._timesync_endpoint = mock.Mock()
    client_._timesync_endpoint.get_robot_time_converter.return_value = converter
    # Stub the schema id generation
    client_._stub.RegisterSignalSchema.future.return_value = future
    client_._stub.RecordSignalTicks.future.return_value = future
    client_._stub.RegisterSignalSchema.return_value = future.result.return_value
    client_._stub.RecordSignalTicks.return_value = future.result.return_value

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
    assert client._stub.RecordDataBlobs.call_args[0][0].sync is False

    client.add_protobuf_async(proto).result()
    assert client._stub.RecordDataBlobs.future.call_count == 1
    assert (client._stub.RecordDataBlobs.call_args == client._stub.RecordDataBlobs.future.call_args)
    assert client._stub.RecordDataBlobs.call_args[0][0].sync is False
    assert (
        client._stub.RecordDataBlobs.call_args[0][0].blob_data[0].data == proto.SerializeToString())
    assert (client._stub.RecordDataBlobs.call_args[0][0].blob_data[0].timestamp ==
            constant_log_timestamp)

    # Synchronous data buffer writes
    client.add_protobuf(proto, write_sync=True)
    assert client._stub.RecordDataBlobs.call_count == 2
    assert client._stub.RecordDataBlobs.call_args[0][0].sync is True

    client.add_protobuf_async(proto, write_sync=True).result()
    assert client._stub.RecordDataBlobs.future.call_count == 2
    assert (client._stub.RecordDataBlobs.call_args == client._stub.RecordDataBlobs.future.call_args)
    assert client._stub.RecordDataBlobs.call_args[0][0].sync is True
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


SERVICE_NAME = 'my-service'


@pytest.fixture
def handler(mock_log_client):
    log_handler = LoggingHandler(SERVICE_NAME, mock_log_client)
    log_handler.setLevel(logging.INFO)
    return log_handler


@pytest.fixture
def logger(request, handler):
    # Get a logger with a name set to the name of the test being run.
    log = logging.getLogger(request.node.name)
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    return log


# Parametrize by the logger record level to use, and what we expect the proto version to be.
# Note that NOTSET doesn't work, so we use 1 instead.
@pytest.mark.parametrize(
    'record_and_proto_level',
    # pylint: disable=no-member
    ((100, TextMessage.LEVEL_ERROR), (logging.ERROR, TextMessage.LEVEL_ERROR),
     (logging.ERROR - 1, TextMessage.LEVEL_WARN), (logging.WARN, TextMessage.LEVEL_WARN),
     (logging.WARN - 1, TextMessage.LEVEL_INFO), (logging.INFO, TextMessage.LEVEL_INFO),
     (logging.INFO - 1, TextMessage.LEVEL_DEBUG), (logging.DEBUG, TextMessage.LEVEL_DEBUG),
     (logging.DEBUG - 1, TextMessage.LEVEL_DEBUG), (1, TextMessage.LEVEL_DEBUG)))
def test_handler_simple(mock_log_client, handler, logger, record_and_proto_level):
    """A single emit/flush should create the expected message."""
    record_level, proto_level = record_and_proto_level

    # Set level on handler and logger.
    handler.setLevel(record_level)
    logger.setLevel(record_level)

    # Log our message, at a specific time.
    msg = 'hello world'
    with mock.patch('bosdyn.client.data_buffer.core_util.now_timestamp') as mock_now_ts:
        mock_now_ts.return_value = timestamp_pb2.Timestamp(seconds=12345, nanos=678)
        with handler:
            logger.log(record_level, msg)

    # Pull the single TextMessage out of the mock client and make sure it looks right.
    text_log_proto_list = mock_log_client.add_text_messages.call_args[0][0]
    assert len(text_log_proto_list) == 1
    assert text_log_proto_list[0].message == msg
    assert text_log_proto_list[0].level == proto_level
    assert text_log_proto_list[0].source == SERVICE_NAME
    assert text_log_proto_list[0].timestamp == mock_now_ts.return_value


@pytest.mark.timeout(10)
def test_handler_autoflush(mock_log_client, handler, logger):
    """The handler should automatically flush messages to the log client."""
    # Build the handler with a specific record level and our mock client.
    msg = 'boo'
    handler.msg_num_limit = 2
    logger.info(msg)
    # Be sure the message was inserted onto the queue.
    while len(handler._msg_queue) == 0:
        time.sleep(0.01)
    logger.info(msg)

    # Wait for queued messages to clear
    while len(handler._msg_queue) != 0:
        time.sleep(0.01)

    # We should have sent one message.
    mock_log_client.add_text_messages.assert_called_once()


@pytest.mark.timeout(10)
@pytest.mark.parametrize('num_msgs', (100, 10, 50, 2))
def test_handler_multi_message(logger, handler, mock_log_client, num_msgs):
    """Ensure proper behavior with a large number of sequential messages."""
    msg = "so many messages!"

    in_first_batch = num_msgs // 2
    with handler:
        for _ in range(in_first_batch):
            logger.info(msg)
        # Encourage one additional transaction.
        time.sleep(handler._flush_event_wait_time * 1.1)
        for _ in range(num_msgs - in_first_batch):
            logger.info(msg)

    # We should have all of the messages passed as regular arguments.
    num_msgs_sent = 0
    for call in mock_log_client.add_text_messages.call_args_list:
        batched_msgs = call[0][0]
        for text_msg_proto in batched_msgs:
            m = text_msg_proto.message
            assert m == msg, f'Unexpected message queued: {m}'
        num_msgs_sent += len(batched_msgs)
    assert num_msgs_sent == num_msgs


@pytest.mark.timeout(10)
def test_handler_failure(logger, handler, mock_log_client):
    """When log client fails, we should get error messages and the failed log message."""
    msg = 'This should fail'
    exception_text = 'this is real bad you guys'
    mock_log_client.add_text_messages.side_effect = Exception(exception_text)
    fallback_msgs = []
    handler.fallback_log = types.MethodType(lambda self, msg: fallback_msgs.append(msg), handler)
    handler._dump_msg_count = 1
    handler.flush()
    with handler:
        logger.info(msg)
        # Expect to get two fallback messages because of that log statement.
        while len(fallback_msgs) < 2:
            time.sleep(0.01)
        mock_log_client.add_text_messages.side_effect = None

    # We should have gotten four messages.
    assert len(fallback_msgs) == 4, 'Got these messages:\n{}'.format('\n'.join(
        [str(m) for m in fallback_msgs]))
    # First message includes the exception.
    assert exception_text in fallback_msgs[0]
    # Second indicates the logger thread itself, by class and function name.
    assert handler.__class__.__name__ in fallback_msgs[1]
    assert '_run_send_thread' in fallback_msgs[1]
    # Third is the warning about messages being dumped.
    assert fallback_msgs[2] == 'Dumping 1 messages!'
    # Fourth is the actual message itself, in TextMessage form.
    assert fallback_msgs[3].message == msg


@pytest.fixture
def mock_log_client():
    """fake API client for sending log messages.."""
    return mock.Mock()


def test_handler_timesync(mock_log_client):  # pylint: disable=redefined-outer-name
    """TimesyncEndpoint without an established timesync cannot be used."""
    mock_ep = mock.Mock()
    mock_ep.has_established_time_sync = False
    with pytest.raises(InvalidArgument):
        LoggingHandler(SERVICE_NAME, mock_log_client, time_sync_endpoint=mock_ep)
