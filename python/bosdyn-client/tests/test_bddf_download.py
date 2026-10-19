# Copyright (c) 2023 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Tests for bosdyn.client.bddf_download."""

import io
import ssl
from unittest import mock

from bosdyn.client import bddf_download


class _FakeResponse(io.BytesIO):
    status = 200
    headers = {'Content-Disposition': 'attachment; filename="capture.bddf"'}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def test_download_data_uses_verifying_tls_context(tmp_path):
    """download_data must verify the server certificate before sending the bearer token."""
    robot = mock.Mock()
    robot.user_token = "secret-bearer-token"
    output_file = tmp_path / "out.bddf"
    captured = {}

    def fake_urlopen(request, context=None, timeout=None):
        captured["auth"] = request.get_header("Authorization")
        captured["context"] = context
        captured["timeout"] = timeout
        return _FakeResponse(b"bddf-bytes")

    with mock.patch.object(bddf_download, "urlopen", side_effect=fake_urlopen):
        result = bddf_download.download_data(
            robot,
            "192.168.80.3",
            start_nsec=1_000_000_000,
            end_nsec=2_000_000_000,
            output_filename=str(output_file),
            robot_time=True,
        )

    assert result == str(output_file)
    assert output_file.read_bytes() == b"bddf-bytes"
    assert captured["auth"] == "Bearer secret-bearer-token"
    assert isinstance(captured["context"], ssl.SSLContext)
    assert captured["context"].verify_mode == ssl.CERT_REQUIRED
    assert captured["context"].check_hostname is True
