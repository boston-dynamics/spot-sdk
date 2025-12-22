# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).


import enum
import ipaddress
import logging
import socket
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import requests

MAX_REDIRECTS = 3
SO_BINDTODEVICE = getattr(socket, "SO_BINDTODEVICE", 25)

_LOGGER = logging.getLogger(__name__)



class InterfaceNameNotFound(Exception):
    """Raised when a specified network interface is not present on the
    system."""

    def __init__(self, name: str):
        super().__init__(f"Interface '{name}' is not found on system.")




class BindAdapter(requests.adapters.HTTPAdapter):
    """Allows binding to a specific network interface and enforcing a custom
    Host header for HTTP."""

    def __init__(self, is_robot=True, interface=None, resolved_ip=None, assert_hostname=None,
                 force_host=None, *args, **kwargs):
        if not is_robot:
            self.interface = interface
        self.resolved_ip = resolved_ip
        self.assert_hostname = assert_hostname
        self.force_host = force_host
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        """Override the send method to enforce a custom Host header for
        HTTP."""
        if self.force_host:
            request.headers["Host"] = self.force_host
        return super().send(request, **kwargs)

    def get_connection_with_tls_context(self, request, verify, proxies=None, cert=None):
        host_params, pool_kwargs = super().build_connection_pool_key_attributes(
            request, verify, cert)

        if self.resolved_ip:
            host_params["host"] = self.resolved_ip
        else:
            raise ValueError("BindAdapter requires a resolved IP address to connect to.")

        if host_params.get("scheme") == "https":
            vanity = self.assert_hostname or (urlparse(request.url).hostname) or self.force_host
            if vanity:
                pool_kwargs["server_hostname"] = vanity  # SNI
                pool_kwargs["assert_hostname"] = vanity  # cert hostname check

        if self.interface:
            so = pool_kwargs.get("socket_options") or []
            so.append((socket.SOL_SOCKET, SO_BINDTODEVICE, (self.interface + "\0").encode("utf-8")))
            pool_kwargs["socket_options"] = so

        conn = self.poolmanager.connection_from_host(
            host=host_params["host"],
            port=host_params.get("port"),
            scheme=host_params.get("scheme", "https"),
            pool_kwargs=pool_kwargs,
        )

        return conn


@contextmanager
def create_bound_session(is_robot=True, interface=None, resolved_ip=None, sni_hostname=None,
                         force_host=None):
    """Creates a session bound to optional interface with optional SNI
    hostname."""
    session = requests.Session()
    adapter = BindAdapter(is_robot, interface=interface, resolved_ip=resolved_ip,
                          assert_hostname=sni_hostname, force_host=force_host)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    try:
        yield session
    finally:
        session.close()




def validate_url(url):
    """Checks if any IP address resolved from a URL is in the blacklist. First
    checks if the hostname is already a valid IP address.

    Args:
        url: The URL to check.

    Returns:
        A Tuple, where the first value is whether or not the given url was valid.
            If True, the second value is a dict containing the url and hostname,
            if False, the second value is an error statement of what went wrong.
    """
    try:
        # The URL here could be a vanity name or IP address (IPv4 or IPv6), with or without a port, e.g., example.com, example.com:1234, 1.1.1.1, 1.1.1.1:1234, [::ffff:101:101], or [::ffff:101:101]:1234.
        parsed_url = urlparse(url)
        ret = {"parsed_url": parsed_url}

        try:
            # This try block is for the case where the host is an explicit IP address, e.g., 1.1.1.1 or [::ffff:101:101].
            ip_address = ipaddress.ip_address(parsed_url.hostname)
            # NOTE: this isn't actually a resolved IP, it's just the IP we were given.
            ret["resolved_ip"] = str(ip_address)
            return (True, ret)
        except ValueError:
            pass

        try:
            # This try block is for the case where the host is a vanity name, e.g., example.com. Note that this can resolve to either an IPv4 or IPv6 address.
            ip_address = socket.getaddrinfo(parsed_url.hostname, port=parsed_url.port)[0][4][0]
            ret["resolved_ip"] = str(ip_address)
            return (True, ret)
        except Exception as e:
            status = f"No IP addresses resolved for URL: {url}"
            _LOGGER.error(f"validate_url exception: {e}\nstatus: {status}")
            return (False, status)
    except ValueError:
        return (False, f"Invalid URL format: {url}")


