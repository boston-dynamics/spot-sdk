# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Test code for bosdyn.bddf"""

import os
import tempfile

import pytest
from google.protobuf.timestamp_pb2 import Timestamp

import bosdyn.api.bddf_pb2 as bddf
import bosdyn.api.robot_id_pb2 as robot_id
from bosdyn.api.data_buffer_pb2 import OperatorComment
from bosdyn.bddf import (DataReader, DataWriter, GrpcReader, GrpcServiceWriter, PodSeriesReader,
                         PodSeriesWriter, ProtobufChannelReader, ProtobufReader,
                         ProtobufSeriesWriter, StreamDataReader)
from bosdyn.util import now_nsec, now_timestamp, nsec_to_timestamp, timestamp_to_nsec


def test_write_read():  # pylint: disable=too-many-statements,too-many-locals
    """Test writing a data to a file, and reading it back."""
    file_annotations = {'robot': 'spot', 'individual': 'spot-BD-99990001'}
    channel_annotations = {'ccc': '3', 'd': '4444'}
    filename = os.path.join(tempfile.gettempdir(), 'test1.bdf')
    series1_type = 'bosdyn/test/1'
    series1_spec = {'channel': 'channel_a'}
    series1_content_type = 'text/plain'
    series1_additional_indexes = ['idxa', 'idxb']
    timestamp_nsec = now_nsec()
    msg_data = b'This is some data'
    operator_message = OperatorComment(message="End of test", timestamp=now_timestamp())
    pod_series_type = 'bosdyn/test/pod'
    pod_spec = {'varname': 'test_var'}

    # pylint: disable=no-member

    # Test writing the file.
    with open(filename, 'wb') as outfile, \
         DataWriter(outfile, annotations=file_annotations) as data_writer:
        # Write generic message data to the file.
        series1_index = data_writer.add_message_series(
            series1_type, series1_spec, series1_content_type, 'test_type',
            annotations=channel_annotations, additional_index_names=series1_additional_indexes)
        data_writer.write_data(series1_index, timestamp_nsec, msg_data, [1, 2])

        # Write a protobuf to the file.
        proto_writer = ProtobufSeriesWriter(data_writer, OperatorComment)
        proto_writer.write(timestamp_to_nsec(operator_message.timestamp), operator_message)

        # Write POD data (floats) to the file.
        pod_writer = PodSeriesWriter(data_writer, pod_series_type, pod_spec, bddf.TYPE_FLOAT32,
                                     annotations={'units': 'm/s^2'})
        for val in range(10, 20):
            pod_writer.write(timestamp_nsec, val)

    # Test reading the file.
    with open(filename, 'rb') as infile, DataReader(infile) as data_reader:
        # Check the file version number.
        assert data_reader.version.major_version == 1
        assert data_reader.version.minor_version == 0
        assert data_reader.version.patch_level == 0
        assert data_reader.annotations == file_annotations

        expected_timestamp = Timestamp()
        expected_timestamp.FromNanoseconds(timestamp_nsec)

        assert data_reader.series_block_index(0).block_entries[0].timestamp == expected_timestamp
        assert data_reader.series_block_index(0).block_entries[0].additional_indexes[0] == 1
        assert data_reader.series_block_index(0).block_entries[0].additional_indexes[1] == 2

        # Check that there are 3 series in the file.
        assert len(data_reader.file_index.series_identifiers) == 3

        # Read generic message data from the file.
        series_a_index = data_reader.series_spec_to_index(series1_spec)
        assert data_reader.num_data_blocks(series_a_index) == 1
        assert data_reader.total_bytes(series_a_index) == len(msg_data)
        _desc, timestamp_, data_ = data_reader.read(series_a_index, 0)
        assert timestamp_ == timestamp_nsec
        assert data_ == msg_data
        assert _desc.timestamp == expected_timestamp
        assert _desc.additional_indexes[0] == 1
        assert _desc.additional_indexes[1] == 2

        # Read a protobuf from the file.
        proto_reader = ProtobufReader(data_reader)
        operator_message_reader = ProtobufChannelReader(proto_reader, OperatorComment)
        assert operator_message_reader.num_messages == 1
        timestamp_, protobuf = operator_message_reader.get_message(0)
        assert protobuf == operator_message
        assert timestamp_ == timestamp_to_nsec(operator_message.timestamp)

        # Read POD (float) data from the file.
        with pytest.raises(ValueError):
            pod_reader = PodSeriesReader(data_reader, {'spec': 'bogus'})
        pod_reader = PodSeriesReader(data_reader, pod_spec)
        assert pod_reader.pod_type.pod_type == bddf.TYPE_FLOAT32
        assert pod_reader.series_descriptor.annotations['units'] == 'm/s^2'
        assert pod_reader.num_data_blocks == 1

        timestamp_, samples = pod_reader.read_samples(0)
        assert timestamp_ == timestamp_nsec
        assert samples == [float(val) for val in range(10, 20)]

    with open(filename, 'rb') as infile, StreamDataReader(infile) as data_reader:
        # Check the file version number.
        assert data_reader.version.major_version == 1
        assert data_reader.version.minor_version == 0
        assert data_reader.version.patch_level == 0
        assert data_reader.annotations == file_annotations

        desc_, sdesc_, data_ = data_reader.read_data_block()
        assert desc_.timestamp == expected_timestamp
        assert desc_.additional_indexes[0] == 1
        assert desc_.additional_indexes[1] == 2
        assert sdesc_.message_type.content_type == series1_content_type
        assert sdesc_.message_type.type_name == 'test_type'
        assert data_ == msg_data

        desc_, sdesc_, data_ = data_reader.read_data_block()
        assert desc_.timestamp == operator_message.timestamp
        assert sdesc_.message_type.content_type == 'application/protobuf'
        assert sdesc_.message_type.type_name == OperatorComment.DESCRIPTOR.full_name
        dec_msg = OperatorComment()
        dec_msg.ParseFromString(data_)
        assert dec_msg == operator_message

        desc_, sdesc_, data_ = data_reader.read_data_block()
        assert desc_.timestamp == expected_timestamp
        assert sdesc_.pod_type.pod_type == bddf.TYPE_FLOAT32

        assert not data_reader.eof

        with pytest.raises(EOFError):
            data_reader.read_data_block()

        assert data_reader.eof

        # Check that there are 3 series in the file.
        assert len(data_reader.file_index.series_identifiers) == 3

        assert data_reader.series_block_indexes[0].block_entries[0].timestamp == expected_timestamp
        assert data_reader.series_block_index(0).block_entries[0].additional_indexes[0] == 1
        assert data_reader.series_block_index(0).block_entries[0].additional_indexes[1] == 2

        assert (data_reader.file_index.series_identifiers ==
                data_reader.stream_file_index.series_identifiers)

    os.unlink(filename)


