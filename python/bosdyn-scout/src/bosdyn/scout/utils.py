# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Utility functions for Scout web API"""
import datetime
import getpass
import os
import sys
from typing import Dict, List

from deprecated.sphinx import deprecated

from bosdyn.orbit.exceptions import WebhookSignatureVerificationError
from bosdyn.orbit.utils import (datetime_from_isostring, get_action_names_from_run_events,
                                get_api_token, validate_webhook_payload, write_image)

SCOUT_USER_ENV_VAR = "BOSDYN_SCOUT_CLIENT_USERNAME"
SCOUT_PASS_ENV_VAR = "BOSDYN_SCOUT_CLIENT_PASSWORD"
DEFAULT_MAX_MESSAGE_AGE_MS = 5 * 60 * 1000


@deprecated(reason='Please, use get_api_token instead.', version='4.0.0', action="always")
def get_credentials() -> [str, str]:
    """ Obtains credentials from either environment variables or terminal inputs

        Returns
            username(str): the username for the Scout instance
            password(str): the password for the Scout instance
    """
    username = os.environ.get(SCOUT_USER_ENV_VAR)
    password = os.environ.get(SCOUT_PASS_ENV_VAR)
    if not username or not password:
        if sys.stdin.isatty():
            print('Username: ', end='', file=sys.stderr)
            username = input()
            password = getpass.getpass(stream=sys.stderr)

    return username, password


@deprecated(
    reason=
    'Scout has been renamed to Orbit. Please, use bosdyn-orbit package instead of bosdyn-scout.',
    version='4.0.0', action="always")
def get_latest_created_at_for_run_events(scout_client: 'bosdyn.scout.client.ScoutClient',
                                         params: Dict = {}) -> datetime.datetime:
    """ Given a dictionary of query params, returns the max created at time for run events

        Args:
            scout_client: the client for Scout web API
            params: the query params associated with the get request
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
        Returns:
            The max created at time for run events in datetime
    """
    base_params = {'limit': 1, 'orderBy': '-created_at'}
    base_params.update(params)
    latest_resource = scout_client.get_run_events(params=base_params).json()
    if not latest_resource["resources"]:
        scout_client_timestamp_response = scout_client.get_scout_system_time()
        ms_since_epoch = int(scout_client_timestamp_response.json()["msSinceEpoch"])
        return datetime.datetime.utcfromtimestamp(ms_since_epoch / 1000)
    return datetime_from_isostring(latest_resource["resources"][0]["createdAt"])


@deprecated(
    reason=
    'Scout has been renamed to Orbit. Please, use bosdyn-orbit package instead of bosdyn-scout.',
    version='4.0.0', action="always")
def get_latest_run_capture_resources(scout_client: 'bosdyn.scout.client.ScoutClient',
                                     params: Dict = {}) -> List:
    """ Given a dictionary of query params, returns the latest run capture resources in json format

        Args:
            scout_client: the client for Scout web API
            params: the query params associated with the get request
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
        Returns:
            A list of resources obtained from Scout's RESTful endpoint
    """
    base_params = {'orderBy': '-created_at'}
    base_params.update(params)
    run_captures = scout_client.get_run_captures(params=base_params).json()
    return run_captures["resources"]


@deprecated(
    reason=
    'Scout has been renamed to Orbit. Please, use bosdyn-orbit package instead of bosdyn-scout.',
    version='4.0.0', action="always")
def get_latest_created_at_for_run_captures(scout_client: 'bosdyn.scout.client.ScoutClient',
                                           params: Dict = {}) -> datetime.datetime:
    """ Given a dictionary of query params, returns the max created at time for run captures

        Args:
            scout_client: the client for Scout web API
            params: the query params associated with the get request
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
        Returns:
            The max created at time for run captures in datetime
    """
    base_params = {'limit': 1, 'orderBy': '-created_at'}
    base_params.update(params)
    latest_resource = scout_client.get_run_captures(params=base_params).json()
    if not latest_resource["resources"]:
        scout_client_timestamp_response = scout_client.get_scout_system_time()
        ms_since_epoch = int(scout_client_timestamp_response.json()["msSinceEpoch"])
        return datetime.datetime.utcfromtimestamp(ms_since_epoch / 1000)
    return datetime_from_isostring(latest_resource["resources"][0]["createdAt"])


@deprecated(
    reason=
    'Scout has been renamed to Orbit. Please, use bosdyn-orbit package instead of bosdyn-scout.',
    version='4.0.0', action="always")
def get_latest_run_resource(scout_client: 'bosdyn.scout.client.ScoutClient',
                            params: Dict = {}) -> List:
    """ Given a dictionary of query params, returns the latest run resource in json format

        Args:
            scout_client: the client for Scout web API
            params: the query params associated with the get request
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
        Returns:
            A list corresponding to a run resource obtained from Scout's RESTful endpoint in json
    """
    base_params = {'limit': 1, 'orderBy': 'newest'}
    base_params.update(params)
    latest_run_json = scout_client.get_runs(params=base_params).json()
    if not latest_run_json['resources']:
        return None
    return latest_run_json['resources'][0]