def safe_api_call(method, url, sni_hostname, timeout, is_robot=True, interface=None,
                  **request_data):
    """Make an API call to a URL, validating the URL and checking for
    redirects. Will attempt to bind the provided network interface.

    Args:
        method (str): method for HTTP request to use
        url (str): URL to make the request to
        sni_hostname (str): Hostname to assert for the Request
        timeout (float): Timeout for the request
        interface (str, optional): Network interface to bind all HTTP calls to, use ("WIFI", "LTE", "ETHERNET"). Will override default interface if provided, currently set to WIFI = "wlp5s0".

    Returns:
        Tuple[Response|None, str]: A tuple containing the response object (or None) and a status message.
    """
    num_redirects = 0
    url_to_check = url
    status = ""

    # Allow only 3 redirects per API call
    while num_redirects < MAX_REDIRECTS:
        (url_valid, return_value) = validate_url(url_to_check)
        if url_valid:
            parsed_url = return_value["parsed_url"]
            resolved_ip = return_value["resolved_ip"]
            status = f"Validation of {url} successful with resolved_ip: {resolved_ip}"
            try:
                with create_bound_session(is_robot, interface, resolved_ip, sni_hostname,
                                          sni_hostname) as session:
                    # Potential argument injection through user-controlled keys and values in request_data.
                    # This is made secure by the webserver's JSON schema allowing only specifically named fields.
                    # Disable automatic redirects, so we can track the new hostname before the call is made.
                    response = session.request(method, urlunparse(parsed_url), timeout=timeout,
                                               allow_redirects=False, **request_data)

                    if 300 <= response.status_code < 400:
                        redirect_location = response.headers.get("Location")
                        url_to_check = redirect_location
                        num_redirects += 1
                        continue
                    else:
                        return response, status
            except requests.exceptions.RequestException as e:
                if isinstance(e, requests.exceptions.SSLError):
                    status = "SSL error occurred. Please upload server SSL certificate to robot."
                elif isinstance(e, requests.exceptions.ConnectTimeout):
                    status = "Connection to server timed out. Check firewall, network, route, server, etc."
                elif isinstance(e, requests.exceptions.ReadTimeout):
                    status = "Connected to server, but server did not respond in time. Check server logs."
                elif isinstance(e, requests.exceptions.URLRequired):
                    status = "URL is required for request."
                elif isinstance(e, requests.exceptions.TooManyRedirects):
                    status = "Too many redirects when accessing server."
                elif isinstance(e, requests.exceptions.MissingSchema):
                    status = "URL is missing schema (http or https)."
                elif isinstance(e, requests.exceptions.InvalidSchema):
                    status = "URL has invalid schema (http and https are supported)."
                elif isinstance(e, requests.exceptions.InvalidURL):
                    status = "Invalid URL for request."
                elif isinstance(e, requests.exceptions.InvalidHeader):
                    status = "Invalid header(s) in request."
                # This catches all other RequestException types, which are not expected to occur. But, if they do, telling the user what type of exception occurred may help them resolve the problem on their own.
                else:
                    status = f"Unknown RequestException of type {e.__class__.__name__} occurred."
                _LOGGER.error(f"safe_api_call exception: {e}\nstatus: {status}")
            except InterfaceNameNotFound as e:
                status = "Check route in config file. Only WIFI, LTE, and ETHERNET are supported."
                _LOGGER.error(f"safe_api_call exception: {e}\nstatus: {status}")
            except Exception as e:
                status = (f"Unknown exception of type {e.__class__.__name__} occurred.")
                _LOGGER.error(f"safe_api_call exception: {e}\nstatus: {status}")
        else:
            status = f"{return_value}"
        return None, status

    # Don't expect to get here, but if it does there was a problem
    status = f"Max redirects reached on url {url}"
    return None, status
