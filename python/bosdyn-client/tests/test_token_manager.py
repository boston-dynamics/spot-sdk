"""Unit tests for the token_manager module."""
import datetime
import pytest
import time

from bosdyn.client.exceptions import Error
from bosdyn.client.token_manager import TokenManager
from bosdyn.client.util import cli_login_prompt, cli_auth

class MockRobot:
    def __init__(self, token=None):
        self.user_token = token
        self.address = 'mock-address'

    def authenticate(self, username, password):
        if not (username == 'user' and password == 'password'):
            raise Error('mock exception')

        self.user_token = 'mock-token-auth'

    def authenticate_with_token(self, token):
        self.user_token = 'mock-token-refresh'

def test_token_refresh():
    robot = MockRobot(token='mock-token-default')

    assert robot.user_token == 'mock-token-default'

    local = datetime.datetime.now() + datetime.timedelta(hours=-2)
    tm = TokenManager(robot, timestamp=local)

    time.sleep(0.1)
    assert robot.user_token == 'mock-token-refresh'

    tm.stop()

def test_cli_login(monkeypatch):
    real_login = ('user', 'password')
    monkeypatch.setattr('six.moves.input', lambda _: real_login[0])
    monkeypatch.setattr('getpass.getpass', lambda: real_login[1])
    login = cli_login_prompt()
    assert login == real_login

def test_cli_login_with_username(monkeypatch):
    real_login = ('bad_user', 'bad_password')
    monkeypatch.setattr('six.moves.input', lambda _: real_login[0])
    monkeypatch.setattr('getpass.getpass', lambda: real_login[1])
    login = cli_login_prompt('mock-user')
    assert login == real_login

def test_cli_login_with_password(monkeypatch):
    real_login = ('bad_user', 'good_password')
    monkeypatch.setattr('six.moves.input', lambda _: real_login[0])
    monkeypatch.setattr('getpass.getpass', lambda: 'bad_password')
    login = cli_login_prompt('mock-user', real_login[1])
    assert login == real_login

def test_cli_authentication(monkeypatch):
    robot = MockRobot(token='mock-token-default')

    monkeypatch.setattr('six.moves.input', lambda _: 'user')
    monkeypatch.setattr('getpass.getpass', lambda: 'password')
    cli_auth(robot)

    assert robot.user_token == 'mock-token-auth'

