# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Utility functions for bosdyn-orbit"""
import datetime
import hashlib
import hmac
import json
import os
import secrets
import shutil
import sys
import time
from typing import Dict, List

from bosdyn.orbit.exceptions import WebhookSignatureVerificationError

API_TOKEN_ENV_VAR = "BOSDYN_ORBIT_CLIENT_API_TOKEN"
DEFAULT_MAX_MESSAGE_AGE_MS = 5 * 60 * 1000


def get_api_token() -> str:
    """ Obtains an API token from either an environment variable or terminal input

        Returns
            api_token: the API token obtained from the instance
    """
    api_token = os.environ.get(API_TOKEN_ENV_VAR)
    if not api_token:
        if sys.stdin.isatty():
            print('API Token: ', end='', file=sys.stderr)
            api_token = input()
    return api_token


def get_latest_created_at_for_run_events(client: 'bosdyn.orbit.client.Client',
                                         params: Dict = {}) -> datetime.datetime:
    """ Given a dictionary of query params, returns the max created at time for run events

        Args:
            client: the client for the web API
            params: the query params associated with the get request
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedClientError:  indicates that the client is not authenticated properly
        Returns:
            The max created at time for run events in datetime
    """
    base_params = {'limit': 1, 'orderBy': '-created_at'}
    base_params.update(params)
    latest_resource = client.get_run_events(params=base_params).json()
    if not latest_resource["resources"]:
        client_timestamp_response = client.get_system_time()
        ms_since_epoch = int(client_timestamp_response.json()["msSinceEpoch"])
        return datetime.datetime.utcfromtimestamp(ms_since_epoch / 1000)
    return datetime_from_isostring(latest_resource["resources"][0]["createdAt"])


def get_latest_run_capture_resources(client: 'bosdyn.orbit.client.Client',
                                     params: Dict = {}) -> List:
    """ Given a dictionary of query params, returns the latest run capture resources in json format

        Args:
            client: the client for Orbit web API
            params: the query params associated with the get request
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedClientError:  indicates that the client is not authenticated properly
        Returns:
            A list of resources obtained from a RESTful endpoint
    """
    base_params = {'orderBy': '-created_at'}
    base_params.update(params)
    run_captures = client.get_run_captures(params=base_params).json()
    return run_captures["resources"]


def get_latest_created_at_for_run_captures(client: 'bosdyn.orbit.client.Client',
                                           params: Dict = {}) -> datetime.datetime:
    """ Given a dictionary of query params, returns the max created at time for run captures

        Args:
            client: the client for Orbit web API
            params: the query params associated with the get request
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedClientError:  indicates that the client is not authenticated properly
        Returns:
            The max created at time for run captures in datetime
    """
    base_params = {'limit': 1, 'orderBy': '-created_at'}
    base_params.update(params)
    latest_resource = client.get_run_captures(params=base_params).json()
    if not latest_resource["resources"]:
        client_timestamp_response = client.get_system_time()
        ms_since_epoch = int(client_timestamp_response.json()["msSinceEpoch"])
        return datetime.datetime.utcfromtimestamp(ms_since_epoch / 1000)
    return datetime_from_isostring(latest_resource["resources"][0]["createdAt"])


def get_latest_run_resource(client: 'bosdyn.orbit.client.Client', params: Dict = {}) -> List:
    """ Given a dictionary of query params, returns the latest run resource in json format

        Args:
            client: the client for Orbit web API
            params: the query params associated with the get request
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedClientError:  indicates that the client is not authenticated properly
        Returns:
            A list corresponding to a run resource obtained from a RESTful endpoint in json
    """
    base_params = {'limit': 1, 'orderBy': 'newest'}
    base_params.update(params)
    latest_run_json = client.get_runs(params=base_params).json()
    if not latest_run_json['resources']:
        return None
    return latest_run_json['resources'][0]


def get_latest_run_in_progress(client: 'bosdyn.orbit.client.Client', params: Dict = {}) -> List:
    """ Given a dictionary of query params, returns the latest running resource in json format

        Args:
            client: the client for Orbit web API
            params: the query params associated with the get request
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedClientError:  indicates that the client is not authenticated properly
        Returns:
            A list corresponding to a run obtained from a RESTful endpoint in json
    """
    base_params = {'orderBy': 'newest'}
    base_params.update(params)
    latest_resources = client.get_runs(params=base_params).json()["resources"]
    for resource in latest_resources:
        if resource["missionStatus"] not in [
                "SUCCESS", "FAILURE", "ERROR", "STOPPED", "NONE", "UNKNOWN"
        ]:
            return resource
    return None


def get_latest_end_time_for_runs(client: 'bosdyn.orbit.client.Client',
                                 params: Dict = {}) -> datetime.datetime:
    """ Given a dictionary of query params, returns the max end time for runs

        Args:
            client: the client for Orbit web API
            params: the query params associated with the get request
        Raises:
            RequestExceptions: exceptions thrown by the Requests library
            UnauthenticatedClientError:  indicates that the client is not authenticated properly
        Returns:
            The max end time for runs in datetime
    """
    base_params = {'limit': 1, 'orderBy': 'newest'}
    base_params.update(params)
    latest_resource = client.get_runs(params=base_params).json()
    if latest_resource.get("resources"):
        latest_end_time = latest_resource.get("resources")[0]["endTime"]
        if latest_end_time:
            return datetime_from_isostring(latest_end_time)
    client_timestamp_response = client.get_system_time()
    ms_since_epoch = int(client_timestamp_response.json()["msSinceEpoch"])
    return datetime.datetime.utcfromtimestamp(ms_since_epoch / 1000)


