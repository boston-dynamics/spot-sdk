# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""The client library package.
Sets up some convenience imports for commonly used classes.
"""
from .common import BaseClient
# yapf: disable
from .exceptions import (Error,
                             ResponseError,
                                InvalidRequestError,
                                LeaseUseError,
                                LicenseError,
                                ServerError,
                                InternalServerError,
                                UnsetStatusError,
                                RpcError,
                                ClientCancelledOperationError,
                                InvalidAppTokenError,
                                InvalidClientCertificateError,
                                NonexistentAuthorityError,
                                NotFoundError,
                                ProxyConnectionError,
                                ServiceUnavailableError,
                                ServiceFailedDuringExecutionError,
                                TimedOutError,
                                UnableToConnectToRobotError,
                                UnauthenticatedError,
                                UnknownDnsNameError,
                                UnimplementedError)
# yapf: enable
from .auth import AuthClient, ExpiredApplicationTokenError, InvalidLoginError, InvalidApplicationTokenError, InvalidTokenError
from .robot import Robot
from .sdk import Sdk, create_standard_sdk, BOSDYN_RESOURCE_ROOT
