# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Use bosdyn.bddf instead."""

import warnings

from bosdyn.bddf.base_data_reader import BaseDataReader
from bosdyn.bddf.block_writer import BlockWriter
from bosdyn.bddf.bosdyn import MessageChannel
# pylint: disable=unused-import
# from bosdyn.bddf import (
from bosdyn.bddf.common import (BLOCK_HEADER_SIZE_MASK, BLOCK_HEADER_TYPE_MASK, DATA_BLOCK_TYPE,
                                DESCRIPTOR_BLOCK_TYPE, END_BLOCK_TYPE, END_MAGIC,
                                INDEX_OFFSET_OFFSET, LOGGER, MAGIC, POD_TYPE_TO_NUM_BYTES,
                                POD_TYPE_TO_STRUCT, PROTOBUF_CONTENT_TYPE, SHA1_DIGEST_NBYTES,
                                AddSeriesError, ChecksumError, DataError, DataFormatError,
                                ParseError, SeriesNotUniqueError)
from bosdyn.bddf.data_reader import DataReader
from bosdyn.bddf.data_writer import DataWriter
from bosdyn.bddf.file_indexer import FileIndexer
from bosdyn.bddf.pod_series_reader import PodSeriesReader
from bosdyn.bddf.pod_series_writer import PodSeriesWriter
from bosdyn.bddf.protobuf_channel_reader import ProtobufChannelReader
from bosdyn.bddf.protobuf_reader import ProtobufReader
from bosdyn.bddf.protobuf_series_writer import ProtobufSeriesWriter as ProtoSeriesWriter
from bosdyn.bddf.stream_data_reader import StreamDataReader

MESSAGE_CHANNEL_SERIES_TYPE = MessageChannel.SERIES_TYPE

warnings.warn("bddf has moved to bosdyn-core.  Import bosdyn.bddf instead", DeprecationWarning,
              stacklevel=2)
