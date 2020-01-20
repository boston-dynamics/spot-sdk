"""Contains elements common to all service clients."""
import copy
import functools
import logging

from .channel import TransportError, translate_exception
from .exceptions import Error, InternalServerError, InvalidRequestError, LeaseUseError, UnsetStatusError

_LOGGER = logging.getLogger(__name__)

def common_header_errors(response):
    """Return an exception based on common response header. None if no error."""
    if response.header.error.code == response.header.error.CODE_UNSPECIFIED:
        return UnsetStatusError(response)
    if response.header.error.code == response.header.error.CODE_INTERNAL_SERVER_ERROR:
        return InternalServerError(response)
    if response.header.error.code == response.header.error.CODE_INVALID_REQUEST:
        return InvalidRequestError(response)
    return None


def common_lease_errors(response):
    """Return an exception based on lease use result. None if no error."""
    if response.lease_use_result.status != response.lease_use_result.STATUS_OK:
        return LeaseUseError(response)
    return None


def error_factory(response, status, status_to_string, status_to_error):
    """Return an error based on the status field of the given response.

    NOTE: Since most callers of this function are "response to error" callbacks, any exceptions
          raised by this function are a considered a serious problem. Strongly consider using
          collections.defaultdict for the status_to_error mapping, and/or wrapping calls to this
          function in try/except blocks.

    Args:
        response -- Protobuf message to examine.
        status -- Status from the protobuf message.
        status_to_string -- Function that converts numeric status value to string. May raise
                            ValueError, in which case just the numeric code is included in a default
                            error message.
        status_to_error -- mapping of status -> (error_constructor, error_message)
                           error_constructor must take arguments "response" and "error_message".
                           (and ideally will subclass from ResponseError.)

    Returns:
        None if status_to_error[status] maps to (None, _).
        Otherwise, an instance of an error determined by status_to_error.
    """
    error_type, message = status_to_error[status]
    # This status is not an error.
    if error_type is None:
        return None

    # This status doesn't have a default error message, let's make one.
    if message is None:
        try:
            status_str = status_to_string(status)
        except ValueError:
            message = 'Code: {} (Protobuf definition mismatch?)'.format(status)
        else:
            message = 'Code: {} ({})'.format(status, status_str)
    return error_type(response=response, error_message=message)


