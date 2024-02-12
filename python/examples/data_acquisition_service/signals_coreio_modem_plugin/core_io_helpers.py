# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

from http import HTTPStatus

import requests

COREIO_PORT = "21443"


class CoreIOHelper:
    """Handles login process and provides a helper for obtaining LTE data from the Spot CORE I/O's modem."""

    def __init__(self, hostname, username, password, logger):
        self.base_url = f'https://{hostname}:{COREIO_PORT}'
        self.username = username
        self.password = password
        self.logger = logger
        self.auth_cookies = None
        self._is_authenticated = False

    def login(self):
        """Gets cookies and use them in authorization request."""
        init_response = requests.get(self.base_url, verify=False)
        self.auth_cookies = requests.utils.dict_from_cookiejar(init_response.cookies)
        login_response_json = requests.post(
            f'{self.base_url}/api/v0/login', data={
                'username': self.username,
                'password': self.password
            }, verify=False, headers={
                'x-csrf-token': self.auth_cookies['x-csrf-token']
            }, cookies=self.auth_cookies).json()
        if 'error' in login_response_json:
            self._is_authenticated = False
            self.logger.error(login_response_json['error'])
            return False
        else:
            self._is_authenticated = True
            self.logger.info("CORE I/O login success")
            return True

    def get_modem_stats(self):
        if self._is_authenticated is False:
            return {}
        # Warning: This API endpoint request can sometimes take >1 second.
        modem_url = f'{self.base_url}/api/v0/modemStats'
        modem_response = requests.get(modem_url, cookies=self.auth_cookies, verify=False)
        modem_stats_json = modem_response.json()
        if not modem_response.ok:
            if modem_response.status_code == HTTPStatus.UNAUTHORIZED:
                # Try to log in again.
                self.login()
            modem_response.raise_for_status()
        return modem_stats_json
