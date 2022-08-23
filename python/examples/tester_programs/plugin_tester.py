# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Example to test the functionality of a bosdyn.api.DataAcquisitionPluginService in development."""
from __future__ import print_function

import argparse
import datetime
import functools
import logging
import os
import sys
import time

# Logger for all the debug information from the tests.
_LOGGER = logging.getLogger("Plugin Tester")

from testing_helpers import (log_debug_information, run_test, test_directory_registration,
                             test_if_service_has_active_service_faults,
                             test_if_service_is_reachable)

import bosdyn.client
import bosdyn.client.util
from bosdyn.api import data_acquisition_pb2, data_acquisition_store_pb2
from bosdyn.client.data_acquisition import (CancellationFailedError, DataAcquisitionClient,
                                            RequestIdDoesNotExistError)
from bosdyn.client.data_acquisition_helpers import (download_data_REST,
                                                    make_time_query_params_from_group_name)
from bosdyn.client.data_acquisition_plugin import DataAcquisitionPluginClient
from bosdyn.client.data_acquisition_store import DataAcquisitionStoreClient
from bosdyn.client.exceptions import InvalidRequestError, ResponseError
from bosdyn.client.util import setup_logging

# The sets of statuses for the GetStatus RPC that indicate the acquisition is continuing still, complete, or has failed.
kAcquisitionContinuesStatuses = {
    data_acquisition_pb2.GetStatusResponse.STATUS_ACQUIRING,
    data_acquisition_pb2.GetStatusResponse.STATUS_SAVING
}
kAcquisitionFailedStatuses = {
    data_acquisition_pb2.GetStatusResponse.STATUS_DATA_ERROR,
    data_acquisition_pb2.GetStatusResponse.STATUS_TIMEDOUT,
    data_acquisition_pb2.GetStatusResponse.STATUS_INTERNAL_ERROR,
    data_acquisition_pb2.GetStatusResponse.STATUS_REQUEST_ID_DOES_NOT_EXIST
}
kAcquisitionSucceededStatuses = {data_acquisition_pb2.GetStatusResponse.STATUS_COMPLETE}

# The sets of statuses for the GetStatus RPC that indicate the acquisition is continuing still, complete, or has failed
# after a cancellation RPC.
kAcquisitionCancellationSucceededStatuses = {
    data_acquisition_pb2.GetStatusResponse.STATUS_ACQUISITION_CANCELLED
}
kAcquisitionCancellationContinuesStatuses = {
    data_acquisition_pb2.GetStatusResponse.STATUS_CANCEL_IN_PROGRESS
}
kAcquisitionCancellationFailedStatuses = {
    data_acquisition_pb2.GetStatusResponse.STATUS_CANCEL_ACQUISITION_FAILED
}

# The maximum time to wait for a GetStatus RPC to complete.
kMonitorStatusTimeoutSecs = 40


def test_if_data_sources_are_available(plugin_client, main_daq_client, verbose):
    """Checks that the data sources listed by the data acquisition plugin service are valid and all appear in the
    on-robot data acquisition service's complete set of data sources.

    Args:
        plugin_client (DataAcquisitionPluginClient): The client for the data acquisition plugin service being tested.
        main_daq_client (DataAcquisitionClient): The client for the data acquisition service running on robot.
        verbose (boolean): Print additional logging information on failure.

    Returns:
        A boolean indicating that the data sources are fully specified and are listed in the data
        acquisition service, as well as the list of DataCapability proto messages resp
    """
    plugin_service_info = plugin_client.get_service_info()
    # Check that the data source is not an ImageCapability, since these will only
    # be added by the DAQ service for image services.
    if len(plugin_service_info.image_sources) > 0:
        _LOGGER.error(
            "A DataAcquisitionPluginService is not allowed to advertise ImageCapabilities. These "
            "will be created by the main, on-robot data acquisition service for all ImageService services."
        )
        if verbose:
            _LOGGER.info("Capabilities found for the plugin service: %s", plugin_service_info)
        return False, []

    # Get the data sources from the on-robot DAQ service.
    main_daq_service_info = main_daq_client.get_service_info()
    main_daq_data_sources = {src.name for src in main_daq_service_info.data_sources}

    # Iterate through all the plugin service's data sources and make sure they appear in the list of all data
    # sources from the DAQ service.
    data_source_names_not_found = set()
    _LOGGER.info("The following capabilities are advertised by the plugin: ")
    for data_source in plugin_service_info.data_sources:
        _LOGGER.info("Plugin data source: %s", data_source)
        if data_source.name not in main_daq_data_sources:
            data_source_names_not_found.add(data_source.name)

        if not data_source.description:
            _LOGGER.warning(
                "The DataAcquisitionCapability %s has no 'description' field populated and will "
                "not appear in the tablet.", data_source.name)

    if len(data_source_names_not_found) == len(plugin_service_info.data_sources):
        _LOGGER.error(
            "None of the plugin's data sources are being detected by the data acquisition "
            "service. Try rebooting the robot and restarting the plugin service.")
        if verbose:
            _LOGGER.info(
                "The data acquisition service's complete set of DataAcquisitionCapability names: %s",
                main_daq_data_sources)
        return False, []

    if len(data_source_names_not_found) > 0:
        # Missing plugin data sources in the daq service's set of data-sources.
        missing_srcs_string = ""
        for index, src_name in enumerate(data_source_names_not_found):
            missing_srcs_string += src_name
            if index != len(data_source_names_not_found) - 1:
                missing_srcs_string += ", "
        _LOGGER.error(
            "The following data sources are not appearing in the data acquisition service: %s."
            "Make sure the DataAcquisitionCapability name field is unique amongst all other data capabilities.",
            missing_srcs_string)
        if verbose:
            _LOGGER.info(
                "The data acquisition service's complete set of DataAcquisitionCapability names: %s",
                main_daq_data_sources)
        return False, []

    return True, [src for src in plugin_service_info.data_sources]


