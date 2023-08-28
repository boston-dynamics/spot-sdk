# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

""" Scout Client is a client for a single Scout instance. The client uses the Scout web API 
    to send HTTPs requests to a number of REStful endpoints using the Requests library.
"""
import requests

from bosdyn.scout.exceptions import UnauthenticatedScoutClientError
from bosdyn.scout.utils import get_credentials

DEFAULT_HEADERS = {'Accept': 'application/json'}


class ScoutClient():
    """Client for Scout web API"""

    def __init__(self, hostname, verify=True, cert=None):
        ''' Initializes the attributes of the ScoutClient object.
            - Args:
                - hostname(str): the IP address associated with the Scout instance
                - verify(path to a CA bundle or Boolean): controls whether we verify the server’s TLS certificate
                    - Note that verify=False makes your application vulnerable to man-in-the-middle (MitM) attacks
                    - Defaults to True
                - cert(.pem file or a tuple with ('cert', 'key') pair): a local cert to use as client side certificate 
                    - Note that the private key to your local certificate must be unencrypted because Requests does not support using encrypted keys. 
                    - Defaults to None
                - For additional configurations, use the member Session object "_session" in accordance with Requests library
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
        '''
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

    def authenticate_with_password(self, username=None, password=None):
        ''' Authorizes the client with username and password. Must call before using other client functions.
            If username and password are not provided, the function obtains credentials from 
            either environment variables or terminal inputs. 
            - Args:
                - username(str): the username for the Scout instance
                - password(str): the password for the Scout instance
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
            - Returns:
                - requests.Response(Response object): the response associated with the login request
        '''
        if username and password:
            username = username
            password = password
        else:
            input_user, input_pass = get_credentials()
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

    def get_resource(self, path, **kwargs):
        ''' Base function for getting a resource in /api/v0/ 
            - Args:
                - path(str): the path appended to /api/v0/
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        '''
        if not self._is_authenticated:
            raise UnauthenticatedScoutClientError()
        return self._session.get(f'https://{self._hostname}/api/v0/{path}/', **kwargs)

    def post_resource(self, path, **kwargs):
        ''' Base function for posting a resource in /api/v0/ 
            - Args:
                - path(str): the path appended to /api/v0/
                - kwargs(**): a variable number of keyword arguments for the post request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - The response associated with the the post request
        '''
        if not self._is_authenticated and path != "login":
            raise UnauthenticatedScoutClientError()
        return self._session.post(f'https://{self._hostname}/api/v0/{path}', **kwargs)

    def delete_resource(self, path, **kwargs):
        ''' Base function for deleting a resource in /api/v0/ 
            - Args:
                - path(str): the path appended to /api/v0/
                - kwargs(**): a variable number of keyword arguments for the delete request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - The response associated with the the delete request
        '''
        if not self._is_authenticated:
            raise UnauthenticatedScoutClientError()
        return self._session.delete(f'https://{self._hostname}/api/v0/{path}', **kwargs)

    def get_scout_version(self, **kwargs):
        """ Retrieves info about a scout . 
            - Args:
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource("version", **kwargs)

    def get_scout_system_time(self, **kwargs):
        """ Returns scout's current system time. 
            - Args:
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource("settings/system-time", **kwargs)

    def get_robots(self, **kwargs):
        """ Returns robots on the specified scout instance. 
            - Args:
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource("robots", **kwargs)

    def get_robot_by_hostname(self, hostname, **kwargs):
        """ Returns a robot on given a hostname of a specific robot. 
            - Args:
                - hostname(str): the IP address associated with the desired robot on the Scout instance
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource(f'robots/{hostname}', **kwargs)

    def get_site_walks(self, **kwargs):
        """ Returns site walks on the specified scout instance
            - Args:
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource("site_walks", **kwargs)

    def get_site_walk_by_id(self, uuid):
        """ Given a site walk uuid, returns a site walk on the specified scout instance
            - Args:
                - uuid(str): the ID associated with the site walk 
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource(f'site_walks/{uuid}')

    def get_site_elements(self, **kwargs):
        """ Returns site elements on the specified scout instance
            - Args:
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource("site_elements", **kwargs)

    def get_site_element_by_id(self, uuid, **kwargs):
        """ Given a site element uuid, returns a site element on the specified scout instance
            - Args:
                - uuid(str): the ID associated with the site element
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource(f'site_elements/{uuid}', **kwargs)

    def get_site_docks(self, **kwargs):
        """ Returns site docks on the specified scout instance
            - Args:
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource("site_docks", **kwargs)

    def get_site_dock_by_id(self, uuid, **kwargs):
        """ Given a site dock uuid, returns a site dock on the specified scout instance
            - Args:
                - uuid(str): the ID associated with the site dock
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource(f'site_docks/{uuid}', **kwargs)

    def get_calendar(self, **kwargs):
        """ Returns calendar events on the specified scout instance
            - Args:
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource("calendar/schedule", **kwargs)

    def get_run_events(self, **kwargs):
        """ Given a dictionary of query params, returns run events 
            - Args:
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource("run_events", **kwargs)

    def get_run_event_by_id(self, uuid, **kwargs):
        """ Given a runEventUuid, returns a run event 
            - Args:
                - uuid(str): the ID associated with the run event
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource(f'run_events/{uuid}', **kwargs)

    def get_run_captures(self, **kwargs):
        """ Given a dictionary of query params, returns run captures 
            - Args:
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource("run_captures", **kwargs)

    def get_run_capture_by_id(self, uuid, **kwargs):
        """ Given a runCaptureUuid, returns a run capture 
            - Args:
                - uuid(str): the ID associated with the run capture
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource(f'run_captures/{uuid}', **kwargs)

    def get_runs(self, **kwargs):
        """ Given a dictionary of query params, returns runs 
            - Args:
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource("runs", **kwargs)

    def get_run_by_id(self, uuid, **kwargs):
        """ Given a runUuid, returns a run 
            - Args:
                - uuid(str): the ID associated with the run
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource(f'runs/{uuid}', **kwargs)

    def get_run_archives_by_id(self, uuid, **kwargs):
        """ Given a runUuid, returns run archives 
            - Args:
                - uuid(str): the ID associated with the run
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the get request
        """
        return self.get_resource(f'run_archives/{uuid}', **kwargs)

    def get_image(self, url, **kwargs):
        """ Given a data capture url, returns a raw image 
            - Args:
                - url(str): the url associated with the data capture
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response: the raw response associated with the the get request
        """
        if not self._is_authenticated:
            raise UnauthenticatedScoutClientError()
        response = self._session.get(url, stream=True, **kwargs)
        response.raw.decode_content = True
        return response.raw

    def post_export_as_walk(self, site_walk_uuid, **kwargs):
        """ Given a site walk uuid, it exports the walks_pb2.Walk equivalent
            - Args:
                - uuid(str): the ID associated with the site walk 
                - kwargs(**): a variable number of keyword arguments for the get request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError: indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the post request
        """
        return self.post_resource(f'site_walks/export_as_walk/{site_walk_uuid}', **kwargs)

    def post_import_from_walk(self, **kwargs):
        """ Given a walk data, imports it to the specified scout instance
            - Args:
                - kwargs(**): a variable number of keyword arguments for the post request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the post request
        """
        return self.post_resource("site_walks/import_from_walk", **kwargs)

    def post_site_element(self, **kwargs):
        """ Create a site element 
            - Args:
                - kwargs(**): a variable number of keyword arguments for the post request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the post request
        """
        return self.post_resource("site_elements", **kwargs)

    def post_site_walk(self, **kwargs):
        """ Create a site walk 
            - Args:
                - kwargs(**): a variable number of keyword arguments for the post request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the post request
        """
        return self.post_resource("site_walks", **kwargs)

    def post_site_dock(self, **kwargs):
        """ Create a site element 
            - Args:
                - kwargs(**): a variable number of keyword arguments for the post request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the post request
        """
        return self.post_resource("site_docks", **kwargs)

    def post_robot(self, **kwargs):
        """ Add a robot to the specified scout instance
            - Args:
                - kwargs(**): a variable number of keyword arguments for the post request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the post request
        """
        return self.post_resource("robots", **kwargs)

    def post_calendar_event(self, **kwargs):
        """ Create a calendar event to play a mission
            - Args:
                - kwargs(**): a variable number of keyword arguments for the post request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the post request
        """
        return self.post_resource("calendar/set", **kwargs)

    def delete_site_walk(self, uuid, **kwargs):
        """ Given a site walk uuid, deletes the site walk associated with the uuid on the specified scout instance
            - Args:
                - uuid(str): the ID associated with the desired site walk
                - kwargs(**): a variable number of keyword arguments for the delete request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the delete request
        """
        return self.delete_resource(f'site_walks/{uuid}', **kwargs)

    def delete_robot(self, robotHostname, **kwargs):
        """ Given a robotHostname, deletes the robot associated with the hostname on the specified scout instance
            - Args:
                - hostname(str): the IP address associated with the robot
                - kwargs(**): a variable number of keyword arguments for the delete request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the delete request
        """
        return self.delete_resource(f'robots/{robotHostname}', **kwargs)

    def delete_calendar_event(self, **kwargs):
        """ Delete the specified calendar event on the specified scout instance
            - Args:
                - kwargs(**): a variable number of keyword arguments for the delete request
            - Raises:
                - RequestExceptions: exceptions thrown by the Requests library 
                - UnauthenticatedScoutClientError:  indicates that the scout client is not authenticated properly
            - Returns 
                - requests.Response(Response object): the response associated with the the delete request
        """
        return self.post_resource('calendar/delete', **kwargs)
