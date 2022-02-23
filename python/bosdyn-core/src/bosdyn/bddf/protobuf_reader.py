# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A class for reading Protobuf data from a DataFile."""
from .message_reader import MessageReader


class ProtobufReader(MessageReader):
    """A class for reading Protobuf data from a DataFile.

    Methods raise ParseError if there is a problem with the format of the file.
    """

    def __init__(self, data_reader):
        super(ProtobufReader, self).__init__(data_reader, require_protobuf=True)

    def get_message(self, series_index, protobuf_type, index_in_series):
        """Return a deserialized protobuf from bytes stored in the file.

        Args:
         series_index:     index (int) from the series_index() call
         protobuf_type:    class of the protobuf we want to deserialize
         index_in_series:  the index of the message within the series

        Returns: DataTypeDescriptor for channel, timestamp_nsec (int), deserialized protobuf object
        """
        desc, timestamp_nsec, data = self.get_blob(series_index, index_in_series)
        protobuf = protobuf_type()
        protobuf.ParseFromString(data)
        return desc, timestamp_nsec, protobuf
