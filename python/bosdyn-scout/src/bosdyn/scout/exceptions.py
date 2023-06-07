# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Relevant exceptions for bosdyn-scout"""


class Error(Exception):
    """Base exception"""


class UnauthenticatedScoutClientError(Error):
    """The Scout client is not authenticated properly."""

    def __str__(self):
        return 'The Scout client is not authenticated properly. Run the proper authentication before calling other client functions!'
