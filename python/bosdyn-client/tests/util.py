# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import bosdyn.api.header_pb2
import bosdyn.util


def set_common_response_header(header, code=bosdyn.api.header_pb2.CommonError.CODE_OK):
    now_nsec = bosdyn.util.now_nsec()
    bosdyn.util.set_timestamp_from_nsec(header.response_timestamp, now_nsec)
    header.error.code = code
