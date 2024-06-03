# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

""" Scout Client is a client for a single Scout instance. The client uses the Scout web API
    to send HTTPs requests to a number of REStful endpoints using the Requests library.
"""
from typing import Dict, Iterable

import requests
from deprecated.sphinx import deprecated

import bosdyn.scout.utils
from bosdyn.scout.exceptions import UnauthenticatedScoutClientError

DEFAULT_HEADERS = {'Accept': 'application/json'}
OCTET_HEADER = {'Content-type': 'application/octet-stream', 'Accept': 'application/octet-stream'}


@deprecated(
    reason=
    'Scout has been renamed to Orbit. Please, use bosdyn-orbit package instead of bosdyn-scout.',
    version='4.0.0', action="always")
class ScoutClient():
    """Client for Scout web API"""

    def __init__(self, hostname: str, verify: bool = True, cert: str = None):
        """ Initializes the attributes of the ScoutClient object.

            Args:
                hostname: the IP address associated with the Scout instance
                verify(path to a CA bundle or Boolean): controls whether we verify the server’s TLS certificate
                    Note that verify=False makes your application vulnerable to man-in-the-middle (MitM) attacks
                    Defaults to True
                cert(.pem file or a tuple with ('cert', 'key') pair): a local cert to use as client side certificate
                    Note that the private key to your local certificate must be unencrypted because Requests does not support using encrypted keys.
                    Defaults to None. For additional configurations, use the member Session object "_session" in accordance with Requests library
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
        """
        # The hostname of the Scout instance
        self._hostname = hostname
        # Set a Session object to persist certain parameters across requests
        self._session = requests.Session()
        # Set SSL verification strategy
        self._session.verify = verify
        # Client Side Certificates
        self._session.cert = cert
        # Initialize session
        self._session.get(f'https://{self._hostname}')
        # Set default headers for self._session
        self._session.headers.update(DEFAULT_HEADERS)
        # Set x-csrf-token for self._session
        self._session.headers.update({'x-csrf-token': self._session.cookies['x-csrf-token']})
        # Flag indicating that the ScoutClient is authenticated
        self._is_authenticated = False

    @deprecated(reason='Please, use authenticate_with_api_token.', version='4.0.0', action="always")
    def authenticate_with_password(self, username: str = None,
                                   password: str = None) -> requests.Response:
        """ Authorizes the client with username and password. Must call before using other client functions.
            If username and password are not provided, the function obtains credentials from
            either environment variables or terminal inputs.

            Args:
                username: the username for the Scout instance
                password: the password for the Scout instance
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
            Returns::
                requests.Response: the response associated with the login request
        """
        if username and password:
            username = username
            password = password
        else:
            input_user, input_pass = bosdyn.scout.utils.get_credentials()
            username = input_user
            password = input_pass
        login_response = self.post_resource("login", data={
            'username': username,
            'password': password
        })
        if login_response.ok:
            self._is_authenticated = True
        else:
            print('ScoutClient: Login failed: {}'.format(login_response.text))
        return login_response

    def authenticate_with_api_token(self, api_token: str = None) -> requests.Response:
        """ Authorizes the client using the provided API token obtained from the Scout instance.
            Must call before using other client functions.

            Args:
                api_token: the API token obtained from the Scout instance
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
        """
        if not api_token:
            api_token = bosdyn.scout.utils.get_api_token()
        # Set API token for self._session
        self._session.headers.update({'Authorization': 'Bearer ' + api_token})
        # Check the validity of the API token
        authenticate_response = self._session.get(
            f'https://{self._hostname}/api/v0/api_token/authenticate')
        if authenticate_response.ok:
            self._is_authenticated = True
        else:
            print(
                'ScoutClient: Login failed: {} Please, obtain a valid API token from the Scout instance!'
                .format(authenticate_response.text))
            # Remove the invalid API token from session headers
            self._session.headers.pop('Authorization')
        return authenticate_response

    def get_resource(self, path: str, **kwargs) -> requests.Response:
        """ Base function for getting a resource in /api/v0/

            Args:
                path: the path appended to /api/v0/
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        if not self._is_authenticated:
            raise UnauthenticatedScoutClientError()
        return self._session.get(f'https://{self._hostname}/api/v0/{path}/', **kwargs)

    def post_resource(self, path: str, **kwargs) -> requests.Response:
        """ Base function for posting a resource in /api/v0/

            Args:
                path: the path appended to /api/v0/
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                The response associated with the post request
        """
        if not self._is_authenticated and path != "login":
            raise UnauthenticatedScoutClientError()
        return self._session.post(f'https://{self._hostname}/api/v0/{path}', **kwargs)

    def delete_resource(self, path: str, **kwargs) -> requests.Response:
        """ Base function for deleting a resource in /api/v0/

            Args:
                path: the path appended to /api/v0/
                kwargs(**): a variable number of keyword arguments for the delete request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                The response associated with the delete request
        """
        if not self._is_authenticated:
            raise UnauthenticatedScoutClientError()
        return self._session.delete(f'https://{self._hostname}/api/v0/{path}', **kwargs)

    def get_scout_version(self, **kwargs) -> requests.Response:
        """ Retrieves info about a scout .

            Args:
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource("version", **kwargs)

    def get_scout_system_time(self, **kwargs) -> requests.Response:
        """ Returns scout's current system time.

            Args:
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource("settings/system-time", **kwargs)

    def get_robots(self, **kwargs) -> requests.Response:
        """ Returns robots on the specified scout instance.

            Args:
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource("robots", **kwargs)

    def get_robot_by_hostname(self, hostname: str, **kwargs) -> requests.Response:
        """ Returns a robot on given a hostname of a specific robot.

            Args:
                hostname: the IP address associated with the desired robot on the Scout instance
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource(f'robots/{hostname}', **kwargs)

    def get_site_walks(self, **kwargs) -> requests.Response:
        """ Returns site walks on the specified scout instance

            Args:
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource("site_walks", **kwargs)

    def get_site_walk_by_id(self, uuid: str, **kwargs) -> requests.Response:
        """ Given a site walk uuid, returns a site walk on the specified scout instance

            Args:
                uuid: the ID associated with the site walk
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource(f'site_walks/{uuid}', **kwargs)

    def get_site_elements(self, **kwargs) -> requests.Response:
        """ Returns site elements on the specified scout instance

            Args:
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource("site_elements", **kwargs)

    def get_site_element_by_id(self, uuid: str, **kwargs) -> requests.Response:
        """ Given a site element uuid, returns a site element on the specified scout instance

            Args:
                uuid: the ID associated with the site element
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource(f'site_elements/{uuid}', **kwargs)

    def get_site_docks(self, **kwargs) -> requests.Response:
        """ Returns site docks on the specified scout instance

            Args:
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource("site_docks", **kwargs)

    def get_site_dock_by_id(self, uuid: str, **kwargs) -> requests.Response:
        """ Given a site dock uuid, returns a site dock on the specified scout instance

            Args:
                uuid: the ID associated with the site dock
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource(f'site_docks/{uuid}', **kwargs)

    def get_calendar(self, **kwargs) -> requests.Response:
        """ Returns calendar events on the specified scout instance

            Args:
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource("calendar/schedule", **kwargs)

    def get_run_events(self, **kwargs) -> requests.Response:
        """ Given a dictionary of query params, returns run events

            Args:
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource("run_events", **kwargs)

    def get_run_event_by_id(self, uuid: str, **kwargs) -> requests.Response:
        """ Given a runEventUuid, returns a run event

            Args:
                uuid: the ID associated with the run event
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource(f'run_events/{uuid}', **kwargs)

    def get_run_captures(self, **kwargs) -> requests.Response:
        """ Given a dictionary of query params, returns run captures

            Args:
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource("run_captures", **kwargs)

    def get_run_capture_by_id(self, uuid: str, **kwargs) -> requests.Response:
        """ Given a runCaptureUuid, returns a run capture

            Args:
                uuid: the ID associated with the run capture
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource(f'run_captures/{uuid}', **kwargs)

    def get_runs(self, **kwargs) -> requests.Response:
        """ Given a dictionary of query params, returns runs

            Args:
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource("runs", **kwargs)

    def get_run_by_id(self, uuid: str, **kwargs) -> requests.Response:
        """ Given a runUuid, returns a run

            Args:
                uuid: the ID associated with the run
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource(f'runs/{uuid}', **kwargs)

    def get_run_archives_by_id(self, uuid: str, **kwargs) -> requests.Response:
        """ Given a runUuid, returns run archives

            Args:
                uuid: the ID associated with the run
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource(f'run_archives/{uuid}', **kwargs)

    def get_image(self, url: str, **kwargs) -> 'urllib3.response.HTTPResponse':
        """ Given a data capture url, returns a decoded image

            Args:
                url: the url associated with the data capture in the form of https://hostname + RunCapture["dataUrl"]
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                urllib3.response.HTTPResponse: the decoded response associated with the get request
        """
        if not self._is_authenticated:
            raise UnauthenticatedScoutClientError()
        response = self._session.get(url, stream=True, **kwargs)
        response.raise_for_status()
        response.raw.decode_content = True
        return response.raw

    def get_image_response(self, url: str, **kwargs) -> requests.Response:
        """ Given a data capture url, returns an image response

            Args:
                url: the url associated with the data capture in the form of https://hostname + RunCapture["dataUrl"]
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the image response associated with the get request
        """
        if not self._is_authenticated:
            raise UnauthenticatedScoutClientError()
        response = self._session.get(url, stream=True, **kwargs)
        return response

    def get_webhook(self, **kwargs) -> requests.Response:
        """ Returns webhook on the specified scout instance

            Args:
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource("webhooks", **kwargs)

    def get_webhook_by_id(self, uuid: str, **kwargs) -> requests.Response:
        """ Given a uuid, returns a specific webhook instance

            Args:
                uuid: the ID associated with the webhook
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the get request
        """
        return self.get_resource(f'webhooks/{uuid}', **kwargs)

    def get_robot_info(self, robot_nickname: str, **kwargs) -> requests.Response:
        """ Given a robot nickname, returns information about the robot

            Args:
                robot_nickname: the nickname of the robot
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.get_resource(f'robot-session/{robot_nickname}/session', **kwargs)

    def post_export_as_walk(self, site_walk_uuid: str, **kwargs) -> requests.Response:
        """ Given a site walk uuid, it exports the walks_pb2.Walk equivalent

            Args:
                site_walk_uuid: the ID associated with the site walk
                kwargs(**): a variable number of keyword arguments for the get request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError: indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.post_resource(f'site_walks/export_as_walk/{site_walk_uuid}', **kwargs)

    def post_import_from_walk(self, **kwargs) -> requests.Response:
        """ Given a walk data, imports it to the specified scout instance

            Args:
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.post_resource("site_walks/import_from_walk", **kwargs)

    def post_site_element(self, **kwargs) -> requests.Response:
        """ Create a site element. It also updates a pre-existing Site Element using the associated UUID.

            Args:
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.post_resource("site_elements", **kwargs)

    def post_site_walk(self, **kwargs) -> requests.Response:
        """ Create a site walk. It also updates a pre-existing Site Walk using the associated UUID.

            Args:
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.post_resource("site_walks", **kwargs)

    def post_site_dock(self, **kwargs) -> requests.Response:
        """ Create a site element. It also updates a pre-existing Site Dock using the associated UUID.

            Args:
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.post_resource("site_docks", **kwargs)

    def post_robot(self, **kwargs) -> requests.Response:
        """ Add a robot to the specified scout instance

            Args:
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.post_resource("robots", **kwargs)

    def post_calendar_event(self, nickname: str = None, time_ms: int = None, repeat_ms: int = None,
                            mission_id: str = None, force_acquire_estop: bool = None,
                            require_docked: bool = None, schedule_name: str = None,
                            blackout_times: Iterable[Dict[str,
                                                          int]] = None, disable_reason: str = None,
                            event_id: str = None, **kwargs) -> requests.Response:
        """  This function serves two purposes. It creates a new calendar event on Scout using the following arguments
             when Event ID is not specified. When the Event ID associated with a pre-existing calendar event is specified,
             the function overwrites the attributes of the pre-existing calendar event.

            Args:
                nickname: the name associated with the robot
                time_ms: the first kickoff time in terms of milliseconds since epoch
                repeat_ms:the delay time in milliseconds for repeating calendar events
                mission_id: the UUID associated with the mission( also known as Site Walk)
                force_acquire_estop: instructs the system to force acquire the estop when the mission kicks off
                require_docked: determines whether the event will require the robot to be docked to start
                schedule_name: the desired name of the calendar event
                blackout_times: a specification for a time period over the course of a week when a schedule should not run
                                  specified as list of a dictionary defined as {"startMs": <int>, "endMs" : <int>}
                                  with startMs (inclusive) being the millisecond offset from the beginning of the week (Sunday) when this blackout period starts
                                  and endMs (exclusive) being the millisecond offset from beginning of the week(Sunday) when this blackout period ends
                disable_reason: (optional) a reason for disabling the calendar event
                event_id: the auto-generated ID for a calendar event that is already posted on the Scout instance.
                            This is only useful when editing a pre-existing calendar event.
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        # Check if the input contains the json param that is constructed outside the function
        if 'json' in kwargs:
            return self.post_resource("calendar/schedule", **kwargs)
        # Construct payload based on provided inputs
        payload = {
            "agent": {
                "nickname": nickname
            },
            "schedule": {
                "timeMs": time_ms,
                "repeatMs": repeat_ms,
                "blackouts": blackout_times,
                "disableReason": disable_reason,
            },
            "task": {
                "missionId": mission_id,
                "forceAcquireEstop": force_acquire_estop,
                "requireDocked": require_docked,
            },
            "eventMetadata": {
                "name": schedule_name,
                "eventId": event_id
            },
        }
        return self.post_resource("calendar/schedule", json=payload, **kwargs)

    def post_calendar_events_disable_all(self, disable_reason: str, **kwargs) -> requests.Response:
        """ Disable all scheduled missions

            Args:
                disable_reason: Reason for disabling all scheduled missions
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.post_resource("calendar/disable-enable", json={"disableReason": disable_reason},
                                  **kwargs)

    def post_calendar_event_disable_by_id(self, event_id: str, disable_reason: str,
                                          **kwargs) -> requests.Response:
        """ Disable specific scheduled mission by event ID

            Args:
                event_id: eventId associated with a mission to disable
                disable_reason: Reason for disabling a scheduled mission
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.post_resource("calendar/disable-enable", json={
            "disableReason": disable_reason,
            "eventId": event_id
        }, **kwargs)

    def post_calendar_events_enable_all(self, **kwargs) -> requests.Response:
        """ Enable all scheduled missions

            Args:
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.post_resource("calendar/disable-enable", json={"disableReason": ""}, **kwargs)

    def post_calendar_event_enable_by_id(self, event_id: str, **kwargs) -> requests.Response:
        """ Enable specific scheduled mission by event ID

            Args:
                event_id: eventId associated with a mission to enable
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.post_resource("calendar/disable-enable", json={
            "disableReason": "",
            "eventId": event_id
        }, **kwargs)

    def post_webhook(self, **kwargs) -> requests.Response:
        """ Create a webhook instance

            Args:
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.post_resource("webhooks", **kwargs)

    def post_webhook_by_id(self, uuid: str, **kwargs) -> requests.Response:
        """ Update an existing webhook instance

            Args:
                uuid: the ID associated with the desired webhook instance
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.post_resource(f'webhooks/{uuid}', **kwargs)

    def post_return_to_dock_mission(self, robot_nickname: str, site_dock_uuid: str,
                                    **kwargs) -> requests.Response:
        """ Generate a mission to send the robot back to the dock

            Args:
                robot_nickname: the nickname of the robot
                site_dock_uuid: the uuid of the dock to send robot to
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        return self.post_resource('graph/send-robot', json={
            "nickname": robot_nickname,
            "siteDockUuid": site_dock_uuid
        }, **kwargs)

    def post_dispatch_mission_to_robot(self, robot_nickname: str, driver_id: str, mission_uuid: str,
                                       delete_mission: bool, force_acquire_estop: bool,
                                       **kwargs) -> requests.Response:
        """ Dispatch the robot to a mission given a mission uuid

            Args:
                robot_nickname: the nickname of the robot
                driver_id: the current driver ID of the mission
                mission_uuid: uuid of the mission(also known as Site Walk) to dispatch
                delete_mission: whether to delete the mission after playback
                force_acquire_estop: whether to force acquire E-stop from the previous client
                kwargs(**): a variable number of keyword arguments for the post request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the post request
        """
        # Payload required for dispatching a mission
        payload = {
            "agent": {
                "nickname": robot_nickname
            },
            "schedule": {
                "timeMs": {
                    "low": 1,
                    "high": 0,
                    "unsigned": False
                },
                "repeatMs": {
                    "low": 0,
                    "high": 0,
                    "unsigned": False
                }
            },
            "task": {
                "missionId": mission_uuid,
                "forceAcquireEstop": force_acquire_estop,
                "deleteMission": delete_mission,
                "requireDocked": False
            },
            "eventMetadata": {
                "name": "Scout API Triggered Mission"
            }
        }
        return self.post_resource(
            f'calendar/mission/dispatch/{robot_nickname}?currentDriverId={driver_id}', json=payload,
            **kwargs)

    def delete_site_walk(self, uuid: str, **kwargs) -> requests.Response:
        """ Given a site walk uuid, deletes the site walk associated with the uuid on the specified scout instance

            Args:
                uuid: the ID associated with the desired site walk
                kwargs(**): a variable number of keyword arguments for the delete request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the delete request
        """
        return self.delete_resource(f'site_walks/{uuid}', **kwargs)

    def delete_robot(self, robot_hostname: str, **kwargs) -> requests.Response:
        """ Given a robot hostname, deletes the robot associated with the hostname on the specified scout instance

            Args:
                robot_hostname: the IP address associated with the robot
                kwargs(**): a variable number of keyword arguments for the delete request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the delete request
        """
        return self.delete_resource(f'robots/{robot_hostname}', **kwargs)

    def delete_calendar_event(self, event_id: str, **kwargs) -> requests.Response:
        """ Delete the specified calendar event on the specified scout instance

            Args:
                event_id(string): the ID associated with the calendar event
                kwargs(**): a variable number of keyword arguments for the delete request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the delete request
        """
        return self.delete_resource(f'calendar/schedule/{event_id}', **kwargs)

    def delete_webhook(self, uuid: str, **kwargs) -> requests.Response:
        """ Delete the specified webhook instance on the specified scout instance

            Args:
                uuid: the ID associated with the desired webhook
                kwargs(**): a variable number of keyword arguments for the delete request
            Raises:
                RequestExceptions: exceptions thrown by the Requests library
                UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            Returns:
                requests.Response: the response associated with the delete request
        """
        return self.delete_resource(f'webhooks/{uuid}', **kwargs)


def create_scout_client(options: 'argparse.Namespace') -> 'bosdyn.scout.client.ScoutClient':
    """ Creates a Scout client object.

        Args:
            options: User input containing Scout hostname, verification, and certification info.
        Returns:
            scout_client: Scout client object.
    """
    # Determine the value for the argument "verify"
    if options.verify in ["True", "False"]:
        verify = options.verify == "True"
    else:
        print(
            "The provided value for the argument verify [%s] is not either 'True' or 'False'. Assuming verify is set to 'path/to/CA bundle'"
            .format(options.verify))
        verify = options.verify

    # A Scout client object represents a single Scout instance.
    scout_client = ScoutClient(hostname=options.hostname, verify=verify, cert=options.cert)

    # The Scout client needs to be authenticated before using its functions
    if options.use_api_token:
        scout_client.authenticate_with_api_token()
    else:
        scout_client.authenticate_with_password()

    return scout_client
