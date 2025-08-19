# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import enum


class ErrorCallbackResult(enum.Enum):
    """Enum indicating error resolution for errors encountered on SDK background threads.

    There are a few places in the SDK where errors can occur in background threads and it would
    be useful to provide these errors to client code to resolve. Once the application's provided
    callback performs its action, it returns one of these enum values to indicate what the
    background thread should do next.
    """
    #: Take the default action as if no error handler had been provided.
    DEFAULT_ACTION = 1
    #: Retry the operation immediately, presumably because the error has been resolved and the
    #: operation can be retried.
    RETRY_IMMEDIATELY = 2
    #: Retry, with the period between successive retries increasing exponentially.
    RETRY_WITH_EXPONENTIAL_BACK_OFF = 3
    #: Continue normal operation, presuming the error has been resolved and no further action
    #: is needed.
    RESUME_NORMAL_OPERATION = 4
    #: Abort the loop in the background thread.
    ABORT = 5
