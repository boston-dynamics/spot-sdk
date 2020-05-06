# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Constants relevant to the missions service."""

import enum


@enum.unique
class Result(enum.IntEnum):
    FAILURE = 1
    RUNNING = 2
    SUCCESS = 3
    ERROR = 4
