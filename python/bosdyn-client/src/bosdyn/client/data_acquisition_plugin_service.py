# Copyright (c) 2020 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""A set of helper functions for implementing a Data Acquisition plugin service.

The DataAcquisitionPluginService class in this module is the recommended way to create a
plugin service for data acquisition.  To use it, you must define a function for performing the
data collection with the following signature:

``def data_collect_fn(request:AcquirePluginDataRequest, store_helper: DataAcquisitionStoreHelper)``

This function is responsible for collecting all of your plugin's data, and storing it with through
the store_helper. The store_helper (DataAcquisitionStoreHelper) kicks off asynchronous data store calls
for each piece of data, metadata, or images. The plugin service class has an internal helper function
which calls DataAcquisitionStoreHelper.wait_for_Stores_complete method that blocks until all saving
to the data acquistion store is finished. The helper class will monitor the futures for completion and
update the state status and errors appropriately.

If errors occur during the data collection+saving process, use state.add_errors to report which
intended DataIdentifiers had problems:

``state.add_errors([DataIdentifiers], 'Failure to collect data 1')``

Long-running acquisitions should be sure to call state.cancel_check() occasionally to exit early
and cleanly if the acquisition has been cancelled by the user or a timeout. If your plugin has
extra cleanup that it needs to perform in the event of a cancelled request, wrap your check
in a try-except block that can catch the RequestCancelledError thrown by the cancel_check function,
then perform the cleanup and re-raise the exception. For example::

    try:
        # Data collection and storage here
        state.cancel_check()
    except RequestCancelledError:
        # Perform cleanup here
        raise

