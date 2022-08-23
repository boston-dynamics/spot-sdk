# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import argparse
import logging
import sys
import time
import types

import pytest
from google.protobuf import timestamp_pb2

import bosdyn.client
from bosdyn.api.log_annotation_pb2 import LogAnnotationTextMessage
from bosdyn.client.log_annotation import InvalidArgument, LogAnnotationClient, LogAnnotationHandler

if sys.version_info[0:2] >= (3, 3):
    # Python version 3.3 added unittest.mock
    from unittest import mock
else:
    # The backport is on PyPi as just "mock"
    import mock



class DummyClass0:

    def __init__(self):
        self.var0 = 2


class DummyClass1:

    def __init__(self):
        self.var0 = 0.0
        self.var1 = 1
        self.var2 = True

        self.embedded_class = DummyClass0()


@pytest.fixture
def mock_log_client():
    return mock.Mock()


SERVICE_NAME = 'my-service'


@pytest.fixture
def handler(mock_log_client):
    handler = LogAnnotationHandler(SERVICE_NAME, mock_log_client)
    handler.setLevel(logging.INFO)
    yield handler
    handler.close()


@pytest.fixture
def logger(request, handler):
    # Get a logger with a name set to the name of the test being run.
    logger = logging.getLogger(request.node.name)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    yield logger
    logger.removeHandler(handler)


# Parametrize by the logger record level to use, and what we expect the proto version to be.
# Note that NOTSET doesn't work, so we use 1 instead.
@pytest.mark.parametrize('record_and_proto_level',
                         ((100, LogAnnotationTextMessage.LEVEL_ERROR),
                          (logging.ERROR, LogAnnotationTextMessage.LEVEL_ERROR),
                          (logging.ERROR - 1, LogAnnotationTextMessage.LEVEL_WARN),
                          (logging.WARN, LogAnnotationTextMessage.LEVEL_WARN),
                          (logging.WARN - 1, LogAnnotationTextMessage.LEVEL_INFO),
                          (logging.INFO, LogAnnotationTextMessage.LEVEL_INFO),
                          (logging.INFO - 1, LogAnnotationTextMessage.LEVEL_DEBUG),
                          (logging.DEBUG, LogAnnotationTextMessage.LEVEL_DEBUG),
                          (logging.DEBUG - 1, LogAnnotationTextMessage.LEVEL_DEBUG),
                          (1, LogAnnotationTextMessage.LEVEL_DEBUG)))
def test_handler_simple(mock_log_client, handler, logger, record_and_proto_level):
    """A single emit/flush should create the expected message."""
    record_level, proto_level = record_and_proto_level

    # Set level on handler and logger.
    handler.setLevel(record_level)
    logger.setLevel(record_level)

    # Log our message, at a specific time.
    msg = 'hello world'
    with mock.patch('bosdyn.client.log_annotation.core_util.now_timestamp') as mock_now_ts:
        mock_now_ts.return_value = timestamp_pb2.Timestamp(seconds=12345, nanos=678)
        with handler:
            logger.log(record_level, msg)

    # Pull the single LogAnnotationTextMessage out of the mock client and make sure it looks right.
    text_log_proto_list = mock_log_client.add_text_messages.call_args[0][0]
    assert len(text_log_proto_list) == 1
    assert text_log_proto_list[0].message == msg
    assert text_log_proto_list[0].level == proto_level
    assert text_log_proto_list[0].service == SERVICE_NAME
    assert text_log_proto_list[0].timestamp == mock_now_ts.return_value


@pytest.mark.timeout(1)
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


@pytest.mark.timeout(1)
@pytest.mark.parametrize('num_msgs', (100, 10, 50, 2))
def test_handler_multi_message(logger, handler, mock_log_client, num_msgs):
    """Ensure proper behavior with a large number of sequential messages."""
    msg = "so many messages!"

    in_first_batch = num_msgs // 2
    with handler:
        for i in range(in_first_batch):
            logger.info(msg)
        # Encourage one additional transaction.
        time.sleep(handler._flush_event_wait_time * 1.1)
        for i in range(num_msgs - in_first_batch):
            logger.info(msg)

    # We should have all of the messages passed as regular arguments.
    num_msgs_sent = 0
    for call in mock_log_client.add_text_messages.mock_calls:
        num_msgs_sent += len(mock_log_client.add_text_messages.call_args[0][0])
    assert num_msgs_sent == num_msgs


@pytest.mark.timeout(1)
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
    assert 'Dumping 1 messages!' == fallback_msgs[2]
    # Fourth is the actual message itself, in LogAnnotationTextMessage form.
    assert msg == fallback_msgs[3].message


def test_handler_timesync(logger):
    """TimesyncEndpoint without an established timesync cannot be used."""
    mock_ep = mock.Mock()
    mock_ep.has_established_time_sync = False
    with pytest.raises(InvalidArgument):
        LogAnnotationHandler(SERVICE_NAME, mock_log_client, time_sync_endpoint=mock_ep)


@pytest.fixture(scope='function')
def constant_log_timestamp():
    return timestamp_pb2.Timestamp(seconds=12345, nanos=6789)


@pytest.fixture(scope='function')
def log_client(constant_log_timestamp):
    """Get a LogAnnotationClient with its stub and timesync endpoint mocked."""
    converter = mock.Mock()
    converter.robot_timestamp_from_local_secs.return_value = constant_log_timestamp

    client = LogAnnotationClient()
    # Mock out the stub so we can call AddLogAnnotation without a server.
    client._stub = mock.Mock()
    future = mock.Mock()
    future.exception.return_value = None
    client._stub.AddLogAnnotation.future.return_value = future
    # Set up the endpoint such that its conversions will return the constant_log_timestamp.
    client._timesync_endpoint = mock.Mock()
    client._timesync_endpoint.get_robot_time_converter.return_value = converter
    return client




def test_add_text_messages(log_client):
    test_msg = LogAnnotationTextMessage(service='foo', level=LogAnnotationTextMessage.LEVEL_ERROR,
                                        message='hello world')
    log_client.add_text_messages([test_msg])
    assert log_client._stub.AddLogAnnotation.call_count == 1
    log_client.add_text_messages_async([test_msg]).result()
    assert log_client._stub.AddLogAnnotation.future.call_count == 1
    assert (log_client._stub.AddLogAnnotation.call_args ==
            log_client._stub.AddLogAnnotation.future.call_args)


def test_add_operator_comment(log_client):
    test_msg = 'hello world'
    log_client.add_operator_comment(test_msg)
    assert log_client._stub.AddLogAnnotation.call_count == 1
    log_client.add_operator_comment_async(test_msg).result()
    assert log_client._stub.AddLogAnnotation.future.call_count == 1
    assert (log_client._stub.AddLogAnnotation.call_args ==
            log_client._stub.AddLogAnnotation.future.call_args)


def test_add_log_protobuf(log_client, constant_log_timestamp):
    proto = timestamp_pb2.Timestamp(seconds=1, nanos=123456789)
    log_client.add_log_protobuf(proto)
    assert log_client._stub.AddLogAnnotation.call_count == 1
    log_client.add_log_protobuf_async(proto).result()
    assert log_client._stub.AddLogAnnotation.future.call_count == 1
    assert (log_client._stub.AddLogAnnotation.call_args ==
            log_client._stub.AddLogAnnotation.future.call_args)

    assert (log_client._stub.AddLogAnnotation.call_args[0][0].annotations.blob_data[0].data ==
            proto.SerializeToString())
    assert (log_client._stub.AddLogAnnotation.call_args[0][0].annotations.blob_data[0].timestamp ==
            constant_log_timestamp)
