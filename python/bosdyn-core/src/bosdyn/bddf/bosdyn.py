# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Boston Dynamics conventions for bddf files"""

from .common import SeriesIdentifier

# pylint: disable=too-few-public-methods


class MessageChannel(SeriesIdentifier):
    """Data series for named channels containing a list of messages."""

    SERIES_TYPE = 'bosdyn:channel'
    CHANNEL = "bosdyn:message-channel"
    KEYS = (CHANNEL,)


class TypedMessageChannel(SeriesIdentifier):
    """Data series for named channels containing a list of messages."""

    SERIES_TYPE = 'bosdyn:typed-message-channel'

    CHANNEL = 'bosdyn:channel'
    MESSAGE_TYPE = 'bosdyn:message-type'
    KEYS = (CHANNEL, MESSAGE_TYPE)


class GrpcRequests(SeriesIdentifier):
    """Data series for request protobuf messages to a grpc service."""

    SERIES_TYPE = 'bosdyn:grpc:requests'

    SERVICE_NAME = 'bosdyn:grpc:service'
    MESSAGE_TYPE = 'bosdyn:message-type'

    KEYS = (SERVICE_NAME, MESSAGE_TYPE)


class GrpcResponses(SeriesIdentifier):
    """Data series for response protobuf messages to a grpc service."""

    SERIES_TYPE = 'bosdyn:grpc:responses'

    SERVICE_NAME = 'bosdyn:grpc:service'
    MESSAGE_TYPE = 'bosdyn:message-type'

    KEYS = (SERVICE_NAME, MESSAGE_TYPE)
