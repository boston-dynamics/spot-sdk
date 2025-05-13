# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""The client library package.
Sets up some convenience imports for commonly used classes.
"""
# yapf: enable
from .auth import AuthClient, InvalidLoginError, InvalidTokenError
from .common import BaseClient
# yapf: disable
from .exceptions import (ClientCancelledOperationError, CustomParamError, Error,
                         InternalServerError, InvalidClientCertificateError, InvalidRequestError,
                         LeaseUseError, LicenseError, NonexistentAuthorityError, NotFoundError,
                         PersistentRpcError, ProxyConnectionError, ResponseError, RetryableRpcError,
                         RetryableUnavailableError, RpcError, ServerError,
                         ServiceFailedDuringExecutionError, ServiceUnavailableError, TimedOutError,
                         TooManyRequestsError, UnableToConnectToRobotError, UnauthenticatedError,
                         UnimplementedError, UnknownDnsNameError, UnsetStatusError)
from .robot import Robot
from .sdk import BOSDYN_RESOURCE_ROOT, Sdk, create_standard_sdk