@deprecated(
    reason=
    'Scout has been renamed to Orbit. Please, use bosdyn-orbit package instead of bosdyn-scout.',
    version='4.0.0', action="always")
def get_latest_run_in_progress(scout_client: 'bosdyn.scout.client.ScoutClient',
                               params: Dict = {}) -> List:
    """ Given a dictionary of query params, returns the latest running resource in json format

        Args:
            scout_client: the client for Scout web API
            params: the query params associated with the get request
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
        Returns:
            A list corresponding to a run obtained from Scout's RESTful endpoint in json
    """
    base_params = {'orderBy': 'newest'}
    base_params.update(params)
    latest_resources = scout_client.get_runs(params=base_params).json()["resources"]
    for resource in latest_resources:
        if resource["missionStatus"] not in [
                "SUCCESS", "FAILURE", "ERROR", "STOPPED", "NONE", "UNKNOWN"
        ]:
            return resource
    return None


@deprecated(
    reason=
    'Scout has been renamed to Orbit. Please, use bosdyn-orbit package instead of bosdyn-scout.',
    version='4.0.0', action="always")
def get_latest_end_time_for_runs(scout_client: 'bosdyn.scout.client.ScoutClient',
                                 params: Dict = {}) -> datetime.datetime:
    """ Given a dictionary of query params, returns the max end time for runs

        Args:
            scout_client: the client for Scout web API
            params: the query params associated with the get request
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
        Returns:
            The max end time for runs in datetime
    """
    base_params = {'limit': 1, 'orderBy': 'newest'}
    base_params.update(params)
    latest_resource = scout_client.get_runs(params=base_params).json()
    if latest_resource.get("resources"):
        latest_end_time = latest_resource.get("resources")[0]["endTime"]
        if latest_end_time:
            return datetime_from_isostring(latest_end_time)
    scout_client_timestamp_response = scout_client.get_scout_system_time()
    ms_since_epoch = int(scout_client_timestamp_response.json()["msSinceEpoch"])
    return datetime.datetime.utcfromtimestamp(ms_since_epoch / 1000)


@deprecated(
    reason=
    'Scout has been renamed to Orbit. Please, use bosdyn-orbit package instead of bosdyn-scout.',
    version='4.0.0', action="always")
def data_capture_urls_from_run_events(scout_client: 'bosdyn.scout.client.ScoutClient',
                                      run_events: List, list_of_channel_names: List = None) -> List:
    """ Given run events and list of desired channel names, returns the list of data capture urls

        Args:
            scout_client: the client for Scout web API
            run_events: a json representation of run events obtained from Scout's RESTful endpoint
            list_of_channel_names: a list of channel names associated with the desired data captures.
                                           Defaults to None which returns all the available channels.
        Returns:
            data_urls: a list of urls
    """
    all_run_events_resources = run_events["resources"]
    data_urls = []
    for resource in all_run_events_resources:
        all_data_captures = resource["dataCaptures"]
        for data_capture in all_data_captures:
            if list_of_channel_names is None:
                # check if exists in unique_list or not
                if list_of_channel_names not in data_urls:
                    data_urls.append(f'https://{scout_client._hostname}' + data_capture["dataUrl"])
            elif data_capture["channelName"] in list_of_channel_names:
                # check if exists in unique_list or not
                if list_of_channel_names not in data_urls:
                    data_urls.append(f'https://{scout_client._hostname}' + data_capture["dataUrl"])
    return data_urls


@deprecated(
    reason=
    'Scout has been renamed to Orbit. Please, use bosdyn-orbit package instead of bosdyn-scout.',
    version='4.0.0', action="always")
def data_capture_url_from_run_capture_resources(scout_client: 'bosdyn.scout.client.ScoutClient',
                                                run_capture_resources: List,
                                                list_of_channel_names: List = None) -> List:
    """ Given run capture resources and list of desired channel names, returns the list of data capture urls

        Args:
            scout_client: the client for Scout web API
            run_capture_resources: a list of resources obtained from Scout's RESTful endpoint
            list_of_channel_names: a list of channel names associated with the desired data captures.
                                           Defaults to None which returns all the available channels.
        Returns:
            data_urls: a list of urls
    """
    data_urls = []
    for data_capture in run_capture_resources:
        if list_of_channel_names is None:
            # check if exists in unique_list or not
            if list_of_channel_names not in data_urls:
                data_urls.append(f'https://{scout_client._hostname}' + data_capture["dataUrl"])
        elif data_capture["channelName"] in list_of_channel_names:
            # check if exists in unique_list or not
            if list_of_channel_names not in data_urls:
                data_urls.append(f'https://{scout_client._hostname}' + data_capture["dataUrl"])
    return data_urls