Note, the data acquisition plugin service helper class will monitor and respond to the GetStatus RPC.
However, the data_collect_fn function should update the status to STATUS_SAVING when it transitions to
storing the data.
"""

from __future__ import print_function

import logging
import time
import threading
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from bosdyn.api import data_acquisition_pb2, data_acquisition_plugin_service_pb2_grpc, header_pb2
from bosdyn.api.data_acquisition_pb2 import DataAcquisitionCapability as Capability
from bosdyn.client import Robot
from bosdyn.client.data_acquisition_store import DataAcquisitionStoreClient
from bosdyn.client.util import populate_response_header

_LOGGER = logging.getLogger(__name__)

# How long should completed requests be queryable?
kDefaultRequestExpiration = 30


class RequestCancelledError(Exception):
    """The request has been cancelled and should no longer be handled."""


def make_error(data_id, error_msg, error_data=None):
    """Helper to simplify creating a DataError to send to RequestState.add_errors.

    Args:
        data_id (DataIdentifier): The proto for the data identifier which has an error.
        error_msg (string): The error message to associate with the data id.
        error_data (google.protobuf.Any): Additional data to be packed with the error.

    Returns:
        The DataError protobuf message for this errored data id.
    """
    proto = data_acquisition_pb2.DataError(data_id=data_id, error_message=error_msg)
    if error_data is not None:
        proto.error_data.Pack(error_data)
    return proto


class RequestState(object):
    """Interface for a data collection to update its state as it proceeds.

    Each AcquireData RPC made to the plugin service will create an instance of RequestState
    to manage the incoming acquisition request's overall state, including if it has been
    cancelled, any errors that occur, and the current status of the request.
    """

    # Statuses for the GetStatus RPC which indicate the data acquisition and saving is still
    # in progress and has not completed or failed.
    kNonError = {
        data_acquisition_pb2.GetStatusResponse.STATUS_ACQUIRING,
        data_acquisition_pb2.GetStatusResponse.STATUS_SAVING
    }

    def __init__(self):
        self._lock = threading.Lock()
        # Boolean indicating if a CancelAcquisition RPC has been recieved for this acquisition request.
        self._cancelled = False
        # The current status of the request, including any data errors.
        self._status_proto = data_acquisition_pb2.GetStatusResponse(
            status=data_acquisition_pb2.GetStatusResponse.STATUS_ACQUIRING)
        # The time which the acquisition request completes; used by the RequestManager for cleanup.
        self._completion_time = None

    def set_status(self, status):
        """Update the status of the request.

        Args:
            status (GetStatusResponse.Status): An updated status enum to be set in the
                                               stored GetStatusResponse.
        """
        with self._lock:
            self._cancel_check_locked()
            self._status_proto.status = status

    def set_complete_if_no_error(self, logger=None):
        """Mark that everything is complete."""
        with self._lock:
            self._cancel_check_locked()
            if self._status_proto.status in self.kNonError:
                self._status_proto.status = self._status_proto.STATUS_COMPLETE
                return True
            if logger:
                # Intentionally doing the formatting here while we're holding the lock.
                logger.error('Error encountered during request:\n{}'.format(self._status_proto))

        return False

    def add_saved(self, data_ids):
        """Record that some data was saved successfully.

        Args:
            data_ids (Iterable[DataId]): Data IDs that have been successfully saved.
        """
        with self._lock:
            self._cancel_check_locked()
            self._status_proto.data_saved.extend(data_ids)

    def add_errors(self, data_errors):
        """Report that some errors have occurred during the data capture.
        Use the make_error function to simplify creating data errors.

        Args:
            data_errors (Iterable[DataError]): data errors to include as errors in the status.
        """
        with self._lock:
            self._cancel_check_locked()
            self._status_proto.data_errors.extend(data_errors)
            self._status_proto.status = data_acquisition_pb2.GetStatusResponse.STATUS_DATA_ERROR
            _LOGGER.error('Errors occurred during acquisition:\n%s', data_errors)

    def has_data_errors(self):
        """Return True if any data errors have been added to this status."""
        with self._lock:
            self._cancel_check_locked()
            return bool(self._status_proto.data_errors)

    def cancel_check(self):
        """Raises RequestCancelledError if the request has already been cancelled."""
        with self._lock:
            self._cancel_check_locked()

    def is_cancelled(self):
        """Query if the request is already cancelled."""
        with self._lock:
            return self._cancelled

    def _cancel_check_locked(self):
        if self._cancelled:
            raise RequestCancelledError


class DataAcquisitionStoreHelper(object):
    """This class simplifies the management of data acquisition stores for a single request.

    Request state will be updated according to store progress.

    Args:
        store_client (bosdyn.client.DataAcquisitionStoreClient): A data acquisition store client.
        state (RequestState): state of the request, to be modified with errors or completion.
        cancel_interval (float): How often to check for cancellation of the request while
            waiting for the futures to complete.

    Attributes:
        store_client (bosdyn.client.DataAcquisitionStoreClient): A data acquisition store client.
        state (RequestState): state of the request, to be modified with errors or completion.
        cancel_interval (float): How often to check for cancellation of the request while
            waiting for the futures to complete.
        data_id_future_pairs (List[Pair(DataIdentifier, Future)]): The data identifier and the associated
            future which results from the async store data rpc.
    """

    def __init__(self, store_client, state, cancel_interval=1):
        self.store_client = store_client
        self.state = state
        self.cancel_interval = cancel_interval
        self.data_id_future_pairs = []

    def store_metadata(self, metadata, data_id):
        """Store metadata with the data acquisition store service.

        Args:
            metadata (bosdyn.api.AssociatedMetadata): Metadata message to store.
            data_id (bosdyn.api.DataIdentifier) : Data identifier to use for storing this data.

        Raises:
            RPCError: Problem communicating with the robot.
        """
        future = self.store_client.store_metadata_async(metadata, data_id)
        self.data_id_future_pairs.append((data_id, future))

    def store_image(self, image_capture, data_id):
        """Store an image with the data acquisition store service.

        Args:
            image_capture (bosdyn.api.ImageCapture): Image to store.
            data_id (bosdyn.api.DataIdentifier) : Data identifier to use for storing this data.

        Raises:
            RPCError: Problem communicating with the robot.
        """
        future = self.store_client.store_image_async(image_capture, data_id)
        self.data_id_future_pairs.append((data_id, future))

    def store_data(self, message, data_id, file_extension=None):
        """Store a data message with the data acquisition store service.

        Args:
            message (bytes): Data to store.
            data_id (bosdyn.api.DataIdentifier) : Data identifier to use for storing this data.
            file_extension (string) : File extension to use for writing the data to a file.

        Raises:
            RPCError: Problem communicating with the robot.
        """
        future = self.store_client.store_data_async(message, data_id, file_extension)
        self.data_id_future_pairs.append((data_id, future))

    def cancel_check(self):
        """Raises RequestCancelledError if the request has already been cancelled."""
        self.state.cancel_check()

    def wait_for_stores_complete(self):
        """Block and wait for all stores to complete. Update state with store success/failures.

        Raises:
            RequestCancelledError: The data acquisition request was cancelled.
        """
        self.state.cancel_check()

        # Block until all futures are done.
        while not all(future.done() for _, future in self.data_id_future_pairs):
            time.sleep(self.cancel_interval)
            self.state.cancel_check()

        # Check each future status and update the status saved and errors.
        for data_id, future in self.data_id_future_pairs:
            if future.exception() is None:
                self.state.add_saved([data_id])
            else:
                self.state.add_errors([
                    make_error(data_id, 'Failed to store data: {}'.format(future.exception()))])

        return not self.state.has_data_errors()


class DataAcquisitionPluginService(
        data_acquisition_plugin_service_pb2_grpc.DataAcquisitionPluginServiceServicer):
    """Implementation of a data acquisition plugin. It relies on the provided data_collect_fn
    to implement the heart of the data collection and storage.

    Args:
        robot: Authenticated robot object.
        capabilities: List of DataAcquisitionCapability that describe what this plugin can do.
        data_collect_fn: Function that performs the data collection and storage. Ordered input
            arguments (to data_collect_fn): data_acquisition_pb2.AcquirePluginDataRequest, DataAcquisitionStoreHelper.
            Output(to data_collect_fn): None
        acquire_response_fn: Optional function that can validate a request and provide a timeout deadline. Function returns
            a boolean indicating if the request is valid; if False, the response is returned immediately without calling
            the data collection function or saving any data. Ordered input arguments (to acquire_response_fn):
            data_acquisition_pb2.AcquirePluginDataRequest, data_acquisition_pb2.AcquirePluginDataResponse. Output (to
            data_collect_fn): Boolean
        executor: Optional thread pool.

    Attributes:
        logger (logging.Logger): Logger used by the service.
        capabilities (List[DataAcquisitionCapability]): List of capabilities that describe what
            this plugin can do.
        data_collect_fn: Function that performs the data collection and storage.
        acquire_response_fn: Function that can validate a request and provide a timeout deadline.
        request_manager (RequestManager): Helper class which manages the RequestStates created with
            each acquisition RPC.
        executor (ThreadPoolExecutor): Thread pool to run the plugin service on.
        robot (Robot): Authenticated robot object.
        store_client (DataAcqusitionStoreClient): Client for the data acquisition store service.
    """
    service_type = 'bosdyn.api.DataAcquisitionPluginService'

    def __init__(self, robot, capabilities, data_collect_fn, acquire_response_fn=None,
                 executor=None, logger=None):
        super(DataAcquisitionPluginService, self).__init__()
        self.logger = logger or _LOGGER
        self.capabilities = capabilities
        self.data_collect_fn = data_collect_fn
        self.acquire_response_fn = acquire_response_fn
        self.request_manager = RequestManager()
        self.executor = executor or ThreadPoolExecutor(max_workers=2)
        self.robot = robot
        self.store_client = robot.ensure_client(DataAcquisitionStoreClient.default_service_name)

    def _data_collection_wrapper(self, request_id, request, state):
        """Helper function which initiates the data collection and storage in sequence.

        Args:
            request_id (int): The request_id for the acquisition request being inspected.
            request (DataAcquisitionPluginRequest): The data acquisition request.
            state (RequestState): The associated internal request state for the data.
        """
        try:
            store_helper = DataAcquisitionStoreHelper(self.store_client, state)
            self.data_collect_fn(request, store_helper)
            store_helper.wait_for_stores_complete()
            state.set_complete_if_no_error(logger=self.logger)
        except RequestCancelledError:
            # Cannot use set_status because it will raise the exception again.
            with state._lock:
                state._status_proto.status = state._status_proto.STATUS_ACQUISITION_CANCELLED
            self.logger.info('Request %d cancelled', request_id)
        except Exception as e:  # pylint: disable=broad-except
            self.logger.exception("Failed during call to user function")
            with state._lock:
                state._status_proto.status = state._status_proto.STATUS_INTERNAL_ERROR
                state._status_proto.header.error.message = str(e)

        finally:
            self.request_manager.mark_request_finished(request_id)
            self.logger.info('Finished request %d', request_id)

    def AcquirePluginData(self, request, context):
        """Trigger a data acquisition and store results in the data acquisition store service.

        Args:
            request (data_acquisition_pb2.AcquirePluginDataRequest): The data acquisition request.
            context (GRPC ClientContext): tracks internal grpc statuses and information.

        Returns:
            An AcquirePluginDataResponse containing a request_id to use with GetStatus.
        """
        response = data_acquisition_pb2.AcquirePluginDataResponse()
        if self.acquire_response_fn is not None:
            try:
                if not self.acquire_response_fn(request, response):
                    return response
            except Exception as e:
                self.logger.exception('Failed during call to user acquire response function')
                populate_response_header(response, request,
                                         error_code=header_pb2.CommonError.CODE_INTERNAL_ERROR,
                                         error_msg=str(e))
                return response
        self.request_manager.cleanup_requests()
        response.request_id, state = self.request_manager.add_request()
        self.logger.info('Beginning request %d for %s', response.request_id,
                         [capture.name for capture in request.acquisition_requests.data_captures])
        self.executor.submit(self._data_collection_wrapper, response.request_id, request, state)
        response.status = data_acquisition_pb2.AcquireDataResponse.STATUS_OK
        populate_response_header(response, request)
        return response

    def GetStatus(self, request, context):
        """Query the status of a data acquisition by ID.

        Args:
            request (data_acquisition_pb2.GetStatusRequest): The get status request.
            context (GRPC ClientContext): tracks internal grpc statuses and information.

        Returns:
            An GetStatusResponse containing the details of the data acquisition.
        """
        try:
            response = self.request_manager.get_status_proto(request.request_id)
        except KeyError:
            response = data_acquisition_pb2.GetStatusResponse()
            response.status = response.STATUS_REQUEST_ID_DOES_NOT_EXIST
        populate_response_header(response, request)
        return response

    def GetServiceInfo(self, request, context):
        """Get a list of data acquisition capabilities.

        Args:
            request (data_acquisition_pb2.GetServiceInfoRequest): The get service info request.
            context (GRPC ClientContext): tracks internal grpc statuses and information.

        Returns:
            An GetServiceInfoResponse containing the list of data acquisition capabilities for the plugin.
        """
        response = data_acquisition_pb2.GetServiceInfoResponse()
        response.capabilities.data_sources.extend(self.capabilities)
        populate_response_header(response, request)
        return response

    def CancelAcquisition(self, request, context):
        """Cancel a data acquisition by ID.

        Args:
            request (data_acquisition_pb2.CancelAcquisitionRequest): The cancel acquisition request.
            context (GRPC ClientContext): tracks internal grpc statuses and information.

        Returns:
            An CancelAcquisitionResponse containing the status of the cancel operation.
        """
        response = data_acquisition_pb2.CancelAcquisitionResponse()
        try:
            self.request_manager.mark_request_cancelled(request.request_id)
            self.logger.info('Cancelling request %d', request.request_id)

        except KeyError:
            response.status = response.STATUS_REQUEST_ID_DOES_NOT_EXIST
        else:
            response.status = response.STATUS_OK
        populate_response_header(response, request)
        return response


# pylint: disable=protected-access
class RequestManager:
    """Manage request lifecycles and status.

    The RequestManager manages some internals of the RequestState class, so it will access its
    protected variables.  We leave those variables protected so that users of the RequestState
    class are less tempted to fiddle with them incorrectly, but we turn off the linting for the
    rest of this file.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._requests = {}
        self._counter = 0

    def add_request(self):
        """Create a new request to manage"""
        with self._lock:
            self._counter += 1
            state = RequestState()
            self._requests[self._counter] = state
            return self._counter, state

    def get_request_state(self, request_id):
        """Get the RequestState object for managing a request.

        Args:
            request_id (int): The request_id for the acquisition request being inspected.
        """
        with self._lock:
            return self._requests[request_id]

    def get_status_proto(self, request_id):
        """Get a copy of the current status for the specified request.

        Args:
            request_id (int): The request_id for the acquisition request being inspected.
        """
        state = self.get_request_state(request_id)
        status = data_acquisition_pb2.GetStatusResponse()
        with state._lock:
            status.CopyFrom(state._status_proto)
        return status

    def mark_request_cancelled(self, request_id):
        """Mark a request as cancelled, and no longer able to be updated.

        Args:
            request_id (int): The request_id for the acquisition request being cancelled.
        """
        state = self.get_request_state(request_id)
        with state._lock:
            state._cancelled = True
            state._status_proto.status = state._status_proto.STATUS_CANCEL_IN_PROGRESS

    def mark_request_finished(self, request_id):
        """Mark a request as finished, and able to be removed later.

        Args:
            request_id (int): The request_id for the acquisition request being completed.
        """
        state = self.get_request_state(request_id)
        with state._lock:
            state._completion_time = time.time()

    def cleanup_requests(self, older_than_time=None):
        """Remove all requests that were completed farther in the past than older_than_time.

        Defaults to removing anything older than 30 seconds.

        Args:
            older_than_time (float): Optional time (in seconds) that requests will be removed after.
        """
        older_than_time = older_than_time or time.time() - kDefaultRequestExpiration
        with self._lock:
            # Grab the contents to iterate through outside of the lock
            requests = list(self._requests.items())
        to_remove = []
        for request_id, state in requests:
            with state._lock:
                if state._completion_time is not None and state._completion_time < older_than_time:
                    to_remove.append(request_id)
        with self._lock:
            for key in to_remove:
                # Won't fail even if the key was already removed
                self._requests.pop(key, None)