def acquire_data_and_check_errors(acquisition_request, data_acq_client, capability_name,
                                  action_name, group_name, verbose):
    """Helper function which makes the acquisition request for this data source and checks for errors.

    Args:
        acquisition_request (AcquisitionRequestList): The acquisition request for the capability_name.
        data_acq_client (DataAcquisitionClient): The client for the on-robot data acquisition service.
        capability_name (string): The data source name being acquired.
        action_name (string): The action name for saving in the CaptureActionId of the AcquireData request.
        group_name (string): The group name for saving in the CaptureActionId of the AcquireData request.
        verbose (boolean): Print additional logging information on failure.

    Returns:
        A tuple consisting of 1) a boolean indicating that the AcquireData RPC completed without any errors,
        and 2) an integer representing the request_id for the acquisition request. The request_id will be None
        if the AcquireData RPC fails.
    """
    acquire_data_request_id = None
    try:
        # Issue the AcquireData RPC to the on-robot data acquisition service.
        acquire_data_request_id = data_acq_client.acquire_data(acquisition_request, action_name,
                                                               group_name)
    except InvalidRequestError as err:
        _LOGGER.error("The AcquireData RPC to the data-acquisition service for %s was invalid: %s",
                      capability_name, err.error_message)
        if verbose:
            _LOGGER.info(
                "The capture action ID associated with the request: %s",
                data_acquisition_pb2.CaptureActionId(action_name=action_name,
                                                     group_name=group_name))
            log_debug_information(err, acquisition_request)
        return False, acquire_data_request_id
    except ResponseError as err:
        _LOGGER.error(
            "Exception raised when testing the AcquireData RPC to the data-acquisition service for %s: %s",
            capability_name, err)
        if verbose:
            _LOGGER.info(
                "The capture action ID associated with the request: %s",
                data_acquisition_pb2.CaptureActionId(action_name=action_name,
                                                     group_name=group_name))
            log_debug_information(err, acquisition_request)
        return False, acquire_data_request_id
    return True, acquire_data_request_id