def write_image(img_raw, image_fp: str) -> None:
    """ Given a raw image and a desired output directory, writes the image to a file

        Args:
            img_raw(Raw image object): the input raw image
            image_fp: the output filepath for the image
    """
    os.makedirs(os.path.dirname(image_fp), exist_ok=True)
    with open(image_fp, 'wb') as out_file:
        shutil.copyfileobj(img_raw, out_file)


def data_capture_urls_from_run_events(client: 'bosdyn.orbit.client.Client', run_events: List,
                                      list_of_channel_names: List = None) -> List:
    """ Given run events and list of desired channel names, returns the list of data capture urls

        Args:
            client: the client for Orbit web API
            run_events: a json representation of run events obtained from a RESTful endpoint
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
                    data_urls.append(f'https://{client._hostname}' + data_capture["dataUrl"])
            elif data_capture["channelName"] in list_of_channel_names:
                # check if exists in unique_list or not
                if list_of_channel_names not in data_urls:
                    data_urls.append(f'https://{client._hostname}' + data_capture["dataUrl"])
    return data_urls


def data_capture_url_from_run_capture_resources(client: 'bosdyn.orbit.client.Client',
                                                run_capture_resources: List,
                                                list_of_channel_names: List = None) -> List:
    """ Given run capture resources and list of desired channel names, returns the list of data capture urls

        Args:
            client: the client for Orbit web API
            run_capture_resources: a list of resources obtained from a RESTful endpoint
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
                data_urls.append(f'https://{client._hostname}' + data_capture["dataUrl"])
        elif data_capture["channelName"] in list_of_channel_names:
            # check if exists in unique_list or not
            if list_of_channel_names not in data_urls:
                data_urls.append(f'https://{client._hostname}' + data_capture["dataUrl"])
    return data_urls


def get_action_names_from_run_events(run_events: Dict) -> List:
    """ Given run events, returns a list of action names

        Args:
            run_events: a representation of run events obtained from a RESTful endpoint
        Returns:
            action_names: a list of action names
    """
    all_run_events_resources = run_events["resources"]
    action_names = []
    for resource in all_run_events_resources:
        action_names.append(resource["actionName"])
    return action_names


def datetime_from_isostring(datetime_isostring: str) -> datetime.datetime:
    """ Returns the datetime representation of the iso string representation of time

        Args:
            datetime_isostring: the iso string representation of time
        Returns:
            The datetime representation of the iso string representation of time
    """
    if "Z" in datetime_isostring:
        return datetime.datetime.strptime(datetime_isostring, "%Y-%m-%dT%H:%M:%S.%fZ")
    if "+" in datetime_isostring:
        return datetime.datetime.strptime(datetime_isostring[0:datetime_isostring.index("+")],
                                          "%Y-%m-%dT%H:%M:%S.%f")


def validate_webhook_payload(payload: Dict, signature_header: str, secret: str,
                             max_age_ms: int = DEFAULT_MAX_MESSAGE_AGE_MS) -> None:
    """ Verifies that the webhook payload came from

        Args:
            payload: the JSON body of the webhooks req
            signature_header: the value of the signature header
            secret: the configured secret value for this webhook
            max_age_ms: the maximum age of the message before it's considered invalid (default is 5 minutes)
        Raises:
            bosdyn.orbit.exceptions.WebhookSignatureVerificationError: thrown if the webhook signature is invalid
    """
    if not signature_header:
        raise WebhookSignatureVerificationError("Signature header cannot be empty")

    header_components = dict(entry.split('=') for entry in signature_header.split(','))
    send_time = header_components.get('t')
    send_time_ms = int(send_time) if send_time is not None and send_time.isdigit() else None
    received_hmac = header_components.get('v1')
    if not send_time_ms or not received_hmac:
        raise WebhookSignatureVerificationError(
            "Missing either send time or HMAC in signature header")

    current_time_ns = time.time()
    current_time_ms = round(current_time_ns) * 1000
    time_diff_ms = current_time_ms - send_time_ms
    if time_diff_ms > max_age_ms:
        raise WebhookSignatureVerificationError(
            f"The payload is {time_diff_ms}ms old, which is greater than the maximum age {max_age_ms}ms"
        )

    full_payload_string = f'{send_time}.{json.dumps(payload, separators=(",",":"))}'
    calculated_hmac = hmac.new(bytes.fromhex(secret), full_payload_string.encode('utf-8'),
                               hashlib.sha256).hexdigest()

    time_safe_equal = secrets.compare_digest(received_hmac, calculated_hmac)
    if not time_safe_equal:
        raise WebhookSignatureVerificationError(
            "The received HMAC did not match the expected value")
