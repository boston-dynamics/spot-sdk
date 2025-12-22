# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

import json
from pathlib import Path
from string import Template

import requests

from bosdyn.client.url_validation_util import safe_api_call

API_TIMEOUT_DEFAULT = 30


def file_to_json(file_path):
    """
    Helper to read and parse JSON files.
    Args:
        file_path (Path): Path to JSON file.
    Returns:
        dict: Parsed JSON data.
    """
    return json.loads(file_path.read_text())




# Functions to handle api calls to access control systems
def door_action(api_calls, door_id, action, path_to_cert=None, is_robot=True):
    """Executes a sequence of API calls required to perform an action (e.g., open or close) on a specified door,
    handling data substitutions and certificate verification as needed.

        api_calls (list of dict): List of API call specifications, where each dict contains information
            such as 'method', 'url', 'action', 'sni_hostname', 'route', 'request_data', and 'responses'.
        door_id (str): Identifier of the door to perform the action on.
        action (list of str): The action(s) to perform (e.g., "open", "close"). Only calls matching
            the specified action(s) will be executed.
        path_to_cert (str, optional): Path to a certificate file for SSL verification. If None, no certificate
            is used.
        is_robot (bool, optional): Indicates if the API calls are being made on behalf of a robot. Defaults to True.

    Returns:
        dict: An error message dictionary containing details about any error encountered during the API calls.
            If all calls succeed, returns an empty dictionary.
    """
    error_msg = {}
    cross_call_substitutions = {"door_id": door_id}

    for call_data in api_calls:

        if call_data.get("action") not in action:
            continue

        method = call_data.get("method")
        url = call_data.get("url")
        sni_hostname = call_data.get("sni_hostname")
        route = call_data.get("route")
        request_data = call_data.get("request_data", {})
        responses = call_data.get("responses", {})
        call_action = call_data.get("action", "")

        if not method or not url:
            error_msg["extra_message"] = "API call error: missing method or url"
            break

        # Format URL and data - note: substitutions are case-INsensitive
        try:
            # This will only replace instances of values formatted like $variable or ${variable}
            url = Template(url).safe_substitute(cross_call_substitutions)

            templated_request_data = {}
            for k, v in request_data.items():
                if isinstance(v, dict):  # Handle nested dicts, like headers
                    templated_request_data[k] = {
                        k2:
                            Template(v2).safe_substitute(cross_call_substitutions) if isinstance(
                                v2, str) else v2 for k2, v2 in v.items()
                    }
                elif isinstance(v, str):  # Handle top level string values
                    templated_request_data[k] = Template(v).safe_substitute(
                        cross_call_substitutions)
                else:
                    templated_request_data[k] = v
            # Check if cert file was included at the configuration, if yes use it
            if path_to_cert:
                templated_request_data["verify"] = path_to_cert
        except Exception as e:
            print(f"{e} has no value, couldn't make substitution")

        result_of_call, api_error_msg = make_access_control_system_api_call(
            method, url, templated_request_data, responses, sni_hostname=sni_hostname,
            is_robot=is_robot, route=route)
        if api_error_msg:
            error_msg["action"] = call_action
            error_msg["api_error"] = api_error_msg
            break

        # If the call returned data, store it for subsequent calls
        if result_of_call:
            try:
                for result in result_of_call:
                    tag = result[0]
                    content = result[1]
                    cross_call_substitutions[tag] = content
            except Exception as e:
                print(f"API call error: couldn't read data, got exception {e}")
                error_msg["extra_message"] = f"API call error: couldn't read data, got exception"
                break
    return error_msg




def make_access_control_system_api_call(method, url, request_data, store_responses=None,
                                        sni_hostname=None, is_robot=True, route=None):
    """Makes an HTTP request and optionally extracts specific fields from the JSON response.
    
    Args:
        method (str): HTTP method to use (e.g., 'GET', 'POST')
        url (str): The endpoint URL for the API call
        request_data (dict): Request configuration including headers, body, etc.
        store_responses (Optional[Dict[str, str]]): Dictionary mapping response field names to 
            JSON paths. For example:
            {
                "token": "auth.token",  # Store response's auth.token as "token"
                "session_id": "data.session"  # Store response's data.session as "session_id"
            }
            If None, no data will be extracted from the response.
        sni_hostname (str|None): If specified, this parameter provides the hostname declared by
            and expected by the access control server during TLS negotiation. This should only be
            required if the server's hostname is not resolvable via DNS.
        route (str|None): Route type to use ("WIFI", "LTE").
            If None, default interface (WIFI) will be used.
    
    Returns:
        Tuple[Optional[List[Tuple[str, Any]]], Optional[Dict]]:
            - First element: If store_responses was provided and matching data was found,
              returns list of tuples [(field_name, value), ...]. None otherwise.
            - Second element: If error occurred, returns dict with error details:
              {
                  'status_code': int,
                  'reason': str,
                  'elapsed': float
              }
              None if successful.
    
    Example:
        >>> store_responses = {"auth_token": "data.token"}
        >>> data, error = make_access_control_system_api_call("POST", "https://api.door/auth",
        ...                                                   {"json": {"key": "value"}},
        ...                                                   store_responses)
        >>> if data:
        ...     # data might be [("auth_token", "abc123")]
        ...     token = dict(data)["auth_token"]
    """
    try:
        response, status_message = safe_api_call(method, url, sni_hostname,
                                                 timeout=API_TIMEOUT_DEFAULT, is_robot=is_robot,
                                                 interface=route, **request_data)

        if response is None:
            # There was an error during the API call
            return None, status_message

        if response.status_code == 200:
            if store_responses:
                # Only try to parse JSON and extract data if we need to store responses
                data_json = response.json()
                return [(tag, get_value_by_path(data_json, path))
                        for tag, path in store_responses.items()
                        if get_value_by_path(data_json, path) is not None], None
            # If we don't need to store responses, just return success
            return None, None

        # If the status code isn't 200, something went wrong
        return None, {
            'status_code': response.status_code,
            'reason': response.reason,
            'elapsed': response.elapsed.total_seconds(),
        }

    except requests.exceptions.RequestException as e:
        print(f"API call failed: {str(e)}")
        return None, {
            'status_code': getattr(e.response, 'status_code', None),
            'reason': getattr(e.response, 'reason', str(e)),
            'elapsed': getattr(e.response, 'elapsed', None)
        }


def get_value_by_path(data_json, path_to_info):
    """Takes in a json representing the data of a call response, and a string representing the 
        path through the json to the desired data. Traverses the json and returns the data.      
    """
    keys = path_to_info.split('.')
    result = data_json

    for key in keys:
        result = result.get(key, None)
    if result is not None:
        return result
    else:
        return False