def monitor_status_until_complete_or_failed(request_id, client, capability_name, action_name,
                                            verbose):
    """Helper status that monitors the status (using the GetStatus RPC) for the acquisition request until it
    completes, fails, or times out.

    Args:
        request_id (int): The request_id for the acquisition request (returned by the AcquireData RPC).
        client (DataAcquisitionClient): The client for the data acquisition service running on robot.
        capability_name (string): The data source name being acquired.
        action_name (string): The action name from the AcquireData RPC being monitored.
        verbose (boolean): Print additional logging information on failure.

    Returns:
        A boolean indicating that the GetStatus RPC eventually received a "complete" status.
    """
    start_time = time.time()
    should_continue = time.time() - start_time < kMonitorStatusTimeoutSecs
    while should_continue:
        get_status_response = None
        try:
            get_status_response = client.get_status(request_id)
        except ResponseError as err:
            _LOGGER.error(
                "Exception raised when monitoring the status of request %s for data '%s' with action_name '%s'.",
                request_id, capability_name, action_name)
            if verbose:
                log_debug_information(err)
            return False

        if get_status_response.status in kAcquisitionSucceededStatuses:
            return True
        elif get_status_response.status in kAcquisitionFailedStatuses:
            _LOGGER.error(
                "Request %s for data '%s' with action_name '%s' failed the GetStatus RPC with status %s.",
                request_id, capability_name, action_name,
                data_acquisition_pb2.GetStatusResponse.Status.Name(get_status_response.status))
            if verbose:
                _LOGGER.info("The full GetStatus response: %s", get_status_response)
            return False
        elif get_status_response.status in kAcquisitionContinuesStatuses:
            # Sleep briefly, then re-attempt to make a GetStatus RPC to see if the acquisition has completed.
            time.sleep(0.2)
            should_continue = time.time() - start_time < kMonitorStatusTimeoutSecs
            continue
        else:
            _LOGGER.error(
                "Unexpected status %s when monitoring request %s for data '%s' with action_name '%s'.",
                data_acquisition_pb2.GetStatusResponse.Status.Name(get_status_response.status),
                request_id, capability_name, action_name)
            if verbose:
                _LOGGER.info("The full GetStatus response: %s", get_status_response)
            return False

    _LOGGER.warning(
        "No result to the GetStatus RPC within %s seconds for request %s of data '%s' with action_name '%s'.",
        kMonitorStatusTimeoutSecs, request_id, capability_name, action_name)
    return True


def test_capabilities_acquires_and_saves(capabilities, data_acq_client, data_store_client,
                                         group_name, verbose):
    """Checks that each capability can individually be acquired, saved to the data store, and respond with
    a status "complete". Also checks the same sequence of events for an acquisition requesting all data
    source at once.

    Args:
        capabilities (list): All the data source capabilities listed for the plugin service (using the
                             GetServiceInfo RPC).
        data_acq_client (DataAcquisitionClient): The client for the data acquisition service running on robot.
        data_store_client (DataAcquisitionStoreClient): The client for the data acquisition store service running on robot.
        group_name (string): Group name for saving in the CaptureActionId of every acquisition tested.
        verbose (boolean): Print additional logging information on failure.

    Returns:
        A boolean indicating that every capability received a "complete" status for the GetStatus RPC and an action id for
        the acquisition can be found in the data store.
    """
    success = True
    # Test each capability individually.
    for capability in capabilities:
        action_name = "acquire and status check: " + capability.name
        acquisition_request = data_acquisition_pb2.AcquisitionRequestList()
        acquisition_request.data_captures.extend(
            [data_acquisition_pb2.DataCapture(name=capability.name)])
        capability_success = acquire_get_status_and_save(acquisition_request, capability.name,
                                                         action_name, group_name, data_acq_client,
                                                         data_store_client, verbose)
        success = capability_success and success

    # Test requesting all the capabilities at once (if there are more than one data capabilities available).
    if len(capabilities) > 1:
        action_name = "acquire and status check: all data at once"
        acquisition_request = data_acquisition_pb2.AcquisitionRequestList()
        acquisition_request.data_captures.extend(
            [data_acquisition_pb2.DataCapture(name=capability.name) for capability in capabilities])
        all_capabilities_success = acquire_get_status_and_save(acquisition_request, "all data",
                                                               action_name, group_name,
                                                               data_acq_client, data_store_client,
                                                               verbose)
        success = all_capabilities_success and success

    return success


