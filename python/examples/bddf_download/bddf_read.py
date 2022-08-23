# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Read downloaded data from bddf files."""
import datetime
import logging
import sys

from bosdyn.api.data_buffer_pb2 import Event, OperatorComment
from bosdyn.bddf import DataReader, GrpcReader, ProtobufChannelReader, ProtobufReader

LOGGER = logging.getLogger()


def get_data(proto_type, filename, channel=None):
    """Iterator for message of the given protobuf type stored in bddf file 'filename'."""
    with open(filename, 'rb') as infile:
        data_reader = DataReader(infile)
        protobuf_reader = ProtobufReader(data_reader)
        try:
            channel_reader = ProtobufChannelReader(protobuf_reader, proto_type,
                                                   channel_name=channel)
        except KeyError:
            LOGGER.error("No messages of type '%s' found", proto_type.DESCRIPTOR.full_name)
            sys.exit(1)
        for i in range(channel_reader.num_messages):
            yield channel_reader.get_message(i)


def get_grpc_data(proto_name, filename):
    """Iterator for message of the given protobuf type stored in bddf file 'filename'."""
    with open(filename, 'rb') as infile:
        data_reader = DataReader(infile)
        grpc_reader = GrpcReader(data_reader, MessageLister.PROTO_CLASSES)
        proto_reader = grpc_reader.get_proto_reader(proto_name)
        for i in range(proto_reader.num_messages):
            yield proto_reader.get_message(i)


class MessageLister:
    """A class for printing messages of a given kind of protobuf."""

    PROTO_CLASSES = []
    INSTANCES = {}

    def __init__(self, proto_type):
        self._proto_type = proto_type
        self.PROTO_CLASSES.append(proto_type)
        self.INSTANCES[proto_type.DESCRIPTOR.full_name] = self

    @property
    def proto_type(self):
        """Return protobuf class supported by this MessageLister."""
        return self._proto_type

    def show(self, timestamp_msg):  # pylint: disable=no-self-use
        """Print the given message from the pair (timestamp, message) returned by get_data()"""
        timestamp = datetime.datetime.fromtimestamp(timestamp_msg[0] * 1e-9)
        msg = timestamp_msg[1]
        print('== {} -- {}\n{}'.format(timestamp, msg.DESCRIPTOR.full_name, msg))


class OperatorCommentLister(MessageLister):
    """A class for printing messages of the type bosdyn.api.OperatorComment."""

    def __init__(self):
        super(OperatorCommentLister, self).__init__(OperatorComment)

    def show(self, timestamp_msg):
        msg = timestamp_msg[1]
        timestamp = datetime.datetime.fromtimestamp(msg.timestamp.seconds +
                                                    1e-9 * msg.timestamp.nanos)
        print('{}   {}'.format(timestamp, msg.message.strip()))


class EventLister(MessageLister):
    """A class for printing messages of the type bosdyn.api.Event."""

    def __init__(self):
        super(EventLister, self).__init__(Event)

    def show(self, timestamp_msg):
        msg = timestamp_msg[1]
        start_sec = msg.start_time.seconds + 1e-9 * msg.start_time.nanos
        start_timestamp = datetime.datetime.fromtimestamp(start_sec)
        if msg.HasField('end_time'):
            if msg.start_time == msg.end_time:
                dur_str = '(instantaneous)'
            else:
                end_sec = msg.end_time.seconds + 1e-9 * msg.end_time.nanos
                dur = end_sec - start_sec
                dur_str = '{:.09f} sec'.format(dur)
        else:
            dur_str = '(start)        '
        print('{} ({}) {} {} {}'.format(msg.type, msg.Level.Name(msg.level), start_timestamp,
                                        dur_str, msg.description))
        for param in msg.parameters:
            print("  {}".format(param))


