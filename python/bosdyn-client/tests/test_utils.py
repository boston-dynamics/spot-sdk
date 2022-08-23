# Copyright (c) 2022 Boston Dynamics, Inc.  All rights reserved.
#
# Downloading, reproducing, distributing or otherwise using the SDK Software
# is subject to the terms and conditions of the Boston Dynamics Software
# Development Kit License (20191101-BDSDK-SL).

"""Unit tests for the server_utils module."""
import datetime
import time

import pytest

from bosdyn.api import data_acquisition_store_pb2 as daq_store
from bosdyn.api import local_grid_pb2 as grid
from bosdyn.client.server_util import populate_response_header, strip_large_bytes_fields


def test_strip_large_bytes():
    req = daq_store.StoreImageRequest()
    temp_data = bytes("mybytes", 'utf-8')
    req.image.image.data = temp_data
    req.image.image.cols = 21
    assert len(req.image.image.data) > 0
    assert req.image.image.cols == 21

    stripped_req = strip_large_bytes_fields(req)

    # Check the stripped request.
    assert len(req.image.image.data) == 0
    assert req.image.image.cols == 21


def test_strip_large_bytes_repeated_msg():
    req = grid.GetLocalGridsResponse()
    grid1 = grid.LocalGridResponse()
    grid1.local_grid.data = bytes("mybytes", 'utf-8')
    grid1.local_grid.frame_name_local_grid_data = "my_frame"
    grid2 = grid.LocalGridResponse()
    grid2.local_grid.data = bytes("mybytes", 'utf-8')
    grid2.local_grid.frame_name_local_grid_data = "my_frame"
    req.local_grid_responses.extend([grid1, grid2])

    for g in req.local_grid_responses:
        assert len(g.local_grid.data) > 0
        assert g.local_grid.frame_name_local_grid_data == "my_frame"

    strip_large_bytes_fields(req)

    # Check the stripped request.
    for g in req.local_grid_responses:
        assert len(g.local_grid.data) == 0
        assert g.local_grid.frame_name_local_grid_data == "my_frame"


def test_stripped_headers():
    request = daq_store.StoreImageRequest()
    request.header.client_name = "my_client"
    request.image.image.data = bytes("mybytes", 'utf-8')
    request.image.image.cols = 21
    response = daq_store.StoreImageResponse()

    populate_response_header(response, request)

    assert response.header.request_header.client_name == "my_client"
    req_unpacked = daq_store.StoreImageRequest()
    response.header.request.Unpack(req_unpacked)
    assert req_unpacked.image.image.cols == 21
    assert len(req_unpacked.image.image.data) == 0
    # check that the original request is unchanged.
    assert len(request.image.image.data) > 0