def acquire_get_status_and_save(acquisition_request, capability_name, action_name, group_name,
                                data_acq_client, data_store_client, verbose):
    """Helper function which issues an acquisition request and checks that its data is saved to the data store, and the
    GetStatus RPC eventually respond with a status "complete".

    Args:
        acquisition_request (AcquisitionRequestList): The acquisition request proto message to send to the AcquireData RPC.
        capability_name (string): The name of the data capability being acquired.
        action_name (string): The action name for the acquisition request's CaptureActionId.
        group_name (string): The group name for the acquisition request's CaptureActionId.
        data_acq_client (DataAcquisitionClient): The client for the data acquisition service running on robot.
        data_store_client (DataAcquisitionStoreClient): The client for the data acquisition store service running on robot.
        verbose (boolean): Print additional logging information on failure.

    Returns:
        A boolean indicating that the acquisition request received a "complete" status for the GetStatus RPC and
        an action id for the acquisition can be found in the data store.
    """
    # Make a request for this data capability and check that it completes successfully.
    acquire_success, acquired_request_id = acquire_data_and_check_errors(
        acquisition_request, data_acq_client, capability_name, action_name, group_name, verbose)
    if not acquire_success:
        # Exit early if the AcquireData RPC did not succeed and did not return a request_id.
        return False
    success = monitor_status_until_complete_or_failed(acquired_request_id, data_acq_client,
                                                      capability_name, action_name, verbose)

    if success:
        # If the GetStatus responds with "Complete", then check the data store for the action id.
        action_id = data_acquisition_pb2.CaptureActionId(action_name=action_name,
                                                         group_name=group_name)
        query_params = data_acquisition_store_pb2.DataQueryParams(
            action_ids=data_acquisition_store_pb2.ActionIdQuery(action_ids=[action_id]))
        try:
            saved_capture_actions = data_store_client.list_capture_actions(query_params)
            if len(saved_capture_actions) == 0:
                # Nothing saved with a matching action and group name!
                _LOGGER.error(
                    "The request %s for data '%s' with action_name '%s' did NOT save to the data "
                    "acquisition store or returned prematurely with a STATUS_COMPLETE in the GetStatus RPC.",
                    acquired_request_id, capability_name, action_name)
                if verbose:
                    _LOGGER.info("ListCaptureAction RPC's query parameters: ", query_params)
                return False
        except ResponseError as err:
            _LOGGER.error(
                "Exception raised when checking if request %s for data '%s' with action_name '%s' was "
                "saved in the data acquisition store.", request_id, capability_name, action_name)
            if verbose:
                log_debug_information(err)
            return False
    else:
        # The GetStatus checks failed in some way.
        return False

    # The acquisition request went through, the GetStatus RPC responded with "status complete" and the data was
    # successfully found in the data store service.
    return True


def cancel_request_and_monitor_status(request_id, client, capability_name, action_name, verbose):
    """Helper status that monitors the status (using the GetStatus RPC) for the acquisition request after it
    is cancelled until it receives a "cancellation complete" status, or fails and times out.

    Args:
        request_id (int): The request_id for the acquisition request (returned by the AcquireData RPC).
        client (DataAcquisitionClient): The client for the data acquisition service running on robot.
        capability_name (string): The data source name being acquired.
        action_name (string): The action name from the AcquireData RPC being monitored.
        verbose (boolean): Print additional logging information on failure.

    Returns:
        A boolean indicating that the GetStatus RPC eventually received a "cancellation complete" status.
    """
    try:
        cancel_res = client.cancel_acquisition(request_id)
    except CancellationFailedError as err:
        _LOGGER.error(
            "The CancelAcquisition RPC for request %s of data '%s' with action_name '%s' failed. "
            "Check that the CancelAcquisition RPC is implemented and working in the plugin service.",
            request_id, capability_name, action_name)
        if verbose:
            log_debug_information(err)
        return False
    except RequestIdDoesNotExistError as err:
        _LOGGER.error(
            "The request ID %s for data '%s' with action_name '%s' does not exist. Something may have "
            "gone wrong with the AcquireData request or the id was not saved/deleted by the plugin service.",
            request_id, capability_name, action_name)
        if verbose:
            log_debug_information(err)
        return False
    except ResponseError as err:
        _LOGGER.error(
            "Exception raised when cancelling request %s for data '%s' with action_name '%s'.",
            request_id, capability_name, action_name)
        if verbose:
            log_debug_information(err)
        return False

    start_time = time.time()
    should_continue = time.time() - start_time < kMonitorStatusTimeoutSecs
    first_time_warning = True
    while should_continue:
        get_status_response = None
        try:
            get_status_response = client.get_status(request_id)
        except ResponseError as err:
            _LOGGER.error(
                "Exception raised when monitoring the cancellation status of request %s for data '%s'"
                " with action_name '%s'.", request_id, capability_name, action_name)
            if verbose:
                log_debug_information(err)
            return False

        if get_status_response.status in kAcquisitionCancellationSucceededStatuses:
            return True
        elif get_status_response.status in kAcquisitionCancellationContinuesStatuses:
            # Sleep briefly, then re-attempt to make a GetStatus RPC to see if the acquisition has cancelled.
            time.sleep(0.2)
        elif get_status_response.status in kAcquisitionContinuesStatuses:
            # Warning that plugin did not update status to reflect that cancel rpc was received.
            if first_time_warning:
                _LOGGER.warning(
                    "The plugin did not update the status to reflect that a CancelAcquisition RPC was received. Try "
                    "setting the status as STATUS_CANCEL_IN_PROGRESS after responding to the RPC.")
                _LOGGER.info("Request %s for data '%s' with action_name '%s", request_id,
                             capability_name, action_name)
                if verbose:
                    _LOGGER.info("Request %s for data '%s' with action_name '%s", request_id,
                                 capability_name, action_name)
                    _LOGGER.info("The full GetStatus response: %s", get_status_response)
                first_time_warning = False
            # Sleep briefly, then re-attempt to make a GetStatus RPC to see if the acquisition has cancelled.
            time.sleep(0.2)
        elif get_status_response.status in kAcquisitionCancellationFailedStatuses:
            # Cancellation-specific failure.
            _LOGGER.error(
                "The cancellation request %s for data '%s' with action_name '%s' failed the GetStatus "
                "RPC with status %s.", request_id, capability_name, action_name,
                data_acquisition_pb2.GetStatusResponse.Status.Name(get_status_response.status))
            if verbose:
                _LOGGER.info("The full GetStatus response: %s", get_status_response)
            return False
        elif get_status_response.status in kAcquisitionFailedStatuses:
            # Failed for reason other than cancellation failed statuses.
            _LOGGER.error(
                "The cancellation request %s for data '%s' with action_name '%s' failed the GetStatus RPC with status %s."
                "This is not an expected failure status after a CancelAcquisition RPC.", request_id,
                capability_name, action_name,
                data_acquisition_pb2.GetStatusResponse.Status.Name(get_status_response.status))
            if verbose:
                _LOGGER.info("The full GetStatus response: %s", get_status_response)
            return False
        else:
            _LOGGER.error(
                "Unexpected status %s when monitoring cancellation request %s for data '%s' with action_name '%s'.",
                data_acquisition_pb2.GetStatusResponse.Status.Name(get_status_response.status),
                request_id, capability_name, action_name)
            if verbose:
                _LOGGER.info("The full GetStatus response: %s", get_status_response)
            return False

        should_continue = time.time() - start_time < kMonitorStatusTimeoutSecs

    _LOGGER.warning(
        "Did not get a result for the GetStatus RPC within %s seconds for request %s of data '%s' with "
        "action_name '%s'.", kMonitorStatusTimeoutSecs, request_id, capability_name, action_name)
    return True


