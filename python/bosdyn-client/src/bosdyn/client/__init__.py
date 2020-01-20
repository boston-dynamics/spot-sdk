"""The client library package.
Sets up some convenience imports for commonly used classes.
"""
from .common import BaseClient
# yapf: disable
from .exceptions import (Error,
                             ResponseError,
                                 InvalidRequestError,
                                 LeaseUseError,
                                 ServerError,
                                     InternalServerError,
                                     UnsetStatusError,
                             RpcError,
                                ClientCancelledOperationError,
                                InvalidAppTokenError,
                                InvalidClientCertificateError,
                                NonexistentAuthorityError,
                                ProxyConnectionError,
                                ServiceUnavailableError,
                                ServiceFailedDuringExecutionError,
                                TimedOutError,
                                UnableToConnectToRobotError,
                                UnauthenticatedError,
                                UnknownDnsNameError,
                                UnimplementedError)
# yapf: enable
from .auth import AuthClient, InvalidLoginError, InvalidTokenError
from .robot import Robot
from .sdk import Sdk, create_standard_sdk, BOSDYN_RESOURCE_ROOT
