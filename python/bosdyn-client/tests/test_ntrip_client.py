# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tests for bosdyn.client.gps.ntrip_client."""

from unittest import mock

from bosdyn.client.gps.ntrip_client import (
    DEFAULT_NTRIP_PORT,
    DEFAULT_NTRIP_TLS_PORT,
    NtripClient,
    NtripClientParams,
)


def test_ntrip_client_params_defaults_to_tls():
    """NtripClientParams should default to TLS transport and the standard TLS port."""
    params = NtripClientParams(server="caster.example.com", user="u", password="p")
    assert params.tls is True
    assert params.port == DEFAULT_NTRIP_TLS_PORT


def test_ntrip_client_params_plaintext_opt_in_selects_plaintext_port():
    """Explicitly opting into tls=False without a port should select DEFAULT_NTRIP_PORT."""
    params = NtripClientParams(server="caster.example.com", tls=False)
    assert params.tls is False
    assert params.port == DEFAULT_NTRIP_PORT


def test_ntrip_client_params_preserves_explicit_port():
    """An explicit port argument must be preserved regardless of the tls flag."""
    params_tls = NtripClientParams(server="caster.example.com", port=9999, tls=True)
    params_plain = NtripClientParams(server="caster.example.com", port=8888, tls=False)
    assert params_tls.port == 9999
    assert params_plain.port == 8888


def test_create_icy_session_wraps_socket_with_tls_by_default():
    """Default NtripClient parameters must wrap the TCP socket in a verified TLS context."""
    device = mock.Mock()
    logger = mock.Mock()
    params = NtripClientParams(
        server="caster.example.com", user="spot", password="secret", mountpoint="RTCM3"
    )
    client = NtripClient(device, params, logger)

    raw_sock = mock.Mock()
    tls_sock = mock.Mock()
    tls_sock.recv.return_value = b"ICY 200 OK\r\n\r\nrtcm-payload"

    fake_ctx = mock.Mock()
    fake_ctx.wrap_socket.return_value = tls_sock

    with mock.patch("bosdyn.client.gps.ntrip_client.socket.socket", return_value=raw_sock), \
         mock.patch("bosdyn.client.gps.ntrip_client.ssl.create_default_context", return_value=fake_ctx):
        assert client.create_icy_session() is True

    fake_ctx.wrap_socket.assert_called_once_with(raw_sock, server_hostname="caster.example.com")
    tls_sock.connect.assert_called_once_with(("caster.example.com", DEFAULT_NTRIP_TLS_PORT))
    device.write.assert_called_once_with(b"rtcm-payload")