def test_cancelling(capabilities, data_acq_client, group_name, verbose):
    """Checks that each capability can be cancelled successfully after the acquisition begins.

    Args:
        capabilities (list): All the data source capabilities listed for the plugin service (using the
                             GetServiceInfo RPC).
        data_acq_client (DataAcquisitionClient): The client for the data acquisition service running on robot.
        group_name (string): Group name for saving in the CaptureActionId of every acquisition tested.
        verbose (boolean): Print additional logging information on failure.

    Returns:
        A boolean indicating that every capability responds to the CancelAcquisition RPC and received a "cancellation
        complete" status for the GetStatus RPC.
    """
    all_cancels_succeed = True
    for capability in capabilities:
        acquisition_request = data_acquisition_pb2.AcquisitionRequestList()
        acquisition_request.data_captures.extend(
            [data_acquisition_pb2.DataCapture(name=capability.name)])

        # Make a request for this data capability and then attempt to cancel the request immediately after.
        action_name = "cancel acquisition check: " + capability.name
        request_id = data_acq_client.acquire_data(acquisition_request, action_name, group_name)
        success = cancel_request_and_monitor_status(request_id, data_acq_client, capability.name,
                                                    action_name, verbose)
        if not success:
            all_cancels_succeed = False

    return all_cancels_succeed


def test_downloading_all_data_via_REST(data_store_client, group_name, robot_hostname, robot,
                                       destination_folder):
    """Check that all of the data can successfully be downloaded via the REST endpoint.

    Args:
        data_store_client (DataAcquisitionStoreClient): The client for the data acquisition store service running on robot.
        group_name (string): The group name for all the acquisitions during the test, such that we can determine
                             which data to download.
        robot_hostname (string): The hostname for the robot used for testing.
        robot (Robot): The SDK robot object created for the robot used for testing.
        destination_folder (string): The filepath for where the downloaded data will be saved.

    Returns:
        Boolean indicating if the REST download succeeded or not.
    """
    # Make the download data request with a time query parameter.
    query_params = make_time_query_params_from_group_name(group_name, data_store_client)
    success = download_data_REST(query_params, robot_hostname, robot.user_token, destination_folder)
    return success


