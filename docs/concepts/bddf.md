<!--
Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.

Downloading, reproducing, distributing or otherwise using the SDK Software
is subject to the terms and conditions of the Boston Dynamics Software
Development Kit License (20191101-BDSDK-SL).
-->

# BDDF data format

## Motivation

Data stored on Spot robots is downloaded in the BDDF format. BDDF is a file format created by Boston Dynamics for storing timestamped data, along with metadata.  It supports both binary blobs and POD ("plain old data") such as integers or floating point numbers.

BDDF was created to satisfy the following set of requirements:
* **Safe and cheap to write**.  This format is used internally on the robot as well as externally.  Thus, it was designed for minimal, predictable disk and CPU usage while saving data to disk.  Additionally, it is designed so that all data that is written into the file is recoverable (e.g., for when software dies or computer power is cut while the file is being written).
* **No additional processing required.** BDDF is meant to be usable by user tools without processing into other formats.  Thus, it contains an index so that arbitrary data may be accessed efficiently.  The index:
   * Can be used to determine the kinds and time spans of data contained in the file.
   * Supports efficiently extracting data by kind and time span.
* **Secure**.  Little or no parsing logic.  Reading a BDDF requires only handling simple framing, and parsing a few protobuf messages.
* **General**.  BDDF can store data with any encoding.
* **Streamable.**  Data is streamed from the robot in this format based on queries, so it is designed such that the format can be written without seeking backwards in the stream.  This is why the index and checksums are at the end of the file.


## Organization

The structure of the file is a sequence of "blocks" with simple framing.  Some blocks store descriptive information about the file and its contents, and some blocks store data.

BDDF can store both binary "blobs" and "plain old data" (POD) values such as integers or floating point numbers.

Stored data is organized into "data series".  A data series:
* Is either of message type or POD type.
* Consists of a sequence of timestamped data blocks.
* Has a series description explaining the content of the data blocks.
* Has a series identifier to "name" the data series within the file.
* Has a set of index-names for a list of index-values (int64) attached to each data block in the series.

Within a data file, a data series is addressed with a series-index.  Within a data series, a data block is addressed by an integer index-in-series.  At the end of the BDDF file, a file index lists all the data series and locations of the series indexes in the file.


## Identifying data series

Depending on the broad class of content which may be stored in a data series, the series might be described in different ways.  For this reason, instead of requiring a unique string name to identify a series, we use a slightly more flexible identifier: a unique mapping of {key -> value}.

A BDDF SeriesIdentifier has a `series_type`, which describes the kind of series, and a `spec` which is a mapping of {key -> value} further identifying the series.  The `series_type` implies the set of keys which should be used in the `spec`.

For example:

* A series containing GRPC robot-id request messages might thus be specified as: `series_type="bosdyn:grpc:requests"` and
  `spec={"bosdyn:grpc:service": "robot_id", "bosdyn:message-type": "bosdyn.api.RobotIdRequest"}`.
* A series containing OperatorComment messages might be specified as `series_type="bosdyn:message-channel"` with `spec={"bosdyn:channel": "bosdyn.api.OperatorComment"}`

Because BDDF SeriesIdentifier is a structure, the BDDF format provides a method to hash this structure to make it easier to index.  The hash is the first 64 bits of `SHA1(S K1 V1 K2 V2 ...)` where `S` is series identifier text, `K1` and `V1` are the key and value of the first key and value of the `spec`, `K2` and `V2` are the second key and value of the spec, etc...  Here, all strings are encoded as utf-8, and keys are sorted least-to-greatest using this encoding.


## Data series annotations

Annotations, in the form of a set of string key -> value mappings, should be used to express further information about a data series.  The format of annotation keys should be {project-or-organization}:{annotation-name}.  For example, 'bosdyn:channel-name', 'bosdyn:protobuf-type'.  Annotation keys without a ':' or starting with ':' are reserved.  The only current key in the reserved namespace is `units`: e.g., `{'units': 'm/s2'}`.

Units should be specified using the [Unified Code for Units of Measure](https://unitsofmeasure.org/ucum.html).


## File structure

There are three basic kinds of blocks in the file:
* **DescriptorBlocks**.  These describe either the file as a whole, a data series or a file index.
* **DataDescriptors**.  These describe a following block of data, including its timestamp and which series it belongs to.
*  **Data**.  These are blocks of raw binary message data.

All binary values are little-endian.

```
<File>     ::= <Magic> <FileFormatDescriptor> <blocks> \
               <FileIndex> <end-header> <Offset> <CheckSum> <EndMagic>
<Magic>    ::= 4 bytes: "BDDF"
<Offset>   ::= 64-bits: unsigned int
<EndMagic> ::= 4 bytes: "FDDB"
<CheckSum> ::= 160-bits: SHA1 digest of all data up until this point in the file/stream.
```
```
<blocks> ::= <block> <blocks> | ""
```
```
<block> ::= <block-header><block-body>
<block-header> ::= <block-type><block-size>
<block-type> ::= 8 bit unsigned integer
<block-size> ::= 56 bit unsigned integer
<block> ::= <block-header (type=0x00)> <DescriptorBlock>
           | <block-header (type=0x01)r><descriptor-size> <DataDescriptor> <Data>

<end-header> :: <block-header (block-type=0x02, block-size=20)>
```

`<DescriptorBlock>` is a serialized `bosdyn.api.data.DescriptorBlock` protobuf, of size `<block-size>` bytes.

`<FileFormatDescriptor>` is a serialized `bosdyn.api.data.DescriptorBlock` protobuf containing a `bosdyn.api.data.FileFormatDescriptor` submessage.

`<FileIndex>` is a serialized `bosdyn.api.data.DescriptorBlock` protobuf containing a `bosdyn.api.data.FileIndex` submessage.

`<DataDescriptor>` is a serialized `bosdyn.api.data.DataDescriptor` protobuf, of size `<descriptor-size>` bytes.

`<Data>` is binary data representing the data content of the block, of size `<block-size> - <descriptor-size>`.

`block-types` 0x02 through 0xFF are reserved.


```
<bit-zero> ::= 1 bit: 0
<bit-one>  ::= 1 bit: 1
```
```
<block-size> ::= 63-bit unsigned int
<descriptor-size> ::= 32-bit unsigned int
```

The first `<block>` in the file should be a `DescriptorBlock` containing a `FileFormatDescriptor`.  This specifies the file format version (currently 1.0.0) and a list of `{key -> value}` (`string -> string`) which for a robot log could be used to specify from which robot the log came from, the release running, etc....   The format of annotation keys should be {project-or-organization}:{annotation-name}.  For example, `bosdyn:robot-serial-number`.

The final `<block>` in the file should be a `DescriptorBlock` containing a `FileIndex`.  This structure lists the `SeriesIdentifier` for each series of messages and a list of `(timestamp_nsec, file_offset)` pairs for each message in the series.  If  `<Offset>` is zero, this means that the file does not have an index block.

The index helps make it easier to find data in the file.  The offset at the end of the file shows where start of the index block is. So you can seek 20 bytes from the end of the file, read the index offset, seek to the index block and read it, and then you have a map to the rest of the data in the file. The index offset is at the end of the file to allow the file to be written purely as a stream. You thus never need to seek to the beginning to insert the offset.