def test_grpc_read_write():
    """Test writing GRPC data."""
    file_annotations = {'robot': 'spot', 'individual': 'spot-BD-99990001'}
    service_name = 'robot-id'
    filename = os.path.join(tempfile.gettempdir(), service_name + '.bddf')
    filename = service_name + '.bddf'

    # pylint: disable=no-member
    request = robot_id.RobotIdRequest()
    request.header.request_timestamp.CopyFrom(now_timestamp())
    request.header.client_name = 'test_bddf'

    response = robot_id.RobotIdResponse()
    response.header.response_timestamp.CopyFrom(now_timestamp())
    response.header.request.Pack(request)

    # Test writing the file.
    with open(filename, 'wb') as outfile, \
         DataWriter(outfile, annotations=file_annotations) as data_writer:

        grpc_log = GrpcServiceWriter(data_writer, service_name)
        grpc_log.log_request(request)
        grpc_log.log_response(response)

    # Test reading the file.
    with open(filename, 'rb') as infile:
        data_reader = DataReader(infile)
        grpc_reader = GrpcReader(data_reader, [robot_id.RobotIdRequest, robot_id.RobotIdResponse])
        proto_reader = grpc_reader.get_proto_reader(robot_id.RobotIdRequest.DESCRIPTOR.full_name)
        assert proto_reader.num_messages == 1
        nsec, msg = proto_reader.get_message(0)
        assert msg == request
        assert nsec_to_timestamp(nsec) == msg.header.request_timestamp

        proto_reader = grpc_reader.get_proto_reader(robot_id.RobotIdResponse.DESCRIPTOR.full_name)
        nsec, msg = proto_reader.get_message(0)
        assert msg == response
        assert nsec_to_timestamp(nsec) == msg.header.response_timestamp