def main(argv):
    """Main testing interface."""
    parser = argparse.ArgumentParser()
    bosdyn.client.util.add_base_arguments(parser)
    parser.add_argument(
        "--service-name", required=True, type=str,
        help="Unique service name for the data acquisition plugin service being tested.")
    parser.add_argument('--destination-folder',
                        help=('The folder where the data should be downloaded to.'), required=False,
                        default='.')
    options = parser.parse_args(argv)

    # Setup logger specific for this test program.
    streamlog = logging.StreamHandler()
    streamlog.setLevel(logging.INFO)
    streamlog.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    _LOGGER.addHandler(streamlog)
    _LOGGER.setLevel(logging.INFO)
    setup_logging()

    sdk = bosdyn.client.create_standard_sdk('TestDAQPlugin')
    sdk.register_service_client(DataAcquisitionPluginClient)
    robot = sdk.create_robot(options.hostname)
    bosdyn.client.util.authenticate(robot)
    robot.time_sync.wait_for_sync()
    robot.sync_with_directory()

    # Create a group name for all data collected during this test of the plugin service
    group_name = "Plugin [%s] Test %s" % (options.service_name,
                                          datetime.datetime.today().strftime("%b %d %Y %H:%M:%S"))

    # Create a client for the data-acquisition service on robot.
    main_daq_client = robot.ensure_client(DataAcquisitionClient.default_service_name)

    # Create a client for the data store.
    data_store_client = robot.ensure_client(DataAcquisitionStoreClient.default_service_name)

    # Test the directory registration of the plugin.
    run_test(test_directory_registration, "DAQ Plugin is registered in the robot's directory.",
             robot, options.service_name, DataAcquisitionPluginClient.service_type)

    # Now create a data acquisition plugin client for the plugin service since we know it is
    # registered in the directory.
    robot.sync_with_directory()
    plugin_daq_client = robot.ensure_client(options.service_name)

    # Test that the gRPC communications go through to the plugin service.
    run_test(test_if_service_is_reachable,
             ("Plugin's directory registration networking information "
              "is correct and the plugin can be communicated with via gRPC."),
             plugin_daq_client.get_service_info)

    # Test if there are any active service faults thrown by the plugin service in the current
    # robot state proto.
    run_test(test_if_service_has_active_service_faults, "The plugin service has no active service "
             "faults in the current robot state.", robot, options.service_name)

    # Test that the data-acquisition plugin service is detected by the data acquisition service
    # on robot and that the plugin's data sources are listed as well.
    _LOGGER.info(
        "TEST: Plugin is recognized by the data acquisition service and its data sources are present."
    )
    success, data_sources = test_if_data_sources_are_available(plugin_daq_client, main_daq_client,
                                                               options.verbose)
    if success:
        _LOGGER.info("SUCCESS!\n")
    else:
        return False

    # Test that each data capability successfully gets acquired and saved to the data store by monitoring
    # the GetStatus request and then checking if the action id is in the data store afterwards.
    run_test(test_capabilities_acquires_and_saves,
             ("All data sources are successfully acquired, respond "
              "with 'status complete' to the GetStatus RPC, and are saved to the data store."),
             data_sources, main_daq_client, data_store_client, group_name, options.verbose)

    # Test that each data capability can successfully be cancelled with no errors.
    run_test(test_cancelling, "All data sources can be cancelled with the CancelAcquisition RPC.",
             data_sources, main_daq_client, group_name, options.verbose)

    # Test that after running multiple different tests that send each RPC to the plugin service, check
    # that there are still no service faults in the robot state.
    run_test(test_if_service_has_active_service_faults,
             ("The plugin service has no active service "
              "faults after running multiple tests sending RPCs to the plugin service."), robot,
             options.service_name)

    # Test downloading all of the capture data via the REST endpoint and save the captured data to a
    # specific location.
    run_test(test_downloading_all_data_via_REST,
             "All of the captured data can be downloaded via the "
             "REST endpoint.", data_store_client, group_name, options.hostname, robot,
             options.destination_folder)

    _LOGGER.info("Data is downloaded to: %s", options.destination_folder)
    _LOGGER.info("All tests passed for plugin service %s", options.service_name)
    return True


if __name__ == '__main__':
    if not main(sys.argv[1:]):
        sys.exit(1)