class GrpcProtoReader:
    """Reads a particular series of GRPC request or response messages from a bddf file."""

    def __init__(  # pylint: disable=too-many-arguments
            self, service_reader, series_index, series_type, proto_type, series_descriptor):
        self._service_reader = service_reader
        self._series_index = series_index
        self._series_type = series_type
        self._proto_type = proto_type
        self._series_descriptor = series_descriptor
        self._num_messages = None

    @property
    def num_messages(self):
        """Number of messages in of the given type."""
        if self._num_messages is None:
            self._num_messages = self._service_reader.data_reader.num_data_blocks(
                self._series_index)
        return self._num_messages

    def get_message(self, index_in_series):
        """Get a message from the series by its index number in the series."""
        _desc, timestamp_nsec, data = self._service_reader.data_reader.read(
            self._series_index, index_in_series)
        protobuf = self._proto_type()
        protobuf.ParseFromString(data)
        return timestamp_nsec, protobuf


def index_protos(package):
    """Given a python package, register the protobuf messages it defines with MessageLister."""
    for (type_name, _type_desc) in package.DESCRIPTOR.message_types_by_name.items():
        MessageLister(package.__dict__[type_name])


def setup():
    """Register protobuf type information that might be needed."""
    # Import and index more packages here as needed.
    # pylint: disable=import-outside-toplevel
    import bosdyn.api.data_buffer_pb2
    import bosdyn.api.robot_id_pb2
    import bosdyn.api.robot_state_pb2
    index_protos(bosdyn.api.data_buffer_pb2)
    index_protos(bosdyn.api.robot_id_pb2)
    index_protos(bosdyn.api.robot_state_pb2)
    # Specialized listers
    EventLister()
    OperatorCommentLister()


def show_supported_types():
    """Show the protobuf types supported by this utility."""
    print("Supported types:\n  {}".format('\n  '.join(sorted(MessageLister.INSTANCES.keys()))))


def list_series(options):
    """Show the list of series available in the bddf file."""
    with open(options.filename, 'rb') as infile:
        data_reader = DataReader(infile)
        series_identifiers = data_reader.file_index.series_identifiers
        print("Series in '{}' ({}):".format(options.filename, len(series_identifiers)))
        for i, sid in enumerate(series_identifiers):
            print("- [{}] {}: {}".format(i, sid.series_type, {k: v for k, v in sid.spec.items()}))


def show_messages(options):
    """Show messages of a given message type from a given bddf file."""
    try:
        lister = MessageLister.INSTANCES[options.message_type]
    except KeyError:
        print("No support for printing messages of type '{}'".format(options.message_type))
        sys.exit(1)

    for msg in get_data(lister.proto_type, options.filename, channel=options.channel):
        lister.show(msg)


def show_grpc_messages(options):
    """Show grpc request or response messages from a given bddf file."""
    try:
        lister = MessageLister.INSTANCES[options.message_type]
    except KeyError:
        print("No support for printing messages of type '{}'".format(options.message_type))
        sys.exit(1)
    try:
        for msg in get_grpc_data(options.message_type, options.filename):
            lister.show(msg)
    except KeyError:
        LOGGER.error("Could not find GRPC messages of type '%s'.", options.message_type)
        sys.exit(1)


def main():  # pylint: disable=too-many-locals
    """Command-line interface"""
    import argparse  # pylint: disable=import-outside-toplevel
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', help='show debug messages')

    subparsers = parser.add_subparsers(help='commands', dest='command')
    _types_parser = subparsers.add_parser('types',
                                          help='show protobuf types supported by this utility')
    channel_parser = subparsers.add_parser('series', help='List available series in the file')
    channel_parser.add_argument('filename', default='download.bddf', help='input file')

    show_parser = subparsers.add_parser('show', help='Show messages from a given channel')
    show_parser.add_argument('filename', default='download.bddf', help='input file')
    show_parser.add_argument('message_type', help='type of messages to show')
    show_parser.add_argument('--channel', help='name of channel, if not the same as message_type')

    grpc_parser = subparsers.add_parser('show-grpc', help='Show grpc requests/responses by type')
    grpc_parser.add_argument('filename', default='download.bddf', help='input file')
    grpc_parser.add_argument('message_type', help='type of messages to show')

    options = parser.parse_args()

    if options.verbose:
        LOGGER.setLevel(logging.DEBUG)

    setup()

    if options.command == 'types':
        show_supported_types()
    elif options.command == 'series':
        list_series(options)
    elif options.command == 'show':
        show_messages(options)
    elif options.command == 'show-grpc':
        show_grpc_messages(options)
    else:
        parser.print_help()
        return False
    return True


if __name__ == "__main__":
    if not main():
        sys.exit(1)
