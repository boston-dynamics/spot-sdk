# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""DataWriter is a class for writing data to a file."""

import bosdyn.api.bddf_pb2 as bddf

from .block_writer import BlockWriter
from .file_indexer import FileIndexer


class DataWriter:
    """Class for writing data to a file."""

    # pylint: disable=too-many-arguments

    def __init__(self, outfile, annotations=None):
        """
        Args:
         outfile:       a file-like objet for writing binary data (e.g., from open(fname, 'wb')).
         annotations:   optional dict of key (string) -> value (string) pairs.
        """
        self._writer = BlockWriter(outfile)
        self._indexer = FileIndexer()
        self._annotations = annotations
        self._writer.write_header(annotations)
        self._on_close = []

    def __del__(self):
        self._close()

    def __enter__(self):
        return self

    def __exit__(self, type_, value_, tb_):
        self._close()

    @property
    def file_index(self):
        """Get the FileIndex proto used which describes how to access data in the file."""
        return self._indexer.file_index

    def add_message_series(self, series_type, series_spec, content_type, type_name,
                           is_metadata=False, annotations=None, additional_index_names=None):
        """Add a new series for storing message data.  Message data is variable-sized binary data.

        Args:
         series_type:   the kind of spec, corresponding to the set of keys expected in series_spec.
         series_spec:   dict of {key (string) -> value (string)} describing the series.
         content_type:  data encoding, like http content-type header (string)
         type_name:     string describing the kind of data
         is_metadata:   Metadata messages are needed to interpret other messages which
                         may be stored in the file.  If the file is split into parts,
                         metadata messages must be duplicated into each part. (default=False)
         annotations:   optional dict of key (string) -> value (string) pairs to
                          associate with the message channel
         additional_index_names: names of additional timestamps to store with
                                        each message (list of string).

        Returns series id (int).
        """
        message_type = bddf.MessageTypeDescriptor(content_type=content_type, type_name=type_name,
                                                  is_metadata=is_metadata)
        return self.add_series(series_type, series_spec, message_type=message_type,
                               annotations=annotations,
                               additional_index_names=additional_index_names)

    def add_pod_series(self, series_type, series_spec, type_enum, dimension=None, annotations=None):
        """Add a new series for storing data POD data (float, double, int, etc....).

        Args:
         series_type:   the kind of spec, corresponding to the set of keys expected in series_spec.
         series_spec:   dict of {key (string) -> value (string)} describing the series.
         type_enum:     kind of values stored in the file (PodTypeEnum).
         dimension:     None or empty-array means elements are single values,
                           [3] means vectors of size 3, [4, 4] is a 4x4 matrix, etc....
         annotations:   optional dict of key (string) -> value (string) pairs to
                            associate with the message channel

        Returns series id (int).
        """
        pod_type = bddf.PodTypeDescriptor(pod_type=type_enum, dimension=dimension)
        return self.add_series(series_type, series_spec, pod_type=pod_type, annotations=annotations)

    def add_series(self, series_type, series_spec, message_type=None, pod_type=None,
                   annotations=None, additional_index_names=None):
        """Register a new series for messages.

        Args:
         series_type:   the kind of spec, corresponding to the set of keys expected in series_spec.
         series_spec:   dict of {key (string) -> value (string)} describing the series.
         message_type:  MessageTypeDescriptor (need EITHER this OR pod_type)
         pod_type:      PodTypeDescriptor (need EITHER this OR pod_type)
         annotations:   optional dict of key (string) -> value (string) pairs to
                            associate with the message channel
         additional_index_names: names of additional timestamps to store with
                                        each message (list of string).

        Returns series id (int).

        Raises SeriesNotUniqueError if a series matching series_spec is already added.
        """
        return self._indexer.add_series(series_type, series_spec, message_type, pod_type,
                                        annotations, additional_index_names, self._writer)

    def write_data(self, series_index, timestamp_nsec, data, additional_indexes=None):
        """Store binary data into the file, under a previously-defined channel.

        Args:
         series_index:   integer returned when series was registered with the file.
         timestamp_nsec: nsec since unix epoch to timestamp the data.
         data:           binary data to store.
         additional_indexes: additional timestamps if needed for this channel.

        Raises:
            DataFormatError if the data or additional_indexes are not valid for this series.
        """
        self._indexer.index_data_block(series_index, timestamp_nsec, self._writer.tell(), len(data),
                                       additional_indexes)
        data_descriptor = self._indexer.make_data_descriptor(series_index, timestamp_nsec,
                                                             additional_indexes)
        self._writer.write_data_block(data_descriptor, data)

    def run_on_close(self, thunk):
        """Register a function to be called when file is closed, before index is written."""
        self._on_close.append(thunk)

    def _close(self):
        if self._writer.closed:
            return
        for thunk in self._on_close:
            thunk()
        self._indexer.write_index(self._writer)
        self._writer.close()