def handle_unset_status_error(unset, field='status', statustype=None):
    """Decorate "error from response" functions to handle unset status field errors."""

    def decorator(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # See if the given field is the given "unset" value.
            _statustype = statustype if statustype else args[0]
            if getattr(args[0], field) == getattr(_statustype, unset):
                return UnsetStatusError(args[0])
            return func(*args, **kwargs)

        return wrapper

    return decorator


def handle_common_header_errors(func):
    """Decorate "error from response" functions to handle typical header errors."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Look for errors in the common response, before looking for specific errors.
        # pylint: disable=no-value-for-parameter
        return common_header_errors(*args) or func(*args, **kwargs)

    return wrapper


def handle_lease_use_result_errors(func):
    """Decorate "error from response" functions to handle typical lease errors."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # pylint: disable=no-value-for-parameter
        return common_lease_errors(*args) or func(*args, **kwargs)

    return wrapper


class BaseClient(object):
    """Helper base class for all clients to Boston Dynamics services."""

    _SPLIT_SERVICE = '.'
    _SPLIT_METHOD = '/'

    def __init__(self, stub_creation_func, name=None):
        self._service_type_short = getattr(self.__class__, 'service_type', 'BaseClient').split(BaseClient._SPLIT_SERVICE)[-1]

        self._channel = None
        self._logger = None
        self._name = name
        self._stub = None
        self._stub_creation_func = stub_creation_func

        self.logger = logging.getLogger(self._name or 'bosdyn.{}'.format(self._service_type_short))
        self.request_processors = []
        self.response_processors = []
        self.lease_wallet = None

    @staticmethod
    def request_trim_for_log(req):
        return '\n{}\n'.format(req)

    @staticmethod
    def response_trim_for_log(resp):
        return '\n{}\n'.format(resp)

    @property
    def channel(self):
        if self._channel is None:
            raise Error('Client channel is unset!')
        return self._channel

    @channel.setter
    def channel(self, channel):
        self._channel = channel
        self._stub = self._stub_creation_func(channel)

    def update_from(self, other):
        """Adopt key objects like processors, logger, and wallet from other."""
        self.request_processors = other.request_processors + self.request_processors
        self.response_processors = other.response_processors + self.response_processors
        self.logger = other.logger.getChild(self._name or self._service_type_short)
        self.lease_wallet = other.lease_wallet

    def call(self, rpc_method, request, value_from_response=None, error_from_response=None,
             **kwargs):
        """Returns result of calling rpc_method(request, **kwargs) after running processors.

        NOTE: value_from_response and error_from_response should not raise their own exceptions!
        """
        request = self._apply_request_processors(copy.deepcopy(request))
        logger = self._get_logger(rpc_method)
        logger.debug('blocking request: %s %s', rpc_method._method,
                     self.request_trim_for_log(request))
        try:
            response = rpc_method(request, **kwargs)
        except TransportError as e:
            raise translate_exception(e)

        response = self._apply_response_processors(response)
        logger.debug('response: %s %s', rpc_method._method, self.response_trim_for_log(response))
        if error_from_response is not None:
            exc = error_from_response(response)
        else:
            exc = None
        if exc is not None:
            raise exc
        if value_from_response is None:
            return response
        return value_from_response(response)

    def call_async(self, rpc_method, request, value_from_response=None, error_from_response=None,
                   **kwargs):
        """Returns a Future for rpc_method(request, **kwargs) after running processors.

        NOTE: value_from_response and error_from_response should not raise their own exceptions!
        """
        request = self._apply_request_processors(copy.deepcopy(request))
        logger = self._get_logger(rpc_method)
        logger.debug('async request: %s %s', rpc_method._method, self.request_trim_for_log(request))
        response_future = rpc_method.future(request, **kwargs)

        def on_finish(fut):
            try:
                result = fut.result()
            except Exception as exc:  # pylint: disable=broad-except
                logger.debug('async exception: %s\n%s\n', rpc_method._method, exc)
            else:
                try:
                    self._apply_response_processors(result)
                except Exception:  # pylint: disable=broad-except
                    logger.exception("Error applying response processors.")
                else:
                    logger.debug('async response: %s %s', rpc_method._method,
                                 self.response_trim_for_log(result))

        response_future.add_done_callback(on_finish)
        return FutureWrapper(response_future, value_from_response, error_from_response)

    def _apply_request_processors(self, request):
        if request is None:
            return
        for proc in self.request_processors:
            proc.mutate(request)
        return request

    def _apply_response_processors(self, response):
        if response is None:
            return
        for proc in self.response_processors:
            proc.mutate(response)
        return response

    def _get_logger(self, rpc_method):
        method_name = getattr(rpc_method, '_method', None)
        if method_name:
            method_name_short = str(method_name).split(BaseClient._SPLIT_METHOD)[-1]
            # This returns the same instance if it's been created before.
            return self.logger.getChild(method_name_short)
        return self.logger


class FutureWrapper():
    """Wraps a Future to aid more complicated clients' async calls."""

    def __init__(self, future, value_from_response, error_from_response):
        self.original_future = future
        self._error_from_response = error_from_response
        self._value_from_response = value_from_response

    def __repr__(self):
        return self.original_future.__repr__()

    def cancel(self):
        return self.original_future.cancel()

    def cancelled(self):
        return self.original_future.cancelled()

    def running(self):
        return self.original_future.running()

    def done(self):
        return self.original_future.done()

    def traceback(self, **kwargs):
        return self.original_future.traceback(**kwargs)

    def add_done_callback(self, cb):
        """Add callback executed on FutureWrapper when future is done."""
        self.original_future.add_done_callback(lambda not_used_original_future: cb(self))

    def result(self, **kwargs):
        """Get the result of the value_from_response(future.result())."""
        error = self.exception()
        if error is not None:
            raise error

        base_result = self.original_future.result(**kwargs)

        if self._value_from_response is None:
            return base_result

        return self._value_from_response(base_result)

    def exception(self, **kwargs):
        """Get exceptions from the Future, or from custom response processing."""
        error = self.original_future.exception(**kwargs)

        if error is None:	
            return self._error_from_response(self.original_future.result())	

        return translate_exception(error)
